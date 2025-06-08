"""Test data models."""

import pytest
import base64
from src.models import Challenge, TestFile, ChallengeLevel, ModelConfig, Config


def test_test_file_creation():
    """Test TestFile model creation and validation."""
    test_file = TestFile(
        name="test.exe",
        content_b64=base64.b64encode(b"test content").decode(),
        should_match=True
    )
    
    assert test_file.name == "test.exe"
    assert test_file.should_match is True
    assert base64.b64decode(test_file.content_b64) == b"test content"


def test_challenge_creation():
    """Test Challenge model creation."""
    test_files = [
        TestFile(
            name="malware.exe",
            content_b64=base64.b64encode(b"malicious content").decode(),
            should_match=True
        ),
        TestFile(
            name="benign.exe", 
            content_b64=base64.b64encode(b"benign content").decode(),
            should_match=False
        )
    ]
    
    challenge = Challenge(
        id="test_001",
        level=ChallengeLevel.LEVEL1,
        actionable=True,
        description="Test challenge description",
        expected_strings=["malicious", "content"],
        expected_keywords=["pe"],
        test_files=test_files
    )
    
    assert challenge.id == "test_001"
    assert challenge.level == ChallengeLevel.LEVEL1
    assert challenge.actionable is True
    assert len(challenge.test_files) == 2
    assert len(challenge.expected_strings) == 2


def test_model_config():
    """Test ModelConfig creation."""
    config = ModelConfig(
        name="test-model",
        api_key="test-key",
        base_url="https://api.test.com"
    )
    
    assert config.name == "test-model"
    assert config.api_key == "test-key"
    assert str(config.base_url) == "https://api.test.com/"


def test_config_creation():
    """Test main Config model."""
    model_configs = [
        ModelConfig(name="model1", api_key="key1"),
        ModelConfig(name="model2", api_key="key2")
    ]
    
    config = Config(
        models=model_configs,
        levels=["level1", "level2"],
        output_format="json",
        synthetic_count=5
    )
    
    assert len(config.models) == 2
    assert config.levels == ["level1", "level2"]
    assert config.output_format == "json"
    assert config.synthetic_count == 5