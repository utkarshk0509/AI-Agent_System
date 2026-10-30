"""Reviewer Node: Analyzes stderr, tracebacks, and code logic to produce fix guidance."""

from typing import Dict, Any
from app.graph.state import AgentState
from app.services.gemini_service import gemini_service

REVIEWER_SYSTEM_INSTRUCTION = """
You are a Principal Code Reviewer and Debugging Specialist. 
Analyze the broken Python script and the runtime error/traceback.

Output structured, concise debugging instructions:
1. Root Cause: Identify the exact line and semantic reason for the failure (e.g., missing package, KeyError, division by zero, invalid Docker command).
2. Fix Strategy: Specify exactly what code modifications are required.
3. Verification: Note any edge cases that must be guarded against.

Keep instructions actionable and directly targeted at the Coder Agent.
"""

def reviewer_node(state: AgentState) -> Dict[str, Any]:
    """Inspects execution failures and generates remediation instructions."""
    code = state.get("generated_code", "")
    stderr = state.get("stderr", "")
    error_trace = state.get("error_trace", "")
    query = state.get("user_query", "")

    prompt = f"""
Analyze this code execution failure and provide remediation guidance.

Original User Query:
{query}

Broken Code:
```python
{code}
```

Runtime stderr / Exception:
{stderr or error_trace}

Provide concise, precise correction instructions for the coder agent.
"""

    feedback = gemini_service.generate_text(
        prompt=prompt,
        system_instruction=REVIEWER_SYSTEM_INSTRUCTION,
        temperature=0.1,
    )

    return {
        "review_feedback": feedback,
        "status": "review_completed",
        "execution_logs": ["[Reviewer Node] Diagnostic review generated actionable fix instructions."],
    }

