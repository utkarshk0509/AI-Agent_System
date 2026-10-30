"""Planner Node: Breaks the user query into structured coding tasks."""

from typing import Dict, Any
from app.graph.state import AgentState
from app.services.gemini_service import gemini_service

PLANNER_SYSTEM_INSTRUCTION = """
You are a Principal Data Systems Architect. Your job is to analyze the user's data analysis 
or calculation request and break it into a clear, deterministic Python execution plan.

Guidelines:
1. Define the input data format, mock data structures (if none provided), and required libraries.
2. Outline step-by-step algorithmic transformations.
3. Require that the resulting Python script prints clean, structured summary output to stdout.
4. Keep the plan concise, practical, and directly translatable into self-contained Python code.
"""

def planner_node(state: AgentState) -> Dict[str, Any]:
    """Analyzes the user_query and produces an actionable implementation plan."""
    query = state.get("user_query", "")
    
    prompt = f"Create a step-by-step implementation plan for the following data query:\n\n{query}"
    
    # In production, call Gemini 2.5 API via gemini_service
    plan_output = gemini_service.generate_text(
        prompt=prompt,
        system_instruction=PLANNER_SYSTEM_INSTRUCTION,
        temperature=0.2,
    )
    
    return {
        "plan": plan_output,
        "status": "planned",
        "execution_logs": ["[Planner Node] Formulated execution plan."],
    }

