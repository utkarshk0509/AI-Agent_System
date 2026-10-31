"""Tests for Docker sandbox execution logic."""

from unittest.mock import MagicMock
from app.services.docker_sandbox import DockerSandbox, ExecutionResult


def test_sandbox_mock_fallback():
    """Verify fallback when Docker is unavailable."""
    sandbox = DockerSandbox()
    sandbox.client = None
    result = sandbox.execute_code("print('test')")
    assert isinstance(result, ExecutionResult)
    assert result.exit_code == 0
    assert "Mock Execution" in result.stdout


def test_sandbox_timeout_handling(monkeypatch):
    """Verify timeout is properly handled and returns exit code 124."""
    sandbox = DockerSandbox()
    
    # Mock container and client
    mock_container = MagicMock()
    mock_container.wait.side_effect = Exception("Read timed out")
    mock_client = MagicMock()
    mock_client.containers.run.return_value = mock_container
    sandbox.client = mock_client

    result = sandbox.execute_code("import time; time.sleep(10)", timeout_seconds=1)
    
    assert result.exit_code == 124
    assert "timed out" in result.stderr.lower()
    mock_container.kill.assert_called_once()
    mock_container.remove.assert_called_once()

