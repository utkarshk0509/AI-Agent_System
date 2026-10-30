"""Tests for isolated agent nodes."""

from app.graph.nodes.planner import planner_node
from app.graph.nodes.coder import coder_node
from app.graph.nodes.executor import executor_node
from app.graph.nodes.reviewer import reviewer_node
from app.graph.state import AgentState


def test_planner_node(mock_gemini_service, sample_initial_state):
    result = planner_node(sample_initial_state)
    assert "plan" in result
    assert result["status"] == "planned"
    assert len(result["execution_logs"]) == 1


def test_coder_node_initial(mock_gemini_service, sample_initial_state):
    sample_initial_state["plan"] = "1. Step one"
    result = coder_node(sample_initial_state)
    assert "generated_code" in result
    assert "print" in result["generated_code"]
    assert result["status"] == "coding_completed"


def test_executor_node_success(mock_docker_success, sample_initial_state):
    sample_initial_state["generated_code"] = "print('hello')"
    result = executor_node(sample_initial_state)
    assert result["exit_code"] == 0
    assert result["status"] == "execution_success"
    assert result["iteration_count"] == 1
    assert result["final_result"] is not None


def test_reviewer_node(mock_gemini_service, sample_initial_state):
    sample_initial_state["generated_code"] = "print(undefined_var)"
    sample_initial_state["stderr"] = "NameError: name 'undefined_var' is not defined"
    sample_initial_state["exit_code"] = 1
    
    result = reviewer_node(sample_initial_state)
    assert "review_feedback" in result
    assert result["status"] == "review_completed"
