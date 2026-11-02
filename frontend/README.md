# Autonomous Code Workspace — React Frontend

Production-ready, highly optimized frontend dashboard for the Autonomous Code & Analysis Workspace.

Built with:
- **React 18** + **Vite**
- **React Router v6**
- **Tailwind CSS** (Dark cyber-theme)
- **Framer Motion** (Smooth transitions & staggered telemetry)
- **Lucide React** (Icons)

---

## Getting Started

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
```bash
cp .env.example .env
# By default, VITE_BACKEND_URL points to http://localhost:8000
```

### 3. Start Development Server
```bash
npm run dev
```

The application will be live at: [http://localhost:5173](http://localhost:5173)

---

## Features
- **Real-Time Streaming (SSE):** Consumes live Server-Sent Events from `/api/v1/workspace/stream` with real-time log appending and automatic reconnection.
- **Visual State Graph:** Live pipeline indicator (`planner` -> `coder` -> `executor` -> `reviewer`) with self-healing indicators.
- **Multi-Tab Terminal:** Monospace dark-mode console with live logs, generated Python code viewer, Docker stdout/stderr separation, and reviewer diagnosis instructions.
- **Dynamic Configuration:** Change backend URL on the fly in the Settings view without rebuilding.

