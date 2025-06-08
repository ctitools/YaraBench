"""Main benchmark orchestrator."""

import time
from typing import List, Dict, Any
from datetime import datetime

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from .models import Config, Challenge, RuleResult, BenchmarkResult
from .levels import Level1, Level2, Level3
from .llm import LLMClient
from .parsing import YaraExtractor
from .evaluation import YaraValidator, FileMatcher, LLMJudge
from .output import TerminalOutput, JSONOutput, CSVOutput

console = Console()


class Benchmark:
    """Main benchmark orchestrator."""
    
    def __init__(self, config: Config):
        """Initialize the benchmark.
        
        Args:
            config: Benchmark configuration
        """
        self.config = config
        self.llm_clients = {
            model.name: LLMClient(model) for model in config.models
        }
        
        # Initialize challenge levels
        self.levels = self._init_levels()
        
        # Initialize evaluators
        self.evaluators = [
            YaraValidator(),
            FileMatcher()
        ]
        if config.judge_model:
            self.evaluators.append(LLMJudge(LLMClient(config.judge_model)))
        
        # Initialize output handler
        self.output_handler = self._init_output_handler()
    
    def _init_levels(self) -> Dict[str, Any]:
        """Initialize challenge levels based on config."""
        levels = {}
        
        if "level1" in self.config.levels:
            levels["level1"] = Level1()
        if "level2" in self.config.levels:
            # Level 2 needs an LLM client for synthetic generation
            # Use the first model's client for generation
            first_model = list(self.llm_clients.values())[0] if self.llm_clients else None
            levels["level2"] = Level2(llm_client=first_model)
        if "level3" in self.config.levels:
            levels["level3"] = Level3()
        
        return levels
    
    def _init_output_handler(self):
        """Initialize the appropriate output handler."""
        if self.config.output_format == "json":
            return JSONOutput(self.config.output_file)
        elif self.config.output_format == "csv":
            return CSVOutput(self.config.output_file)
        else:
            return TerminalOutput()
    
    def run(self):
        """Run the benchmark."""
        start_time = time.time()
        all_results = []
        
        # Run benchmark for each model
        for model_name, client in self.llm_clients.items():
            console.print(f"\n[bold cyan]Benchmarking {model_name}...[/bold cyan]")
            
            model_results = []
            total_challenges = 0
            successful_challenges = 0
            total_score = 0.0
            
            # Process each level
            for level_name, level in self.levels.items():
                console.print(f"\n[yellow]Processing {level_name}...[/yellow]")
                
                # Get challenges
                if level_name == "level2":
                    challenges = level.get_challenges(self.config.synthetic_count)
                else:
                    challenges = level.get_challenges()
                
                # Process challenges with progress bar
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    console=console
                ) as progress:
                    
                    task = progress.add_task(
                        f"Running {len(challenges)} challenges...",
                        total=len(challenges)
                    )
                    
                    for challenge in challenges:
                        result = self._evaluate_challenge(client, challenge)
                        model_results.append(result)
                        
                        total_challenges += 1
                        if result.valid_syntax:
                            successful_challenges += 1
                        total_score += result.score
                        
                        progress.update(task, advance=1)
            
            # Create benchmark result
            benchmark_result = BenchmarkResult(
                model=model_name,
                levels=list(self.levels.keys()),
                total_challenges=total_challenges,
                successful_challenges=successful_challenges,
                average_score=total_score / total_challenges if total_challenges > 0 else 0.0,
                results=model_results,
                total_time_ms=(time.time() - start_time) * 1000
            )
            
            all_results.append(benchmark_result)
        
        # Output results
        self.output_handler.write(all_results)
        
        # Show summary
        if self.config.output_format == "terminal":
            self._show_summary(all_results)
    
    def _evaluate_challenge(self, client: LLMClient, challenge: Challenge) -> RuleResult:
        """Evaluate a single challenge."""
        # Generate rule
        start_time = time.time()
        
        try:
            response = client.generate_rule(challenge)
            latency_ms = (time.time() - start_time) * 1000
            
            # Extract YARA rule
            rule = YaraExtractor.extract_single_rule(response)
            
            # If not actionable and no rule returned, that's correct
            if not challenge.actionable and not rule:
                return RuleResult(
                    challenge_id=challenge.id,
                    model=client.model_config.name,
                    generated_rule=None,
                    generated_response=response,
                    valid_syntax=True,  # No rule is valid for non-actionable
                    score=1.0,
                    latency_ms=latency_ms
                )
            
            # If actionable but no rule, that's a failure
            if challenge.actionable and not rule:
                return RuleResult(
                    challenge_id=challenge.id,
                    model=client.model_config.name,
                    generated_rule=None,
                    generated_response=response,
                    valid_syntax=False,
                    score=0.0,
                    error="No valid YARA rule extracted",
                    latency_ms=latency_ms
                )
            
            # Evaluate the rule
            eval_results = {}
            for evaluator in self.evaluators:
                eval_results.update(evaluator.evaluate(challenge, rule))
            
            # Calculate score
            score = self._calculate_score(challenge, rule, eval_results)
            
            return RuleResult(
                challenge_id=challenge.id,
                model=client.model_config.name,
                generated_rule=rule,
                generated_response=response,
                valid_syntax=eval_results.get("valid_syntax", False),
                execution_results=eval_results.get("execution_results", {}),
                expected_strings_found=eval_results.get("expected_strings_found", []),
                expected_keywords_found=eval_results.get("expected_keywords_found", []),
                score=score,
                error=eval_results.get("error"),
                latency_ms=latency_ms,
                llm_judge_score=eval_results.get("llm_judge_score"),
                llm_judge_feedback=eval_results.get("llm_judge_feedback"),
                llm_judge_details=eval_results.get("llm_judge_details")
            )
            
        except Exception as e:
            return RuleResult(
                challenge_id=challenge.id,
                model=client.model_config.name,
                generated_rule=None,
                generated_response="",
                valid_syntax=False,
                score=0.0,
                error=str(e),
                latency_ms=(time.time() - start_time) * 1000
            )
    
    def _calculate_score(self, challenge: Challenge, rule: str, eval_results: Dict[str, Any]) -> float:
        """Calculate composite score for a rule."""
        # Base score components
        syntax_score = 1.0 if eval_results.get("valid_syntax", False) else 0.0
        
        # Feature coverage score
        expected_strings = len(challenge.expected_strings)
        found_strings = len(eval_results.get("expected_strings_found", []))
        string_score = found_strings / expected_strings if expected_strings > 0 else 1.0
        
        expected_keywords = len(challenge.expected_keywords)
        found_keywords = len(eval_results.get("expected_keywords_found", []))
        keyword_score = found_keywords / expected_keywords if expected_keywords > 0 else 1.0
        
        # File matching score
        execution_results = eval_results.get("execution_results", {})
        if execution_results:
            correct_matches = sum(
                1 for test_file in challenge.test_files
                if execution_results.get(test_file.name, False) == test_file.should_match
            )
            match_score = correct_matches / len(challenge.test_files)
        else:
            match_score = 0.0
        
        # Check if LLM judge score is available
        llm_judge_score = eval_results.get("llm_judge_score", None)
        
        if llm_judge_score is not None:
            # Weight the scores with LLM judge
            weights = {
                "syntax": 0.2,
                "strings": 0.15,
                "keywords": 0.1,
                "matches": 0.35,
                "judge": 0.2
            }
            
            final_score = (
                weights["syntax"] * syntax_score +
                weights["strings"] * string_score +
                weights["keywords"] * keyword_score +
                weights["matches"] * match_score +
                weights["judge"] * llm_judge_score
            )
        else:
            # Weight the scores without LLM judge
            weights = {
                "syntax": 0.3,
                "strings": 0.2,
                "keywords": 0.1,
                "matches": 0.4
            }
            
            final_score = (
                weights["syntax"] * syntax_score +
                weights["strings"] * string_score +
                weights["keywords"] * keyword_score +
                weights["matches"] * match_score
            )
        
        return final_score
    
    def _show_summary(self, results: List[BenchmarkResult]):
        """Show summary table of results."""
        table = Table(title="Benchmark Summary")
        
        table.add_column("Model", style="cyan")
        table.add_column("Total", justify="right")
        table.add_column("Valid", justify="right", style="green")
        table.add_column("Score", justify="right")
        table.add_column("Time (s)", justify="right")
        
        for result in results:
            table.add_row(
                result.model,
                str(result.total_challenges),
                str(result.successful_challenges),
                f"{result.average_score:.2f}",
                f"{result.total_time_ms / 1000:.1f}"
            )
        
        console.print("\n")
        console.print(table)