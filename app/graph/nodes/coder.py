"""Coder Node: Generates or refactors self-contained Python code using the Gemini 2.5 API."""

import re
from typing import Dict, Any
from app.graph.state import AgentState
from app.services.gemini_service import gemini_service

CODER_SYSTEM_INSTRUCTION = """
You are an expert Python Data Engineer. Write clean, robust, self-contained Python 3.11 code.
Rules:
1. Output ONLY executable Python code inside standard ```python ``` fences.
2. The code must be self-contained (all imports, data generation/fetching, processing, and output logic included).
3. Always print the final answer and meaningful telemetry to stdout using print().
4. Do not prompt for interactive input (no input() calls).
5. If fixing existing code, apply the specific instructions provided in the reviewer feedback.
"""

def _extract_python_code(raw_text: str) -> str:
    """Extracts raw python code from markdown code blocks if present."""
    pattern = r"```(?:python)?\s*(.*?)\s*```"
    matches = re.findall(pattern, raw_text, re.DOTALL)
    if matches:
        return matches[0].strip()
    return raw_text.strip()


def coder_node(state: AgentState) -> Dict[str, Any]:
    """Generates initial code or patches existing code based on review feedback."""
    query = state.get("user_query", "")
    plan = state.get("plan", "")
    existing_code = state.get("generated_code")
    review_feedback = state.get("review_feedback")
    error_trace = state.get("error_trace")
    iteration = state.get("iteration_count", 0)

    # Differentiate between initial generation and iterative debugging
    if review_feedback and existing_code:
        prompt = f"""
Task: Fix the following Python code based on the execution error and reviewer feedback.

Original Query:
{query}

Plan:
{plan}

Current Broken Code:
```python
{existing_code}
```

Error / Traceback:
{error_trace}

Reviewer Feedback & Fix Instructions:
{review_feedback}

Please provide the corrected, complete, and self-contained Python code.
"""
        log_msg = f"[Coder Node] Refactoring code for iteration #{iteration + 1} using reviewer feedback."
    else:
        prompt = f"""
Task: Write self-contained Python code to solve the following data analysis task.

User Query:
{query}

Plan:
{plan}

Please provide the complete, executable Python code.
"""
        log_msg = f"[Coder Node] Generated initial Python code."

    # Invoke Gemini 2.5 API
    raw_response = gemini_service.generate_text(
        prompt=prompt,
        system_instruction=CODER_SYSTEM_INSTRUCTION,
        temperature=0.1,  # Low temperature for precise code generation
    )

    clean_code = _extract_python_code(raw_response)

    return {
        "generated_code": clean_code,
        "status": "coding_completed",
        "execution_logs": [log_msg],
    }

