"""Zero-dependency standalone test runner for Autonomous Code & Analysis Workspace.

Tests all layers: state validation, edge routing, individual async nodes, and full graph cycle.
Run with:
    python scripts/run_tests.py
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph.state import AgentState, AgentStateModel
from app.graph.edges import route_after_execution
from app.graph.nodes.planner import planner_node
from app.graph.nodes.coder import coder_node
from app.graph.nodes.executor import executor_node
from app.graph.nodes.reviewer import reviewer_node
from app.graph.workflow import create_code_workspace_graph
from app.services.docker_sandbox import DockerSandbox, ExecutionResult
from app.services import gemini_service, docker_sandbox

# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _base_state() -> AgentState:
    return {
        "user_query": "Find median of [3,1,4,1,5,9,2,6]",
        "plan": None,
        "generated_code": None,
        "stdout": None,
        "stderr": None,
        "exit_code": None,
        "error_trace": None,
        "review_feedback": None,
        "iteration_count": 0,
        "max_iterations": 3,
        "execution_logs": [],
        "status": "initialized",
        "final_result": None,
    }

# ─────────────────────────────────────────────
# Test Cases
# ─────────────────────────────────────────────

def test_state_validation():
    print("  [TEST] State schema validation... ", end="", flush=True)
    m = AgentStateModel(user_query="test", max_iterations=4)
    assert m.user_query == "test"
    assert m.max_iterations == 4
    assert m.iteration_count == 0
    assert m.status == "initialized"
    print("PASSED")


def test_edge_routing():
    print("  [TEST] Conditional edges & circuit breakers... ", end="", flush=True)
    assert route_after_execution({"exit_code": 0, "iteration_count": 1, "max_iterations": 5}) == "success"
    assert route_after_execution({"exit_code": 1, "iteration_count": 2, "max_iterations": 5}) == "reviewer"
    assert route_after_execution({"exit_code": 1, "iteration_count": 5, "max_iterations": 5}) == "max_iterations_reached"
    print("PASSED")


async def test_individual_async_nodes():
    print("  [TEST] Async agent nodes (Planner, Coder, Reviewer)... ", end="", flush=True)
    state = _base_state()

    # Mock Gemini — match actual prompt strings used by each node
    async def mock_gemini(prompt, system_instruction=None, temperature=None):
        p = prompt.lower()
        if "create a concise step-by-step" in p:
            # planner prompt
            return "1. Use statistics.median\n2. Print result"
        elif "fix the broken python code" in p:
            # coder repair prompt
            return "```python\nimport statistics\nprint(statistics.median([3,1,4,1,5,9,2,6]))\n```"
        else:
            # coder initial prompt
            return "```python\nimport statistics\nprint(statistics.median([3,1,4,1,5,9,2,6]))\n```"

    orig = gemini_service.generate_text_async
    gemini_service.generate_text_async = mock_gemini

    try:
        p_res = await planner_node(state)
        assert "plan" in p_res and p_res["status"] == "planned"
        state["plan"] = p_res["plan"]

        c_res = await coder_node(state)
        assert "generated_code" in c_res and c_res["status"] == "coding_completed"
        assert "print" in c_res["generated_code"]
        state["generated_code"] = c_res["generated_code"]
        state["exit_code"] = 1
        state["stderr"] = "NameError: name 'x' is not defined"

        r_res = await reviewer_node(state)
        assert "review_feedback" in r_res and r_res["status"] == "review_completed"
    finally:
        gemini_service.generate_text_async = orig

    print("PASSED")


async def test_full_graph_self_healing():
    print("  [TEST] Full LangGraph self-healing cycle... ", end="", flush=True)

    async def mock_gemini(prompt, system_instruction=None, temperature=None):
        p_lower = prompt.lower()
        if "create a concise step-by-step" in p_lower:
            return "1. Use statistics module\n2. Print median"
        elif "fix the broken python code" in p_lower:
            return "```python\nimport statistics\ndata=[3,1,4,1,5]\nprint(statistics.median(data))\n```"
        else:
            return "```python\nimport numpy as np\nprint(np.median([3,1,4,1,5]))\n```"  # will fail

    attempt = 0
    async def mock_docker(code, timeout_seconds=None, image_name=None):
        nonlocal attempt
        attempt += 1
        if attempt == 1:
            return ExecutionResult(stdout="", stderr="ModuleNotFoundError: No module named 'numpy'", exit_code=1, error_trace="No module named 'numpy'")
        return ExecutionResult(stdout="3.0\n", stderr="", exit_code=0, error_trace=None)

    orig_g = gemini_service.generate_text_async
    orig_d = docker_sandbox.execute_code_async
    gemini_service.generate_text_async = mock_gemini
    docker_sandbox.execute_code_async = mock_docker

    try:
        graph = create_code_workspace_graph()
        state = _base_state()
        final = await graph.ainvoke(state)
        assert final["exit_code"] == 0, f"Expected exit_code=0, got {final['exit_code']}"
        assert final["iteration_count"] == 2, f"Expected 2 iterations, got {final['iteration_count']}"
        assert attempt == 2
    finally:
        gemini_service.generate_text_async = orig_g
        docker_sandbox.execute_code_async = orig_d

    print("PASSED")


def test_docker_mock_fallback():
    print("  [TEST] Subprocess fallback (no daemon)... ", end="", flush=True)
    sb = DockerSandbox()
    sb.client = None  # simulate Docker being offline
    result = sb.execute_code("print('hello from subprocess')")
    assert result.exit_code == 0, f"Expected exit 0, got {result.exit_code}: {result.stderr}"
    assert "hello from subprocess" in result.stdout, f"Unexpected stdout: {result.stdout!r}"
    print("PASSED")


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

async def run_all():
    test_state_validation()
    test_edge_routing()
    await test_individual_async_nodes()
    await test_full_graph_self_healing()
    test_docker_mock_fallback()


def main():
    print("=" * 55)
    print("  AUTONOMOUS WORKSPACE — STANDALONE TEST RUNNER        ")
    print("=" * 55)
    try:
        asyncio.run(run_all())
        print("\n  [ALL TESTS PASSED]\n")
    except AssertionError as e:
        print(f"\n  [FAILED] AssertionError: {e}\n")
        sys.exit(1)
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"\n  [ERROR] {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
