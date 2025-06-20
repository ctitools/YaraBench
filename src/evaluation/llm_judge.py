"""LLM-based rule evaluator."""

import json
from typing import Dict, Any, Optional

from ..models import Challenge
from .base import Evaluator


class LLMJudge(Evaluator):
    """LLM-based evaluator for comprehensive rule quality assessment."""
    
    def __init__(self, llm_client, judge_model: Optional[str] = None):
        """Initialize with an LLM client.
        
        Args:
            llm_client: LLM client instance for judge queries
            judge_model: Optional specific model to use for judging (defaults to client's model)
        """
        self.llm_client = llm_client
        self.judge_model = judge_model
    
    @property
    def name(self) -> str:
        """Get the name of this evaluator."""
        return "LLM Judge"
    
    def evaluate(self, challenge: Challenge, rule: str) -> Dict[str, Any]:
        """Evaluate rule quality using an LLM judge.
        
        Evaluates multiple aspects:
        - Correctness: Does the rule match the challenge requirements?
        - Completeness: Are all required elements present?
        - Efficiency: Is the rule well-optimized?
        - Best Practices: Does it follow YARA conventions?
        - Security: Are there potential false positives/negatives?
        
        Args:
            challenge: The challenge
            rule: The YARA rule to evaluate
            
        Returns:
            Dictionary with judge results including scores and feedback
        """
        if not self.llm_client:
            return {
                "llm_judge_score": 0.0,
                "llm_judge_feedback": "LLM judge not configured",
                "llm_judge_details": {}
            }
        
        # Create evaluation prompt
        evaluation_prompt = self._create_evaluation_prompt(challenge, rule)
        
        try:
            # Get LLM evaluation
            response = self._get_llm_evaluation(evaluation_prompt)
            
            # Parse the response
            evaluation_data = self._parse_evaluation_response(response)
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(evaluation_data)
            
            # Format feedback
            feedback = self._format_feedback(evaluation_data)
            
            return {
                "llm_judge_score": overall_score,
                "llm_judge_feedback": feedback,
                "llm_judge_details": evaluation_data
            }
            
        except Exception as e:
            return {
                "llm_judge_score": 0.0,
                "llm_judge_feedback": f"LLM judge error: {str(e)}",
                "llm_judge_details": {"error": str(e)}
            }
    
    def _create_evaluation_prompt(self, challenge: Challenge, rule: str) -> str:
        """Create a comprehensive evaluation prompt for the LLM judge.
        
        Args:
            challenge: The challenge
            rule: The YARA rule to evaluate
            
        Returns:
            Formatted prompt for LLM evaluation
        """
        prompt = f"""You are an expert YARA rule evaluator. Evaluate the following YARA rule against the given challenge.

CHALLENGE:
{challenge.description}

Expected Requirements:
- Strings to detect: {', '.join(challenge.expected_strings) if challenge.expected_strings else 'None specified'}
- Keywords to use: {', '.join(challenge.expected_keywords) if challenge.expected_keywords else 'None specified'}
- Actionable: {'Yes' if challenge.actionable else 'No'}

SUBMITTED YARA RULE:
{rule}

Evaluate the rule on these criteria and respond with JSON only:
{{
  "correctness": {{
    "score": 0-10,
    "feedback": "Does the rule correctly implement the challenge requirements?"
  }},
  "completeness": {{
    "score": 0-10,
    "feedback": "Are all required strings and features included?"
  }},
  "efficiency": {{
    "score": 0-10,
    "feedback": "Is the rule optimized and efficient?"
  }},
  "best_practices": {{
    "score": 0-10,
    "feedback": "Does it follow YARA best practices and conventions?"
  }},
  "false_positive_risk": {{
    "score": 0-10,
    "feedback": "How well does it avoid false positives? (10=very low risk)"
  }},
  "overall_assessment": "Brief overall assessment of the rule quality"
}}

Be strict but fair. Consider:
- Syntax correctness
- Logic accuracy
- String matching appropriateness
- Condition complexity
- Preference for string-based detection over module usage
- Potential for false positives/negatives"""
        
        return prompt
    
    def _get_llm_evaluation(self, prompt: str) -> str:
        """Get evaluation from the LLM.
        
        Args:
            prompt: The evaluation prompt
            
        Returns:
            LLM response
        """
        # Use the judge-specific prompt system
        judge_system_prompt = """You are a YARA rule expert evaluator. Your role is to:
1. Analyze YARA rules for correctness, efficiency, and best practices
2. Provide constructive feedback
3. Score rules fairly on multiple criteria
4. Return structured JSON responses
5. Prefer string-based detection over module usage when possible

Be thorough but concise in your evaluations. Encourage simple, effective rules that use string matching rather than complex module-based analysis."""
        
        # If we have a custom judge model, we'd use it here
        # For now, use the standard generate method
        try:
            # Check if llm_client has the expected method
            if hasattr(self.llm_client, 'generate_rule_description'):
                return self.llm_client.generate_rule_description(prompt)
            elif hasattr(self.llm_client, 'generate_rule'):
                # Use a mock challenge for the generate_rule method
                from ..models import Challenge, ChallengeLevel
                mock_challenge = Challenge(
                    id="judge_eval",
                    level=ChallengeLevel.LEVEL1,
                    actionable=True,
                    description=prompt,
                    expected_strings=[],
                    expected_keywords=[],
                    test_files=[]
                )
                return self.llm_client.generate_rule(mock_challenge)
            else:
                return "Failed to call LLM client"
        except Exception as e:
            raise Exception(f"LLM evaluation failed: {str(e)}")
    
    def _parse_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse the LLM evaluation response.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Parsed evaluation data
        """
        try:
            # Try to extract JSON from the response
            # Handle potential markdown code blocks
            clean_response = response.strip()
            if "```json" in clean_response:
                clean_response = clean_response.split("```json")[1].split("```")[0]
            elif "```" in clean_response:
                clean_response = clean_response.split("```")[1].split("```")[0]
            
            # Parse JSON
            evaluation_data = json.loads(clean_response.strip())
            
            # Validate expected structure
            required_keys = ["correctness", "completeness", "efficiency", 
                           "best_practices", "false_positive_risk"]
            
            for key in required_keys:
                if key not in evaluation_data:
                    evaluation_data[key] = {"score": 5, "feedback": "Not evaluated"}
                elif not isinstance(evaluation_data[key], dict):
                    evaluation_data[key] = {"score": 5, "feedback": str(evaluation_data[key])}
                elif "score" not in evaluation_data[key]:
                    evaluation_data[key]["score"] = 5
            
            return evaluation_data
            
        except json.JSONDecodeError:
            # Fallback: try to extract some meaning from the response
            return {
                "correctness": {"score": 5, "feedback": "Unable to parse evaluation"},
                "completeness": {"score": 5, "feedback": "Unable to parse evaluation"},
                "efficiency": {"score": 5, "feedback": "Unable to parse evaluation"},
                "best_practices": {"score": 5, "feedback": "Unable to parse evaluation"},
                "false_positive_risk": {"score": 5, "feedback": "Unable to parse evaluation"},
                "overall_assessment": response[:200] + "..." if len(response) > 200 else response
            }
    
    def _calculate_overall_score(self, evaluation_data: Dict[str, Any]) -> float:
        """Calculate weighted overall score from individual criteria.
        
        Args:
            evaluation_data: Parsed evaluation data
            
        Returns:
            Overall score between 0.0 and 1.0
        """
        # Define weights for each criterion
        weights = {
            "correctness": 0.35,      # Most important
            "completeness": 0.25,     # Very important
            "efficiency": 0.15,       # Important
            "best_practices": 0.15,   # Important
            "false_positive_risk": 0.10  # Important but harder to judge
        }
        
        total_score = 0.0
        total_weight = 0.0
        
        for criterion, weight in weights.items():
            if criterion in evaluation_data and isinstance(evaluation_data[criterion], dict):
                score = evaluation_data[criterion].get("score", 5) / 10.0  # Normalize to 0-1
                total_score += score * weight
                total_weight += weight
        
        # Normalize in case some weights were missing
        if total_weight > 0:
            return total_score / total_weight
        else:
            return 0.5  # Default middle score
    
    def _format_feedback(self, evaluation_data: Dict[str, Any]) -> str:
        """Format the evaluation data into readable feedback.
        
        Args:
            evaluation_data: Parsed evaluation data
            
        Returns:
            Formatted feedback string
        """
        feedback_parts = []
        
        # Add overall assessment if available
        if "overall_assessment" in evaluation_data:
            feedback_parts.append(f"Overall: {evaluation_data['overall_assessment']}")
        
        # Add criterion-specific feedback
        criteria_names = {
            "correctness": "Correctness",
            "completeness": "Completeness", 
            "efficiency": "Efficiency",
            "best_practices": "Best Practices",
            "false_positive_risk": "False Positive Risk"
        }
        
        for key, display_name in criteria_names.items():
            if key in evaluation_data and isinstance(evaluation_data[key], dict):
                score = evaluation_data[key].get("score", "?")
                feedback = evaluation_data[key].get("feedback", "No feedback")
                feedback_parts.append(f"{display_name} ({score}/10): {feedback}")
        
        return " | ".join(feedback_parts)