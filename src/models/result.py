"""Result data models for YaraBench."""

from typing import Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class RuleResult(BaseModel):
    """Result of evaluating a single YARA rule."""
    challenge_id: str = Field(..., description="ID of the challenge")
    model: str = Field(..., description="Model that generated the rule")
    generated_rule: Optional[str] = Field(None, description="The extracted YARA rule")
    generated_response: str = Field(..., description="Full LLM response")
    valid_syntax: bool = Field(..., description="Whether the rule has valid YARA syntax")
    execution_results: Dict[str, bool] = Field(
        default_factory=dict,
        description="File match results (filename -> matched)"
    )
    expected_strings_found: List[str] = Field(
        default_factory=list,
        description="Expected strings that were found in the rule"
    )
    expected_keywords_found: List[str] = Field(
        default_factory=list,
        description="Expected keywords that were found in the rule"
    )
    score: float = Field(..., description="Composite score (0-1)")
    error: Optional[str] = Field(None, description="Error message if evaluation failed")
    latency_ms: float = Field(..., description="Time taken to generate rule in milliseconds")
    llm_judge_score: Optional[float] = Field(None, description="LLM judge score (0-1) if available")
    llm_judge_feedback: Optional[str] = Field(None, description="LLM judge feedback if available")
    llm_judge_details: Optional[Dict] = Field(None, description="Detailed LLM judge evaluation")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the evaluation ran")


class BenchmarkResult(BaseModel):
    """Result of running a full benchmark."""
    model: str = Field(..., description="Model being benchmarked")
    levels: List[str] = Field(..., description="Challenge levels that were run")
    total_challenges: int = Field(..., description="Total number of challenges")
    successful_challenges: int = Field(..., description="Number of challenges with valid rules")
    average_score: float = Field(..., description="Average score across all challenges")
    results: List[RuleResult] = Field(..., description="Individual challenge results")
    total_time_ms: float = Field(..., description="Total benchmark runtime in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="When the benchmark ran")
    
    class Config:
        """Pydantic config."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }