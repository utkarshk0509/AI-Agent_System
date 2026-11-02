import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Settings, Server, Shield, Cpu, RefreshCw, Check, AlertTriangle, Save } from 'lucide-react';
import { useAgent } from '../context/AgentContext';
import { checkBackendHealth } from '../services/api';

export default function ConfigPage() {
  const {
    backendUrl,
    updateBackendUrl,
    backendStatus,
    healthInfo,
    maxIterations,
    setMaxIterations,
    executionMode,
    setExecutionMode,
  } = useAgent();

  const [inputUrl, setInputUrl] = useState(backendUrl);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleTestConnection = async () => {
    setTesting(true);
    setTestResult(null);
    const t0 = performance.now();
    const res = await checkBackendHealth(inputUrl);
    const latency = Math.round(performance.now() - t0);

    if (res.status === 'healthy') {
      setTestResult({
        success: true,
        latency,
        message: `Connected successfully in ${latency}ms! Model: ${res.gemini_model}, Docker: ${
          res.docker_available ? 'Available' : 'Fallback Mock'
        }`,
      });
    } else {
      setTestResult({
        success: false,
        latency,
        message: `Failed to connect: ${res.error || 'Server unreachable at ' + inputUrl}`,
      });
    }
    setTesting(false);
  };

  const handleSave = (e) => {
    e.preventDefault();
    updateBackendUrl(inputUrl);
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.25 }}
      className="max-w-4xl mx-auto space-y-6"
    >
      {/* Header */}
      <div className="flex items-center space-x-3 border-b border-borderDim pb-4">
        <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
          <Settings className="w-6 h-6" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-100">Workspace Configuration</h1>
          <p className="text-xs text-slate-400">
            Configure backend connection endpoints, execution policies, and model routing.
          </p>
        </div>
      </div>

      {/* Backend API Connection Form */}
      <div className="bg-panel/90 border border-borderDim rounded-2xl p-5 shadow-xl space-y-4">
        <div className="flex items-center space-x-2 text-sm font-semibold text-slate-200">
          <Server className="w-4 h-4 text-cyan-400" />
          <span>Backend API Gateway</span>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-mono text-slate-400 mb-1.5">
              BACKEND ENDPOINT URL
            </label>
            <div className="flex items-center space-x-2">
              <input
                type="url"
                required
                value={inputUrl}
                onChange={(e) => setInputUrl(e.target.value)}
                placeholder="http://localhost:8000"
                className="flex-1 bg-[#090D16] border border-borderDim rounded-xl px-4 py-2.5 text-sm text-slate-100 font-mono focus:outline-none focus:border-cyan-500/60"
              />
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testing}
                className="px-4 py-2.5 rounded-xl bg-surface hover:bg-surfaceHover border border-borderDim text-slate-200 text-xs font-medium flex items-center space-x-1.5 transition-colors disabled:opacity-50 cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${testing ? 'animate-spin' : ''}`} />
                <span>Test Ping</span>
              </button>
              <button
                type="submit"
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white text-xs font-semibold flex items-center space-x-1.5 transition-all shadow-md cursor-pointer"
              >
                {saved ? <Check className="w-4 h-4 text-white" /> : <Save className="w-4 h-4" />}
                <span>{saved ? 'Saved!' : 'Save URL'}</span>
              </button>
            </div>
          </div>
        </form>

        {/* Test Connection Result Box */}
        {testResult && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            className={`p-3.5 rounded-xl border text-xs font-mono flex items-start space-x-2.5 ${
              testResult.success
                ? 'bg-emerald-950/30 border-emerald-800/50 text-emerald-300'
                : 'bg-rose-950/30 border-rose-800/50 text-rose-300'
            }`}
          >
            {testResult.success ? (
              <Check className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            )}
            <div>
              <p className="font-semibold">{testResult.message}</p>
              <p className="text-[11px] opacity-75 mt-0.5">Round-trip response time: {testResult.latency}ms</p>
            </div>
          </motion.div>
        )}
      </div>

      {/* Execution Policies & Guardrails */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        
        {/* Guardrail Iterations */}
        <div className="bg-panel/90 border border-borderDim rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center space-x-2 text-sm font-semibold text-slate-200">
            <Shield className="w-4 h-4 text-violet-400" />
            <span>Circuit Breaker Guardrail</span>
          </div>
          <p className="text-xs text-slate-400">
            Enforces a hard upper ceiling on self-healing retry iterations to protect your API budget and avoid infinite repair loops.
          </p>

          <div className="pt-2">
            <div className="flex items-center justify-between text-xs text-slate-300 mb-1.5 font-mono">
              <span>Max Retries per Task:</span>
              <span className="text-cyan-400 font-bold">{maxIterations} attempts</span>
            </div>
            <input
              type="range"
              min="1"
              max="10"
              value={maxIterations}
              onChange={(e) => setMaxIterations(Number(e.target.value))}
              className="w-full accent-cyan-500 cursor-pointer"
            />
            <div className="flex justify-between text-[10px] text-slate-500 font-mono mt-1">
              <span>1 (No retry)</span>
              <span>5 (Recommended)</span>
              <span>10 (Max)</span>
            </div>
          </div>
        </div>

        {/* Transport Mode */}
        <div className="bg-panel/90 border border-borderDim rounded-2xl p-5 shadow-xl space-y-3">
          <div className="flex items-center space-x-2 text-sm font-semibold text-slate-200">
            <Cpu className="w-4 h-4 text-emerald-400" />
            <span>Telemetry Transport Protocol</span>
          </div>
          <p className="text-xs text-slate-400">
            Select between real-time step-by-step event streaming or synchronous batch output.
          </p>

          <div className="grid grid-cols-2 gap-2 pt-2">
            <button
              type="button"
              onClick={() => setExecutionMode('stream')}
              className={`p-3 rounded-xl border text-left transition-all ${
                executionMode === 'stream'
                  ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-300'
                  : 'bg-surface border-borderDim text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="text-xs font-bold font-mono">SSE Stream</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Real-time node transitions</div>
            </button>

            <button
              type="button"
              onClick={() => setExecutionMode('sync')}
              className={`p-3 rounded-xl border text-left transition-all ${
                executionMode === 'sync'
                  ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-300'
                  : 'bg-surface border-borderDim text-slate-400 hover:text-slate-200'
              }`}
            >
              <div className="text-xs font-bold font-mono">Sync REST</div>
              <div className="text-[10px] text-slate-400 mt-0.5">Single JSON response</div>
            </button>
          </div>
        </div>

      </div>

      {/* Security Policies Overview */}
      <div className="p-4 rounded-xl bg-surface/60 border border-borderDim text-xs text-slate-400 space-y-2">
        <div className="font-semibold text-slate-300 flex items-center space-x-1.5">
          <Shield className="w-3.5 h-3.5 text-emerald-400" />
          <span>Active Sandboxing Hardening Constraints</span>
        </div>
        <ul className="list-disc pl-5 space-y-1 text-[11px] font-mono text-slate-400">
          <li>Network isolation: <code className="text-cyan-400">network_mode="none"</code> (prevents SSRF & data exfiltration)</li>
          <li>Memory ceiling: <code className="text-cyan-400">mem_limit="512m"</code> with process cgroup quota</li>
          <li>Execution timeout: <code className="text-cyan-400">EXECUTION_TIMEOUT_SECONDS=30</code> with exit code 124 termination</li>
          <li>Privilege escalation: <code className="text-cyan-400">no-new-privileges:true</code> under unprivileged user</li>
        </ul>
      </div>
    </motion.div>
  );
}

