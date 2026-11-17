"""FastAPI Entry Point for the Autonomous Code & Analysis Workspace.

Exposes REST endpoints to trigger the LangGraph orchestration, stream agent
telemetry, and query execution health.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import json

from app.core.config import settings
from app.schemas.api import CodeExecutionRequest, CodeExecutionResponse
from app.graph.workflow import app_graph
from app.services.docker_sandbox import docker_sandbox
from app.services.gemini_service import gemini_service, GeminiUnavailableError


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for resource verification."""
    # Pre-flight check: Verify Docker daemon connectivity
    if not docker_sandbox.client:
        print("[WARNING] Docker daemon is not connected. Execution node will use subprocess fallback (no container isolation).")
    else:
        print("[INFO] Connected to Docker daemon successfully.")
    if not gemini_service.client:
        print("[WARNING] GEMINI_API_KEY is not set - every query will fail until it is configured in .env.")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-agent cyclic orchestration system for automated code generation, sandboxed execution, and self-debugging.",
    version="0.1.0",
    lifespan=lifespan,
)

# Standard CORS Middleware for frontend dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["System"])
async def root():
    """Root landing page directing users to Swagger UI and API endpoints."""
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/health",
        "endpoints": {
            "execute": "POST /api/v1/workspace/execute",
            "stream": "POST /api/v1/workspace/stream",
        },
    }


@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to probe container and service status."""
    docker_up = docker_sandbox.client is not None
    return {
        "status": "healthy",
        "docker_available": docker_up,
        # execution_mode tells the frontend which sandbox is active
        "execution_mode": "docker" if docker_up else "subprocess",
        "gemini_model": settings.GEMINI_MODEL,
        "gemini_fallback_models": settings.gemini_model_chain[1:],
        "gemini_configured": gemini_service.client is not None,
    }


def _initial_state(query: str, max_iterations: int | None, first_log: str) -> dict:
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
        "max_iterations": max_iterations or settings.MAX_ITERATIONS,
        "execution_logs": [first_log],
        "status": "initialized",
        "final_result": None,
    }


def _final_status(state: dict) -> str:
    if state.get("exit_code") == 0 and state.get("final_result"):
        return "completed"
    if state.get("iteration_count", 0) >= state.get("max_iterations", 5):
        return "max_iterations_exceeded"
    return "failed"


def _build_response(query: str, state: dict) -> CodeExecutionResponse:
    return CodeExecutionResponse(
        status=_final_status(state),
        query=query,
        answer=state.get("final_result"),
        plan=state.get("plan"),
        final_code=state.get("generated_code"),
        stdout=state.get("stdout"),
        stderr=state.get("stderr"),
        exit_code=state.get("exit_code"),
        iteration_count=state.get("iteration_count", 0),
        execution_logs=state.get("execution_logs", []),
        review_feedback=state.get("review_feedback"),
    )


# State keys forwarded to the client in each SSE event when a node updates them
_STREAMED_KEYS = (
    "plan", "generated_code", "stdout", "stderr", "exit_code",
    "review_feedback", "final_result",
)


@app.post("/api/v1/workspace/execute", response_model=CodeExecutionResponse, tags=["Orchestration"])
async def execute_query(payload: CodeExecutionRequest):
    """Executes the full LangGraph multi-agent loop to solve a data analysis query.

    The graph iteratively plans, codes, executes in the sandbox, self-corrects
    until success or max_iterations, then synthesizes a direct answer.
    """
    initial_state = _initial_state(
        payload.query, payload.max_iterations, "[System] Workspace execution initiated."
    )
    try:
        final_state = await app_graph.ainvoke(initial_state)
    except GeminiUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow orchestration error: {exc}",
        )
    return _build_response(payload.query, final_state)


@app.post("/api/v1/workspace/stream", tags=["Orchestration"])
async def stream_query(payload: CodeExecutionRequest):
    """Streams step-by-step agent transitions using Server-Sent Events (SSE).

    Each event carries the node name, status, logs and any artifacts that node
    produced (plan, code, stdout, ...). The stream ends with a single
    ``{"node": "done", "result": <CodeExecutionResponse>}`` event so the client
    always receives the final answer.
    """
    initial_state = _initial_state(
        payload.query, payload.max_iterations, "[System] Streaming started."
    )

    async def event_generator() -> AsyncGenerator[str, None]:
        # Accumulate state locally (stream_mode="updates" yields only deltas)
        state = dict(initial_state)
        try:
            async for event in app_graph.astream(initial_state):
                for node_name, node_update in event.items():
                    node_update = node_update or {}
                    for k, v in node_update.items():
                        if k == "execution_logs":
                            state[k] = state.get(k, []) + list(v)
                        else:
                            state[k] = v
                    event_data = {
                        "node": node_name,
                        "status": node_update.get("status"),
                        "logs": node_update.get("execution_logs", []),
                        "iteration": node_update.get("iteration_count"),
                        "data": {k: node_update[k] for k in _STREAMED_KEYS if k in node_update},
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
            final = _build_response(payload.query, state).model_dump()
            yield f"data: {json.dumps({'node': 'done', 'status': final['status'], 'result': final})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'node': 'done', 'status': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
