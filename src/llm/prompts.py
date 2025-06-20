"""Prompts for LLM interactions."""

from ..models import Challenge


SYSTEM_PROMPT = """You are a cybersecurity expert specialized in writing YARA rules for malware detection.

When given a description of malware behavior or characteristics, you should:
1. Generate a valid YARA rule that accurately detects the described patterns
2. Use basic YARA features (strings, conditions, meta, etc.) - avoid using modules when possible
3. Focus on string-based detection rather than complex module-based analysis
4. Make the rule as specific as possible to avoid false positives
5. Include relevant metadata in the rule

IMPORTANT: Prefer string-based detection over module usage. Only use modules when absolutely necessary and when the challenge explicitly requires it. Most detection can be accomplished with basic string matching and conditions.

If the description is not actionable or cannot be effectively detected with a YARA rule, respond with an explanation of why a YARA rule is not suitable for this case.

Always provide just the YARA rule without additional explanation unless the task is not suitable for YARA detection."""


def format_challenge_prompt(challenge: Challenge) -> str:
    """Format a challenge into a prompt for the LLM.
    
    Args:
        challenge: The challenge to format
        
    Returns:
        Formatted prompt string
    """
    prompt = f"Create a YARA rule based on the following description:\n\n{challenge.description}"
    
    # Add hints about expected features if available
    if challenge.expected_strings:
        prompt += f"\n\nHint: The rule should detect these strings: {', '.join(repr(s) for s in challenge.expected_strings)}"
    
    if challenge.expected_keywords:
        prompt += f"\n\nHint: Consider using these YARA features: {', '.join(challenge.expected_keywords)}"
    
    return prompt