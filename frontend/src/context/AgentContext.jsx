import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { checkBackendHealth, executeWorkspace, streamWorkspace, getBackendUrl, setBackendUrl } from '../services/api';

const AgentContext = createContext();

export function AgentProvider({ children }) {
  const [backendUrl, setBackendUrlState] = useState(getBackendUrl());
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [healthInfo, setHealthInfo] = useState({ docker_available: false, execution_mode: 'subprocess', gemini_model: '' });
  
  // Execution state
  const [status, setStatus] = useState('idle'); // 'idle' | 'running' | 'completed' | 'error' | 'aborted'
  const [activeNode, setActiveNode] = useState(null); // 'planner' | 'coder' | 'executor' | 'reviewer'
  const [executionMode, setExecutionMode] = useState('stream'); // 'stream' | 'sync'
  const [query, setQuery] = useState('');
  const [maxIterations, setMaxIterations] = useState(5);
  const [iterationCount, setIterationCount] = useState(0);

  // Artifacts
  const [plan, setPlan] = useState(null);
  const [generatedCode, setGeneratedCode] = useState(null);
  const [stdout, setStdout] = useState(null);
  const [stderr, setStderr] = useState(null);
  const [exitCode, setExitCode] = useState(null);
  const [reviewFeedback, setReviewFeedback] = useState(null);
  const [answer, setAnswer] = useState(null);
  const [logs, setLogs] = useState([]);
  const [error, setError] = useState(null);
  const [startTime, setStartTime] = useState(null);
  const [elapsedTime, setElapsedTime] = useState(0);

  const abortControllerRef = useRef(null);
  const timerRef = useRef(null);

  // Health check on mount and url change
  const refreshHealth = async (targetUrl = null) => {
    setBackendStatus('checking');
    const health = await checkBackendHealth(targetUrl || backendUrl);
    if (health.status === 'healthy') {
      setBackendStatus('online');
      setHealthInfo(health);
    } else {
      setBackendStatus('offline');
      setHealthInfo(health);
    }
  };

  useEffect(() => {
    refreshHealth();
    const interval = setInterval(() => refreshHealth(), 20000);
    return () => clearInterval(interval);
  }, [backendUrl]);

  // Elapsed timer tracking during run
  useEffect(() => {
    if (status === 'running') {
      const start = Date.now();
      setStartTime(start);
      timerRef.current = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - start) / 1000));
      }, 500);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [status]);

  const updateBackendUrl = (url) => {
    setBackendUrl(url);
    setBackendUrlState(getBackendUrl());
    refreshHealth(url);
  };

  const addLog = (message, node = 'system', level = 'info') => {
    setLogs((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        timestamp: new Date().toLocaleTimeString(),
        message,
        node,
        level,
      },
    ]);
  };

  const clearWorkspace = () => {
    setStatus('idle');
    setActiveNode(null);
    setPlan(null);
    setGeneratedCode(null);
    setStdout(null);
    setStderr(null);
    setExitCode(null);
    setReviewFeedback(null);
    setAnswer(null);
    setLogs([]);
    setError(null);
    setIterationCount(0);
    setElapsedTime(0);
  };

  const abortRun = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setStatus('aborted');
    setActiveNode(null);
    addLog('Execution manually stopped by operator.', 'system', 'warn');
  };

  // Apply a CodeExecutionResponse payload (sync response or final stream event)
  const applyResult = (result) => {
    setPlan(result.plan ?? null);
    setGeneratedCode(result.final_code ?? null);
    setStdout(result.stdout ?? null);
    setStderr(result.stderr ?? null);
    setExitCode(result.exit_code ?? null);
    setIterationCount(result.iteration_count ?? 0);
    setReviewFeedback(result.review_feedback ?? null);
    setAnswer(result.answer ?? null);
  };

  const runAgent = async (userQuery, customMaxIter = null) => {
    if (!userQuery.trim() || status === 'running') return;

    clearWorkspace();
    setQuery(userQuery);
    setStatus('running');
    setActiveNode('planner');
    setError(null);
    const iterLimit = customMaxIter || maxIterations;

    abortControllerRef.current = new AbortController();
    addLog(`Initiated orchestration workspace for: "${userQuery.slice(0, 70)}..."`, 'system', 'info');

    if (executionMode === 'stream') {
      let finalEvent = null;
      try {
        await streamWorkspace(
          { query: userQuery, max_iterations: iterLimit },
          {
            signal: abortControllerRef.current.signal,
            onEvent: (event) => {
              // Final event: carries the full result (or an error) and the real status
              if (event.node === 'done') {
                finalEvent = event;
                if (event.error) {
                  setError(event.error);
                  addLog(`Stream error: ${event.error}`, 'system', 'error');
                  return;
                }
                applyResult(event.result || {});
                return;
              }

              if (event.error) {
                setError(event.error);
                addLog(`Stream error: ${event.error}`, 'system', 'error');
                return;
              }

              // Artifacts produced by this node (plan, code, stdout, ...)
              const d = event.data || {};
              if ('plan' in d) setPlan(d.plan);
              if ('generated_code' in d) setGeneratedCode(d.generated_code);
              if ('stdout' in d) setStdout(d.stdout);
              if ('stderr' in d) setStderr(d.stderr);
              if ('exit_code' in d) setExitCode(d.exit_code);
              if ('review_feedback' in d) setReviewFeedback(d.review_feedback);
              if ('final_result' in d && d.final_result) setAnswer(d.final_result);

              if (event.node) {
                setActiveNode(event.node);
              }
              if (event.iteration !== undefined && event.iteration !== null) {
                setIterationCount(event.iteration);
              }

              // Append event logs
              if (event.logs && Array.isArray(event.logs)) {
                event.logs.forEach((log) => {
                  const level = log.toLowerCase().includes('fail') || log.toLowerCase().includes('error')
                    ? 'error'
                    : log.toLowerCase().includes('success')
                    ? 'success'
                    : 'info';
                  addLog(log, event.node || 'agent', level);
                });
              }
            },
            onComplete: async () => {
              setActiveNode(null);
              const finalStatus = finalEvent?.status;
              if (finalStatus === 'completed') {
                setStatus('completed');
                addLog('Multi-agent pipeline completed successfully.', 'system', 'success');
              } else {
                setStatus('error');
                const reason =
                  finalStatus === 'max_iterations_exceeded'
                    ? 'Circuit breaker tripped: max iterations reached without a working answer.'
                    : finalEvent?.error || 'Pipeline ended without producing an answer.';
                setError(reason);
                addLog(reason, 'system', 'error');
              }
            },
            onError: (err) => {
              setStatus('error');
              setActiveNode(null);
              setError(err.message);
              addLog(`Failed: ${err.message}`, 'system', 'error');
            },
          }
        );
      } catch (err) {
        if (err.name !== 'AbortError') {
          setStatus('error');
          setError(err.message);
          addLog(`Error encountered: ${err.message}`, 'system', 'error');
        }
      }
    } else {
      // Synchronous fallback
      try {
        const result = await executeWorkspace(
          { query: userQuery, max_iterations: iterLimit },
          { signal: abortControllerRef.current.signal }
        );

        applyResult(result);

        if (result.execution_logs && Array.isArray(result.execution_logs)) {
          result.execution_logs.forEach((log) => {
            const level = log.includes('SUCCESS') ? 'success' : log.includes('FAILED') ? 'error' : 'info';
            addLog(log, 'orchestrator', level);
          });
        }

        setStatus(result.status === 'completed' ? 'completed' : 'error');
        setActiveNode(null);
      } catch (err) {
        if (err.name !== 'AbortError') {
          setStatus('error');
          setActiveNode(null);
          setError(err.message);
          addLog(`Execution error: ${err.message}`, 'system', 'error');
        }
      }
    }
  };

  return (
    <AgentContext.Provider
      value={{
        backendUrl,
        updateBackendUrl,
        backendStatus,
        healthInfo,
        refreshHealth,
        status,
        activeNode,
        executionMode,
        setExecutionMode,
        query,
        maxIterations,
        setMaxIterations,
        iterationCount,
        plan,
        generatedCode,
        stdout,
        stderr,
        exitCode,
        reviewFeedback,
        answer,
        logs,
        error,
        elapsedTime,
        runAgent,
        abortRun,
        clearWorkspace,
      }}
    >
      {children}
    </AgentContext.Provider>
  );
}

export function useAgent() {
  const context = useContext(AgentContext);
  if (!context) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
}

