import React from 'react';
import { LayoutDashboard, MessageSquareX, TrendingUp } from 'lucide-react';

export const CanvasKitShowcase: React.FC = () => {
  return (
    <section id="canvaskit" className="py-16 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-xs text-[#6366f1] uppercase tracking-widest font-semibold">
            UI Dashboards &gt; Chat Bubbles
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--text)]">
            Dashboards, not chat bubbles.
          </h2>
          <p className="text-[var(--muted)] text-xs sm:text-sm max-w-2xl leading-relaxed">
            One goal produces structured visual dashboards. Agent output is declared via CanvasKit manifests, compiled deterministically, and rendered natively.
          </p>
        </div>

        {/* Side-by-Side Comparison */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* LEFT: Plain Text Chat Bubble */}
          <div className="border border-[var(--line)] rounded-xl overflow-hidden bg-[var(--card-bg)] flex flex-col justify-between shadow-sm transition-colors">
            <div className="px-4 py-2.5 border-b border-[var(--line)] bg-[var(--bg)] font-mono text-xs text-[var(--faint)] flex items-center justify-between">
              <span className="flex items-center gap-2">
                <MessageSquareX className="w-3.5 h-3.5 text-[var(--faint)]" /> Plain text prose
              </span>
              <span className="text-[var(--muted)] text-[11px]">unverifiable</span>
            </div>
            
            <div className="p-5 text-xs sm:text-sm text-[var(--muted)] font-mono leading-relaxed space-y-2 my-auto">
              <div className="bg-[var(--bg)] border border-[var(--line)] p-3.5 rounded-lg text-[var(--muted)]">
                "Your portfolio is worth approximately $142,300 across 8 positions. NVDA is your largest holding at around 22%. Tech did well this week. Let me know if you'd like a chart summary."
              </div>
            </div>

            <div className="px-4 py-2 border-t border-[var(--line)] bg-[var(--bg)] font-mono text-[11px] text-[var(--faint)]">
              Unverifiable text prose · Unstructured output
            </div>
          </div>

          {/* RIGHT: Orcha CanvasKit Output */}
          <div className="border border-[#6366f1]/40 rounded-xl overflow-hidden bg-[var(--card-bg)] flex flex-col justify-between shadow-sm transition-colors">
            <div className="px-4 py-2.5 border-b border-[var(--line)] bg-[var(--bg)] font-mono text-xs text-[var(--text)] flex items-center justify-between font-semibold">
              <span className="flex items-center gap-2">
                <LayoutDashboard className="w-3.5 h-3.5 text-[#6366f1]" /> Orcha CanvasKit output
              </span>
              <span className="text-[var(--muted)] text-[11px]">rendered &amp; persisted</span>
            </div>

            <div className="p-5 space-y-4">
              
              {/* Metric Card */}
              <div className="bg-[var(--bg)] border border-[var(--line)] p-3.5 rounded-lg flex items-center justify-between shadow-sm">
                <div>
                  <span className="font-mono text-[10px] text-[var(--faint)] uppercase block font-medium">Portfolio Value</span>
                  <span className="font-display font-bold text-xl text-[var(--text)]">
                    $142,300 <span className="font-mono text-xs text-[#6366f1] ml-1.5 font-semibold">+4.8%</span>
                  </span>
                </div>
                <div className="w-8 h-8 rounded bg-[#6366f1]/10 flex items-center justify-center text-[#6366f1]">
                  <TrendingUp className="w-4 h-4" />
                </div>
              </div>

              {/* Table Breakdown of Positions */}
              <div className="bg-[var(--bg)] border border-[var(--line)] rounded-lg overflow-hidden font-mono text-xs shadow-sm">
                <div className="px-3 py-1.5 border-b border-[var(--line)] text-[10px] text-[var(--faint)] flex justify-between uppercase font-semibold">
                  <span>Ticker</span>
                  <span>Weight</span>
                  <span>Value</span>
                </div>
                <div className="divide-y divide-[var(--line)]">
                  <div className="px-3 py-1.5 flex justify-between text-[var(--text)]">
                    <span className="font-semibold text-[#6366f1]">NVDA</span>
                    <span>22.4%</span>
                    <span>$31,875</span>
                  </div>
                  <div className="px-3 py-1.5 flex justify-between text-[var(--text)]">
                    <span className="font-semibold text-[var(--text)]">AAPL</span>
                    <span>18.5%</span>
                    <span>$26,325</span>
                  </div>
                  <div className="px-3 py-1.5 flex justify-between text-[var(--text)]">
                    <span className="font-semibold text-[var(--text)]">MSFT</span>
                    <span>15.2%</span>
                    <span>$21,629</span>
                  </div>
                </div>
              </div>

            </div>

            <div className="px-4 py-2 border-t border-[var(--line)] bg-[var(--bg)] font-mono text-[11px] text-[var(--muted)]">
              Declarative CanvasKit manifest · Persisted in runtime
            </div>
          </div>

        </div>

      </div>
    </section>
  );
};
