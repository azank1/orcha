import React, { useEffect, useState } from 'react';
import { ArrowRight } from 'lucide-react';

const steps = [
  { num: '01', label: 'User Goal', desc: 'Natural language goal in' },
  { num: '02', label: '3-Tier Gate', desc: 'Auth, DID & scope verification' },
  { num: '03', label: 'SuperAgent', desc: 'LLM + pgvector DAG planner' },
  { num: '04', label: 'Protocol Dispatch', desc: 'MCP · A2A · Computer-use' },
  { num: '05', label: 'CanvasKit Output', desc: 'Live visual dashboard' },
];

const CYCLE_MS = 1600;

export const PipelineStrip: React.FC = () => {
  const [autoStep, setAutoStep] = useState(0);
  const [hoverStep, setHoverStep] = useState<number | null>(null);
  const [paused, setPaused] = useState(false);

  const reduced =
    typeof window !== 'undefined' &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => {
    if (reduced || paused) return;
    const id = setInterval(() => setAutoStep((s) => (s + 1) % steps.length), CYCLE_MS);
    return () => clearInterval(id);
  }, [reduced, paused]);

  const active = hoverStep ?? autoStep;

  return (
    <section className="bg-[var(--bg)] text-[var(--fg)] border-b border-[var(--line-dark)]">
      <div className="max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 py-14">
        <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted-dark)] mb-8">
          Execution flow
        </p>
        <div
          className="relative"
          onMouseEnter={() => setPaused(true)}
          onMouseLeave={() => {
            setPaused(false);
            setHoverStep(null);
          }}
        >
          {/* Traveling scan line across the top of the strip */}
          {!reduced && (
            <div className="absolute -top-px left-0 right-0 h-px overflow-hidden" aria-hidden="true">
              <div
                className="h-full w-1/5 bg-white/70"
                style={{
                  animation: `pipeline-scan ${CYCLE_MS * steps.length}ms linear infinite`,
                }}
              />
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-5 border border-[var(--line-dark)] divide-y md:divide-y-0 md:divide-x divide-[var(--line-dark)]">
            {steps.map((step, i) => {
              const isActive = active === i;
              return (
                <div
                  key={step.num}
                  onMouseEnter={() => setHoverStep(i)}
                  onMouseLeave={() => setHoverStep(null)}
                  className={`p-5 transition-all duration-500 ${isActive ? 'bg-white text-black' : ''}`}
                >
                  <div className="flex items-center justify-between mb-4">
                    <span
                      className={`text-[10px] transition-colors duration-500 ${
                        isActive ? 'text-black/60' : 'text-[var(--faint)]'
                      }`}
                    >
                      {step.num}
                    </span>
                    {i < steps.length - 1 && (
                      <ArrowRight
                        className={`w-3.5 h-3.5 hidden md:block transition-all duration-500 ${
                          isActive ? 'text-black translate-x-0.5' : 'text-[var(--faint)]'
                        }`}
                      />
                    )}
                  </div>
                  <div className="text-xs font-semibold mb-1">{step.label}</div>
                  <p
                    className={`text-[11px] leading-relaxed transition-colors duration-500 ${
                      isActive ? 'text-black/70' : 'text-[var(--muted-dark)]'
                    }`}
                  >
                    {step.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <style>{`@keyframes pipeline-scan { from { transform: translateX(-100%); } to { transform: translateX(500%); } }`}</style>
    </section>
  );
};
