# Autonomous Code & Analysis Workspace

You ask a question that needs some calculation (for example "what is the median
of these numbers?"). The backend asks Gemini to plan and write a Python script,
runs that script in a Docker container, and if it fails, sends the error back to
Gemini to get it fixed and runs it again. When the script works, Gemini turns its
output into a short answer.

Built with **FastAPI**, **LangGraph**, the **Gemini API** (`google-genai`), the
**Docker SDK for Python** and a **React** frontend.

---

## How it works

The workflow is a LangGraph `StateGraph` with five nodes:

```
START -> planner -> coder -> executor
                      ^         |
                      |         |-- exit code 0 and printed output --> answer -> END
                      |         |-- reached max_iterations ----------> END
                      |         |
                      +--- reviewer <-- anything else (error, or no output)
```

- **planner** – asks Gemini for a short step-by-step plan.
- **coder** – asks Gemini for the Python script (or a fixed version of it, using the reviewer's notes).
- **executor** – runs the script in the sandbox and saves stdout, stderr and the exit code.
- **reviewer** – reads the error and writes fix instructions. For `ModuleNotFoundError` it
  skips Gemini and just says to use the standard library, since that's always the fix.
- **answer** – asks Gemini to answer the question using only the script's output. If that
  call fails, the raw output is returned instead.

`max_iterations` (1–10, default 5) limits how many times the code is run, so a script that
keeps failing can't loop forever or burn through API calls.

### Things worth knowing

- **Sandbox:** each run uses a new container with no network, a memory and CPU limit,
  a 100-process limit, `no-new-privileges`, and a read-only mount for the script.
  The container is removed afterwards.
- **No Docker?** If the Docker daemon isn't reachable, the script runs as a normal local
  subprocess instead. **There is no isolation in that mode**, so only use it on your own
  machine. `/health` reports which mode is active (`execution_mode`).
- **Model fallback:** if the main model returns 429/500/502/503 the call is retried with
  backoff. On 404/504, or when retries run out, the next model in `GEMINI_FALLBACK_MODELS`
  is tried. 400/401/403 errors are raised straight away because another model won't fix them.
- **Streaming:** `/api/v1/workspace/stream` sends one Server-Sent Event per node, so the
  frontend can show progress while the run is going.

---

## Project structure

```text
├── app/
│   ├── main.py                  # FastAPI app and endpoints
│   ├── core/config.py           # settings loaded from .env (pydantic-settings)
│   ├── schemas/api.py           # request / response models
│   ├── services/
│   │   ├── gemini_service.py    # Gemini calls with retry + model fallback
│   │   └── docker_sandbox.py    # runs code in Docker (or a subprocess)
│   └── graph/
│       ├── state.py             # AgentState (TypedDict shared by all nodes)
│       ├── edges.py             # routing after the executor
│       ├── workflow.py          # builds the graph
│       └── nodes/               # planner, coder, executor, reviewer, answer
├── tests/                       # pytest tests (Gemini and Docker are mocked)
├── scripts/test_manual.py       # manual checks: mock / docker / live
├── frontend/                    # React + Vite app (see frontend/README.md)
├── docker/
│   ├── app/Dockerfile           # backend image
│   └── runner/Dockerfile        # optional sandbox image with numpy, pandas, etc.
├── docker-compose.yml           # runs backend + frontend together
├── .env.example
├── pyproject.toml
└── requirements.txt
```

---

## Setup

You need Python 3.10+, a [Gemini API key](https://aistudio.google.com/), and Docker Desktop
if you want the container sandbox. Node.js is needed for the frontend.

### Option 1: Docker Compose

Create a `.env` file (copy `.env.example`) and set `GEMINI_API_KEY`, then:

```bash
docker compose up -d --build
```

Open http://localhost:3000. The backend is on http://localhost:8000.

Both containers use `restart: unless-stopped`, so they come back up whenever Docker starts.
Run the command again after changing code. `docker compose down` stops everything.

The backend container gets access to the Docker socket so it can start the sandbox
containers. The script is passed to them through a shared named volume
(`SANDBOX_SHARED_VOLUME`), because a path inside the backend container can't be
bind-mounted into another container.

### Option 2: Run it locally

```bash
cp .env.example .env        # then put your GEMINI_API_KEY in .env

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

docker pull python:3.11-slim   # the default sandbox image

python -m uvicorn app.main:app --reload --port 8000
```

API docs (Swagger) are at http://localhost:8000/docs.

Frontend, in another terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### Sandbox image

By default scripts run in the official `python:3.11-slim` image. It only has the
standard library, which is why the prompts tell Gemini to stick to it.

`docker/runner/Dockerfile` builds an image with numpy, pandas, scipy, etc. that runs as a
non-root user. To use it:

```bash
docker build -t code-runner -f docker/runner/Dockerfile .
```

then set `DOCKER_SANDBOX_IMAGE=code-runner` in `.env`. The prompts would also need to
be changed to allow those libraries.

---

## API

### `POST /api/v1/workspace/execute`

Runs the whole workflow and returns the result in one response.

```bash
curl -X POST "http://localhost:8000/api/v1/workspace/execute" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the median of 3, 1, 4, 1, 5, 9, 2, 6?", "max_iterations": 3}'
```

The response looks like this (shortened):

```json
{
  "status": "completed",
  "query": "What is the median of 3, 1, 4, 1, 5, 9, 2, 6?",
  "answer": "The median is 3.5.",
  "plan": "1. Use statistics.median ...",
  "final_code": "import statistics\n...",
  "stdout": "3.5\n",
  "stderr": "",
  "exit_code": 0,
  "iteration_count": 1,
  "execution_logs": [
    "[System] Workspace execution initiated.",
    "[Planner Node] Formulated execution plan.",
    "[Coder Node] Generated initial Python code.",
    "[Executor Node] Attempt #1 — SUCCESS. stdout=4 chars, stderr=0 chars.",
    "[Answer Node] Synthesized final answer from program output."
  ],
  "review_feedback": null
}
```

`status` is `completed`, `max_iterations_exceeded` or `failed`. If Gemini isn't configured
or every model fails, the endpoint returns HTTP 503.

### `POST /api/v1/workspace/stream`

Same request body, but the response is a Server-Sent Events stream:

```bash
curl -N -X POST "http://localhost:8000/api/v1/workspace/stream" \
  -H "Content-Type: application/json" \
  -d '{"query": "Calculate the 50th Fibonacci number", "max_iterations": 3}'
```

Each event is `{"node", "status", "logs", "iteration", "data"}`. `data` has whatever that
node produced (`plan`, `generated_code`, `stdout`, `stderr`, `exit_code`, `review_feedback`,
`final_result`). The last event is always
`{"node": "done", "status": ..., "result": <same shape as /execute>}`, or
`{"node": "done", "status": "error", "error": "..."}` if something went wrong.

### `GET /health`

Reports whether Docker is connected, which sandbox mode is in use, the Gemini models
and whether an API key is set.

---

## Configuration

All settings are in `app/core/config.py` and can be set in `.env`:

| Variable | Default | What it does |
|---|---|---|
| `GEMINI_API_KEY` | – | required |
| `GEMINI_MODEL` | `gemini-3.8-flash` | main model |
| `GEMINI_FALLBACK_MODELS` | `gemini-3.5-flash-lite,gemini-3.1-flash-lite` | tried in order if the main model fails |
| `GEMINI_TIMEOUT_SECONDS` | `60` | per request |
| `GEMINI_MAX_RETRIES` | `2` | retries per model |
| `DOCKER_SANDBOX_IMAGE` | `python:3.11-slim` | image the code runs in |
| `EXECUTION_TIMEOUT_SECONDS` | `30` | the script is killed after this |
| `MAX_CONTAINER_MEMORY` | `512m` | container memory limit |
| `CPU_QUOTA_MICROS` | `100000` | 100000 = one CPU core |
| `SANDBOX_NETWORK_MODE` | `none` | no network for generated code |
| `MAX_ITERATIONS` | `5` | default when the request doesn't set one |

---

## Tests

```bash
pip install -e ".[dev]"
pytest -v
```

The tests mock Gemini and the sandbox, so they don't need an API key or Docker (the
subprocess tests really run Python). They cover the routing logic, each node, the full
graph (success, fix-and-retry, hitting the limit), the API endpoints, the Gemini
retry/fallback logic and the sandbox.

`scripts/test_manual.py` is for checking things by hand:

```bash
python scripts/test_manual.py --mode=mock     # whole graph with fake Gemini and fake sandbox
python scripts/test_manual.py --mode=docker   # real container: output, errors, timeout
python scripts/test_manual.py --mode=live     # real Gemini + sandbox, needs GEMINI_API_KEY
```

GitHub Actions (`.github/workflows/ci.yml`) runs the tests on Python 3.11 and 3.12 on every
push and pull request.

---

## License

[MIT](LICENSE)
