# Frontend

React app for the Code Workspace backend. You type a question, it calls the
backend, and shows the plan, generated code, program output and final answer.

Built with React 18, Vite, React Router, Tailwind CSS and lucide-react icons.

## Running it

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. The backend needs to be running on http://localhost:8000.

To point at a different backend, either copy `.env.example` to `.env` and change
`VITE_BACKEND_URL`, or change the address on the Settings page (saved in the
browser's localStorage).

## What's in `src/`

- `services/api.js` – `fetch` calls to `/health`, `/api/v1/workspace/execute` and
  `/api/v1/workspace/stream`. The stream endpoint is a POST, so the Server-Sent
  Events are read manually from the response body instead of using `EventSource`.
- `context/AgentContext.jsx` – holds all the run state (status, plan, code, output,
  logs, ...) and the `runAgent` / `abortRun` functions.
- `pages/DashboardPage.jsx` – the main page: prompt box, progress steps and results.
- `pages/ConfigPage.jsx` – backend URL, max attempts, streaming vs. single response.
- `components/` – `Navbar`, `PromptBox`, `RunProgress` (the Plan → Code → Run → Answer
  steps) and `ResultPanel` (Answer / Code / Output / Plan / Log tabs).

## Docker

`Dockerfile` builds the app and serves it with nginx on port 80. It is started
by the `docker-compose.yml` in the repo root.
