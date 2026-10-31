"""Pytest test configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from app.graph.state import AgentState
from app.services.docker_sandbox import ExecutionResult


@pytest.fixture
def sample_initial_state() -> AgentState:
    """Returns a pristine initial agent state."""
    return {
        "user_query": "Calculate the first 10 prime numbers and print them.",
        "plan": None,
        "generated_code": None,
        "stdout": None,
        "stderr": None,
        "exit_code": None,
        "error_trace": None,
        "review_feedback": None,
        "iteration_count": 0,
        "max_iterations": 3,
        "execution_logs": ["[System] Test initialized."],
        "status": "initialized",
        "final_result": None,
    }


@pytest.fixture
def mock_gemini_service(monkeypatch):
    """Mocks GeminiService.generate_text_async to return predictable outputs."""
    from app.services import gemini_service

    async def fake_generate_text_async(prompt, system_instruction=None, temperature=None):
        prompt_lower = prompt.lower()
        if "create a concise step-by-step implementation plan" in prompt_lower:
            return "1. Define sieve function.\n2. Collect primes.\n3. Print primes."
        elif "fix the broken python code" in prompt_lower:
            return "```python\nprint('Fixed: Primes are [2, 3, 5, 7, 11]')\n```"
        elif "analyze this code execution failure" in prompt_lower:
            return "ROOT CAUSE: NameError. FIX: Define the variable before use."
        else:
            return "```python\nprint('Primes are [2, 3, 5, 7, 11]')\n```"

    # Also patch sync version for fallback paths
    def fake_generate_text(prompt, system_instruction=None, temperature=None):
        return "```python\nprint('Primes are [2, 3, 5, 7, 11]')\n```"

    monkeypatch.setattr(gemini_service, "generate_text_async", fake_generate_text_async)
    monkeypatch.setattr(gemini_service, "generate_text", fake_generate_text)
    return gemini_service


@pytest.fixture
def mock_docker_success(monkeypatch):
    """Mocks DockerSandbox.execute_code_async to simulate clean execution."""
    from app.services import docker_sandbox

    async def fake_execute_async(code, timeout_seconds=None, image_name=None):
        return ExecutionResult(
            stdout="Primes are [2, 3, 5, 7, 11]\n",
            stderr="",
            exit_code=0,
            error_trace=None,
        )

    monkeypatch.setattr(docker_sandbox, "execute_code_async", fake_execute_async)
    return docker_sandbox


@pytest.fixture
def mock_docker_failure(monkeypatch):
    """Mocks DockerSandbox.execute_code_async to simulate a runtime failure."""
    from app.services import docker_sandbox

    async def fake_execute_async(code, timeout_seconds=None, image_name=None):
        return ExecutionResult(
            stdout="",
            stderr="Traceback (most recent call last):\n  File 'script.py', line 2\nNameError: name 'x' is not defined",
            exit_code=1,
            error_trace="NameError: name 'x' is not defined",
        )

    monkeypatch.setattr(docker_sandbox, "execute_code_async", fake_execute_async)
    return docker_sandbox
