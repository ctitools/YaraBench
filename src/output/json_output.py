"""JSON output handler for YaraBench."""

import json
from typing import List
from pathlib import Path

from .base import OutputHandler
from ..models import BenchmarkResult


class JSONOutput(OutputHandler):
    """JSON output handler that writes results to a JSON file."""
    
    def __init__(self, output_file: str):
        """Initialize JSON output handler.
        
        Args:
            output_file: Path to the output JSON file
        """
        self.output_file = Path(output_file)
    
    def write(self, results: List[BenchmarkResult]) -> None:
        """Write benchmark results to JSON file.
        
        Args:
            results: List of benchmark results to write
        """
        # Convert results to JSON-serializable format
        json_data = []
        for result in results:
            json_data.append({
                "model": result.model,
                "levels": result.levels,
                "total_challenges": result.total_challenges,
                "successful_challenges": result.successful_challenges,
                "average_score": result.average_score,
                "total_time_ms": result.total_time_ms,
                "results": [
                    {
                        "challenge_id": r.challenge_id,
                        "model": r.model,
                        "generated_rule": r.generated_rule,
                        "generated_response": r.generated_response,
                        "valid_syntax": r.valid_syntax,
                        "execution_results": r.execution_results,
                        "expected_strings_found": r.expected_strings_found,
                        "expected_keywords_found": r.expected_keywords_found,
                        "score": r.score,
                        "error": r.error,
                        "latency_ms": r.latency_ms,
                        "llm_judge_score": r.llm_judge_score,
                        "llm_judge_feedback": r.llm_judge_feedback,
                        "llm_judge_details": r.llm_judge_details
                    }
                    for r in result.results
                ]
            })
        
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to file
        with open(self.output_file, 'w') as f:
            json.dump(json_data, f, indent=2, default=str) 