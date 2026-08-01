import React from 'react';
import { ROADMAP_PHASES } from '../data/orchaData';

export const RoadmapAndNonGoals: React.FC = () => {
  return (
    <section id="roadmap" className="py-16 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-xs text-[#6366f1] uppercase tracking-widest font-semibold">
            Honest Roadmap
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--text)]">
            Roadmap
          </h2>
          <p className="text-[var(--muted)] text-xs sm:text-sm max-w-2xl leading-relaxed">
            Shipped, next, and what is honestly not here yet.
          </p>
        </div>

        {/* Roadmap Phases */}
        <div className="space-y-4 mb-10">
          {ROADMAP_PHASES.map((phase, idx) => (
            <div
              key={idx}
              className="bg-[var(--card-bg)] border border-[var(--line)] rounded-xl p-5 sm:p-6 grid grid-cols-1 md:grid-cols-12 gap-4 items-start shadow-sm transition-colors"
            >
              <div className="md:col-span-3 space-y-1 font-mono">
                <span className="text-sm font-semibold text-[var(--text)] block">
                  {phase.version}
                </span>
                <span className="text-xs text-[var(--muted)] uppercase tracking-wider block font-semibold">
                  {phase.status}
                </span>
              </div>

              <div className="md:col-span-6 space-y-1.5">
                <h3 className="font-display font-bold text-sm sm:text-base text-[var(--text)]">
                  {phase.title}
                </h3>
                <p className="text-xs sm:text-sm text-[var(--muted)] leading-relaxed">
                  {phase.description}
                </p>
              </div>

              <div className="md:col-span-3 font-mono text-xs text-[var(--faint)] md:text-right">
                <span className="px-2.5 py-1 rounded bg-[var(--bg)] border border-[var(--line)] inline-block">
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
