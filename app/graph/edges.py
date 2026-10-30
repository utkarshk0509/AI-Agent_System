"""Conditional edges and routing logic for the LangGraph StateGraph."""

from typing import Literal
from app.graph.state import AgentState


def route_after_execution(state: AgentState) -> Literal["success", "reviewer", "max_iterations_reached"]:
    """Determines whether to finish, proceed to review/repair, or abort due to limits.
    
    Circuit Breaker Rules:
    1. If exit_code == 0: The script executed cleanly -> route to 'success' (END).
    2. If iteration_count >= max_iterations: Circuit breaker trips to prevent infinite 
       repair loops and uncontrolled API spend -> route to 'max_iterations_reached' (END).
    3. If exit_code != 0 and iteration_count < max_iterations: Route to 'reviewer' node.
    """
    exit_code = state.get("exit_code")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 5)

    # 1. Clean execution check
    if exit_code == 0:
        return "success"

    # 2. Infinite loop prevention circuit breaker
    if iteration_count >= max_iterations:
        return "max_iterations_reached"

    # 3. Fault detected, route to reviewer for diagnosis
    return "reviewer"

