"""Abstract base class for challenge levels."""

from abc import ABC, abstractmethod
from typing import List, Optional, Union
from pathlib import Path

from ..models import Challenge


class ChallengeLevel(ABC):
    """Abstract base class for challenge levels."""
    
    def __init__(self, data_dir: Optional[Union[str, Path]] = None):
        """Initialize the challenge level.
        
        Args:
            data_dir: Directory containing challenge data (str or Path)
        """
        if data_dir is None:
            self.data_dir = Path("data")
        else:
            self.data_dir = Path(data_dir)
    
    @abstractmethod
    def get_challenges(self, count: Optional[int] = None) -> List[Challenge]:
        """Get challenges for this level.
        
        Args:
            count: Maximum number of challenges to return (None for all)
            
        Returns:
            List of challenges
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate that this level is properly configured.
        
        Returns:
            True if valid, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this challenge level."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Get a description of this challenge level."""
        pass