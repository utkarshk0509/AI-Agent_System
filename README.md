# Autonomous Code & Analysis Workspace

[![CI Pipeline](https://github.com/your-username/autonomous-code-workspace/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/autonomous-code-workspace/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Gemini 2.5](https://img.shields.io/badge/Google-Gemini%202.5-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev)
[![Docker](https://img.shields.io/badge/Docker-Sandboxed-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An enterprise-grade, cyclic multi-agent orchestration system that writes, executes, and debugs code to solve complex data queries using **LangGraph**, **Gemini 2.5 API**, **FastAPI**, **Docker SDK for Python**, and **Pydantic**.

---

## Architecture Overview

```
                      ┌────────────────┐
                      │  [START] Node  │
                      └───────┬────────┘
                              │
                              ▼
                      ┌────────────────┐
                      │  planner_node  │  (Breaks query into algorithmic task)
                      └───────┬────────┘
                              │
                              ▼
            ┌─────────► ┌─────────────┐
            │           │ coder_node  │ ◄────────────────────────┐
            │           └──────┬──────┘                          │
            │                  │                                 │
            │                  ▼                                 │
            │           ┌─────────────┐                          │
            │           │executor_node│ (Isolated Docker SDK)    │
            │           └──────┬──────┘                          │
            │                  │                                 │
  (review & retry)             │                                 │
            │         [Conditional Edge]                         │
            │       exit_code == 0?                              │
            │       ├── YES ───────────────────► [END] (Success) │
            │       └── NO                                       │
            │           ├── iter >= max_iters ─► [END] (Circuit) │
            │           └── iter < max_iters                     │
            │                    │                               │
            └─────────── ┌───────┴───────┐                       │
                         │ reviewer_node │───────────────────────┘
                         └───────────────┘  (Root cause diagnosis)
```

---

## Key Features

- **Cyclic Agent Orchestration:** Powered by **LangGraph**, the system manages state transitions across planning, code generation, sandboxed execution, and automated remediation.
- **Isolated Docker Sandbox:** Executes generated Python code inside ephemeral, hardened containers with resource ceilings (512MB RAM, 1 CPU core), disabled networking (`none`), and guaranteed cleanup.
- **Deterministic Circuit Breakers:** Enforces `max_iterations` caps to prevent infinite loops, runaway compute, or unbounded API charges.
- **Real-Time Streaming:** Full support for Server-Sent Events (SSE) via `/api/v1/workspace/stream` for live agent terminal outputs.
- **Pydantic Validation:** Strict schema boundaries for state serialization, API inputs/outputs, and environment settings.

---

## Repository Structure

```text
autonomous-code-workspace/
├── .github/
│   └── workflows/
│       └── ci.yml                   # GitHub Actions CI pipeline
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore rules
├── LICENSE                          # MIT License
├── pyproject.toml                   # Project metadata and build configuration
├── requirements.txt                 # Production dependencies
├── docker/
│   ├── app/
│   │   └── Dockerfile               # FastAPI backend application image
│   └── runner/
│       └── Dockerfile               # Execution sandbox image (data science stack, non-root)
├── app/
│   ├── main.py                      # FastAPI initialization & endpoints
│   ├── core/
│   │   └── config.py                # Pydantic Settings
│   ├── schemas/
│   │   └── api.py                   # API DTOs (Request / Response)
│   ├── services/
│   │   ├── gemini_service.py        # Gemini 2.5 API client abstraction
│   │   └── docker_sandbox.py        # Docker SDK isolated container manager
│   └── graph/
│       ├── state.py                 # LangGraph AgentState TypedDict
│       ├── edges.py                 # Conditional routing and circuit breaker logic
│       ├── workflow.py              # StateGraph assembly & compilation
│       └── nodes/
│           ├── planner.py           # Planner Agent Node
│           ├── coder.py             # Coder Agent Node
│           ├── executor.py          # Docker Execution Agent Node
│           └── reviewer.py          # Reviewer Debugging Agent Node
├── tests/                           # Complete Pytest test suite
│   ├── conftest.py                  # Test fixtures & mocks
│   ├── test_state.py                # State schema validation tests
│   ├── test_edges.py                # Conditional routing tests
│   ├── test_nodes.py                # Isolated agent node tests
│   ├── test_graph.py                # End-to-end graph tests (success, retry, circuit breaker)
│   ├── test_api.py                  # FastAPI endpoint tests
│   └── test_sandbox.py              # Docker sandbox unit tests
└── scripts/
    └── test_manual.py               # Interactive CLI diagnostic & testing tool
```

---

## Quickstart Guide

### 1. Prerequisites
- **Python 3.10+** (or [uv](https://docs.astral.sh/uv/))
- **Docker Desktop / Docker Engine** (running locally or remote socket)
- **Google Gemini API Key** ([Get key here](https://aistudio.google.com/))

### 2. Clone & Environment Setup
```bash
git clone https://github.com/your-username/autonomous-code-workspace.git
cd autonomous-code-workspace

cp .env.example .env
# Edit .env and paste your GEMINI_API_KEY
```

### 3. Install Dependencies
```bash
# Using standard venv + pip
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Or using uv (recommended for ultra-fast installs)
uv venv
uv pip install -r requirements.txt
```

### 4. Build the Execution Sandbox Container
Build the hardened Python execution container:
```bash
docker build -t python:3.11-slim -f docker/runner/Dockerfile .
```

### 5. Launch the FastAPI Backend Server
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
Interactive API documentation is now live at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Launch the React Web Dashboard
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
Open your browser to: [http://localhost:5173](http://localhost:5173)

---

## API Usage

### Execute Query (Synchronous REST)
```bash
curl -X POST "http://localhost:8000/api/v1/workspace/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Generate 100 samples from a normal distribution with mean 50 and std 10, then print the summary statistics as JSON.",
    "max_iterations": 3
  }'
```

**Sample Response:**
```json
{
  "status": "completed",
  "query": "Generate 100 samples from a normal distribution...",
  "plan": "1. Import numpy and json\n2. Generate sample\n3. Calculate metrics\n4. Output JSON",
  "final_code": "import numpy as np\nimport json\n...",
  "stdout": "{\"mean\": 50.12, \"std\": 9.87}\n",
  "stderr": "",
  "exit_code": 0,
  "iteration_count": 1,
  "execution_logs": [
    "[System] Workspace execution initiated.",
    "[Planner Node] Formulated execution plan.",
    "[Coder Node] Generated initial Python code.",
    "[Executor Node] Attempt #1 - SUCCESS."
  ],
  "review_feedback": null
}
```

### Stream Agent Progress (Server-Sent Events)
```bash
curl -N -X POST "http://localhost:8000/api/v1/workspace/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the 50th Fibonacci number", "max_iterations": 3}'
```

---

## Testing & Verification

We provide three complementary testing layers:

### 1. Interactive Diagnostic Script (`scripts/test_manual.py`)
Run zero-dependency or live checks directly from the command line:

```bash
# Level 1: Deterministic LangGraph verification (Mocked Gemini + Mocked Docker)
python scripts/test_manual.py --mode=mock

# Level 2: Docker Sandbox verification (Tests container launch, stderr capture, and timeout enforcement)
python scripts/test_manual.py --mode=docker

# Level 3: Full End-to-End Live Run (Requires GEMINI_API_KEY and active Docker daemon)
python scripts/test_manual.py --mode=live
```

### 2. Automated Pytest Suite
Run the full test suite with coverage:
```bash
pytest -v tests/
```

### 3. Continuous Integration (CI)
GitHub Actions workflow runs on every push and pull request to verify:
- Python 3.11 and 3.12 compatibility
- Clean compilation across all modules
- Complete test suite passing

---

## Security & Sandbox Hardening

- **Non-Root Execution:** Code runs under the unprivileged `sandboxuser` (`UID 1000`).
- **Resource Ceilings:** Containers are bounded to `512MB RAM` and `1 CPU core` (`cpu_quota=100000`).
- **Network Mode:** By default set to `none` to block Server-Side Request Forgery (SSRF) and data exfiltration.
- **Privilege Escalation:** Disabled via `security_opt=["no-new-privileges:true"]`.
- **Guaranteed Cleanup:** Containers and temporary volume mounts are destroyed via `finally` blocks, eliminating orphaned processes.

---

## License

This project is licensed under the [MIT License](LICENSE).
