"""Tests for State models and validation."""

from app.graph.state import AgentState, AgentStateModel


def test_agent_state_model_valid():
    """Verify that a valid dictionary parses cleanly into AgentStateModel."""
    data = {
        "user_query": "Test query",
        "iteration_count": 0,
        "max_iterations": 5,
        "execution_logs": ["Init"],
    }
    model = AgentStateModel(**data)
    assert model.user_query == "Test query"
    assert model.iteration_count == 0
    assert model.max_iterations == 5
    assert model.status == "initialized"
    assert model.execution_logs == ["Init"]


def test_agent_state_model_defaults():
    """Verify default values and optional fields in AgentStateModel."""
    model = AgentStateModel(user_query="Minimal query")
    assert model.plan is None
    assert model.generated_code is None
    assert model.exit_code is None
    assert model.iteration_count == 0
    assert model.max_iterations == 5
    assert model.execution_logs == []
