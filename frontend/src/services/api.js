// Calls to the FastAPI backend.

export const getBackendUrl = () => {
  return localStorage.getItem('agentic_backend_url') || import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
};

export const setBackendUrl = (url) => {
  if (url) {
    localStorage.setItem('agentic_backend_url', url.replace(/\/+$/, ''));
  } else {
    localStorage.removeItem('agentic_backend_url');
  }
};

// FastAPI puts the error message in "detail"
async function readError(response, fallback) {
  try {
    const body = await response.json();
    return body.detail || fallback;
  } catch {
    return fallback;
  }
}

export async function checkBackendHealth(baseUrl = getBackendUrl()) {
  try {
    const res = await fetch(`${baseUrl}/health`, { signal: AbortSignal.timeout(5000) });
    if (!res.ok) {
      throw new Error(`Health check returned status ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    return {
      status: 'offline',
      error: err.message,
      docker_available: false,
      gemini_model: 'unavailable',
    };
  }
}

// Runs the whole workflow and waits for the final result.
export async function executeWorkspace(payload, signal) {
  const response = await fetch(`${getBackendUrl()}/api/v1/workspace/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: payload.query,
      max_iterations: payload.max_iterations || 5,
    }),
    signal,
  });

  if (!response.ok) {
    throw new Error(await readError(response, `Execution failed with HTTP ${response.status}`));
  }
  return await response.json();
}

// Reads the Server-Sent Events stream and calls onEvent for each event.
// EventSource only supports GET, so the stream is read by hand from fetch().
export async function streamWorkspace(payload, { onEvent, onError, onComplete, signal }) {
  try {
    const response = await fetch(`${getBackendUrl()}/api/v1/workspace/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: payload.query,
        max_iterations: payload.max_iterations || 5,
      }),
      signal,
    });

    if (!response.ok) {
      throw new Error(await readError(response, `Stream request failed with HTTP ${response.status}`));
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      // Events are separated by a blank line. The last piece may be incomplete, so keep it.
      const chunks = buffer.split('\n\n');
      buffer = chunks.pop();

      for (const chunk of chunks) {
        const line = chunk.trim();
        if (!line.startsWith('data:')) continue;
        const json = line.slice(5).trim();
        if (!json) continue;
        try {
          onEvent(JSON.parse(json));
        } catch (e) {
          console.warn('Failed to parse SSE line:', line, e);
        }
      }
    }

    onComplete();
  } catch (err) {
    // Stopped by the user: abortRun() already updated the UI
    if (err.name === 'AbortError') return;
    onError(err);
  }
}
