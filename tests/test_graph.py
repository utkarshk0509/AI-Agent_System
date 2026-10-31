"""End-to-End LangGraph orchestration tests."""

import pytest
from app.graph.workflow import create_code_workspace_graph
from app.services.docker_sandbox import ExecutionResult


@pytest.mark.asyncio
async def test_workflow_clean_success(mock_gemini_service, mock_docker_success, sample_initial_state):
    """Test full workflow where execution succeeds on the first attempt."""
    graph = create_code_workspace_graph()
    final_state = await graph.ainvoke(sample_initial_state)

    assert final_state["exit_code"] == 0
    assert final_state["status"] == "execution_success"
    assert final_state["iteration_count"] == 1
    assert final_state["plan"] is not None
    assert final_state["generated_code"] is not None


@pytest.mark.asyncio
async def test_workflow_repair_loop_success(monkeypatch, mock_gemini_service, sample_initial_state):
    """Test workflow that fails on iteration 1, routes to reviewer, fixes, and passes on iteration 2."""
    from app.services import docker_sandbox
    
    call_count = 0

    def fail_then_succeed(code, timeout_seconds=None):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return ExecutionResult(
                stdout="",
                stderr="NameError: name 'x' is not defined",
                exit_code=1,
                error_trace="NameError: name 'x' is not defined",
            )
        else:
            return ExecutionResult(
                stdout="Success: 55\n",
                stderr="",
                exit_code=0,
                error_trace=None,
            )

    monkeypatch.setattr(docker_sandbox, "execute_code", fail_then_succeed)

    graph = create_code_workspace_graph()
    final_state = await graph.ainvoke(sample_initial_state)

    assert final_state["exit_code"] == 0
    assert final_state["iteration_count"] == 2
    assert final_state["review_feedback"] is not None
    assert call_count == 2


@pytest.mark.asyncio
async def test_workflow_circuit_breaker(mock_gemini_service, mock_docker_failure, sample_initial_state):
    """Test that recurring failure terminates safely once max_iterations is reached."""
    sample_initial_state["max_iterations"] = 3
    
    graph = create_code_workspace_graph()
    final_state = await graph.ainvoke(sample_initial_state)

    assert final_state["exit_code"] == 1
    assert final_state["iteration_count"] == 3

