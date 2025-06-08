"""Configuration models for YaraBench."""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ModelConfig(BaseModel):
    """Configuration for an LLM model."""
    name: str = Field(..., description="Model name (e.g., 'gpt-4o')")
    base_url: Optional[HttpUrl] = Field(
        None,
        description="API base URL (defaults to OpenAI)"
    )
    api_key: Optional[str] = Field(
        None,
        description="API key (can also use environment variable)"
    )
    temperature: float = Field(0.0, description="Model temperature")
    max_tokens: int = Field(2000, description="Maximum tokens to generate")
    timeout: int = Field(30, description="Request timeout in seconds")


class Config(BaseModel):
    """Main configuration for YaraBench."""
    models: List[ModelConfig] = Field(..., description="Models to benchmark")
    levels: List[str] = Field(
        default_factory=lambda: ["level1"],
        description="Challenge levels to run"
    )
    judge_model: Optional[ModelConfig] = Field(
        None,
        description="Optional LLM judge for evaluation"
    )
    synthetic_count: int = Field(
        10,
        description="Number of synthetic challenges to generate for Level 2"
    )
    output_format: str = Field(
        "terminal",
        description="Output format: terminal, json, csv"
    )
    output_file: Optional[str] = Field(
        None,
        description="Output file path (for json/csv formats)"
    )
    verbose: bool = Field(False, description="Enable verbose output")
    max_retries: int = Field(3, description="Maximum retries for LLM calls")
    retry_delay: float = Field(1.0, description="Initial retry delay in seconds")