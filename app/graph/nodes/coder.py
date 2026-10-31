"""Coder Node: Generates or repairs Python code using the Gemini API.

FIX: Now async — uses gemini_service.generate_text_async() so it doesn't block the event loop.
"""

import re
from typing import Dict, Any
from app.graph.state import AgentState
from app.services.gemini_service import gemini_service

CODER_SYSTEM_INSTRUCTION = """
You are an expert Python Engineer. Write clean, robust, self-contained Python 3.11 code.

STRICT RULES:
1. Output ONLY code inside ```python ``` fences. Nothing else — no explanations, no markdown prose.
2. Code must be fully self-contained: all imports, data, logic, and print() output included.
3. Use ONLY Python standard library modules (math, json, random, statistics, itertools, etc.).
   Do NOT import numpy, pandas, requests, or any third-party library unless told the sandbox has it.
4. Always print final results to stdout using print().
5. No input() calls, no file reads from external paths.
6. If fixing code, apply the reviewer's fix instructions exactly and return the complete fixed script.
"""


def _extract_python_code(raw_text: str) -> str:
    """Strips markdown fences and returns raw Python code."""
    pattern = r"```(?:python)?\s*(.*?)\s*```"
    matches = re.findall(pattern, raw_text, re.DOTALL)
    if matches:
        return matches[0].strip()
    # If no fences found, return as-is (Gemini sometimes skips fences)
    return raw_text.strip()


async def coder_node(state: AgentState) -> Dict[str, Any]:
    """Async coder: generates initial code or repairs failing code based on reviewer feedback."""
    query = state.get("user_query", "")
    plan = state.get("plan", "")
    existing_code = state.get("generated_code")
    review_feedback = state.get("review_feedback")
    error_trace = state.get("error_trace")
    iteration = state.get("iteration_count", 0)

    is_repair = bool(review_feedback and existing_code)

    if is_repair:
        print(f"\n[Coder] Repair iteration #{iteration + 1}...", flush=True)
        prompt = f"""
Task: Fix the broken Python code using the reviewer's instructions.

Original Query: {query}

Plan:
{plan}

Broken Code:
```python
{existing_code}
```

Error / Traceback:
{error_trace}

Reviewer Fix Instructions:
{review_feedback}

Provide the COMPLETE corrected Python script.
"""
        log_msg = f"[Coder Node] Repaired code for iteration #{iteration + 1}."
    else:
        print(f"\n[Coder] Generating initial code...", flush=True)
        prompt = f"""
Task: Write self-contained Python code to solve this task.

User Query: {query}

Plan:
{plan}

Provide the complete, executable Python script.
"""
        log_msg = "[Coder Node] Generated initial Python code."

    raw_response = await gemini_service.generate_text_async(
        prompt=prompt,
        system_instruction=CODER_SYSTEM_INSTRUCTION,
        temperature=0.1,
    )

    clean_code = _extract_python_code(raw_response)
    print(f"[Coder] Code ready ({len(clean_code)} chars).", flush=True)

    return {
        "generated_code": clean_code,
        "status": "coding_completed",
        "execution_logs": [log_msg],
    }
