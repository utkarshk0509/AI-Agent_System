from typing import Literal

from app.graph.state import AgentState


def route_after_execution(state: AgentState) -> Literal["success", "reviewer", "max_iterations_reached"]:
    """Decide where to go after the executor runs the code."""
    exit_code = state.get("exit_code")
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 5)
    has_output = bool((state.get("stdout") or "").strip())

    # A script that exits 0 but prints nothing hasn't answered anything,
    # so it goes back for a fix too.
    if exit_code == 0 and has_output:
        return "success"

    # Stop here so a script that keeps failing can't loop (and call the API) forever
    if iteration_count >= max_iterations:
        return "max_iterations_reached"

    return "reviewer"
