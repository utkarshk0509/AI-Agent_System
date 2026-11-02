import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Compass, Code, Box, Wrench, CheckCircle2, AlertOctagon, RotateCw, Clock } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

const NODES = [
  { id: 'planner', name: 'Planner', description: 'Decompose query', icon: Compass, color: 'cyan' },
  { id: 'coder', name: 'Coder', description: 'Gemini Python synth', icon: Code, color: 'violet' },
  { id: 'executor', name: 'Executor', description: 'Docker sandbox run', icon: Box, color: 'emerald' },
  { id: 'reviewer', name: 'Reviewer', description: 'Self-healing audit', icon: Wrench, color: 'amber' },
];

export default function AgentPipeline() {
  const { status, activeNode, iterationCount, maxIterations, elapsedTime, exitCode } = useAgent();

  const isRunning = status === 'running';

  return (
    <div className="bg-panel/80 border border-borderDim rounded-2xl p-4 sm:p-5 shadow-lg relative overflow-hidden backdrop-blur-sm">
      {/* Header Info */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5 border-b border-borderDim/70 pb-3">
        <div className="flex items-center space-x-2">
          <div className="w-2 h-2 rounded-full bg-cyan-400" />
          <h2 className="text-xs font-semibold uppercase tracking-wider text-slate-300">
            Multi-Agent State Graph
          </h2>
          <span className="text-[11px] text-slate-500 font-mono">
            (Cyclic LangGraph Orchestrator)
          </span>
        </div>

        {/* Telemetry Chips */}
        <div className="flex items-center space-x-2 text-xs font-mono">
          {/* Iteration Counter */}
          <div className="px-2.5 py-1 rounded-lg bg-surface border border-borderDim text-slate-300 flex items-center space-x-1.5">
            <RotateCw className={`w-3 h-3 text-cyan-400 ${isRunning ? 'animate-spin' : ''}`} />
            <span>
              Iter: <strong className="text-white">{iterationCount}</strong>/{maxIterations}
            </span>
          </div>

          {/* Execution Timer */}
          <div className="px-2.5 py-1 rounded-lg bg-surface border border-borderDim text-slate-300 flex items-center space-x-1.5">
            <Clock className="w-3 h-3 text-violet-400" />
            <span>{Math.floor(elapsedTime / 60)}m {elapsedTime % 60}s</span>
          </div>

          {/* Exit Code Status */}
          {exitCode !== null && (
            <div
              className={`px-2.5 py-1 rounded-lg border flex items-center space-x-1 ${
                exitCode === 0
                  ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                  : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
              }`}
            >
              <span>Exit Code: {exitCode}</span>
            </div>
          )}
        </div>
      </div>

      {/* Pipeline Node Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 relative">
        {NODES.map((node, index) => {
          const Icon = node.icon;
          const isActive = activeNode === node.id;
          const isCompleted =
            status === 'completed' ||
            (node.id === 'planner' && ['coder', 'executor', 'reviewer'].includes(activeNode));

          return (
            <motion.div
              key={node.id}
              layout
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
              className={`relative rounded-xl p-3.5 border transition-all duration-300 flex flex-col justify-between ${
                isActive
                  ? 'bg-surface border-cyan-500 shadow-glow-cyan'
                  : isCompleted
                  ? 'bg-surface/60 border-slate-700/80'
                  : 'bg-[#090D16]/50 border-borderDim opacity-65'
              }`}
            >
              {/* Active Pulse Glow */}
              {isActive && (
                <span className="absolute -top-1 -right-1 flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-cyan-500"></span>
                </span>
              )}

              {/* Node Top: Icon & Step Number */}
              <div className="flex items-center justify-between mb-2">
                <div
                  className={`w-8 h-8 rounded-lg flex items-center justify-center border ${
                    isActive
                      ? 'bg-cyan-500/20 border-cyan-500/40 text-cyan-300'
                      : isCompleted
                      ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
                      : 'bg-panel border-borderDim text-slate-400'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-[10px] font-mono font-semibold text-slate-500 uppercase tracking-widest">
                  Step 0{index + 1}
                </span>
              </div>

              {/* Node Title & Description */}
              <div>
                <h3 className="text-sm font-semibold text-slate-100 flex items-center space-x-1.5">
                  <span>{node.name}</span>
                  {isActive && (
                    <span className="text-[10px] font-normal text-cyan-400 animate-pulse font-mono">
                      [Active]
                    </span>
                  )}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">{node.description}</p>
              </div>

              {/* Status Footer */}
              <div className="mt-3 pt-2 border-t border-borderDim/50 flex items-center justify-between text-[11px] font-mono">
                <span className="text-slate-500">Node ID:</span>
                <span
                  className={
                    isActive
                      ? 'text-cyan-400 font-semibold'
                      : isCompleted
                      ? 'text-emerald-400'
                      : 'text-slate-400'
                  }
                >
                  {node.id}_node
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Cyclic Repair Notice */}
      <AnimatePresence>
        {activeNode === 'reviewer' && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3.5 p-3 rounded-xl bg-amber-950/30 border border-amber-800/50 flex items-center space-x-3 text-xs text-amber-300"
          >
            <RotateCw className="w-4 h-4 animate-spin text-amber-400 shrink-0" />
            <div>
              <span className="font-semibold">Self-Healing Cycle Engaged:</span> Reviewer detected non-zero exit code or stderr. Formulating repair instructions and routing back to Coder node...
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

