"""Level 1: Static JSON challenges."""

import json
from pathlib import Path
from typing import List, Optional
import random

from ..models import Challenge
from .base import ChallengeLevel as BaseChallengeLevel


class Level1(BaseChallengeLevel):
    """Static challenge loader for Level 1."""
    
    @property
    def name(self) -> str:
        """Get the name of this challenge level."""
        return "Level 1: Static Challenges"
    
    @property
    def description(self) -> str:
        """Get a description of this challenge level."""
        return "Pre-defined JSON challenges testing specific YARA rule capabilities"
    
    def get_challenges(self, count: Optional[int] = None) -> List[Challenge]:
        """Get challenges for this level.
        
        Args:
            count: Maximum number of challenges to return (None for all)
            
        Returns:
            List of challenges
        """
        challenges = []
        challenge_dir = self.data_dir / "level1"
        
        if not challenge_dir.exists():
            return []
        
        # Load all JSON files
        for json_file in sorted(challenge_dir.glob("*.json")):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    challenge = Challenge(**data)
                    challenges.append(challenge)
            except Exception as e:
                print(f"Error loading challenge {json_file}: {e}")
                continue
        
        # Return requested number of challenges
        if count and count < len(challenges):
            return random.sample(challenges, count)
        return challenges
    
    def validate(self) -> bool:
        """Validate that this level is properly configured.
        
        Returns:
            True if valid, False otherwise
        """
        challenge_dir = self.data_dir / "level1"
        
        if not challenge_dir.exists():
            print(f"Challenge directory {challenge_dir} does not exist")
            return False
        
        # Check that we have at least one valid challenge
        json_files = list(challenge_dir.glob("*.json"))
        if not json_files:
            print(f"No JSON files found in {challenge_dir}")
            return False
        
        # Try to load each challenge
        valid_count = 0
        for json_file in json_files:
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    Challenge(**data)  # Validate with Pydantic
                    valid_count += 1
            except Exception as e:
                print(f"Invalid challenge {json_file}: {e}")
        
        return valid_count > 0