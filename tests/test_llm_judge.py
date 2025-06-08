"""Test LLM judge evaluator."""

import pytest
import json
from unittest.mock import Mock

from src.evaluation.llm_judge import LLMJudge
from src.models import Challenge, TestFile, ChallengeLevel


class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, judge_response=None):
        self.judge_response = judge_response
        self.call_count = 0
    
    def generate_rule_description(self, prompt):
        """Return mock judge evaluation."""
        self.call_count += 1
        
        if self.judge_response:
            return self.judge_response
        
        # Default response
        return json.dumps({
            "correctness": {
                "score": 8,
                "feedback": "Rule correctly implements the requirements"
            },
            "completeness": {
                "score": 9,
                "feedback": "All required strings are present"
            },
            "efficiency": {
                "score": 7,
                "feedback": "Rule is reasonably efficient"
            },
            "best_practices": {
                "score": 8,
                "feedback": "Follows most YARA conventions"
            },
            "false_positive_risk": {
                "score": 6,
                "feedback": "Moderate risk of false positives"
            },
            "overall_assessment": "Good rule implementation with minor improvements possible"
        })


class TestLLMJudge:
    """Test LLM judge functionality."""
    
    def test_judge_initialization(self):
        """Test judge initialization."""
        mock_client = MockLLMClient()
        judge = LLMJudge(mock_client)
        
        assert judge.llm_client == mock_client
        assert judge.name == "LLM Judge"
    
    def test_judge_evaluation_success(self):
        """Test successful judge evaluation."""
        mock_client = MockLLMClient()
        judge = LLMJudge(mock_client)
        
        # Create test challenge and rule
        challenge = Challenge(
            id="test_001",
            level=ChallengeLevel.LEVEL1,
            actionable=True,
            description="Detect malware with string 'evil'",
            expected_strings=["evil"],
            expected_keywords=[],
            test_files=[]
        )
        
        rule = """
        rule DetectEvil {
            strings:
                $evil = "evil"
            condition:
                $evil
        }
        """
        
        # Evaluate
        result = judge.evaluate(challenge, rule)
        
        assert "llm_judge_score" in result
        assert "llm_judge_feedback" in result
        assert "llm_judge_details" in result
        
        # Check score calculation (weighted average)
        assert 0.0 <= result["llm_judge_score"] <= 1.0
        assert result["llm_judge_score"] > 0.7  # Should be good score
        
        # Check feedback formatting
        assert "Correctness" in result["llm_judge_feedback"]
        assert "Completeness" in result["llm_judge_feedback"]
        
        # Check details
        assert "correctness" in result["llm_judge_details"]
        assert mock_client.call_count == 1
    
    def test_judge_evaluation_with_custom_response(self):
        """Test judge evaluation with custom response."""
        custom_response = json.dumps({
            "correctness": {"score": 3, "feedback": "Incorrect implementation"},
            "completeness": {"score": 2, "feedback": "Missing required strings"},
            "efficiency": {"score": 5, "feedback": "Average efficiency"},
            "best_practices": {"score": 4, "feedback": "Poor conventions"},
            "false_positive_risk": {"score": 2, "feedback": "High false positive risk"},
            "overall_assessment": "Poor rule implementation"
        })
        
        mock_client = MockLLMClient(judge_response=custom_response)
        judge = LLMJudge(mock_client)
        
        challenge = Challenge(
            id="test_002",
            level=ChallengeLevel.LEVEL1,
            actionable=True,
            description="Test challenge",
            expected_strings=[],
            expected_keywords=[],
            test_files=[]
        )
        
        result = judge.evaluate(challenge, "rule BadRule { condition: true }")
        
        # Should get low score
        assert result["llm_judge_score"] < 0.4
        assert "Poor rule implementation" in result["llm_judge_feedback"]
    
    def test_judge_evaluation_error_handling(self):
        """Test judge evaluation error handling."""
        class ErrorClient:
            def generate_rule_description(self, prompt):
                raise Exception("API error")
        
        judge = LLMJudge(ErrorClient())
        
        challenge = Challenge(
            id="test_003",
            level=ChallengeLevel.LEVEL1,
            actionable=True,
            description="Test challenge",
            expected_strings=[],
            expected_keywords=[],
            test_files=[]
        )
        
        result = judge.evaluate(challenge, "rule Test { condition: true }")
        
        assert result["llm_judge_score"] == 0.0
        assert "LLM judge error" in result["llm_judge_feedback"]
        assert "error" in result["llm_judge_details"]
    
    def test_judge_evaluation_malformed_json(self):
        """Test judge evaluation with malformed JSON response."""
        mock_client = MockLLMClient(judge_response="This is not JSON")
        judge = LLMJudge(mock_client)
        
        challenge = Challenge(
            id="test_004",
            level=ChallengeLevel.LEVEL1,
            actionable=True,
            description="Test challenge",
            expected_strings=[],
            expected_keywords=[],
            test_files=[]
        )
        
        result = judge.evaluate(challenge, "rule Test { condition: true }")
        
        # Should handle gracefully
        assert "llm_judge_score" in result
        assert "llm_judge_feedback" in result
        assert result["llm_judge_score"] == 0.5  # Default middle score
    
    def test_judge_evaluation_partial_response(self):
        """Test judge evaluation with partial response."""
        partial_response = json.dumps({
            "correctness": {"score": 8},  # Missing feedback
            "completeness": 7,  # Not a dict
            # Missing other criteria
        })
        
        mock_client = MockLLMClient(judge_response=partial_response)
        judge = LLMJudge(mock_client)
        
        challenge = Challenge(
            id="test_005",
            level=ChallengeLevel.LEVEL1,
            actionable=True,
            description="Test challenge",
            expected_strings=[],
            expected_keywords=[],
            test_files=[]
        )
        
        result = judge.evaluate(challenge, "rule Test { condition: true }")
        
        # Should handle gracefully with defaults
        assert "llm_judge_score" in result
        assert 0.0 <= result["llm_judge_score"] <= 1.0
    
    def test_judge_evaluation_no_client(self):
        """Test judge evaluation without LLM client."""
        judge = LLMJudge(None)
        
        challenge = Challenge(
            id="test_006",
            level=ChallengeLevel.LEVEL1,
            actionable=True,
            description="Test challenge",
            expected_strings=[],
            expected_keywords=[],
            test_files=[]
        )
        
        result = judge.evaluate(challenge, "rule Test { condition: true }")
        
        assert result["llm_judge_score"] == 0.0
        assert "not configured" in result["llm_judge_feedback"]
    
    def test_judge_prompt_creation(self):
        """Test judge prompt creation."""
        judge = LLMJudge(MockLLMClient())
        
        challenge = Challenge(
            id="test_007",
            level=ChallengeLevel.LEVEL1,
            actionable=True,
            description="Detect malware with strings 'evil' and 'malicious'",
            expected_strings=["evil", "malicious"],
            expected_keywords=["pe"],
            test_files=[]
        )
        
        rule = "rule Test { condition: true }"
        
        prompt = judge._create_evaluation_prompt(challenge, rule)
        
        # Check prompt contains key elements
        assert "Detect malware" in prompt
        assert "evil" in prompt
        assert "malicious" in prompt
        assert "pe" in prompt
        assert "rule Test" in prompt
        assert "JSON" in prompt