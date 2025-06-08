"""Level 2: Synthetic challenges."""

from typing import List, Optional

from ..models import Challenge, ChallengeLevel as ChallengeLevelEnum, ModelConfig
from ..utils import SeedGenerator
from ..llm import LLMClient
from ..llm import SyntheticChallengeGenerator
from .base import ChallengeLevel as BaseChallengeLevel


class Level2(BaseChallengeLevel):
    """Synthetic challenge generator for Level 2."""
    
    def __init__(self, data_dir=None, llm_client=None):
        """Initialize Level 2 with synthetic generator.
        
        Args:
            data_dir: Data directory (not used for Level 2)
            llm_client: LLM client for challenge generation
        """
        super().__init__(data_dir)
        self.llm_client = llm_client
        self.synthetic_generator = None
        if llm_client:
            self.synthetic_generator = SyntheticChallengeGenerator(llm_client)
    
    @property
    def name(self) -> str:
        """Get the name of this challenge level."""
        return "Level 2: Synthetic Challenges"
    
    @property
    def description(self) -> str:
        """Get a description of this challenge level."""
        return "Dynamically generated challenges using LLM"
    
    def get_challenges(self, count: Optional[int] = None) -> List[Challenge]:
        """Get challenges for this level.
        
        Args:
            count: Number of challenges to generate (default: 10)
            
        Returns:
            List of challenges
        """
        if not self.synthetic_generator:
            print("No LLM client provided for Level 2 synthetic generation")
            return []
        
        challenge_count = count or 10
        return self.synthetic_generator.generate_challenges(challenge_count)
    
    def validate(self) -> bool:
        """Validate that this level is properly configured.
        
        Returns:
            True if valid, False otherwise
        """
        # Level 2 requires an LLM client for generation
        return self.llm_client is not None