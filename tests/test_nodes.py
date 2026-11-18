"""Tests for isolated agent nodes."""

import pytest

from app.graph.nodes.answer import answer_node
from app.graph.nodes.coder import coder_node, extract_code
from app.graph.nodes.executor import executor_node
from app.graph.nodes.planner import planner_node
from app.graph.nodes.reviewer import reviewer_node
from app.services.docker_sandbox import ExecutionResult, docker_sandbox
from app.services.gemini_service import GeminiUnavailableError, gemini_service


@pytest.mark.asyncio
async def test_planner_node(mock_gemini_service, sample_initial_state):
    result = await planner_node(sample_initial_state)
    assert "plan" in result
    assert result["status"] == "planned"
    assert len(result["execution_logs"]) == 1


@pytest.mark.asyncio
async def test_coder_node_initial(mock_gemini_service, sample_initial_state):
    sample_initial_state["plan"] = "1. Step one"
    result = await coder_node(sample_initial_state)
    assert "generated_code" in result
    assert "print" in result["generated_code"]
    assert result["status"] == "coding_completed"


@pytest.mark.asyncio
async def test_executor_node_success(mock_docker_success, sample_initial_state):
    sample_initial_state["generated_code"] = "print('hello')"
    result = await executor_node(sample_initial_state)
    assert result["exit_code"] == 0
    assert result["status"] == "execution_success"
    assert result["iteration_count"] == 1
    assert result["final_result"] is not None


@pytest.mark.asyncio
async def test_reviewer_node(mock_gemini_service, sample_initial_state):
    sample_initial_state["generated_code"] = "print(undefined_var)"
    sample_initial_state["stderr"] = "NameError: name 'undefined_var' is not defined"
    sample_initial_state["exit_code"] = 1

    result = await reviewer_node(sample_initial_state)
    assert "review_feedback" in result
    assert result["status"] == "review_completed"


@pytest.mark.asyncio
async def test_executor_node_empty_output_is_failure(monkeypatch, sample_initial_state):
    """exit 0 with no stdout produced no answer and must not count as success."""
    async def fake(code, timeout_seconds=None):
        return ExecutionResult(stdout="", stderr="", exit_code=0)

    monkeypatch.setattr(docker_sandbox, "execute_code_async", fake)
    sample_initial_state["generated_code"] = "x = 1"
    result = await executor_node(sample_initial_state)
    assert result["status"] == "execution_error"
    assert result["final_result"] is None
    assert "printed NOTHING" in result["error_trace"]


@pytest.mark.asyncio
async def test_answer_node_falls_back_to_stdout(monkeypatch, sample_initial_state):
    async def boom(*a, **k):
        raise GeminiUnavailableError("down")

    monkeypatch.setattr(gemini_service, "generate_text_async", boom)
    sample_initial_state["stdout"] = "42\n"
    result = await answer_node(sample_initial_state)
    assert result["final_result"] == "42"
    assert result["status"] == "completed"


def test_extract_code_strips_fences():
    assert extract_code("Here you go:\n```python\nprint(1)\n```\nDone.") == "print(1)"
    assert extract_code("  print(2)  ") == "print(2)"
