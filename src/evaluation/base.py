"""Abstract base class for evaluators."""

from abc import ABC, abstractmethod
from typing import Dict, Any

from ..models import Challenge


class Evaluator(ABC):
    """Abstract base class for YARA rule evaluators."""
    
    @abstractmethod
    def evaluate(self, challenge: Challenge, rule: str) -> Dict[str, Any]:
        """Evaluate a YARA rule against a challenge.
        
        Args:
            challenge: The challenge to evaluate against
            rule: The YARA rule to evaluate
            
        Returns:
            Dictionary containing evaluation results
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this evaluator."""
        pass