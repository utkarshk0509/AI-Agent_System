import pytest

from app.services.docker_sandbox import ExecutionResult, docker_sandbox
from app.services.gemini_service import gemini_service


@pytest.fixture
def sample_initial_state():
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
    """Fake Gemini that answers based on which node's prompt it gets."""

    async def fake_generate(prompt, system_instruction=None, temperature=None):
        prompt_lower = prompt.lower()
        if "create a concise step-by-step implementation plan" in prompt_lower:
            return "1. Define sieve function.\n2. Collect primes.\n3. Print primes."
        if "fix the broken python code" in prompt_lower:
            return "```python\nprint('Fixed: Primes are [2, 3, 5, 7, 11]')\n```"
        if "analyze this code execution failure" in prompt_lower:
            return "ROOT CAUSE: NameError. FIX: Define the variable before use."
        return "```python\nprint('Primes are [2, 3, 5, 7, 11]')\n```"

    monkeypatch.setattr(gemini_service, "generate_text_async", fake_generate)
    return gemini_service


@pytest.fixture
def mock_docker_success(monkeypatch):
    async def fake_execute(code, timeout_seconds=None):
        return ExecutionResult(stdout="Primes are [2, 3, 5, 7, 11]\n", stderr="", exit_code=0)

    monkeypatch.setattr(docker_sandbox, "execute_code_async", fake_execute)
    return docker_sandbox


@pytest.fixture
def mock_docker_failure(monkeypatch):
    async def fake_execute(code, timeout_seconds=None):
        return ExecutionResult(
            stdout="",
            stderr="Traceback (most recent call last):\n  File 'script.py', line 2\nNameError: name 'x' is not defined",
            exit_code=1,
            error_trace="NameError: name 'x' is not defined",
        )

    monkeypatch.setattr(docker_sandbox, "execute_code_async", fake_execute)
    return docker_sandbox
