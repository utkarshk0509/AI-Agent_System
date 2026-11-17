import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AgentProvider } from './context/AgentContext';
import Navbar from './components/Navbar';
import DashboardPage from './pages/DashboardPage';
import ConfigPage from './pages/ConfigPage';

export default function App() {
  return (
    <AgentProvider>
      <BrowserRouter>
        <div className="min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1 w-full max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-10">
            <Routes>
              <Route path="/config" element={<ConfigPage />} />
              <Route path="*" element={<DashboardPage />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </AgentProvider>
  );
}
