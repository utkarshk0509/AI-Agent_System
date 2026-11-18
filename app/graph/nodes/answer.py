"""Answer: turns the script's raw output into a direct answer to the question.

If the Gemini call fails, the raw stdout is returned instead so a successful
run never loses its result.
"""

from typing import Any, Dict

from app.graph.state import AgentState
from app.services.gemini_service import gemini_service

ANSWER_SYSTEM_INSTRUCTION = """
You answer the user's question using ONLY the program output provided.
- Lead with the direct answer, stating the actual computed values (numbers, names,
  lists) from the output. Never say a value "was computed" without stating it.
- Then list any remaining key results from the output (short bullet list, or keep JSON as-is).
- Do not invent values that are not in the output. Do not describe the code.
"""

MAX_OUTPUT_CHARS = 12_000


async def answer_node(state: AgentState) -> Dict[str, Any]:
    query = state.get("user_query", "")
    stdout = state.get("stdout") or ""
    print("\n[Answer] Synthesizing final answer...", flush=True)

    clipped = stdout[:MAX_OUTPUT_CHARS]
    if len(stdout) > MAX_OUTPUT_CHARS:
        clipped += "\n...[output truncated]"

    prompt = f"User question:\n{query}\n\nProgram output:\n```\n{clipped}\n```"
    try:
        answer = (await gemini_service.generate_text_async(
            prompt=prompt,
            system_instruction=ANSWER_SYSTEM_INSTRUCTION,
            temperature=0.1,
        )).strip()
        log = "[Answer Node] Synthesized final answer from program output."
    except Exception as e:
        answer = stdout.strip()
        log = f"[Answer Node] Synthesis skipped ({type(e).__name__}); returning raw output."

    return {
        "final_result": answer or stdout.strip(),
        "status": "completed",
        "execution_logs": [log],
    }
