import React from 'react';
import { motion } from 'framer-motion';
import { Activity, Cpu, ShieldCheck, Layers } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

export default function MetricCards() {
  const { status, healthInfo, iterationCount, maxIterations, exitCode } = useAgent();

  const metrics = [
    {
      title: 'Pipeline State',
      value: status.toUpperCase(),
      subtext: status === 'running' ? 'Active execution cycle' : 'Awaiting input',
      icon: Activity,
      color:
        status === 'completed'
          ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50'
          : status === 'running'
          ? 'text-cyan-400 bg-cyan-950/40 border-cyan-800/50'
          : status === 'error'
          ? 'text-rose-400 bg-rose-950/40 border-rose-800/50'
          : 'text-slate-400 bg-panel border-borderDim',
    },
    {
      title: 'LLM Orchestrator',
      value: healthInfo.gemini_model || 'gemini-3.8-flash',
      subtext: 'High-speed reasoning model',
      icon: Cpu,
      color: 'text-violet-400 bg-violet-950/40 border-violet-800/50',
    },
    {
      title: 'Execution Sandbox',
      value: healthInfo.docker_available ? 'Docker Container' : 'Mock Dev Sandbox',
      subtext: healthInfo.docker_available ? 'Memory & network bounded' : 'Daemon not detected',
      icon: ShieldCheck,
      color: healthInfo.docker_available
        ? 'text-emerald-400 bg-emerald-950/40 border-emerald-800/50'
        : 'text-amber-400 bg-amber-950/40 border-amber-800/50',
    },
    {
      title: 'Iteration Guardrail',
      value: `${iterationCount} / ${maxIterations} Retries`,
      subtext: exitCode !== null ? `Exit code: ${exitCode}` : 'Circuit breaker armed',
      icon: Layers,
      color: 'text-cyan-400 bg-cyan-950/40 border-cyan-800/50',
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
      {metrics.map((m, idx) => {
        const Icon = m.icon;
        return (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="p-3.5 sm:p-4 rounded-xl bg-panel/70 border border-borderDim backdrop-blur-sm flex items-start space-x-3"
          >
            <div className={`p-2 rounded-lg border ${m.color}`}>
              <Icon className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <span className="text-[11px] font-medium text-slate-400 uppercase tracking-wider block">
                {m.title}
              </span>
              <div className="text-sm sm:text-base font-bold text-slate-100 truncate mt-0.5 font-mono">
                {m.value}
              </div>
              <span className="text-[11px] text-slate-500 block truncate">
                {m.subtext}
              </span>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}

