"""Terminal output handler for YaraBench."""

from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from .base import OutputHandler
from ..models import BenchmarkResult, RuleResult

console = Console()


class TerminalOutput(OutputHandler):
    """Terminal output handler that displays results in the console."""
    
    def write(self, results: List[BenchmarkResult]) -> None:
        """Write benchmark results to terminal.
        
        Args:
            results: List of benchmark results to write
        """
        if not results:
            console.print("[yellow]No results to display[/yellow]")
            return
        
        # Display summary table
        self._show_summary(results)
        
        # Display detailed results for each model
        for result in results:
            self._show_model_details(result)
    
    def _show_summary(self, results: List[BenchmarkResult]) -> None:
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
    
    def _show_model_details(self, result: BenchmarkResult) -> None:
        """Show detailed results for a specific model."""
        console.print(f"\n[bold cyan]Detailed Results for {result.model}[/bold cyan]")
        
        # Create detailed table
        table = Table(title=f"Results for {result.model}")
        table.add_column("Challenge ID", style="dim")
        table.add_column("Valid", justify="center")
        table.add_column("Score", justify="right")
        table.add_column("Latency (ms)", justify="right")
        table.add_column("Error", style="red")
        
        for rule_result in result.results:
            valid_status = "✅" if rule_result.valid_syntax else "❌"
            error_text = rule_result.error or ""
            
            table.add_row(
                rule_result.challenge_id,
                valid_status,
                f"{rule_result.score:.2f}",
                f"{rule_result.latency_ms:.1f}",
                error_text
            )
        
        console.print(table)
        
        # Show statistics
        stats_text = Text()
        stats_text.append(f"Total Challenges: {result.total_challenges}\n", style="white")
        stats_text.append(f"Successful: {result.successful_challenges}\n", style="green")
        if result.total_challenges > 0:
            stats_text.append(f"Success Rate: {result.successful_challenges/result.total_challenges*100:.1f}%\n", style="blue")
        else:
            stats_text.append("Success Rate: N/A\n", style="blue")
        stats_text.append(f"Average Score: {result.average_score:.2f}\n", style="yellow")
        stats_text.append(f"Total Time: {result.total_time_ms/1000:.1f}s", style="magenta")
        
        console.print(Panel(stats_text, title="Statistics")) 