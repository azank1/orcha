import React from 'react';
import { LayoutDashboard, MessageSquareX, TrendingUp } from 'lucide-react';

export const CanvasKitShowcase: React.FC = () => {
  return (
    <section id="canvaskit" className="py-24 sm:py-32 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 space-y-12">

        {/* Section Header */}
        <div className="space-y-4 max-w-3xl">
          <div className="text-sm text-[#6366f1] uppercase tracking-widest font-semibold">
            UI Dashboards &gt; Chat Bubbles
          </div>
          <h2 className="font-display font-bold text-3xl sm:text-4xl tracking-tight text-[var(--text)]">
            Dashboards, not chat bubbles.
          </h2>
          <p className="text-lg text-[var(--muted)] leading-relaxed">
            One goal produces structured visual dashboards. Agent output is declared via CanvasKit manifests, compiled deterministically, and rendered natively.
          </p>
        </div>

        {/* Side-by-Side Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">

          {/* LEFT: Plain Text Chat Bubble */}
          <div className="border border-[var(--line)] rounded-2xl overflow-hidden bg-[var(--card-bg)] flex flex-col justify-between shadow-sm transition-colors">
            <div className="px-5 py-3 border-b border-[var(--line)] bg-[var(--bg)] text-sm text-[var(--faint)] flex items-center justify-between">
              <span className="flex items-center gap-2">
                <MessageSquareX className="w-4 h-4 text-[var(--faint)]" /> Plain text prose
              </span>
              <span className="text-[var(--muted)] text-xs">unverifiable</span>
            </div>

            <div className="p-6 text-sm text-[var(--muted)] leading-relaxed space-y-3 my-auto">
              <div className="bg-[var(--bg)] border border-[var(--line)] p-4 rounded-xl text-[var(--muted)]">
                "Your portfolio is worth approximately $142,300 across 8 positions. NVDA is your largest holding at around 22%. Tech did well this week. Let me know if you'd like a chart summary."
              </div>
            </div>

            <div className="px-5 py-3 border-t border-[var(--line)] bg-[var(--bg)] text-xs text-[var(--faint)]">
              Unverifiable text prose · Unstructured output
            </div>
          </div>

          {/* RIGHT: Orcha CanvasKit Output */}
          <div className="border border-[#6366f1]/40 rounded-2xl overflow-hidden bg-[var(--card-bg)] flex flex-col justify-between shadow-sm transition-colors">
            <div className="px-5 py-3 border-b border-[var(--line)] bg-[var(--bg)] text-sm text-[var(--text)] flex items-center justify-between font-semibold">
              <span className="flex items-center gap-2">
                <LayoutDashboard className="w-4 h-4 text-[#6366f1]" /> Orcha CanvasKit output
              </span>
              <span className="text-[var(--muted)] text-xs">rendered &amp; persisted</span>
            </div>

            <div className="p-6 space-y-5">

              {/* Metric Card */}
              <div className="bg-[var(--bg)] border border-[var(--line)] p-4 rounded-xl flex items-center justify-between shadow-sm">
                <div>
                  <span className="text-xs text-[var(--faint)] uppercase block font-medium">Portfolio Value</span>
                  <span className="font-display font-bold text-2xl text-[var(--text)]">
                    $142,300 <span className="text-sm text-[#6366f1] ml-2 font-semibold">+4.8%</span>
                  </span>
                </div>
                <div className="w-10 h-10 rounded-lg bg-[#6366f1]/10 flex items-center justify-center text-[#6366f1]">
                  <TrendingUp className="w-5 h-5" />
                </div>
              </div>

              {/* Table Breakdown of Positions */}
              <div className="bg-[var(--bg)] border border-[var(--line)] rounded-xl overflow-hidden text-sm shadow-sm">
                <div className="px-4 py-2 border-b border-[var(--line)] text-xs text-[var(--faint)] flex justify-between uppercase font-semibold">
                  <span>Ticker</span>
                  <span>Weight</span>
                  <span>Value</span>
                </div>
                <div className="divide-y divide-[var(--line)]">
                  <div className="px-4 py-2.5 flex justify-between text-[var(--text)]">
                    <span className="font-semibold text-[#6366f1]">NVDA</span>
                    <span>22.4%</span>
                    <span>$31,875</span>
                  </div>
                  <div className="px-4 py-2.5 flex justify-between text-[var(--text)]">
                    <span className="font-semibold text-[var(--text)]">AAPL</span>
                    <span>18.5%</span>
                    <span>$26,325</span>
                  </div>
                  <div className="px-4 py-2.5 flex justify-between text-[var(--text)]">
                    <span className="font-semibold text-[var(--text)]">MSFT</span>
                    <span>15.2%</span>
                    <span>$21,629</span>
                  </div>
                </div>
              </div>

            </div>

            <div className="px-5 py-3 border-t border-[var(--line)] bg-[var(--bg)] text-xs text-[var(--muted)]">
              Declarative CanvasKit manifest · Persisted in runtime
            </div>
          </div>

        </div>

      </div>
    </section>
  );
};
