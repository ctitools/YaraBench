"""Test synthetic challenge generation."""

import pytest
import json
from unittest.mock import Mock

from src.llm.generation import SyntheticChallengeGenerator
from src.utils import SeedGenerator


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, response_data=None):
        self.response_data = response_data or {}
        self.call_count = 0
    
    def generate_rule_description(self, prompt):
        """Mock response based on prompt content."""
        self.call_count += 1
        
        if "behavior_based" in prompt or "specific technical indicators" in prompt:
            return json.dumps({
                "description": "Create a YARA rule to detect malware that injects code and communicates with evil-domain.com",
                "primary_string": "evil-domain.com",
                "secondary_string": "InjectThread",
                "file_indicator": ".dll",
                "expected_keywords": []
            })
        elif "network_based" in prompt or "network communication" in prompt:
            return json.dumps({
                "description": "Create a YARA rule to detect backdoor communicating with c2-server.net on port 443",
                "domain": "c2-server.net",
                "port": "443",
                "protocol_string": "HTTPS",
                "mutex_name": "BackdoorMutex",
                "expected_keywords": []
            })
        elif "file_system" in prompt or "file system" in prompt:
            return json.dumps({
                "description": "Create a YARA rule to detect dropper creating files in Windows temp directory",
                "file_path": "C:\\Windows\\Temp\\malware.exe",
                "file_extension": ".exe",
                "marker_string": "DROPPER_MARK",
                "registry_key": "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                "expected_keywords": []
            })
        elif "pe_analysis" in prompt or "PE analysis" in prompt:
            return json.dumps({
                "description": "Create a YARA rule to detect PE files with UPX packer. Remember to import the PE module with 'import \"pe\"' at the top of your rule.",
                "packer": "UPX",
                "import_function": "GetProcAddress",
                "section_name": ".upx1",
                "version_info": "UPX Packed",
                "expected_keywords": ["pe"]
            })
        else:
            # Fallback
            return json.dumps({
                "description": "Generic test challenge",
                "test_string": "test_value",
                "expected_keywords": []
            })


class TestSyntheticChallengeGenerator:
    """Test synthetic challenge generation."""
    
    def test_generator_initialization(self):
        """Test generator initialization."""
        mock_client = MockLLMClient()
        generator = SyntheticChallengeGenerator(mock_client)
        
        assert generator.llm_client == mock_client
        assert isinstance(generator.seed_generator, SeedGenerator)
        assert len(generator.challenge_templates) == 4
    
    def test_challenge_templates(self):
        """Test challenge templates are properly defined."""
        mock_client = MockLLMClient()
        generator = SyntheticChallengeGenerator(mock_client)
        
        template_types = [t["type"] for t in generator.challenge_templates]
        expected_types = ["behavior_based", "network_based", "file_system", "pe_analysis"]
        
        assert set(template_types) == set(expected_types)
        
        # Check each template has required fields
        for template in generator.challenge_templates:
            assert "type" in template
            assert "prompt_template" in template
            assert "expected_keywords" in template
    
    def test_generate_challenge_with_seed(self):
        """Test generating challenge with seed."""
        mock_client = MockLLMClient()
        generator = SyntheticChallengeGenerator(mock_client)
        
        seed = "injects malicious code; communicates with C2"
        template = generator.challenge_templates[0]  # behavior_based
        
        result = generator._generate_challenge_with_seed(seed, template)
        
        assert result is not None
        assert "description" in result
        assert "primary_string" in result
        assert mock_client.call_count == 1
    
    def test_generate_single_challenge(self):
        """Test generating a single challenge."""
        mock_client = MockLLMClient()
        generator = SyntheticChallengeGenerator(mock_client)
        
        challenge = generator._generate_single_challenge("test_001")
        
        assert challenge is not None
        assert challenge.id == "test_001"
        assert challenge.actionable is True
        assert challenge.description != ""
        assert len(challenge.expected_strings) > 0
        assert len(challenge.test_files) >= 2  # At least matching + non-matching
        assert "seed" in challenge.metadata
        assert "template" in challenge.metadata
    
    def test_generate_multiple_challenges(self):
        """Test generating multiple challenges."""
        mock_client = MockLLMClient()
        generator = SyntheticChallengeGenerator(mock_client)
        
        challenges = generator.generate_challenges(count=3)
        
        assert len(challenges) <= 3  # May be less if some fail
        
        for challenge in challenges:
            assert challenge.id.startswith("l2_synthetic_")
            assert challenge.actionable is True
            assert len(challenge.test_files) >= 2
    
    def test_generate_sophisticated_test_files_behavior_based(self):
        """Test sophisticated test file generation for behavior_based."""
        mock_client = MockLLMClient()
        generator = SyntheticChallengeGenerator(mock_client)
        
        challenge_data = {
            "description": "Test behavior challenge",
            "primary_string": "evil.com",
            "secondary_string": "InjectCode"
        }
        seed = "injects code; communicates with C2"
        
        test_files = generator._generate_sophisticated_test_files(
            "behavior_based", challenge_data, seed
        )
        
        assert len(test_files) >= 2
        assert any(f.should_match for f in test_files)
        assert any(not f.should_match for f in test_files)
        
        # Check that matching file contains indicators
        matching_file = next(f for f in test_files if f.should_match)
        import base64
        content = base64.b64decode(matching_file.content_b64).decode()
        assert "evil.com" in content or "InjectCode" in content
    
    def test_generate_sophisticated_test_files_pe_analysis(self):
        """Test sophisticated test file generation for PE analysis."""
        mock_client = MockLLMClient()
        generator = SyntheticChallengeGenerator(mock_client)
        
        challenge_data = {
            "description": "PE analysis challenge",
            "packer": "UPX",
            "import_function": "LoadLibrary",
            "section_name": ".upx0",
            "version_info": "1.0"
        }
        seed = "uses UPX packer; loads libraries dynamically"
        
        test_files = generator._generate_sophisticated_test_files(
            "pe_analysis", challenge_data, seed
        )
        
        assert len(test_files) >= 2
        
        # Check PE sample contains PE indicators
        matching_file = next(f for f in test_files if f.should_match)
        import base64
        content = base64.b64decode(matching_file.content_b64).decode()
        assert "UPX" in content
        assert "LoadLibrary" in content
    
    def test_error_handling_invalid_json(self):
        """Test error handling for invalid JSON responses."""
        class BadMockClient:
            def generate_rule_description(self, prompt):
                return "invalid json response"
        
        generator = SyntheticChallengeGenerator(BadMockClient())
        challenge = generator._generate_single_challenge("test_error")
        
        # Should handle the error gracefully
        assert challenge is None
    
    def test_error_handling_missing_description(self):
        """Test error handling for missing description."""
        class EmptyMockClient:
            def generate_rule_description(self, prompt):
                return json.dumps({"not_description": "value"})
        
        generator = SyntheticChallengeGenerator(EmptyMockClient())
        challenge = generator._generate_single_challenge("test_empty")
        
        # Should handle missing description gracefully
        assert challenge is None