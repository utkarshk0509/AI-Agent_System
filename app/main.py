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


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for resource verification."""
    # Pre-flight check: Verify Docker daemon connectivity
    if not docker_sandbox.client:
        print("[WARNING] Docker daemon is not connected. Execution node will use subprocess fallback (no container isolation).")
    else:
        print("[INFO] Connected to Docker daemon successfully.")
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
    allow_credentials=True,
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
    }


@app.post("/api/v1/workspace/execute", response_model=CodeExecutionResponse, tags=["Orchestration"])
async def execute_query(payload: CodeExecutionRequest):
    """Executes the full LangGraph multi-agent loop to solve a data analysis query.
    
    The graph iteratively plans, codes, executes inside Docker, and self-corrects 
    until success or max_iterations is reached.
    """
    initial_state = {
        "user_query": payload.query,
        "plan": None,
        "generated_code": None,
        "stdout": None,
        "stderr": None,
        "exit_code": None,
        "error_trace": None,
        "review_feedback": None,
        "iteration_count": 0,
        "max_iterations": payload.max_iterations or settings.MAX_ITERATIONS,
        "execution_logs": ["[System] Workspace execution initiated."],
        "status": "initialized",
        "final_result": None,
    }

    try:
        # Run graph synchronously (or await ainvoke in async mode)
        final_state = await app_graph.ainvoke(initial_state)

        # Map state to response schema
        is_success = (final_state.get("exit_code") == 0)
        final_status = "completed" if is_success else (
            "max_iterations_exceeded" if final_state.get("iteration_count", 0) >= final_state.get("max_iterations", 5)
            else "failed"
        )

        return CodeExecutionResponse(
            status=final_status,
            query=payload.query,
            plan=final_state.get("plan"),
            final_code=final_state.get("generated_code"),
            stdout=final_state.get("stdout"),
            stderr=final_state.get("stderr"),
            exit_code=final_state.get("exit_code"),
            iteration_count=final_state.get("iteration_count", 0),
            execution_logs=final_state.get("execution_logs", []),
            review_feedback=final_state.get("review_feedback"),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow orchestration error: {str(exc)}",
        )


@app.post("/api/v1/workspace/stream", tags=["Orchestration"])
async def stream_query(payload: CodeExecutionRequest):
    """Streams step-by-step agent transitions using Server-Sent Events (SSE)."""

    initial_state = {
        "user_query": payload.query,
        "plan": None,
        "generated_code": None,
        "stdout": None,
        "stderr": None,
        "exit_code": None,
        "error_trace": None,
        "review_feedback": None,
        "iteration_count": 0,
        "max_iterations": payload.max_iterations or settings.MAX_ITERATIONS,
        "execution_logs": ["[System] Streaming started."],
        "status": "initialized",
        "final_result": None,
    }

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            async for event in app_graph.astream(initial_state):
                for node_name, node_update in event.items():
                    event_data = {
                        "node": node_name,
                        "status": node_update.get("status"),
                        "logs": node_update.get("execution_logs", []),
                        "iteration": node_update.get("iteration_count"),
                    }
                    yield f"data: {json.dumps(event_data)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

