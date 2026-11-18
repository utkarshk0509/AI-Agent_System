import operator
from typing import Annotated, List, Optional, TypedDict


class AgentState(TypedDict):
    """State shared by every node in the graph."""

    user_query: str
    plan: Optional[str]
    generated_code: Optional[str]

    # Result of the last run
    stdout: Optional[str]
    stderr: Optional[str]
    exit_code: Optional[int]
    error_trace: Optional[str]

    review_feedback: Optional[str]

    iteration_count: int
    max_iterations: int

    # operator.add makes LangGraph append each node's logs instead of replacing them
    execution_logs: Annotated[List[str], operator.add]

    status: str
    final_result: Optional[str]
