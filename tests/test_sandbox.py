"""Tests for Docker sandbox execution logic."""

from unittest.mock import MagicMock
from app.services.docker_sandbox import DockerSandbox, ExecutionResult


def test_sandbox_subprocess_fallback():
    """Without Docker, code really runs in a local subprocess."""
    sandbox = DockerSandbox()
    sandbox.client = None
    result = sandbox.execute_code("print(6 * 7)")
    assert isinstance(result, ExecutionResult)
    assert result.exit_code == 0
    assert result.stdout.strip() == "42"


def test_sandbox_subprocess_unicode_output():
    """Non-ASCII output must not crash on Windows' cp1252 default encoding."""
    sandbox = DockerSandbox()
    sandbox.client = None
    result = sandbox.execute_code("print('φ ≈ 1.618 ✓')")
    assert result.exit_code == 0, result.stderr
    assert "φ" in result.stdout


def test_sandbox_subprocess_error_exit_code():
    sandbox = DockerSandbox()
    sandbox.client = None
    result = sandbox.execute_code("raise ValueError('boom')")
    assert result.exit_code != 0
    assert "ValueError" in result.stderr


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

