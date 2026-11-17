import React from 'react';
import { NavLink } from 'react-router-dom';
import { Code2 } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

const linkClass = ({ isActive }) =>
  `px-3 py-1.5 rounded-md text-sm transition-colors ${
    isActive ? 'bg-inset text-ink font-medium' : 'text-muted hover:text-ink'
  }`;

function ConnectionStatus() {
  const { backendStatus, healthInfo, refreshHealth } = useAgent();

  const label =
    backendStatus === 'online' ? 'Connected' : backendStatus === 'checking' ? 'Checking…' : 'Offline';
  const dot =
    backendStatus === 'online' ? 'bg-ok' : backendStatus === 'checking' ? 'bg-faint' : 'bg-err';
  const sandbox = healthInfo.docker_available ? 'Docker' : 'Local process';

  return (
    <button
      type="button"
      onClick={() => refreshHealth()}
      title="Check the connection again"
      className="ml-auto flex items-center gap-2 rounded-md px-2.5 py-1.5 text-sm text-muted hover:bg-inset hover:text-ink transition-colors"
    >
      <span className={`h-2 w-2 rounded-full ${dot}`} />
      <span>{label}</span>
      {backendStatus === 'online' && (
        <span className="hidden sm:inline text-faint">· {sandbox}</span>
      )}
    </button>
  );
}

export default function Navbar() {
  return (
    <header className="border-b border-line bg-surface">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 h-14 flex items-center gap-4 sm:gap-6">
        <NavLink to="/" className="flex items-center gap-2 font-semibold text-[15px] shrink-0">
          <Code2 className="h-5 w-5 text-accent" strokeWidth={2.2} />
          <span>Code Workspace</span>
        </NavLink>
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            Workspace
          </NavLink>
          <NavLink to="/config" className={linkClass}>
            Settings
          </NavLink>
        </nav>
        <ConnectionStatus />
      </div>
    </header>
  );
}
