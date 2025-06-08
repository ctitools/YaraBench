"""YARA rule syntax validator."""

from typing import Dict, Any, List, Optional
import yara

from ..models import Challenge
from .base import Evaluator


class YaraValidator(Evaluator):
    """Validates YARA rule syntax and extracts features."""
    
    @property
    def name(self) -> str:
        """Get the name of this evaluator."""
        return "YARA Syntax Validator"
    
    def evaluate(self, challenge: Challenge, rule: str) -> Dict[str, Any]:
        """Evaluate YARA rule syntax and features.
        
        Args:
            challenge: The challenge (used for expected features)
            rule: The YARA rule to validate
            
        Returns:
            Dictionary with validation results
        """
        results = {
            "valid_syntax": False,
            "expected_strings_found": [],
            "expected_keywords_found": [],
            "error": None
        }
        
        # Enhanced structure validation before compilation
        structure_error = self._validate_structure(rule)
        if structure_error:
            results["error"] = structure_error
            return results
        
        # Validate syntax by compiling
        try:
            yara.compile(source=rule)
            results["valid_syntax"] = True
        except yara.SyntaxError as e:
            results["error"] = f"YARA syntax error: {str(e)}"
            return results
        except Exception as e:
            results["error"] = f"YARA compilation error: {str(e)}"
            return results
        
        # Check for expected strings
        if challenge.expected_strings:
            results["expected_strings_found"] = self._find_expected_strings(
                rule, challenge.expected_strings
            )
        
        # Check for expected keywords
        if challenge.expected_keywords:
            results["expected_keywords_found"] = self._find_expected_keywords(
                rule, challenge.expected_keywords
            )
        
        return results
    
    def _find_expected_strings(self, rule: str, expected: List[str]) -> List[str]:
        """Find which expected strings appear in the rule."""
        found = []
        for expected_string in expected:
            # Check various ways the string might appear
            if (expected_string in rule or 
                repr(expected_string) in rule or
                expected_string.encode().hex() in rule or
                expected_string.replace('\\', '\\\\') in rule):
                found.append(expected_string)
        return found
    
    def _find_expected_keywords(self, rule: str, expected: List[str]) -> List[str]:
        """Find which expected keywords appear in the rule."""
        found = []
        rule_lower = rule.lower()
        
        for keyword in expected:
            keyword_lower = keyword.lower()
            # Check if keyword appears (with word boundaries for some keywords)
            if keyword_lower in ['pe', 'elf']:
                # These are usually followed by . or used in imports
                if f"{keyword_lower}." in rule_lower or f"import \"{keyword_lower}\"" in rule_lower:
                    found.append(keyword)
            elif keyword_lower in rule_lower:
                found.append(keyword)
        
        return found
    
    def _validate_structure(self, rule: str) -> Optional[str]:
        """Validate basic YARA rule structure before compilation.
        
        Args:
            rule: YARA rule to validate
            
        Returns:
            Error message if invalid, None if valid
        """
        if not rule or not rule.strip():
            return "Empty rule"
        
        # Check for basic components
        if "rule " not in rule:
            return "Incomplete rule structure - missing 'rule' keyword"
        if "{" not in rule:
            return "Incomplete rule structure - missing opening brace"
        if "}" not in rule:
            return "Incomplete rule structure - missing closing brace"
        if "condition:" not in rule:
            return "Incomplete rule structure - missing condition"
        
        # Check brace balance
        if rule.count("{") != rule.count("}"):
            return "Incomplete rule structure - unbalanced braces"
        
        return None