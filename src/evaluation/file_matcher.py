"""File matching evaluator using YARA."""

import base64
import tempfile
from typing import Dict, Any
import yara

from ..models import Challenge
from ..utils import fix_base64_padding
from .base import Evaluator


class FileMatcher(Evaluator):
    """Evaluates YARA rules against test files."""
    
    @property
    def name(self) -> str:
        """Get the name of this evaluator."""
        return "File Matcher"
    
    def evaluate(self, challenge: Challenge, rule: str) -> Dict[str, Any]:
        """Evaluate YARA rule against test files.
        
        Args:
            challenge: The challenge with test files
            rule: The YARA rule to test
            
        Returns:
            Dictionary with match results
        """
        results = {
            "execution_results": {},
            "error": None
        }
        
        # Skip if no test files
        if not challenge.test_files:
            return results
        
        try:
            # Compile the rule
            compiled_rule = yara.compile(source=rule)
            
            # Test against each file
            for test_file in challenge.test_files:
                # Decode file content with improved base64 handling
                try:
                    fixed_b64 = fix_base64_padding(test_file.content_b64)
                    content = base64.b64decode(fixed_b64)
                except Exception as e:
                    results["execution_results"][test_file.name] = False
                    results["error"] = f"Failed to decode {test_file.name}: {str(e)}"
                    continue
                
                # Match against content
                try:
                    matches = compiled_rule.match(data=content)
                    results["execution_results"][test_file.name] = len(matches) > 0
                except Exception as e:
                    results["execution_results"][test_file.name] = False
                    results["error"] = f"Failed to match {test_file.name}: {str(e)}"
            
        except yara.SyntaxError as e:
            results["error"] = f"YARA syntax error: {str(e)}"
        except Exception as e:
            results["error"] = f"Execution error: {str(e)}"
        
        return results