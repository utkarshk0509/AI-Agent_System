"""Executor Node: Runs generated Python code inside an isolated Docker sandbox.

FIX: Now async — uses docker_sandbox.execute_code_async() so container.wait()
     never blocks FastAPI's event loop.
"""

from typing import Dict, Any
from app.graph.state import AgentState
from app.services.docker_sandbox import docker_sandbox


async def executor_node(state: AgentState) -> Dict[str, Any]:
    """Async executor: runs code in Docker without freezing the server."""
    code = state.get("generated_code")
    current_iteration = state.get("iteration_count", 0) + 1

    print(f"\n[Executor] Running code (attempt #{current_iteration})...", flush=True)

    if not code:
        print("[Executor] No code provided — aborting.", flush=True)
        return {
            "iteration_count": current_iteration,
            "stdout": "",
            "stderr": "No code was generated to execute.",
            "exit_code": -1,
            "error_trace": "ValueError: Empty code block received by executor node.",
            "status": "execution_failed",
            "execution_logs": [f"[Executor Node] Attempt #{current_iteration} — No code provided."],
        }

    # FIX: Use async version — runs Docker SDK in thread pool, not event loop
    result = await docker_sandbox.execute_code_async(code)

    is_success = (result.exit_code == 0)
    log_status = "SUCCESS" if is_success else f"FAILED (exit={result.exit_code})"
    print(f"[Executor] Attempt #{current_iteration} — {log_status}", flush=True)

    updates: Dict[str, Any] = {
        "iteration_count": current_iteration,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "error_trace": result.error_trace,
        "status": "execution_success" if is_success else "execution_error",
        "execution_logs": [
            f"[Executor Node] Attempt #{current_iteration} — {log_status}. "
            f"stdout={len(result.stdout)} chars, stderr={len(result.stderr)} chars."
        ],
    }

    if is_success:
        updates["final_result"] = result.stdout

    return updates
