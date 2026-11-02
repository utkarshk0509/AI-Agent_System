import React from 'react';
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { AgentProvider } from './context/AgentContext';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import ConfigPage from './pages/ConfigPage';

function AnimatedRoutes() {
  const location = useLocation();

  return (
    <AnimatePresence mode="wait">
      <Routes location={location} key={location.pathname}>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="*" element={<DashboardPage />} />
      </Routes>
    </AnimatePresence>
  );
}

export default function App() {
  return (
    <AgentProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col bg-[#090D16] text-slate-100 font-sans selection:bg-cyan-500/30 selection:text-cyan-200">
          {/* Top Sticky Navigation */}
          <Navbar />

          {/* Main View Area */}
          <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <AnimatedRoutes />
          </main>

          {/* Bottom Minimal Footer */}
          <footer className="border-t border-borderDim/70 py-4 text-center text-xs text-slate-500 font-mono">
            Autonomous Code & Analysis Workspace • LangGraph Orchestration • Docker Isolation
          </footer>
        </div>
      </BrowserRouter>
    </AgentProvider>
  );
}

