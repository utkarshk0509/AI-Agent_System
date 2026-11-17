import React from 'react';
import { Check, Loader2 } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

const STEPS = [
  { id: 'planner', label: 'Plan' },
  { id: 'coder', label: 'Write code' },
  { id: 'executor', label: 'Run' },
  { id: 'reviewer', label: 'Fix errors' },
  { id: 'answer', label: 'Answer' },
];

// Stream events arrive after a step finishes, so the step in progress is the one after it.
function nextStep(last, exitCode, stdout) {
  switch (last) {
    case undefined:
      return 'planner';
    case 'planner':
    case 'reviewer':
      return 'coder';
    case 'coder':
      return 'executor';
    case 'executor':
      return exitCode === 0 && stdout?.trim() ? 'answer' : 'reviewer';
    default:
      return null;
  }
}

function formatTime(s) {
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

const SUMMARY = {
  running: 'Working…',
  error: 'Did not finish',
  aborted: 'Stopped',
};

export default function RunProgress() {
  const {
    status,
    activeNode,
    visitedNodes,
    iterationCount,
    maxIterations,
    elapsedTime,
    exitCode,
    stdout,
    reviewFeedback,
  } = useAgent();

  const running = status === 'running';

  // Single-response mode sends no step events, so infer them from the final result.
  let visited = visitedNodes;
  if (!running && visited.length === 0 && status === 'completed') {
    visited = ['planner', 'coder', 'executor', ...(reviewFeedback ? ['reviewer'] : []), 'answer'];
  }
  const current = running ? nextStep(visited.length ? activeNode : undefined, exitCode, stdout) : null;
  const usedFix = visited.includes('reviewer') || current === 'reviewer';
  const steps = STEPS.filter((s) => s.id !== 'reviewer' || usedFix);

  const summary = status === 'completed' ? `Done in ${formatTime(elapsedTime)}` : SUMMARY[status];
  const attempt = Math.max(iterationCount, 1);

  return (
    <div className="rounded-lg border border-line bg-surface px-4 py-3">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
        <span
          className={`font-medium ${
            status === 'error' ? 'text-err' : status === 'completed' ? 'text-ok' : 'text-ink'
          }`}
        >
          {summary}
        </span>
        <span className="text-faint tabular-nums">
          Attempt {attempt} of {maxIterations}
          {running && ` · ${formatTime(elapsedTime)}`}
        </span>
      </div>

      <ol className="mt-3 flex flex-wrap items-center gap-y-2">
        {steps.map((step, i) => {
          const isCurrent = step.id === current;
          const isDone = !isCurrent && visited.includes(step.id);
          return (
            <li key={step.id} className="flex items-center">
              {i > 0 && <span className="mx-1 h-px w-3 sm:w-5 bg-line" aria-hidden="true" />}
              <span
                aria-current={isCurrent ? 'step' : undefined}
                className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[13px] ${
                  isCurrent ? 'bg-accent/10 text-accent font-medium' : isDone ? 'text-ink' : 'text-faint'
                }`}
              >
                {isCurrent ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : isDone ? (
                  <Check className="h-3.5 w-3.5 text-ok" strokeWidth={2.5} />
                ) : (
                  <span className="h-3 w-3 rounded-full border border-current opacity-60" />
                )}
                {step.label}
              </span>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
