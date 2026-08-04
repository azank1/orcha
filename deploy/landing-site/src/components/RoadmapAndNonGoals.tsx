import React from 'react';
import { ROADMAP_PHASES } from '../data/orchaData';

export const RoadmapAndNonGoals: React.FC = () => {
  return (
    <section id="roadmap" className="py-16 border-b border-black/10 bg-[var(--paper)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-[var(--muted-light)] font-semibold">
            Honest Roadmap
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--ink)]">
            Roadmap
          </h2>
          <p className="text-[var(--muted-light)] text-xs sm:text-sm max-w-2xl leading-relaxed">
            Shipped, next, and what is honestly not here yet.
          </p>
        </div>

        {/* Roadmap Phases */}
        <div className="space-y-4 mb-10">
          {ROADMAP_PHASES.map((phase, idx) => (
            <div
              key={idx}
              className="bg-white border border-black/10 rounded-xl p-5 sm:p-6 grid grid-cols-1 md:grid-cols-12 gap-4 items-start shadow-sm transition-colors"
            >
              <div className="md:col-span-3 space-y-1 font-mono">
                <span className="text-sm font-semibold text-[var(--ink)] block">
                  {phase.version}
                </span>
                <span className="text-xs text-[var(--muted-light)] uppercase tracking-wider block font-semibold">
                  {phase.status}
                </span>
              </div>

              <div className="md:col-span-6 space-y-1.5">
                <h3 className="font-display font-bold text-sm sm:text-base text-[var(--ink)]">
                  {phase.title}
                </h3>
                <p className="text-xs sm:text-sm text-[var(--muted-light)] leading-relaxed">
                  {phase.description}
                </p>
              </div>

              <div className="md:col-span-3 font-mono text-xs text-[var(--muted-light)] md:text-right">
                <span className="px-2.5 py-1 rounded bg-[var(--paper)] border border-black/10 inline-block">
                  {phase.gate}
                </span>
              </div>
            </div>
          ))}
        </div>


      </div>
    </section>
  );
};
