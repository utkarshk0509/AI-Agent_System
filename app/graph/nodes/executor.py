"""Executor Node: Executes Python code inside an isolated Docker sandbox."""

from typing import Dict, Any
from app.graph.state import AgentState
from app.services.docker_sandbox import docker_sandbox


def executor_node(state: AgentState) -> Dict[str, Any]:
    """Executes the generated code inside an isolated Docker container and captures telemetry."""
    code = state.get("generated_code")
    current_iteration = state.get("iteration_count", 0) + 1
    
    if not code:
        return {
            "iteration_count": current_iteration,
            "stdout": "",
            "stderr": "No code was generated to execute.",
            "exit_code": -1,
            "error_trace": "ValueError: Empty code block received by executor node.",
            "status": "execution_failed",
            "execution_logs": [f"[Executor Node] Execution failed on attempt #{current_iteration}: No code provided."],
        }

    # Execute code in Docker container sandbox
    result = docker_sandbox.execute_code(code)

    is_success = (result.exit_code == 0)
    log_status = "SUCCESS" if is_success else f"FAILED (exit code {result.exit_code})"

    updates: Dict[str, Any] = {
        "iteration_count": current_iteration,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "error_trace": result.error_trace,
        "status": "execution_success" if is_success else "execution_error",
        "execution_logs": [
            f"[Executor Node] Attempt #{current_iteration} - {log_status}. "
            f"Stdout length: {len(result.stdout)} chars, Stderr length: {len(result.stderr)} chars."
        ],
    }

    if is_success:
        updates["final_result"] = result.stdout

    return updates

