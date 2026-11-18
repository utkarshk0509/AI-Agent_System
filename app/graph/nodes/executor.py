"""Executor: runs the generated script in the sandbox and records the result."""

from typing import Any, Dict

from app.graph.state import AgentState
from app.services.docker_sandbox import docker_sandbox


async def executor_node(state: AgentState) -> Dict[str, Any]:
    code = state.get("generated_code")
    attempt = state.get("iteration_count", 0) + 1

    print(f"\n[Executor] Running code (attempt #{attempt})...", flush=True)

    if not code:
        print("[Executor] No code provided — aborting.", flush=True)
        return {
            "iteration_count": attempt,
            "stdout": "",
            "stderr": "No code was generated to execute.",
            "exit_code": -1,
            "error_trace": "ValueError: Empty code block received by executor node.",
            "status": "execution_failed",
            "execution_logs": [f"[Executor Node] Attempt #{attempt} — No code provided."],
        }

    result = await docker_sandbox.execute_code_async(code)

    printed_something = bool(result.stdout.strip())
    is_success = result.exit_code == 0 and printed_something

    if is_success:
        log_status = "SUCCESS"
    elif result.exit_code == 0:
        # Exited cleanly but printed nothing. Tell the reviewer why this counts as a failure.
        log_status = "FAILED (no output)"
        result.error_trace = (
            "The script exited cleanly but printed NOTHING to stdout, so no answer "
            "was produced. The final result must be printed with print()."
        )
    else:
        log_status = f"FAILED (exit={result.exit_code})"

    print(f"[Executor] Attempt #{attempt} — {log_status}", flush=True)

    return {
        "iteration_count": attempt,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.exit_code,
        "error_trace": result.error_trace,
        "status": "execution_success" if is_success else "execution_error",
        "final_result": result.stdout if is_success else None,
        "execution_logs": [
            f"[Executor Node] Attempt #{attempt} — {log_status}. "
            f"stdout={len(result.stdout)} chars, stderr={len(result.stderr)} chars."
        ],
    }
