import React from 'react';
import { motion } from 'framer-motion';
import MetricCards from '../components/MetricCards';
import CommandInterface from '../components/CommandInterface';
import AgentPipeline from '../components/AgentPipeline';
import RealTimeTerminal from '../components/RealTimeTerminal';

export default function DashboardPage() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -15 }}
      transition={{ duration: 0.25 }}
      className="space-y-5"
    >
      {/* KPI Cards */}
      <MetricCards />

      {/* Main Command Input Interface */}
      <CommandInterface />

      {/* Visual State Graph Pipeline */}
      <AgentPipeline />

      {/* Real-time Multi-Tab Monospace Terminal */}
      <RealTimeTerminal />
    </motion.div>
  );
}

