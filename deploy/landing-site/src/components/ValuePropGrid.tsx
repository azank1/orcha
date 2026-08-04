import React from 'react';

const PILLARS = [
  {
    title: 'Compose',
    body: 'One goal decomposed and routed across MCP, A2A, and computer-use agents in a single run. No glue code.'
  },
  {
    title: 'Verify',
    body: 'Every step carries a verdict. Download the run audit: per-step agent, protocol, cost, timing.'
  },
  {
    title: 'Render',
    body: 'Agents return declarative CanvasKit manifests, not chat bubbles. Metric cards, charts, tables, live.'
  }
];

export const ValuePropGrid: React.FC = () => {
  return (
    <section id="value-props" className="py-24 sm:py-32 border-b border-black/10 bg-[var(--paper)] transition-colors">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">

        {/* 3-Pillar Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PILLARS.map((pillar) => (
            <div
              key={pillar.title}
              className="bg-white border border-black/10 rounded-2xl p-8 shadow-sm transition-colors hover:border-black/40"
            >
              <h3 className="font-display font-bold text-xl text-[var(--ink)] mb-3">
                {pillar.title}
              </h3>
              <p className="text-base text-[var(--muted-light)] leading-relaxed">
                {pillar.body}
              </p>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
};
