import React, { useState } from 'react';
import { Play, Square } from 'lucide-react';
import { useAgent } from '../context/AgentContext';

const EXAMPLES = [
  'Find all prime numbers under 100 and give their sum and average.',
  'Generate 50 samples from a normal distribution (mean 25, sd 5) and report the median and variance.',
  'List the first 30 Fibonacci numbers and show how the ratio approaches the golden ratio.',
];

export default function PromptBox() {
  const { runAgent, abortRun, clearWorkspace, status, maxIterations, setMaxIterations } = useAgent();
  const [text, setText] = useState('');
  const isRunning = status === 'running';

  const submit = () => {
    if (!text.trim() || isRunning) return;
    runAgent(text);
  };

  const onKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-line bg-surface focus-within:border-accent/60 transition-colors">
        <label htmlFor="prompt" className="sr-only">
          Your question
        </label>
        <textarea
          id="prompt"
          rows={4}
          value={text}
          disabled={isRunning}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="e.g. What is the standard deviation of 4, 8, 15, 16, 23, 42?"
          className="block w-full resize-y bg-transparent px-4 py-3 text-[15px] leading-relaxed placeholder:text-faint focus:outline-none disabled:opacity-60"
        />

        <div className="flex flex-wrap items-center gap-3 border-t border-line px-3 py-2.5">
          <label className="flex items-center gap-2 text-sm text-muted">
            Max attempts
            <select
              value={maxIterations}
              disabled={isRunning}
              onChange={(e) => setMaxIterations(Number(e.target.value))}
              className="rounded-md border border-line bg-surface px-2 py-1 text-sm text-ink focus:outline-none focus:border-accent"
            >
              {[1, 2, 3, 5, 8, 10].map((n) => (
                <option key={n} value={n}>
                  {n}
                </option>
              ))}
            </select>
          </label>

          <div className="ml-auto flex items-center gap-2">
            <span className="hidden sm:inline text-xs text-faint">Ctrl + Enter to run</span>
            {(text || status !== 'idle') && !isRunning && (
              <button
                type="button"
                onClick={() => {
                  setText('');
                  clearWorkspace();
                }}
                className="rounded-md px-3 py-1.5 text-sm text-muted hover:bg-inset hover:text-ink transition-colors"
              >
                Clear
              </button>
            )}
            {isRunning ? (
              <button
                type="button"
                onClick={abortRun}
                className="flex items-center gap-1.5 rounded-md border border-line bg-surface px-3.5 py-1.5 text-sm font-medium hover:bg-inset transition-colors"
              >
                <Square className="h-3.5 w-3.5 fill-current" />
                Stop
              </button>
            ) : (
              <button
                type="button"
                onClick={submit}
                disabled={!text.trim()}
                className="flex items-center gap-1.5 rounded-md bg-accent px-3.5 py-1.5 text-sm font-medium text-accent-ink hover:opacity-90 transition-opacity disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                Run
              </button>
            )}
          </div>
        </div>
      </div>

      {status === 'idle' && (
        <div>
          <p className="mb-1.5 px-3 text-sm text-faint">Or try one of these:</p>
          <ul>
            {EXAMPLES.map((ex) => (
              <li key={ex}>
                <button
                  type="button"
                  onClick={() => setText(ex)}
                  className="w-full rounded-md px-3 py-2 text-left text-sm text-muted hover:bg-surface hover:text-ink transition-colors"
                >
                  {ex}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
