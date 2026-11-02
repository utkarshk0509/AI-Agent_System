import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Play, Square, Sparkles, RefreshCw, Layers, Radio, CornerDownLeft } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

const PRESET_QUERIES = [
  {
    title: 'Primes Calculation',
    query: 'Calculate all prime numbers under 100, find their sum and average, and output a clean JSON object.',
  },
  {
    title: 'Data Distribution',
    query: 'Generate 50 random samples from a normal distribution (mean=25, std=5), compute median and variance, and print formatted statistics.',
  },
  {
    title: 'Self-Healing Test',
    query: 'Create a list of numbers. Attempt to access an invalid index to trigger IndexError, but self-correct to handle the error and print recovered state.',
  },
  {
    title: 'Fibonacci Sequence',
    query: 'Compute the first 30 Fibonacci numbers and print the sequence along with the golden ratio convergence.',
  },
];

export default function CommandInterface() {
  const {
    runAgent,
    abortRun,
    clearWorkspace,
    status,
    maxIterations,
    setMaxIterations,
    executionMode,
    setExecutionMode,
  } = useAgent();

  const [inputQuery, setInputQuery] = useState('');

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleSubmit = () => {
    if (!inputQuery.trim() || status === 'running') return;
    runAgent(inputQuery);
  };

  const isRunning = status === 'running';

  return (
    <div className="bg-panel/90 border border-borderDim rounded-2xl p-4 sm:p-5 shadow-xl relative overflow-hidden backdrop-blur-sm">
      {/* Top subtle glow bar */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-cyan-500/50 to-transparent" />

      {/* Preset Pills */}
      <div className="flex items-center space-x-2 overflow-x-auto pb-3 mb-3 scrollbar-none text-xs">
        <span className="text-slate-400 font-medium flex items-center space-x-1 pl-1">
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span className="text-[11px] uppercase tracking-wider">Presets:</span>
        </span>
        {PRESET_QUERIES.map((preset, idx) => (
          <button
            key={idx}
            disabled={isRunning}
            onClick={() => setInputQuery(preset.query)}
            className="px-2.5 py-1 rounded-lg bg-surface/80 hover:bg-surfaceHover text-slate-300 hover:text-cyan-300 border border-borderDim hover:border-cyan-500/40 text-[11px] whitespace-nowrap transition-all disabled:opacity-50"
          >
            {preset.title}
          </button>
        ))}
      </div>

      {/* Main Textarea Input */}
      <div className="relative rounded-xl border border-borderDim bg-[#090D16]/90 focus-within:border-cyan-500/60 focus-within:ring-1 focus-within:ring-cyan-500/40 transition-all">
        <textarea
          rows={3}
          value={inputQuery}
          disabled={isRunning}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the autonomous workspace to calculate, analyze, or process data (e.g. 'Analyze dataset variance and output JSON summary')..."
          className="w-full bg-transparent p-3.5 text-sm text-slate-100 placeholder-slate-500 resize-none focus:outline-none disabled:opacity-60 font-sans"
        />

        {/* Input Controls Footer */}
        <div className="px-3.5 py-2 border-t border-borderDim/70 flex flex-wrap items-center justify-between gap-3 bg-surface/30 rounded-b-xl">
          
          {/* Controls: Iterations & Stream Toggle */}
          <div className="flex items-center space-x-4 text-xs text-slate-400">
            {/* Iterations Limit */}
            <div className="flex items-center space-x-1.5" title="Maximum self-healing attempts before circuit breaker">
              <Layers className="w-3.5 h-3.5 text-slate-400" />
              <span>Max Retries:</span>
              <select
                disabled={isRunning}
                value={maxIterations}
                onChange={(e) => setMaxIterations(Number(e.target.value))}
                className="bg-panel border border-borderDim rounded px-2 py-0.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
              >
                {[1, 2, 3, 5, 8, 10].map((num) => (
                  <option key={num} value={num}>
                    {num} iterations
                  </option>
                ))}
              </select>
            </div>

            {/* Stream Mode Toggle */}
            <div className="hidden sm:flex items-center space-x-1.5" title="Real-time Server-Sent Events vs Single Response">
              <Radio className="w-3.5 h-3.5 text-cyan-400" />
              <span>Mode:</span>
              <button
                type="button"
                onClick={() => setExecutionMode(executionMode === 'stream' ? 'sync' : 'stream')}
                disabled={isRunning}
                className="px-2 py-0.5 rounded bg-panel border border-borderDim hover:border-cyan-500/50 text-[11px] font-mono text-cyan-300 uppercase transition-colors"
              >
                {executionMode}
              </button>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2 ml-auto">
            <span className="hidden md:inline text-[11px] text-slate-500 font-mono pr-1">
              Ctrl + Enter
            </span>

            {/* Clear Button */}
            <button
              onClick={() => {
                setInputQuery('');
                clearWorkspace();
              }}
              disabled={isRunning || (!inputQuery && status === 'idle')}
              title="Clear input and telemetry"
              className="px-3 py-1.5 rounded-lg border border-borderDim text-slate-400 hover:text-slate-200 hover:bg-surfaceHover/70 text-xs font-medium transition-all disabled:opacity-40"
            >
              Clear
            </button>

            {/* Abort Button (when running) */}
            {isRunning ? (
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={abortRun}
                className="px-4 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white font-medium text-xs flex items-center space-x-1.5 shadow-lg shadow-rose-900/40 transition-all cursor-pointer"
              >
                <Square className="w-3.5 h-3.5 fill-current" />
                <span>Stop Agent</span>
              </motion.button>
            ) : (
              /* Run Button */
              <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleSubmit}
                disabled={!inputQuery.trim()}
                className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white font-semibold text-xs flex items-center space-x-1.5 shadow-lg shadow-cyan-950/60 transition-all disabled:opacity-50 disabled:pointer-events-none cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Execute Query</span>
              </motion.button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

