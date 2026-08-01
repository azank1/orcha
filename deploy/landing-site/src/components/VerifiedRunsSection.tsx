import React, { useState } from 'react';
import { VERIFIED_RUNS_DATA, VerifiedRunAudit } from '../data/orchaData';
import { Download, FileJson, Check, ShieldCheck, Clock } from 'lucide-react';

export const VerifiedRunsSection: React.FC = () => {
  const [selectedAudit, setSelectedAudit] = useState<VerifiedRunAudit>(VERIFIED_RUNS_DATA[0]);
  const [copiedJson, setCopiedJson] = useState(false);

  const handleDownloadAudit = (audit: VerifiedRunAudit) => {
    const jsonStr = JSON.stringify(audit, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `orcha-audit-${audit.runId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleCopyAuditJson = () => {
    navigator.clipboard.writeText(JSON.stringify(selectedAudit, null, 2));
    setCopiedJson(true);
    setTimeout(() => setCopiedJson(false), 2000);
  };

  return (
    <section id="verified-runs" className="py-16 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-xs text-[#6366f1] uppercase tracking-widest font-semibold">
            Audit &amp; Evidence
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--text)]">
            Verified Runs
          </h2>
          <p className="text-[var(--muted)] text-xs sm:text-sm max-w-2xl leading-relaxed">
            Every run generates a downloadable evidence package: goal, per-step agent, protocol, verdict, timing, and cost.
          </p>
        </div>

        {/* Audit Run Selector & Preview Split */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Left: Run List */}
          <div className="lg:col-span-5 space-y-3">
            <div className="font-mono text-xs text-[var(--muted)] uppercase tracking-wider mb-2 font-semibold">
              Recent Verified Runs (5/5 Pass Rate)
            </div>

            {VERIFIED_RUNS_DATA.map((audit) => {
              const isSelected = selectedAudit.runId === audit.runId;

              return (
                <div
                  key={audit.runId}
                  onClick={() => setSelectedAudit(audit)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer shadow-sm ${
                    isSelected
                      ? 'border-[#6366f1] bg-[var(--card-bg)] shadow-md'
                      : 'border-[var(--line)] bg-[var(--bg)] hover:border-[var(--faint)]'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono text-xs mb-2">
                    <span className="text-[var(--text)] font-semibold">{audit.runId}</span>
                    <span className="text-[var(--muted)]">{audit.duration}</span>
                  </div>

                  <p className="text-xs text-[var(--muted)] font-mono leading-relaxed mb-3 line-clamp-2">
                    "{audit.goal}"
                  </p>

                  <div className="flex items-center justify-between font-mono text-[11px] pt-2 border-t border-[var(--line)]">
                    <span className="text-[var(--muted)]">{audit.steps.length} steps · {audit.runsVerified}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownloadAudit(audit);
                      }}
                      className="text-[#6366f1] hover:underline flex items-center gap-1 font-semibold"
                    >
                      <Download className="w-3 h-3" /> Download audit
                    </button>
                  </div>
                </div>
              );
            })}

            <div className="p-4 rounded-xl border border-[var(--line)] bg-[var(--card-bg)] text-xs text-[var(--muted)] font-mono space-y-2 shadow-sm">
              <div className="flex items-center gap-2 text-[var(--text)] font-semibold">
                <ShieldCheck className="w-4 h-4 text-[#6366f1]" /> Audit Package Structure
              </div>
              <p className="leading-relaxed">
                Available from the chat interface as "Download audit". Contains the goal, per-step agent, protocol, verdict, timing, and cost.
              </p>
            </div>
          </div>

          {/* Right: JSON Evidence Package Viewer */}
          <div className="lg:col-span-7 border border-[var(--line)] rounded-xl overflow-hidden bg-[#080C14] flex flex-col font-mono text-xs shadow-sm">
            <div className="px-4 py-2.5 border-b border-slate-800 bg-[#0c0f17] flex items-center justify-between">
              <span className="flex items-center gap-2 text-white font-semibold">
                <FileJson className="w-4 h-4 text-[#6366f1]" /> {selectedAudit.runId}.json
              </span>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleCopyAuditJson}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] flex items-center gap-1 transition-colors"
                >
                  {copiedJson ? <Check className="w-3 h-3 text-[#6366f1]" /> : null}
                  {copiedJson ? 'Copied' : 'Copy JSON'}
                </button>
                <button
                  onClick={() => handleDownloadAudit(selectedAudit)}
                  className="px-2.5 py-1 rounded bg-[#6366f1] text-white hover:bg-[#4f52c8] text-[11px] flex items-center gap-1 font-semibold transition-colors"
                >
                  <Download className="w-3 h-3" /> Download audit
                </button>
              </div>
            </div>

            <pre className="p-5 text-slate-200 bg-[#080C14] overflow-x-auto leading-relaxed flex-1 max-h-[380px]">
              <code>{JSON.stringify(selectedAudit, null, 2)}</code>
            </pre>

            <div className="px-4 py-2 border-t border-slate-800 bg-[#0c0f17] text-[11px] text-slate-400 flex items-center justify-between">
              <span>ExecutionObserver seam enabled</span>
              <span>PAYMENT_MODE={selectedAudit.paymentMode}</span>
            </div>
          </div>

        </div>

      </div>
    </section>
  );
};
