"""CSV output handler for YaraBench."""

import csv
from typing import List
from pathlib import Path

from .base import OutputHandler
from ..models import BenchmarkResult


class CSVOutput(OutputHandler):
    """CSV output handler that writes results to a CSV file."""
    
    def __init__(self, output_file: str):
        """Initialize CSV output handler.
        
        Args:
            output_file: Path to the output CSV file
        """
        self.output_file = Path(output_file)
    
    def write(self, results: List[BenchmarkResult]) -> None:
        """Write benchmark results to CSV file.
        
        Args:
            results: List of benchmark results to write
        """
        # Ensure output directory exists
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to CSV file
        with open(self.output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow([
                "model",
                "challenge_id", 
                "valid_syntax",
                "score",
                "latency_ms",
                "error",
                "llm_judge_score",
                "llm_judge_feedback"
            ])
            
            # Write data rows
            for result in results:
                for rule_result in result.results:
                    writer.writerow([
                        result.model,
                        rule_result.challenge_id,
                        rule_result.valid_syntax,
                        rule_result.score,
                        rule_result.latency_ms,
                        rule_result.error or "",
                        rule_result.llm_judge_score or "",
                        rule_result.llm_judge_feedback or ""
                    ]) 