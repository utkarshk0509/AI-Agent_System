import React from 'react';
import { Link } from 'react-router-dom';
import { useAgent } from '../context/AgentContext';
import PromptBox from '../components/PromptBox';
import RunProgress from '../components/RunProgress';
import ResultPanel from '../components/ResultPanel';

export default function DashboardPage() {
  const { status, backendStatus, backendUrl } = useAgent();

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Ask a question</h1>
        <p className="mt-1 text-[15px] text-muted">
          Describe something to calculate or analyze. A Python script is written and run for you, and if it fails it is
          fixed and run again.
        </p>
      </div>

      {backendStatus === 'offline' && (
        <div className="rounded-lg border border-warn/30 bg-warn/5 px-4 py-3 text-sm">
          <p className="font-medium text-warn">Can't reach the backend</p>
          <p className="mt-0.5 text-muted">
            Nothing is responding at <span className="font-mono text-ink">{backendUrl}</span>. Start the server, or
            change the address in{' '}
            <Link to="/config" className="text-accent underline underline-offset-2">
              Settings
            </Link>
            .
          </p>
        </div>
      )}

      <PromptBox />

      {status !== 'idle' && (
        <div className="space-y-3">
          <RunProgress />
          <ResultPanel />
        </div>
      )}
    </div>
  );
}
