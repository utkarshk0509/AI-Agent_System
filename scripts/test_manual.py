"""Manual checks you can run from the command line.

Usage:
    python scripts/test_manual.py --mode=mock     # full graph with fake Gemini + fake sandbox
    python scripts/test_manual.py --mode=docker   # real Docker sandbox: output, errors, timeout
    python scripts/test_manual.py --mode=live     # real Gemini + real sandbox (needs GEMINI_API_KEY)
"""

import argparse
import asyncio
import os
import sys

# Let the script import the app package when run from the repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.graph.workflow import create_code_workspace_graph
from app.services.docker_sandbox import ExecutionResult, docker_sandbox
from app.services.gemini_service import gemini_service


def new_state(query, max_iterations, first_log):
    return {
        "user_query": query,
        "plan": None,
        "generated_code": None,
        "stdout": None,
        "stderr": None,
        "exit_code": None,
        "error_trace": None,
        "review_feedback": None,
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "execution_logs": [first_log],
        "status": "initialized",
        "final_result": None,
    }


async def run_mock_test():
    print("\n=======================================================")
    print("  RUNNING MOCK ORCHESTRATION TEST (No External Deps)   ")
    print("=======================================================")

    # Swap in fakes so the run is the same every time
    async def mock_gemini(prompt, system_instruction=None, temperature=None):
        prompt_lower = prompt.lower()
        if "create a concise step-by-step implementation plan" in prompt_lower:
            return "1. Create the data.\n2. Compute mean and variance.\n3. Print JSON."
        if "program output" in prompt_lower:
            return "The mean is 30 and the variance is 250."
        return "```python\nimport json\nprint(json.dumps({'mean': 30, 'variance': 250}))\n```"

    async def mock_docker(code, timeout_seconds=None):
        return ExecutionResult(stdout='{"mean": 30, "variance": 250}\n', stderr="", exit_code=0)

    gemini_service.generate_text_async = mock_gemini
    docker_sandbox.execute_code_async = mock_docker

    graph = create_code_workspace_graph()
    initial_state = new_state(
        "Calculate mean and variance of [10, 20, 30, 40, 50] and output JSON.", 3, "[CLI] Starting mock test."
    )

    print("[1/3] Triggering LangGraph ainvoke()...")
    final_state = await graph.ainvoke(initial_state)

    print("\n[2/3] Verification Results:")
    print(f"  - Status:         {final_state.get('status')}")
    print(f"  - Exit Code:      {final_state.get('exit_code')}")
    print(f"  - Iterations:     {final_state.get('iteration_count')}")
    print(f"  - Generated Code:\n{final_state.get('generated_code')}")
    print(f"  - Answer:         {final_state.get('final_result')}")

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
    res_ok = docker_sandbox.execute_code("print('Hello from isolated Docker sandbox!')")
    print(f"  - Exit Code: {res_ok.exit_code}")
    print(f"  - Stdout:    {res_ok.stdout.strip()}")
    assert res_ok.exit_code == 0, "Clean execution failed!"

    print("\n[2/3] Testing error handling & traceback capture...")
    res_err = docker_sandbox.execute_code("raise ValueError('Intentional runtime error for testing')")
    print(f"  - Exit Code: {res_err.exit_code}")
    print(f"  - Stderr:    {res_err.stderr.strip()[:100]}...")
    assert res_err.exit_code != 0, "Error capture failed!"

    print("\n[3/3] Testing timeout execution guardrail...")
    res_timeout = docker_sandbox.execute_code("import time\ntime.sleep(10)", timeout_seconds=2)
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

    final_state = await graph.ainvoke(new_state(query, 5, "[CLI] Live run started."))

    print("\n=== Workflow Complete ===")
    print(f"Exit Code:   {final_state.get('exit_code')}")
    print(f"Iterations:  {final_state.get('iteration_count')}")
    print(f"Code:\n{final_state.get('generated_code')}")
    print(f"Output:\n{final_state.get('stdout')}")
    print(f"Answer:\n{final_state.get('final_result')}")


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
