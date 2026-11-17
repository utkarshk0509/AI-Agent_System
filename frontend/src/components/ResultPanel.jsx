import React, { useEffect, useRef, useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

const NODE_LABELS = {
  planner: 'Plan',
  coder: 'Code',
  executor: 'Run',
  reviewer: 'Fix',
  answer: 'Answer',
  orchestrator: 'Run',
  system: '',
};

function Empty({ children }) {
  return <p className="py-12 text-center text-sm text-faint">{children}</p>;
}

function Pre({ children, tone = 'default' }) {
  const tones = {
    default: 'bg-inset text-ink',
    err: 'bg-err/5 text-err border border-err/20',
  };
  return (
    <pre
      className={`overflow-x-auto rounded-md p-3 font-mono text-[13px] leading-relaxed whitespace-pre-wrap break-words ${tones[tone]}`}
    >
      {children}
    </pre>
  );
}

function SectionLabel({ children }) {
  return <h3 className="mb-1.5 text-xs font-medium uppercase tracking-wide text-faint">{children}</h3>;
}

export default function ResultPanel() {
  const { status, answer, error, generatedCode, stdout, stderr, exitCode, plan, reviewFeedback, logs } = useAgent();
  const [tab, setTab] = useState('answer');
  const [copied, setCopied] = useState(false);
  const bodyRef = useRef(null);

  useEffect(() => {
    if (status === 'running') setTab('log');
    if (status === 'completed' || status === 'error') setTab('answer');
  }, [status]);

  useEffect(() => {
    if (tab === 'log' && bodyRef.current) bodyRef.current.scrollTop = bodyRef.current.scrollHeight;
  }, [logs, tab]);

  const tabs = [
    { id: 'answer', label: 'Answer', copy: answer },
    { id: 'code', label: 'Code', copy: generatedCode },
    { id: 'output', label: 'Output', copy: [stdout, stderr].filter(Boolean).join('\n\n') },
    { id: 'plan', label: 'Plan', copy: [plan, reviewFeedback].filter(Boolean).join('\n\n') },
    {
      id: 'log',
      label: `Log${logs.length ? ` (${logs.length})` : ''}`,
      copy: logs.map((l) => `[${l.timestamp}] ${l.node}: ${l.message}`).join('\n'),
    },
  ];
  const copyText = tabs.find((t) => t.id === tab)?.copy;

  const copy = async () => {
    if (!copyText) return;
    try {
      await navigator.clipboard.writeText(copyText);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      /* clipboard unavailable */
    }
  };

  return (
    <div className="rounded-lg border border-line bg-surface">
      <div className="flex items-center border-b border-line px-2">
        <div role="tablist" className="flex overflow-x-auto">
          {tabs.map((t) => (
            <button
              key={t.id}
              role="tab"
              aria-selected={tab === t.id}
              onClick={() => setTab(t.id)}
              className={`-mb-px whitespace-nowrap border-b-2 px-3 py-2.5 text-sm transition-colors ${
                tab === t.id ? 'border-accent text-ink font-medium' : 'border-transparent text-muted hover:text-ink'
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>
        <button
          type="button"
          onClick={copy}
          disabled={!copyText}
          title="Copy"
          className="ml-auto flex shrink-0 items-center gap-1.5 rounded-md px-2.5 py-1.5 text-sm text-muted hover:bg-inset hover:text-ink transition-colors disabled:opacity-30 disabled:pointer-events-none"
        >
          {copied ? <Check className="h-4 w-4 text-ok" /> : <Copy className="h-4 w-4" />}
          <span className="hidden sm:inline">{copied ? 'Copied' : 'Copy'}</span>
        </button>
      </div>

      <div ref={bodyRef} className="max-h-[32rem] overflow-y-auto p-4">
        {tab === 'answer' &&
          (answer ? (
            <div className="whitespace-pre-wrap text-[15px] leading-relaxed">{answer}</div>
          ) : error ? (
            <div className="rounded-md border border-err/20 bg-err/5 p-3 text-sm text-err">
              <p className="font-medium">No answer was produced.</p>
              <p className="mt-1">{error}</p>
              {stderr && <p className="mt-2 opacity-80">The last error is in the Output tab.</p>}
            </div>
          ) : (
            <Empty>{status === 'running' ? 'The answer will show up here when it is ready.' : 'No answer yet.'}</Empty>
          ))}

        {tab === 'code' &&
          (generatedCode ? (
            <div className="overflow-x-auto rounded-md bg-inset py-3 font-mono text-[13px] leading-relaxed">
              <table className="border-collapse">
                <tbody>
                  {generatedCode.split('\n').map((line, i) => (
                    <tr key={i}>
                      <td className="select-none pl-3 pr-4 text-right align-top text-faint">{i + 1}</td>
                      <td className="whitespace-pre pr-4">{line || ' '}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <Empty>No code yet.</Empty>
          ))}

        {tab === 'output' &&
          (stdout || stderr || exitCode !== null ? (
            <div className="space-y-4">
              {exitCode !== null && (
                <p className="text-sm text-muted">
                  Exit code{' '}
                  <span className={`font-mono ${exitCode === 0 ? 'text-ok' : 'text-err'}`}>{exitCode}</span>
                </p>
              )}
              <div>
                <SectionLabel>Printed output</SectionLabel>
                <Pre>{stdout || <span className="text-faint">Nothing was printed.</span>}</Pre>
              </div>
              {stderr && (
                <div>
                  <SectionLabel>Errors</SectionLabel>
                  <Pre tone="err">{stderr}</Pre>
                </div>
              )}
            </div>
          ) : (
            <Empty>The code has not run yet.</Empty>
          ))}

        {tab === 'plan' &&
          (plan || reviewFeedback ? (
            <div className="space-y-4">
              {plan && (
                <div>
                  <SectionLabel>Plan</SectionLabel>
                  <div className="whitespace-pre-wrap text-sm leading-relaxed">{plan}</div>
                </div>
              )}
              {reviewFeedback && (
                <div>
                  <SectionLabel>What was fixed</SectionLabel>
                  <div className="whitespace-pre-wrap rounded-md bg-inset p-3 text-sm leading-relaxed">
                    {reviewFeedback}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <Empty>No plan yet.</Empty>
          ))}

        {tab === 'log' &&
          (logs.length ? (
            <ul className="space-y-1 font-mono text-[13px] leading-relaxed">
              {logs.map((log) => (
                <li key={log.id} className="flex gap-3">
                  <span className="shrink-0 text-faint tabular-nums">{log.timestamp}</span>
                  <span className="w-14 shrink-0 text-muted">{NODE_LABELS[log.node] ?? log.node}</span>
                  <span
                    className={`min-w-0 break-words ${
                      log.level === 'error'
                        ? 'text-err'
                        : log.level === 'success'
                        ? 'text-ok'
                        : log.level === 'warn'
                        ? 'text-warn'
                        : 'text-ink'
                    }`}
                  >
                    {log.message}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <Empty>Nothing logged yet.</Empty>
          ))}
      </div>
    </div>
  );
}
