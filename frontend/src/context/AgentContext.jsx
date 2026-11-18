import React, { createContext, useContext, useState, useEffect, useRef } from 'react';
import { checkBackendHealth, executeWorkspace, streamWorkspace, getBackendUrl, setBackendUrl } from '../services/api';

const AgentContext = createContext();

// Pick a log color from the message text
function logLevel(message) {
  const text = message.toLowerCase();
  if (text.includes('fail') || text.includes('error')) return 'error';
  if (text.includes('success')) return 'success';
  return 'info';
}

export function AgentProvider({ children }) {
  const [backendUrl, setBackendUrlState] = useState(getBackendUrl());
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [healthInfo, setHealthInfo] = useState({ docker_available: false, execution_mode: 'subprocess', gemini_model: '' });
  
  // Execution state
  const [status, setStatus] = useState('idle'); // 'idle' | 'running' | 'completed' | 'error' | 'aborted'
  const [activeNode, setActiveNode] = useState(null); // 'planner' | 'coder' | 'executor' | 'reviewer' | 'answer'
  const [visitedNodes, setVisitedNodes] = useState([]);
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
  const [elapsedTime, setElapsedTime] = useState(0);

  const abortControllerRef = useRef(null);
  const timerRef = useRef(null);

  const refreshHealth = async (targetUrl = null) => {
    setBackendStatus('checking');
    const health = await checkBackendHealth(targetUrl || backendUrl);
    setBackendStatus(health.status === 'healthy' ? 'online' : 'offline');
    setHealthInfo(health);
  };

  // Check the backend on load, when the URL changes, and every 20s
  useEffect(() => {
    refreshHealth();
    const interval = setInterval(() => refreshHealth(), 20000);
    return () => clearInterval(interval);
  }, [backendUrl]);

  // Elapsed time shown while a run is going
  useEffect(() => {
    if (status === 'running') {
      const start = Date.now();
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
    setVisitedNodes([]);
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
    addLog('Run stopped.', 'system', 'warn');
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
    addLog(`Started: "${userQuery.slice(0, 80)}${userQuery.length > 80 ? '…' : ''}"`, 'system', 'info');

    if (executionMode === 'stream') {
      let finalEvent = null;
      // streamWorkspace catches its own errors and reports them through onError
      await streamWorkspace(
        { query: userQuery, max_iterations: iterLimit },
        {
          signal: abortControllerRef.current.signal,
          onEvent: (event) => {
            // The last event carries the full result (or an error) and the real status
            if (event.node === 'done') {
              finalEvent = event;
              if (event.error) {
                setError(event.error);
                addLog(`Stream error: ${event.error}`, 'system', 'error');
              } else {
                applyResult(event.result || {});
              }
              return;
            }

            // Whatever this node produced (plan, code, stdout, ...)
            const d = event.data || {};
            if ('plan' in d) setPlan(d.plan);
            if ('generated_code' in d) setGeneratedCode(d.generated_code);
            if ('stdout' in d) setStdout(d.stdout);
            if ('stderr' in d) setStderr(d.stderr);
            if ('exit_code' in d) setExitCode(d.exit_code);
            if ('review_feedback' in d) setReviewFeedback(d.review_feedback);
            if (d.final_result) setAnswer(d.final_result);

            setActiveNode(event.node);
            setVisitedNodes((prev) => (prev.includes(event.node) ? prev : [...prev, event.node]));
            if (event.iteration != null) {
              setIterationCount(event.iteration);
            }

            (event.logs || []).forEach((log) => addLog(log, event.node, logLevel(log)));
          },
          onComplete: () => {
            setActiveNode(null);
            const finalStatus = finalEvent?.status;
            if (finalStatus === 'completed') {
              setStatus('completed');
              addLog('Finished.', 'system', 'success');
            } else {
              setStatus('error');
              const reason =
                finalStatus === 'max_iterations_exceeded'
                  ? 'Stopped after reaching the retry limit without working code.'
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
    } else {
      // Wait for the single final response
      try {
        const result = await executeWorkspace(
          { query: userQuery, max_iterations: iterLimit },
          abortControllerRef.current.signal
        );

        applyResult(result);
        (result.execution_logs || []).forEach((log) => addLog(log, 'orchestrator', logLevel(log)));

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
        visitedNodes,
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

