"""Reviewer Node: Analyzes stderr/tracebacks and produces targeted fix instructions.

FIX: Now async — uses gemini_service.generate_text_async() so it doesn't block the event loop.
     Also adds special handling for the most common sandbox error: missing third-party packages.
"""

from typing import Dict, Any
from app.graph.state import AgentState
from app.services.gemini_service import gemini_service

REVIEWER_SYSTEM_INSTRUCTION = """
You are a Principal Code Reviewer and Debugging Specialist.
Analyze the broken Python script and the runtime error.

Output ONLY structured fix instructions in this exact format:
1. ROOT CAUSE: One sentence — what exactly failed and why.
2. FIX: Bullet list of exact code changes to make.
3. CONSTRAINT REMINDER: The sandbox only has Python standard library. If error is a missing
   third-party import (numpy, pandas, requests, etc.), instruct the coder to rewrite using
   only standard library (math, statistics, json, random, itertools, collections, etc.).

Be concise. Maximum 10 lines. No code blocks — just instructions.
"""


async def reviewer_node(state: AgentState) -> Dict[str, Any]:
    """Async reviewer: diagnoses failures without blocking the event loop."""
    code = state.get("generated_code", "")
    stderr = state.get("stderr", "")
    error_trace = state.get("error_trace", "")
    query = state.get("user_query", "")
    iteration = state.get("iteration_count", 0)

    print(f"\n[Reviewer] Analyzing failure (iteration #{iteration})...", flush=True)

    # Common fast-path: detect third-party import errors before calling LLM
    error_text = stderr or error_trace or ""
    if "ModuleNotFoundError" in error_text or "No module named" in error_text:
        # Extract the module name for a precise fast fix
        import re
        match = re.search(r"No module named '([^']+)'", error_text)
        module_name = match.group(1) if match else "the missing module"
        feedback = (
            f"1. ROOT CAUSE: Code imports '{module_name}' which is NOT available in the sandbox. "
            f"Only Python standard library is available.\n"
            f"2. FIX: Rewrite the code to use ONLY standard library equivalents:\n"
            f"   - Replace numpy arrays → use list, math, statistics modules\n"
            f"   - Replace pandas DataFrames → use list of dicts or csv.DictReader\n"
            f"   - Replace requests → not needed (no network access in sandbox)\n"
            f"3. CONSTRAINT REMINDER: Sandbox = Python 3.11 standard library ONLY."
        )
        print(f"[Reviewer] Fast-path: detected missing module '{module_name}'. Skipping LLM call.", flush=True)
    else:
        prompt = f"""
Analyze this code execution failure and provide fix instructions.

User Query: {query}

Broken Code:
```python
{code}
```

Runtime Error:
{error_text}

Provide structured fix instructions (ROOT CAUSE, FIX, CONSTRAINT REMINDER).
"""
        feedback = await gemini_service.generate_text_async(
            prompt=prompt,
            system_instruction=REVIEWER_SYSTEM_INSTRUCTION,
            temperature=0.1,
        )

    print(f"[Reviewer] Fix instructions ready ({len(feedback)} chars).", flush=True)
    return {
        "review_feedback": feedback,
        "status": "review_completed",
        "execution_logs": ["[Reviewer Node] Generated fix instructions for coder."],
    }
