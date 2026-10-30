"""Tests for conditional edges and circuit breaker routing."""

from app.graph.edges import route_after_execution
from app.graph.state import AgentState


def test_route_success():
    """Exit code 0 must route directly to 'success'."""
    state: AgentState = {
        "user_query": "q",
        "plan": None,
        "generated_code": "print(1)",
        "stdout": "1\n",
        "stderr": "",
        "exit_code": 0,
        "error_trace": None,
        "review_feedback": None,
        "iteration_count": 1,
        "max_iterations": 5,
        "execution_logs": [],
        "status": "execution_success",
        "final_result": "1\n",
    }
    decision = route_after_execution(state)
    assert decision == "success"


def test_route_error_to_reviewer():
    """Non-zero exit code within iteration budget must route to 'reviewer'."""
    state: AgentState = {
        "user_query": "q",
        "plan": None,
        "generated_code": "invalid",
        "stdout": "",
        "stderr": "SyntaxError",
        "exit_code": 1,
        "error_trace": "SyntaxError",
        "review_feedback": None,
        "iteration_count": 2,
        "max_iterations": 5,
        "execution_logs": [],
        "status": "execution_error",
        "final_result": None,
    }
    decision = route_after_execution(state)
    assert decision == "reviewer"


def test_route_circuit_breaker_tripped():
    """When iteration_count reaches max_iterations, must trip circuit breaker to prevent infinite loops."""
    state: AgentState = {
        "user_query": "q",
        "plan": None,
        "generated_code": "invalid",
        "stdout": "",
        "stderr": "RuntimeError",
        "exit_code": 1,
        "error_trace": "RuntimeError",
        "review_feedback": None,
        "iteration_count": 5,
        "max_iterations": 5,
        "execution_logs": [],
        "status": "execution_error",
        "final_result": None,
    }
    decision = route_after_execution(state)
    assert decision == "max_iterations_reached"
