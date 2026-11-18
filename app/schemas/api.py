from typing import List, Optional

from pydantic import BaseModel, Field


class CodeExecutionRequest(BaseModel):
    query: str
    max_iterations: Optional[int] = Field(default=5, ge=1, le=10)


class CodeExecutionResponse(BaseModel):
    status: str  # "completed", "failed" or "max_iterations_exceeded"
    query: str
    answer: Optional[str] = None
    plan: Optional[str] = None
    final_code: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    exit_code: Optional[int] = None
    iteration_count: int
    execution_logs: List[str] = Field(default_factory=list)
    review_feedback: Optional[str] = None
