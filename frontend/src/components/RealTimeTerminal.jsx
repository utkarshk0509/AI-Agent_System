import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Code, Cpu, Wrench, Copy, Check, ArrowDownCircle, Trash2, FileText } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

export default function RealTimeTerminal() {
  const { logs, generatedCode, stdout, stderr, exitCode, plan, reviewFeedback, status } = useAgent();
  const [activeTab, setActiveTab] = useState('logs'); // 'logs' | 'code' | 'output' | 'plan'
  const [copied, setCopied] = useState(false);
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef(null);

  // Auto-scroll when new logs arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current && activeTab === 'logs') {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll, activeTab]);

  // Automatically switch tab to code or output when available
  useEffect(() => {
    if (generatedCode && activeTab === 'logs' && status === 'running') {
      // Keep on logs during streaming for live feed
    }
    if (status === 'completed') {
      // If code was generated, user often wants to see output or code
    }
  }, [generatedCode, status]);

  const handleCopy = (content) => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getLogColor = (level) => {
    switch (level) {
      case 'success':
        return 'text-emerald-400 bg-emerald-950/30 border-emerald-800/40';
      case 'error':
        return 'text-rose-400 bg-rose-950/30 border-rose-800/40';
      case 'warn':
        return 'text-amber-400 bg-amber-950/30 border-amber-800/40';
      default:
        return 'text-cyan-400 bg-cyan-950/30 border-cyan-800/40';
    }
  };

  return (
    <div className="bg-panel border border-borderDim rounded-2xl shadow-2xl overflow-hidden flex flex-col h-[520px]">
      {/* Terminal Title Bar */}
      <div className="bg-[#0D121D] px-4 py-2.5 border-b border-borderDim flex items-center justify-between select-none">
        
        {/* Left: Window Dots & Tabs */}
        <div className="flex items-center space-x-4">
          <div className="flex space-x-1.5">
            <div className="w-3 h-3 rounded-full bg-rose-500/80" />
            <div className="w-3 h-3 rounded-full bg-amber-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
          </div>

          {/* Navigation Tabs */}
          <div className="flex space-x-1 bg-surface p-0.5 rounded-lg border border-borderDim text-xs font-mono">
            <button
              onClick={() => setActiveTab('logs')}
              className={`px-3 py-1 rounded-md flex items-center space-x-1.5 transition-all ${
                activeTab === 'logs'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Telemetry ({logs.length})</span>
            </button>

            <button
              onClick={() => setActiveTab('code')}
              className={`px-3 py-1 rounded-md flex items-center space-x-1.5 transition-all ${
                activeTab === 'code'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              <span>Code {generatedCode ? '•' : ''}</span>
            </button>

            <button
              onClick={() => setActiveTab('output')}
              className={`px-3 py-1 rounded-md flex items-center space-x-1.5 transition-all ${
                activeTab === 'output'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Cpu className="w-3.5 h-3.5" />
              <span>Stdout / Stderr {stdout || stderr ? '•' : ''}</span>
            </button>

            <button
              onClick={() => setActiveTab('plan')}
              className={`px-3 py-1 rounded-md flex items-center space-x-1.5 transition-all ${
                activeTab === 'plan'
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Plan & Audit</span>
            </button>
          </div>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center space-x-2 text-xs">
          {activeTab === 'logs' && (
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              title={autoScroll ? 'Disable Auto-scroll' : 'Enable Auto-scroll'}
              className={`px-2 py-1 rounded border text-[11px] font-mono flex items-center space-x-1 transition-colors ${
                autoScroll
                  ? 'bg-cyan-950/40 border-cyan-800 text-cyan-300'
                  : 'bg-surface border-borderDim text-slate-400'
              }`}
            >
              <ArrowDownCircle className="w-3 h-3" />
              <span className="hidden sm:inline">Auto-scroll</span>
            </button>
          )}

          <button
            onClick={() => {
              if (activeTab === 'logs') handleCopy(logs.map(l => `[${l.timestamp}] [${l.node}] ${l.message}`).join('\n'));
              else if (activeTab === 'code') handleCopy(generatedCode);
              else if (activeTab === 'output') handleCopy(`STDOUT:\n${stdout || ''}\n\nSTDERR:\n${stderr || ''}`);
              else if (activeTab === 'plan') handleCopy(plan);
            }}
            title="Copy current tab contents"
            className="p-1.5 rounded hover:bg-surfaceHover text-slate-400 hover:text-slate-200 border border-transparent hover:border-borderDim transition-all"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* Terminal View Body */}
      <div ref={scrollRef} className="flex-1 p-4 overflow-y-auto bg-[#070A10] font-mono text-xs leading-relaxed">
        
        {/* Tab 1: Live Logs View */}
        {activeTab === 'logs' && (
          <div className="space-y-1.5">
            {logs.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-slate-500 py-20 select-none">
                <Terminal className="w-10 h-10 mb-2 opacity-30 text-cyan-400" />
                <p>Telemetry stream idle. Submit a query to initiate multi-agent orchestration.</p>
                <p className="text-[11px] mt-1 text-slate-600">Events from planner, coder, Docker container, and reviewer will appear here.</p>
              </div>
            ) : (
              logs.map((log, i) => (
                <motion.div
                  key={log.id || i}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.15 }}
                  className="flex items-start space-x-2 py-0.5 hover:bg-white/[0.02] rounded px-1 group"
                >
                  <span className="text-slate-600 select-none text-[10px] shrink-0 pt-0.5">
                    {log.timestamp}
                  </span>
                  <span
                    className={`px-1.5 py-0.2 rounded border text-[10px] uppercase font-semibold shrink-0 tracking-wider ${getLogColor(
                      log.level
                    )}`}
                  >
                    {log.node}
                  </span>
                  <span
                    className={`flex-1 break-words ${
                      log.level === 'error'
                        ? 'text-rose-300 font-medium'
                        : log.level === 'success'
                        ? 'text-emerald-300 font-medium'
                        : log.level === 'warn'
                        ? 'text-amber-300'
                        : 'text-slate-300'
                    }`}
                  >
                    {log.message}
                  </span>
                </motion.div>
              ))
            )}
          </div>
        )}

        {/* Tab 2: Python Code View */}
        {activeTab === 'code' && (
          <div>
            {generatedCode ? (
              <div className="relative">
                <div className="text-[11px] text-slate-500 mb-2 border-b border-borderDim pb-1 flex items-center justify-between">
                  <span>Python 3.11 Execution Script (Self-Contained)</span>
                  <span className="text-cyan-400 font-semibold">{generatedCode.split('\n').length} lines</span>
                </div>
                <pre className="text-emerald-300 whitespace-pre font-mono overflow-x-auto p-2 bg-[#05070B] rounded-lg border border-borderDim/60">
                  <code>
                    {generatedCode.split('\n').map((line, idx) => (
                      <div key={idx} className="flex space-x-4">
                        <span className="text-slate-600 select-none text-right w-6 shrink-0">{idx + 1}</span>
                        <span className="flex-1">{line}</span>
                      </div>
                    ))}
                  </code>
                </pre>
              </div>
            ) : (
              <div className="text-slate-500 text-center py-20 select-none">
                <Code className="w-10 h-10 mb-2 mx-auto opacity-30 text-violet-400" />
                <p>No Python code generated yet.</p>
                <p className="text-[11px] mt-1 text-slate-600">The Coder Agent will synthesize executable Python code upon query dispatch.</p>
              </div>
            )}
          </div>
        )}

        {/* Tab 3: Docker Sandbox Stdout / Stderr View */}
        {activeTab === 'output' && (
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-slate-400 text-[11px] mb-1 font-semibold uppercase tracking-wider">
                <span className="flex items-center space-x-1.5 text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>Captured stdout (Standard Output)</span>
                </span>
                {exitCode !== null && (
                  <span className={exitCode === 0 ? 'text-emerald-400' : 'text-rose-400'}>
                    Status: {exitCode === 0 ? 'CLEAN (0)' : `EXIT (${exitCode})`}
                  </span>
                )}
              </div>
              <pre className="bg-[#05070B] p-3 rounded-lg border border-borderDim text-slate-200 overflow-x-auto min-h-[100px] whitespace-pre-wrap">
                {stdout || <span className="text-slate-600 italic">No stdout emitted.</span>}
              </pre>
            </div>

            {stderr && (
              <div>
                <div className="flex items-center space-x-1.5 text-rose-400 text-[11px] mb-1 font-semibold uppercase tracking-wider">
                  <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
                  <span>Captured stderr & Traceback</span>
                </div>
                <pre className="bg-rose-950/20 p-3 rounded-lg border border-rose-900/50 text-rose-300 overflow-x-auto whitespace-pre-wrap">
                  {stderr}
                </pre>
              </div>
            )}
          </div>
        )}

        {/* Tab 4: Plan & Diagnostics View */}
        {activeTab === 'plan' && (
          <div className="space-y-4">
            {plan && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-cyan-400 mb-2">
                  Planner Agent Decomposition:
                </h4>
                <div className="p-3 bg-[#05070B] rounded-lg border border-borderDim text-slate-300 whitespace-pre-wrap leading-relaxed text-xs">
                  {plan}
                </div>
              </div>
            )}

            {reviewFeedback && (
              <div>
                <h4 className="text-xs font-semibold uppercase tracking-wider text-amber-400 mb-2 flex items-center space-x-1.5">
                  <Wrench className="w-3.5 h-3.5 text-amber-400" />
                  <span>Reviewer Diagnosis & Repair Instructions:</span>
                </h4>
                <div className="p-3 bg-amber-950/20 rounded-lg border border-amber-900/40 text-amber-200 whitespace-pre-wrap leading-relaxed text-xs">
                  {reviewFeedback}
                </div>
              </div>
            )}

            {!plan && !reviewFeedback && (
              <div className="text-slate-500 text-center py-20 select-none">
                <FileText className="w-10 h-10 mb-2 mx-auto opacity-30 text-cyan-400" />
                <p>No architectural plan or review diagnostics recorded.</p>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}

