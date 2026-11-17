import React, { useState } from 'react';
import { useAgent } from '../context/AgentContext';
import { checkBackendHealth } from '../services/api';

function Section({ title, description, children }) {
  return (
    <section className="grid gap-3 px-5 py-5 sm:grid-cols-[14rem_1fr] sm:gap-8">
      <div>
        <h2 className="text-sm font-medium">{title}</h2>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      <div>{children}</div>
    </section>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex justify-between gap-4 py-1.5 text-sm">
      <dt className="text-muted">{label}</dt>
      <dd className="text-right">{children}</dd>
    </div>
  );
}

export default function ConfigPage() {
  const {
    backendUrl,
    updateBackendUrl,
    backendStatus,
    healthInfo,
    maxIterations,
    setMaxIterations,
    executionMode,
    setExecutionMode,
  } = useAgent();

  const [url, setUrl] = useState(backendUrl);
  const [test, setTest] = useState(null);
  const [testing, setTesting] = useState(false);
  const [saved, setSaved] = useState(false);

  const runTest = async () => {
    setTesting(true);
    setTest(null);
    const t0 = performance.now();
    const res = await checkBackendHealth(url);
    const ms = Math.round(performance.now() - t0);
    setTest(
      res.status === 'healthy'
        ? { ok: true, text: `Connected (${ms} ms)` }
        : { ok: false, text: `Could not connect: ${res.error || 'no response'}` }
    );
    setTesting(false);
  };

  const save = (e) => {
    e.preventDefault();
    updateBackendUrl(url);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const fallbacks = healthInfo.gemini_fallback_models || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Settings</h1>
        <p className="mt-1 text-[15px] text-muted">Saved in this browser only.</p>
      </div>

      <div className="divide-y divide-line rounded-lg border border-line bg-surface">
        <Section title="Backend address" description="Where the API server is running.">
          <form onSubmit={save} className="space-y-2">
            <input
              type="url"
              required
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="http://localhost:8000"
              className="w-full rounded-md border border-line bg-surface px-3 py-2 font-mono text-sm focus:border-accent focus:outline-none"
            />
            <div className="flex flex-wrap items-center gap-2">
              <button
                type="submit"
                className="rounded-md bg-accent px-3.5 py-1.5 text-sm font-medium text-accent-ink hover:opacity-90 transition-opacity"
              >
                {saved ? 'Saved' : 'Save'}
              </button>
              <button
                type="button"
                onClick={runTest}
                disabled={testing}
                className="rounded-md border border-line px-3.5 py-1.5 text-sm hover:bg-inset transition-colors disabled:opacity-50"
              >
                {testing ? 'Testing…' : 'Test connection'}
              </button>
              {test && <span className={`text-sm ${test.ok ? 'text-ok' : 'text-err'}`}>{test.text}</span>}
            </div>
          </form>
        </Section>

        <Section
          title="Max attempts"
          description="How many times broken code is fixed and re-run before giving up."
        >
          <div className="flex items-center gap-4">
            <input
              type="range"
              min="1"
              max="10"
              value={maxIterations}
              onChange={(e) => setMaxIterations(Number(e.target.value))}
              className="w-full max-w-xs accent-accent"
              aria-label="Max attempts"
            />
            <span className="w-6 text-sm font-medium tabular-nums">{maxIterations}</span>
          </div>
        </Section>

        <Section title="Progress updates" description="How results come back from the server.">
          <div className="space-y-2">
            {[
              { id: 'stream', title: 'Show each step as it happens', note: 'Recommended' },
              { id: 'sync', title: 'Wait for the final result', note: 'One response at the end' },
            ].map((opt) => (
              <label
                key={opt.id}
                className={`flex cursor-pointer items-start gap-3 rounded-md border px-3 py-2.5 transition-colors ${
                  executionMode === opt.id ? 'border-accent/60 bg-accent/5' : 'border-line hover:bg-inset'
                }`}
              >
                <input
                  type="radio"
                  name="mode"
                  checked={executionMode === opt.id}
                  onChange={() => setExecutionMode(opt.id)}
                  className="mt-0.5 accent-accent"
                />
                <span>
                  <span className="block text-sm">{opt.title}</span>
                  <span className="block text-xs text-muted">{opt.note}</span>
                </span>
              </label>
            ))}
          </div>
        </Section>

        <Section title="Server details" description="Reported by the backend.">
          {backendStatus === 'online' ? (
            <dl>
              <Row label="Model">
                <span className="font-mono">{healthInfo.gemini_model || '—'}</span>
              </Row>
              {fallbacks.length > 0 && (
                <Row label="Fallback models">
                  <span className="font-mono">{fallbacks.join(', ')}</span>
                </Row>
              )}
              <Row label="API key">
                {healthInfo.gemini_configured ? 'Set' : <span className="text-err">Missing</span>}
              </Row>
              <Row label="Code runs in">
                {healthInfo.docker_available ? 'Docker container' : 'Local process'}
              </Row>
              {!healthInfo.docker_available && (
                <p className="mt-2 text-sm text-warn">
                  Docker isn't available, so generated code runs directly on the server machine without isolation.
                </p>
              )}
            </dl>
          ) : (
            <p className="text-sm text-muted">
              {backendStatus === 'checking' ? 'Checking…' : 'Not connected.'}
            </p>
          )}
        </Section>
      </div>
    </div>
  );
}
