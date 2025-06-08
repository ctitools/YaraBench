"""Level 3: CTI report challenges (mocked)."""

from typing import List, Optional

from ..models import Challenge
from .base import ChallengeLevel as BaseChallengeLevel


class Level3(BaseChallengeLevel):
    """CTI report challenge loader for Level 3 (currently mocked)."""
    
    @property
    def name(self) -> str:
        """Get the name of this challenge level."""
        return "Level 3: CTI Report Challenges"
    
    @property
    def description(self) -> str:
        """Get a description of this challenge level."""
        return "Full threat intelligence reports with malware samples (mocked)"
    
    def get_challenges(self, count: Optional[int] = None) -> List[Challenge]:
        """Get challenges for this level.
        
        Args:
            count: Maximum number of challenges to return
            
        Returns:
            List of challenges
        """
        # TODO: Implement CTI report challenges
        # For now, return empty list (mocked)
        return []
    
    def validate(self) -> bool:
        """Validate that this level is properly configured.
        
        Returns:
            True if valid, False otherwise
        """
        # Level 3 is mocked for now
        return True