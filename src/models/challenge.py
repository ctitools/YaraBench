"""Challenge data models for YaraBench."""

from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ChallengeLevel(str, Enum):
    """Challenge difficulty levels."""
    LEVEL1 = "level1"
    LEVEL2 = "level2"
    LEVEL3 = "level3"


class TestFile(BaseModel):
    """A test file for evaluating YARA rules."""
    name: str = Field(..., description="Filename for display")
    content_b64: str = Field(..., description="Base64-encoded file content")
    should_match: bool = Field(..., description="Whether the YARA rule should match this file")
    metadata: Dict[str, str] = Field(default_factory=dict, description="Additional metadata")


class Challenge(BaseModel):
    """A YARA rule generation challenge."""
    id: str = Field(..., description="Unique challenge identifier")
    level: ChallengeLevel = Field(..., description="Challenge difficulty level")
    actionable: bool = Field(..., description="Whether the challenge is solvable by a YARA rule")
    description: str = Field(..., description="Natural language description of what to detect")
    expected_strings: List[str] = Field(
        default_factory=list,
        description="Strings that should appear in the generated rule"
    )
    expected_keywords: List[str] = Field(
        default_factory=list,
        description="YARA keywords that should be used (pe, filesize, etc.)"
    )
    test_files: List[TestFile] = Field(
        default_factory=list,
        description="Files to test the generated rule against"
    )
    metadata: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional challenge metadata"
    )
    
    class Config:
        """Pydantic config."""
        use_enum_values = True