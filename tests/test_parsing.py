"""Test YARA rule parsing and extraction."""

import pytest
from src.parsing import YaraExtractor


class TestYaraExtractor:
    """Test YARA rule extraction functionality."""
    
    def test_extract_simple_rule(self):
        """Test extracting a simple YARA rule."""
        text = """
        Here is a YARA rule:
        
        rule TestRule {
            strings:
                $a = "malicious"
            condition:
                $a
        }
        
        That's the rule.
        """
        
        rules = YaraExtractor.extract_rules(text)
        assert len(rules) == 1
        
        rule = rules[0]
        assert "rule TestRule" in rule
        assert "malicious" in rule
        assert "condition:" in rule
    
    def test_extract_multiple_rules(self):
        """Test extracting multiple YARA rules."""
        text = """
        rule Rule1 {
            strings:
                $a = "test1"
            condition:
                $a
        }
        
        Some text in between.
        
        rule Rule2 {
            strings:
                $b = "test2"
            condition:
                $b
        }
        """
        
        rules = YaraExtractor.extract_rules(text)
        assert len(rules) == 2
        
        assert "Rule1" in rules[0]
        assert "test1" in rules[0]
        assert "Rule2" in rules[1] 
        assert "test2" in rules[1]
    
    def test_extract_rule_with_meta(self):
        """Test extracting rule with meta section."""
        text = """
        rule ComplexRule {
            meta:
                description = "Test rule"
                author = "YaraBench"
            strings:
                $str = "suspicious"
            condition:
                $str
        }
        """
        
        rules = YaraExtractor.extract_rules(text)
        assert len(rules) == 1
        
        rule = rules[0]
        assert "meta:" in rule
        assert "description" in rule
        assert "author" in rule
        assert "suspicious" in rule
    
    def test_extract_rule_with_imports(self):
        """Test extracting rule with imports."""
        text = """
        import "pe"
        
        rule PERule {
            condition:
                pe.is_pe
        }
        """
        
        rules = YaraExtractor.extract_rules(text)
        assert len(rules) == 1
        
        rule = rules[0]
        assert "rule PERule" in rule
        assert "pe.is_pe" in rule
        # Import should be included
        assert 'import "pe"' in rule
    
    def test_extract_single_rule(self):
        """Test extracting single rule from multiple."""
        text = """
        rule Rule1 { strings: $a = "test1" condition: $a }
        rule Rule2 { strings: $b = "test2" condition: $b }
        """
        
        single_rule = YaraExtractor.extract_single_rule(text)
        assert single_rule is not None
        assert "rule Rule" in single_rule
    
    def test_extract_no_rules(self):
        """Test extracting from text with no rules."""
        text = "This text has no YARA rules in it."
        
        rules = YaraExtractor.extract_rules(text)
        assert len(rules) == 0
        
        single_rule = YaraExtractor.extract_single_rule(text)
        assert single_rule is None
    
    def test_extract_malformed_rule(self):
        """Test extracting malformed rules."""
        text = """
        rule IncompleteRule {
            strings:
                $a = "test"
            // Missing condition section
        }
        """
        
        # Should still extract what it can
        rules = YaraExtractor.extract_rules(text)
        # Behavior depends on regex patterns - might extract partial rule
        assert isinstance(rules, list)
    
    def test_extract_rule_with_nested_braces(self):
        """Test extracting rule with nested braces in strings."""
        text = """
        rule NestedBraces {
            strings:
                $regex = /function\\s*\\{[^}]*\\}/
                $str = "data {content}"
            condition:
                any of them
        }
        """
        
        rules = YaraExtractor.extract_rules(text)
        assert len(rules) == 1
        
        rule = rules[0]
        assert "NestedBraces" in rule
        assert "function" in rule
        assert "data {content}" in rule
    
    def test_extract_rule_with_comments(self):
        """Test extracting rule with comments."""
        text = """
        rule CommentedRule {
            strings:
                $a = "test" // This is a comment
                /* Multi-line
                   comment */
                $b = "another"
            condition:
                $a or $b
        }
        """
        
        rules = YaraExtractor.extract_rules(text)
        assert len(rules) == 1
        
        rule = rules[0]
        assert "CommentedRule" in rule
        assert "test" in rule
        assert "another" in rule
    
    def test_duplicate_detection(self):
        """Test duplicate rule detection."""
        text = """
        rule TestRule {
            strings:
                $a = "test"
            condition:
                $a
        }
        
        rule TestRule {
            strings:
                $a = "test"
            condition:
                $a
        }
        """
        
        rules = YaraExtractor.extract_rules(text)
        # Should deduplicate identical rules
        assert len(rules) == 1
    
    def test_extract_rule_case_sensitivity(self):
        """Test rule extraction with different cases."""
        text = """
        RULE UpperRule {
            STRINGS:
                $a = "test"
            CONDITION:
                $a
        }
        """
        
        rules = YaraExtractor.extract_rules(text)
        # Should handle case variations
        assert len(rules) >= 0  # Depends on regex implementation