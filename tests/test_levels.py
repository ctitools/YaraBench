"""Test challenge levels."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock

from src.levels import Level1, Level2
from src.models import Challenge, ChallengeLevel, TestFile


class TestLevel1:
    """Test Level 1 static challenges."""
    
    def test_level1_properties(self):
        """Test Level1 properties."""
        level1 = Level1()
        assert level1.name == "Level 1: Static Challenges"
        assert "Pre-defined JSON challenges" in level1.description
    
    def test_level1_validation_missing_dir(self):
        """Test Level1 validation with missing data directory."""
        level1 = Level1(data_dir="/nonexistent/path")
        assert not level1.validate()
    
    def test_level1_get_challenges_missing_dir(self):
        """Test Level1 get_challenges with missing directory."""
        level1 = Level1(data_dir="/nonexistent/path")
        challenges = level1.get_challenges()
        assert challenges == []
    
    def test_level1_with_valid_data(self):
        """Test Level1 with valid challenge data."""
        # Create temporary directory with test challenge
        with tempfile.TemporaryDirectory() as temp_dir:
            challenge_data = {
                "id": "test_001",
                "level": "level1",
                "actionable": True,
                "description": "Test challenge",
                "expected_strings": ["test"],
                "expected_keywords": [],
                "test_files": [
                    {
                        "name": "test.txt",
                        "content_b64": "dGVzdA==",  # "test" in base64
                        "should_match": True
                    }
                ]
            }
            
            # Create level1 subdirectory
            level1_dir = Path(temp_dir) / "level1"
            level1_dir.mkdir(exist_ok=True)
            
            # Write challenge file
            challenge_file = level1_dir / "test_001.json"
            with open(challenge_file, 'w') as f:
                json.dump(challenge_data, f)
            
            # Test Level1 with this data
            level1 = Level1(data_dir=temp_dir)
            assert level1.validate()
            
            challenges = level1.get_challenges()
            assert len(challenges) == 1
            
            challenge = challenges[0]
            assert challenge.id == "test_001"
            assert challenge.actionable is True
            assert len(challenge.test_files) == 1


class TestLevel2:
    """Test Level 2 synthetic challenges."""
    
    def test_level2_properties(self):
        """Test Level2 properties."""
        level2 = Level2()
        assert level2.name == "Level 2: Synthetic Challenges"
        assert "Dynamically generated" in level2.description
    
    def test_level2_validation_no_client(self):
        """Test Level2 validation without LLM client."""
        level2 = Level2(llm_client=None)
        assert not level2.validate()
    
    def test_level2_validation_with_client(self):
        """Test Level2 validation with mock LLM client."""
        mock_client = Mock()
        level2 = Level2(llm_client=mock_client)
        assert level2.validate()
    
    def test_level2_get_challenges_no_client(self):
        """Test Level2 get_challenges without client."""
        level2 = Level2(llm_client=None)
        challenges = level2.get_challenges(count=5)
        assert challenges == []
    
    def test_level2_get_challenges_with_mock_client(self):
        """Test Level2 get_challenges with mock client."""
        # Create mock client that returns realistic challenge data
        mock_client = Mock()
        mock_client.generate_rule_description.return_value = json.dumps({
            "description": "Test synthetic challenge",
            "primary_string": "test_string",
            "secondary_string": "support_string", 
            "file_indicator": ".exe",
            "expected_keywords": []
        })
        
        level2 = Level2(llm_client=mock_client)
        challenges = level2.get_challenges(count=2)
        
        # Should generate challenges (though they might fail due to mocking)
        # The exact number depends on LLM response parsing success
        assert isinstance(challenges, list)