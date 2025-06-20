"""Base output handler for YaraBench."""

from abc import ABC, abstractmethod
from typing import List
from ..models import BenchmarkResult


class OutputHandler(ABC):
    """Base class for output handlers."""
    
    @abstractmethod
    def write(self, results: List[BenchmarkResult]) -> None:
        """Write benchmark results to output.
        
        Args:
            results: List of benchmark results to write
        """
        pass 