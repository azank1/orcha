import React, { useEffect, useState } from 'react';
import { REAL_RUN_REPLAY, ReplayLine, CAPTURED_AT } from '../data/realRunReplay';

const lineColor = (cls?: ReplayLine['cls']): string => {
  if (cls === 'ok') return 'text-[var(--ok)]';
  if (cls === 'cm') return 'text-[var(--faint)]';
  return 'text-[var(--muted-dark)]';
};

/** Types out the real captured run, line by line. Extracted from the old hero. */
export const RunReplayTerminal: React.FC = () => {
  const [displayedLines, setDisplayedLines] = useState<ReplayLine[]>([]);
  const [lineIdx, setLineIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);

  useEffect(() => {
    if (lineIdx >= REAL_RUN_REPLAY.length) return;
    const current = REAL_RUN_REPLAY[lineIdx];
    if (charIdx < current.t.length) {
      const t = setTimeout(() => setCharIdx((p) => p + 1), 12 + Math.random() * 14);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => {
      setDisplayedLines((p) => [...p, current]);
      setLineIdx((p) => p + 1);
      setCharIdx(0);
    }, current.d || 300);
    return () => clearTimeout(t);
  }, [lineIdx, charIdx]);

  const typing = lineIdx < REAL_RUN_REPLAY.length;

  return (
    <div className="border border-[var(--line-dark)] bg-[#050505]">
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line-dark)] text-[11px]">
        <span className="flex items-center gap-2 text-[var(--muted-dark)]">
          <span className="w-1.5 h-1.5 bg-white inline-block status-dot" />
          ~/orcha · runtime replay
        </span>
        <span className="text-[var(--faint)]">v1.0-active</span>
      </div>
      <div className="p-4 sm:p-5 min-h-[240px] space-y-1.5 text-xs leading-relaxed">
        {displayedLines.map((line, i) => (
          <div key={i} className={lineColor(line.cls)}>{line.t}</div>
        ))}
        {typing && (
          <div className={lineColor(REAL_RUN_REPLAY[lineIdx].cls)}>
            {REAL_RUN_REPLAY[lineIdx].t.slice(0, charIdx)}
            <span className="caret ml-0.5" />
          </div>
        )}
      </div>
      <div className="px-4 py-2 border-t border-[var(--line-dark)] text-[10px] text-[var(--faint)] flex justify-between">
        <span>handlers: MCP · A2A · COMPUTER_USE</span>
        <span>captured from a live run · {CAPTURED_AT}</span>
      </div>
    </div>
  );
};
