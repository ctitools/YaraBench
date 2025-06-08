"""Test utility functions."""

import pytest
import base64

from src.utils import SeedGenerator, clean_text_output, fix_base64_padding, decode_base64_list


class TestSeedGenerator:
    """Test SeedGenerator functionality."""
    
    def test_default_initialization(self):
        """Test SeedGenerator with default pieces."""
        generator = SeedGenerator()
        assert len(generator.pieces) > 0
        assert "injects malicious code into system processes" in generator.pieces
    
    def test_custom_initialization(self):
        """Test SeedGenerator with custom pieces."""
        custom_pieces = ["behavior 1", "behavior 2", "behavior 3"]
        generator = SeedGenerator(custom_pieces)
        assert generator.pieces == custom_pieces
    
    def test_generate_single_behavior(self):
        """Test generating single behavior."""
        generator = SeedGenerator()
        seed = generator.generate(1)
        
        assert seed.endswith(".")
        # Should be one of the predefined pieces
        seed_without_period = seed[:-1]
        assert seed_without_period in generator.pieces
    
    def test_generate_multiple_behaviors(self):
        """Test generating multiple behaviors."""
        generator = SeedGenerator()
        seed = generator.generate(3)
        
        assert seed.endswith(".")
        assert seed.count(";") == 2  # 3 behaviors = 2 semicolons
        
        # Split and check each behavior
        behaviors = seed[:-1].split("; ")
        assert len(behaviors) == 3
        
        for behavior in behaviors:
            assert behavior in generator.pieces
    
    def test_generate_max_behaviors(self):
        """Test generating more behaviors than available."""
        custom_pieces = ["behavior 1", "behavior 2"]
        generator = SeedGenerator(custom_pieces)
        
        # Request more than available
        seed = generator.generate(5)
        behaviors = seed[:-1].split("; ")
        
        # Should only get the available behaviors
        assert len(behaviors) <= 2
    
    def test_generate_zero_behaviors(self):
        """Test generating zero behaviors."""
        generator = SeedGenerator()
        seed = generator.generate(0)
        
        # Should still return something reasonable
        assert isinstance(seed, str)


class TestTextUtils:
    """Test text utility functions."""
    
    def test_clean_text_output_basic(self):
        """Test basic text cleaning."""
        text = "  Hello World  \n"
        cleaned = clean_text_output(text)
        assert cleaned == "Hello World"
    
    def test_clean_text_output_multiline(self):
        """Test cleaning multiline text."""
        text = "\n  Line 1  \n  Line 2  \n"
        cleaned = clean_text_output(text)
        assert cleaned == "Line 1\nLine 2"
    
    def test_clean_text_output_empty(self):
        """Test cleaning empty text."""
        assert clean_text_output("") == ""
        assert clean_text_output("   ") == ""
        assert clean_text_output("\n\n") == ""
    
    def test_fix_base64_padding_valid(self):
        """Test fixing base64 padding for valid string."""
        # Valid base64
        valid_b64 = base64.b64encode(b"test").decode()
        fixed = fix_base64_padding(valid_b64)
        assert fixed == valid_b64
    
    def test_fix_base64_padding_missing_padding(self):
        """Test fixing base64 with missing padding."""
        # Remove padding
        b64_no_padding = base64.b64encode(b"test").decode().rstrip("=")
        fixed = fix_base64_padding(b64_no_padding)
        
        # Should be able to decode after fixing
        try:
            base64.b64decode(fixed)
            success = True
        except Exception:
            success = False
        
        assert success
    
    def test_fix_base64_padding_invalid(self):
        """Test fixing completely invalid base64."""
        invalid = "not_base64_at_all!"
        fixed = fix_base64_padding(invalid)
        
        # Should handle gracefully (might return original or attempt fix)
        assert isinstance(fixed, str)


class TestDataUtils:
    """Test data utility functions."""
    
    def test_decode_base64_list_valid(self):
        """Test decoding list of valid base64 strings."""
        test_data = [b"hello", b"world", b"test"]
        b64_list = [base64.b64encode(data).decode() for data in test_data]
        
        decoded = decode_base64_list(b64_list)
        
        assert len(decoded) == 3
        assert decoded[0] == b"hello"
        assert decoded[1] == b"world"
        assert decoded[2] == b"test"
    
    def test_decode_base64_list_mixed_validity(self):
        """Test decoding list with some invalid base64."""
        valid_b64 = base64.b64encode(b"valid").decode()
        mixed_list = [valid_b64, "invalid_base64", ""]
        
        decoded = decode_base64_list(mixed_list)
        
        # Should handle errors gracefully
        assert len(decoded) <= 3
        assert b"valid" in decoded
    
    def test_decode_base64_list_empty(self):
        """Test decoding empty list."""
        decoded = decode_base64_list([])
        assert decoded == []
    
    def test_decode_base64_list_all_invalid(self):
        """Test decoding list of all invalid base64."""
        invalid_list = ["not_base64", "also_not_base64", "definitely_not"]
        decoded = decode_base64_list(invalid_list)
        
        # Should return empty list or handle gracefully
        assert isinstance(decoded, list)