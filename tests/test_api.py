"""FastAPI HTTP endpoint integration tests."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    """Verify health check endpoint returns 200 and system details."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "docker_available" in data
        assert "gemini_model" in data


@pytest.mark.asyncio
async def test_execute_endpoint(mock_gemini_service, mock_docker_success):
    """Verify POST /api/v1/workspace/execute returns 200 with structured response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "query": "Find prime numbers below 20",
            "max_iterations": 3,
        }
        response = await client.post("/api/v1/workspace/execute", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["exit_code"] == 0
        assert data["iteration_count"] == 1
        assert len(data["execution_logs"]) > 0


@pytest.mark.asyncio
async def test_stream_endpoint(mock_gemini_service, mock_docker_success):
    """Verify POST /api/v1/workspace/stream returns Server-Sent Events stream."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "query": "Stream prime numbers calculation",
            "max_iterations": 2,
        }
        response = await client.post("/api/v1/workspace/stream", json=payload)
        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")
