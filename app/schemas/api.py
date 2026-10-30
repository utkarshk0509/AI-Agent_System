from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class CodeExecutionRequest(BaseModel):
    """Client request schema to start an autonomous analysis workflow."""
    query: str = Field(..., description="The high-level user request or data analysis query")
    max_iterations: Optional[int] = Field(default=5, ge=1, le=10, description="Upper bound on repair iterations")


class CodeExecutionResponse(BaseModel):
    """Final workflow response returned by FastAPI."""
    status: str = Field(..., description="'completed', 'failed', or 'max_iterations_exceeded'")
    query: str
    plan: Optional[str] = None
    final_code: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    iteration_count: int
    execution_logs: List[str] = Field(default_factory=list)
    review_feedback: Optional[str] = None

