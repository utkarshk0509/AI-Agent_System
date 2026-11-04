import React from 'react';
import { NavLink } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Terminal, Settings, Activity, Cpu, Box, CheckCircle2, AlertCircle, RefreshCw } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

export default function Navbar() {
  const { backendStatus, healthInfo, status, activeNode, refreshHealth } = useAgent();

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-[#0B0F17]/85 border-b border-borderDim">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand Logo & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-violet-600 p-[1px] shadow-glow-cyan">
            <div className="w-full h-full bg-[#0B0F17] rounded-[11px] flex items-center justify-center">
              <Terminal className="w-5 h-5 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                AUTONOMOUS WORKSPACE
              </span>
              <span className="px-1.5 py-0.5 text-[10px] font-semibold tracking-wider uppercase bg-cyan-950/80 text-cyan-400 border border-cyan-800/60 rounded">
                v2.5
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden sm:block">
              Cyclic Multi-Agent Orchestration & Docker Sandbox
            </p>
          </div>
        </div>

        {/* Center Navigation Links */}
        <nav className="flex items-center space-x-1 bg-panel/60 border border-borderDim rounded-xl p-1">
          <NavLink
            to="/"
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-surfaceHover/50'
              }`
            }
          >
            <Activity className="w-3.5 h-3.5" />
            <span>Workspace</span>
          </NavLink>

          <NavLink
            to="/config"
            className={({ isActive }) =>
              `flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-medium transition-all ${
                isActive
                  ? 'bg-cyan-500/15 text-cyan-300 border border-cyan-500/30 shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-surfaceHover/50'
              }`
            }
          >
            <Settings className="w-3.5 h-3.5" />
            <span>Settings</span>
          </NavLink>
        </nav>

        {/* Status Indicators (Backend & Docker Health) */}
        <div className="flex items-center space-x-2 sm:space-x-3">
          {/* Active Node Chip (when running) */}
          {status === 'running' && activeNode && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              className="hidden md:flex items-center space-x-1.5 px-2.5 py-1 rounded-full bg-violet-950/60 border border-violet-700/50 text-[11px] text-violet-300 font-mono shadow-glow-violet"
            >
              <span className="w-2 h-2 rounded-full bg-violet-400 animate-ping" />
              <span className="capitalize">{activeNode} node active</span>
            </motion.div>
          )}

          {/* Docker / Execution Mode Indicator */}
          <div
            title={
              healthInfo.docker_available
                ? 'Docker Sandbox: container isolation active'
                : healthInfo.execution_mode === 'subprocess'
                ? 'Docker offline — running code via local subprocess (no isolation)'
                : 'Docker not detected (fallback mode)'
            }
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono transition-colors ${
              healthInfo.docker_available
                ? 'bg-emerald-950/40 border-emerald-800/60 text-emerald-300'
                : healthInfo.execution_mode === 'subprocess'
                ? 'bg-blue-950/40 border-blue-800/50 text-blue-300'
                : 'bg-amber-950/30 border-amber-800/50 text-amber-300'
            }`}
          >
            <Box className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Sandbox</span>
            <span className="text-[10px] opacity-75">
              {healthInfo.docker_available
                ? 'Docker'
                : healthInfo.execution_mode === 'subprocess'
                ? 'Subprocess'
                : 'Mock'}
            </span>
          </div>

          {/* Backend Health Badge */}
          <button
            onClick={() => refreshHealth()}
            title="Click to re-ping backend server"
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-lg border text-xs font-mono cursor-pointer transition-all hover:brightness-110 ${
              backendStatus === 'online'
                ? 'bg-cyan-950/40 border-cyan-800/60 text-cyan-300'
                : backendStatus === 'checking'
                ? 'bg-slate-900 border-slate-700 text-slate-400'
                : 'bg-rose-950/40 border-rose-800/60 text-rose-300'
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                backendStatus === 'online'
                  ? 'bg-emerald-400 animate-pulse'
                  : backendStatus === 'checking'
                  ? 'bg-amber-400 animate-spin'
                  : 'bg-rose-500'
              }`}
            />
            <span className="capitalize">{backendStatus}</span>
          </button>
        </div>

      </div>
    </header>
  );
}

