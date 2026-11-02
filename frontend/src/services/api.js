/**
 * API Service for connecting to the Autonomous Code & Analysis Workspace Backend.
 * Supports synchronous execution, live Server-Sent Events (SSE) streaming, and health checks.
 */

export const getBackendUrl = () => {
  return localStorage.getItem('agentic_backend_url') || import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';
};

export const setBackendUrl = (url) => {
  if (url) {
    const cleanUrl = url.replace(/\/+$/, '');
    localStorage.setItem('agentic_backend_url', cleanUrl);
  } else {
    localStorage.removeItem('agentic_backend_url');
  }
};

/**
 * Probes the backend /health endpoint to verify Docker connectivity & model availability.
 */
export async function checkBackendHealth(customUrl = null) {
  const baseUrl = customUrl || getBackendUrl();
  try {
    const res = await fetch(`${baseUrl}/health`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
      signal: AbortSignal.timeout(5000),
    });
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

/**
 * Executes an agent workspace query synchronously via POST /api/v1/workspace/execute
 */
export async function executeWorkspace(payload, options = {}) {
  const baseUrl = options.customUrl || getBackendUrl();
  const response = await fetch(`${baseUrl}/api/v1/workspace/execute`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    },
    body: JSON.stringify({
      query: payload.query,
      max_iterations: payload.max_iterations || 5,
    }),
    signal: options.signal,
  });

  if (!response.ok) {
    let errorDetail = `Execution failed with HTTP ${response.status}`;
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errorDetail;
    } catch (_) {}
    throw new Error(errorDetail);
  }

  return await response.json();
}

/**
 * Connects to the SSE streaming endpoint POST /api/v1/workspace/stream
 * Processes streaming events (planner -> coder -> executor -> reviewer) in real-time.
 */
export async function streamWorkspace(payload, callbacks = {}) {
  const { onEvent, onError, onComplete, signal, customUrl } = callbacks;
  const baseUrl = customUrl || getBackendUrl();

  try {
    const response = await fetch(`${baseUrl}/api/v1/workspace/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: payload.query,
        max_iterations: payload.max_iterations || 5,
      }),
      signal,
    });

    if (!response.ok) {
      let errorDetail = `Stream request failed with HTTP ${response.status}`;
      try {
        const errJson = await response.json();
        errorDetail = errJson.detail || errorDetail;
      } catch (_) {}
      throw new Error(errorDetail);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n\n');
      buffer = lines.pop(); // Keep incomplete chunk in buffer

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data:')) {
          try {
            const rawJson = trimmed.slice(5).trim();
            if (rawJson) {
              const parsed = JSON.parse(rawJson);
              if (onEvent) onEvent(parsed);
            }
          } catch (e) {
            console.warn('Failed to parse SSE line:', line, e);
          }
        }
      }
    }

    if (onComplete) onComplete();
  } catch (err) {
    if (err.name === 'AbortError') {
      console.log('Stream aborted by user.');
      if (onEvent) onEvent({ node: 'system', status: 'aborted', logs: ['[System] Execution halted by user.'] });
    } else {
      if (onError) onError(err);
      else console.error('Streaming error:', err);
    }
  }
}

