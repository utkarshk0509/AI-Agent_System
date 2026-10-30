"""Interactive testing and diagnostic CLI tool for Autonomous Code & Analysis Workspace.

Usage:
    python scripts/test_manual.py --mode=mock     # Tests full LangGraph cycle with zero dependencies
    python scripts/test_manual.py --mode=docker   # Tests Docker sandbox isolation and constraints
    python scripts/test_manual.py --mode=live     # Runs end-to-end with live Gemini 2.5 and Docker
"""

import sys
import os
import argparse
import asyncio

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.services.docker_sandbox import docker_sandbox, ExecutionResult
from app.services.gemini_service import gemini_service
from app.graph.workflow import create_code_workspace_graph


async def run_mock_test():
    print("\n=======================================================")
    print("  RUNNING MOCK ORCHESTRATION TEST (No External Deps)   ")
    print("=======================================================")
    
    # Temporarily monkeypatch to guarantee deterministic runs
    def mock_gemini(prompt, system_instruction=None, temperature=None):
        prompt_lower = prompt.lower()
        if "create a step-by-step implementation plan" in prompt_lower:
            return "1. Create synthetic data.\n2. Compute mean and variance.\n3. Print JSON."
        elif "fix the following python code" in prompt_lower or "reviewer feedback" in prompt_lower:
            return "```python\nimport json\nprint(json.dumps({'status': 'fixed', 'result': 42}))\n```"
        elif "write self-contained python code" in prompt_lower:
            return "```python\nimport json\nprint(json.dumps({'status': 'ok', 'result': 42}))\n```"
        else:
            return "```python\nimport json\nprint(json.dumps({'status': 'ok', 'result': 42}))\n```"

    def mock_docker(code, timeout_seconds=None):
        return ExecutionResult(
            stdout='{"status": "ok", "result": 42}\n',
            stderr="",
            exit_code=0,
            error_trace=None,
        )

    gemini_service.generate_text = mock_gemini
    docker_sandbox.execute_code = mock_docker

    graph = create_code_workspace_graph()
    
    initial_state = {
        "user_query": "Calculate mean and variance of [10, 20, 30, 40, 50] and output JSON.",
        "plan": None,
        "generated_code": None,
        "stdout": None,
        "stderr": None,
        "exit_code": None,
        "error_trace": None,
        "review_feedback": None,
        "iteration_count": 0,
        "max_iterations": 3,
        "execution_logs": ["[CLI] Starting mock test."],
        "status": "initialized",
        "final_result": None,
    }

    print("[1/3] Triggering LangGraph ainvoke()...")
    final_state = await graph.ainvoke(initial_state)

    print("\n[2/3] Verification Results:")
    print(f"  - Status:         {final_state.get('status')}")
    print(f"  - Exit Code:      {final_state.get('exit_code')}")
    print(f"  - Iterations:     {final_state.get('iteration_count')}")
    print(f"  - Generated Code:\n{final_state.get('generated_code')}")
    print(f"  - Final Stdout:   {final_state.get('final_result')}")
    
    print("\n[3/3] Execution Log Audit:")
    for log in final_state.get("execution_logs", []):
        print(f"    • {log}")

    print("\n[SUCCESS] Mock test completed cleanly!\n")


def run_docker_test():
    print("\n=======================================================")
    print("        RUNNING DOCKER SANDBOX ISOLATION TEST          ")
    print("=======================================================")
    
    if not docker_sandbox.client:
        print("[ERROR] Docker daemon is not accessible. Please ensure Docker Desktop/Engine is running.")
        sys.exit(1)

    print("[1/3] Testing standard script execution in container...")
    code_ok = "import sys\nprint('Hello from isolated Docker sandbox!')\nsys.stdout.flush()"
    res_ok = docker_sandbox.execute_code(code_ok)
    print(f"  - Exit Code: {res_ok.exit_code}")
    print(f"  - Stdout:    {res_ok.stdout.strip()}")
    assert res_ok.exit_code == 0, "Clean execution failed!"

    print("\n[2/3] Testing error handling & traceback capture...")
    code_err = "raise ValueError('Intentional deliberate runtime error for testing')"
    res_err = docker_sandbox.execute_code(code_err)
    print(f"  - Exit Code: {res_err.exit_code}")
    print(f"  - Stderr:    {res_err.stderr.strip()[:100]}...")
    assert res_err.exit_code != 0, "Error capture failed!"

    print("\n[3/3] Testing timeout execution guardrail...")
    code_hang = "import time\ntime.sleep(10)"
    res_timeout = docker_sandbox.execute_code(code_hang, timeout_seconds=2)
    print(f"  - Exit Code: {res_timeout.exit_code} (Expected 124)")
    print(f"  - Stderr:    {res_timeout.stderr.strip()}")
    assert res_timeout.exit_code == 124, "Timeout enforcement failed!"

    print("\n[SUCCESS] Docker sandbox verified: execution, errors, and timeouts all guarded.\n")


async def run_live_test():
    print("\n=======================================================")
    print("      RUNNING END-TO-END LIVE WORKSPACE TEST           ")
    print("=======================================================")

    if not settings.GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY not found in environment or .env file.")
        sys.exit(1)

    graph = create_code_workspace_graph()
    query = "Find the sum of all primes under 50 and print a clean JSON object with keys 'primes' and 'sum'."

    print(f"Query: {query}")
    initial_state = {
        "user_query": query,
        "plan": None,
        "generated_code": None,
        "stdout": None,
        "stderr": None,
        "exit_code": None,
        "error_trace": None,
        "review_feedback": None,
        "iteration_count": 0,
        "max_iterations": 5,
        "execution_logs": ["[CLI] Live run started."],
        "status": "initialized",
        "final_result": None,
    }

    final_state = await graph.ainvoke(initial_state)

    print("\n=== Workflow Complete ===")
    print(f"Exit Code:   {final_state.get('exit_code')}")
    print(f"Iterations:  {final_state.get('iteration_count')}")
    print(f"Code:\n{final_state.get('generated_code')}")
    print(f"Result:\n{final_state.get('stdout')}")


def main():
    parser = argparse.ArgumentParser(description="Test Autonomous Code Workspace")
    parser.add_argument("--mode", choices=["mock", "docker", "live"], default="mock", help="Test mode")
    args = parser.parse_args()

    if args.mode == "mock":
        asyncio.run(run_mock_test())
    elif args.mode == "docker":
        run_docker_test()
    elif args.mode == "live":
        asyncio.run(run_live_test())


if __name__ == "__main__":
    main()
