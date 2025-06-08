"""OpenAI-compatible LLM client."""

import time
from typing import Optional

from openai import OpenAI

from ..models import ModelConfig, Challenge
from .prompts import SYSTEM_PROMPT, format_challenge_prompt


class LLMClient:
    """OpenAI-compatible LLM client."""
    
    def __init__(self, model_config: ModelConfig):
        """Initialize the LLM client.
        
        Args:
            model_config: Model configuration
        """
        self.model_config = model_config
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=model_config.api_key or None,  # Will use env var if None
            base_url=str(model_config.base_url) if model_config.base_url else None
        )
    
    def generate_rule(self, challenge: Challenge, retry_count: int = 0) -> str:
        """Generate a YARA rule for the given challenge.
        
        Args:
            challenge: The challenge to generate a rule for
            retry_count: Current retry attempt
            
        Returns:
            Generated response
            
        Raises:
            Exception: If generation fails after retries
        """
        prompt = format_challenge_prompt(challenge)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model_config.name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.model_config.temperature,
                max_tokens=self.model_config.max_tokens,
                timeout=self.model_config.timeout
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            # Retry logic
            max_retries = getattr(self.model_config, 'max_retries', 3)
            retry_delay = getattr(self.model_config, 'retry_delay', 1.0)
            
            if retry_count < max_retries:
                # Exponential backoff
                delay = retry_delay * (2 ** retry_count)
                time.sleep(delay)
                return self.generate_rule(challenge, retry_count + 1)
            else:
                raise Exception(f"Failed to generate rule after {max_retries} retries: {str(e)}")
    
    def generate_rule_description(self, prompt: str, retry_count: int = 0) -> str:
        """Generate text response for synthetic challenge generation.
        
        Args:
            prompt: The prompt to send
            retry_count: Current retry attempt
            
        Returns:
            Generated response
            
        Raises:
            Exception: If generation fails after retries
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_config.name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,  # Higher temperature for more creativity
                max_tokens=self.model_config.max_tokens,
                timeout=self.model_config.timeout
            )
            
            return response.choices[0].message.content or ""
            
        except Exception as e:
            # Retry logic
            max_retries = getattr(self.model_config, 'max_retries', 3)
            retry_delay = getattr(self.model_config, 'retry_delay', 1.0)
            
            if retry_count < max_retries:
                # Exponential backoff
                delay = retry_delay * (2 ** retry_count)
                time.sleep(delay)
                return self.generate_rule_description(prompt, retry_count + 1)
            else:
                raise Exception(f"Failed to generate description after {max_retries} retries: {str(e)}")