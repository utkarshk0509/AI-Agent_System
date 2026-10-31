"""Planner Node: Breaks the user query into a structured Python implementation plan.

FIX: Now async — uses gemini_service.generate_text_async() so it doesn't block the event loop.
"""

from typing import Dict, Any
from app.graph.state import AgentState
from app.services.gemini_service import gemini_service

PLANNER_SYSTEM_INSTRUCTION = """
You are a Principal Data Systems Architect. Analyze the user's request and produce a concise,
actionable implementation plan that a Python developer can directly code from.

Guidelines:
1. Define required libraries (standard lib only — no pip installs needed in sandbox).
2. Outline step-by-step algorithmic logic.
3. Specify what must be printed to stdout (format, keys, etc.).
4. Keep the plan SHORT — 5-8 bullet points maximum. No prose, no explanations.
"""


async def planner_node(state: AgentState) -> Dict[str, Any]:
    """Async planner: calls Gemini API without blocking the event loop."""
    query = state.get("user_query", "")
    print(f"\n{'='*50}\n[Planner] Planning for query: {query[:60]}...\n{'='*50}", flush=True)

    prompt = f"Create a concise step-by-step implementation plan for:\n\n{query}"

    plan_output = await gemini_service.generate_text_async(
        prompt=prompt,
        system_instruction=PLANNER_SYSTEM_INSTRUCTION,
        temperature=0.2,
    )

    print(f"[Planner] Plan ready ({len(plan_output)} chars).", flush=True)
    return {
        "plan": plan_output,
        "status": "planned",
        "execution_logs": ["[Planner Node] Formulated execution plan."],
    }
