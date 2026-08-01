import React from 'react';
import { GitPullRequest, MessageSquare, BookOpen, Terminal, Layers, ShieldCheck, Cpu } from 'lucide-react';

export const ContributionSection: React.FC = () => {
  return (
    <section id="contribute" className="py-16 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-xs text-[#6366f1] uppercase tracking-widest font-semibold">
            Open Source Ecosystem
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--text)]">
            Grow at the edges, freeze the core
          </h2>
          <p className="text-[var(--muted)] text-xs sm:text-sm max-w-3xl leading-relaxed">
            Handlers are pluggable: anyone can add a protocol bridge — LangGraph, OpenAPI, gRPC, ACP, or custom RPCs — without prior discussion.
          </p>
        </div>

        {/* 4 Contribution Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <div className="bg-[var(--card-bg)] border border-[var(--line)] p-5 rounded-xl space-y-3 flex flex-col justify-between shadow-sm transition-colors hover:border-[#6366f1]/50">
            <div className="space-y-2">
              <span className="font-mono text-[10.5px] uppercase tracking-wider text-[#6366f1] block font-semibold flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> Highest Leverage
              </span>
              <h3 className="font-display font-bold text-base text-[var(--text)]">
                Write a Protocol Bridge
              </h3>
              <p className="text-xs text-[var(--muted)] leading-relaxed">
                Pluggable protocol handlers unlock entire agent ecosystems. Create a subclass of <code className="text-[#6366f1]">AgentHandler</code> to orchestrate LangGraph, n8n, OpenAPI, gRPC, or custom RPCs.
              </p>
            </div>
            <code className="font-mono text-[11px] text-[var(--text)] bg-[var(--bg)] px-3 py-2 rounded border border-[var(--line)] block truncate">
              templates/your-first-bridge/
            </code>
          </div>

          <div className="bg-[var(--card-bg)] border border-[var(--line)] p-5 rounded-xl space-y-3 flex flex-col justify-between shadow-sm transition-colors hover:border-[#6366f1]/50">
            <div className="space-y-2">
              <span className="font-mono text-[10.5px] uppercase tracking-wider text-[#6366f1] block font-semibold flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" /> Grow the Fleet
              </span>
              <h3 className="font-display font-bold text-base text-[var(--text)]">
                Ship an Example Agent
              </h3>
              <p className="text-xs text-[var(--muted)] leading-relaxed">
                Add specialized agents with <code className="text-[#6366f1]">emerge.yaml</code> manifests specifying capability scopes and DIDs (<code className="text-[#6366f1]">did:orcha:agent:*</code>).
              </p>
            </div>
            <code className="font-mono text-[11px] text-[var(--text)] bg-[var(--bg)] px-3 py-2 rounded border border-[var(--line)] block truncate">
              templates/your-first-agent/
            </code>
          </div>

          <div className="bg-[var(--card-bg)] border border-[var(--line)] p-5 rounded-xl space-y-3 flex flex-col justify-between shadow-sm transition-colors hover:border-[#6366f1]/50">
            <div className="space-y-2">
              <span className="font-mono text-[10.5px] uppercase tracking-wider text-[#6366f1] block font-semibold flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" /> Native Output
              </span>
              <h3 className="font-display font-bold text-base text-[var(--text)]">
                Build CanvasKit UI
              </h3>
              <p className="text-xs text-[var(--muted)] leading-relaxed">
                Build declarative UI dashboard primitives for agent outputs so runs render structured visual widgets instead of chat bubbles.
              </p>
            </div>
            <code className="font-mono text-[11px] text-[var(--text)] bg-[var(--bg)] px-3 py-2 rounded border border-[var(--line)] block truncate">
              frontend/src/components/canvas/
            </code>
          </div>

          <div className="bg-[var(--card-bg)] border border-[var(--line)] p-5 rounded-xl space-y-3 flex flex-col justify-between shadow-sm transition-colors hover:border-[#6366f1]/50">
            <div className="space-y-2">
              <span className="font-mono text-[10.5px] uppercase tracking-wider text-[#6366f1] block font-semibold flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" /> Audit Engine
              </span>
              <h3 className="font-display font-bold text-base text-[var(--text)]">
                Execution Observer
              </h3>
              <p className="text-xs text-[var(--muted)] leading-relaxed">
                Extend the <code className="text-[#6366f1]">ExecutionObserver</code> seam and validator reference code to improve protocol attestation and run evidence.
              </p>
            </div>
            <code className="font-mono text-[11px] text-[var(--text)] bg-[var(--bg)] px-3 py-2 rounded border border-[var(--line)] block truncate">
              services/validator/
            </code>
          </div>

        </div>

        {/* How Bridges Work Callout Box */}
        <div className="bg-[var(--card-bg)] border border-[var(--line)] rounded-xl p-6 space-y-4 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-[var(--line)] pb-3">
            <div>
              <h3 className="font-display font-bold text-base text-[var(--text)]">
                Writing a Bridge Component (3-Step Quick Contract)
              </h3>
              <p className="text-xs text-[var(--muted)]">
                Any protocol can become an Orcha handler in under 50 lines of Python.
              </p>
            </div>
            <span className="font-mono text-[11px] text-[var(--muted)] w-fit">
              No prior discussion needed
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-3.5 rounded-lg bg-[var(--bg)] border border-[var(--line)] space-y-1.5">
              <div className="text-[#6366f1] font-semibold">1. Subclass AgentHandler</div>
              <p className="text-[var(--muted)] text-[11px] leading-relaxed font-sans">
                Create <code className="text-[var(--text)] font-mono">handlers/langgraph_handler.py</code> extending <code className="text-[var(--text)] font-mono">AgentHandler</code>.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-[var(--bg)] border border-[var(--line)] space-y-1.5">
              <div className="text-[#6366f1] font-semibold">2. Implement send_task()</div>
              <p className="text-[var(--muted)] text-[11px] leading-relaxed font-sans">
                Receive task payloads as a dict, return execution strings; prefix hard errors with <code className="text-[var(--text)] font-mono">Error:</code>.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-[var(--bg)] border border-[var(--line)] space-y-1.5">
              <div className="text-[#6366f1] font-semibold">3. Register Protocol</div>
              <p className="text-[var(--muted)] text-[11px] leading-relaxed font-sans">
                Add dispatch mapping in <code className="text-[var(--text)] font-mono">middleware/pipeline.py</code> and registry adapter for <code className="text-[var(--text)] font-mono">emerge.yaml</code>.
              </p>
            </div>
          </div>
        </div>

        {/* Ground Rules & Spec Governance */}
        <div className="bg-[#080C14] border border-slate-800 rounded-xl p-5 sm:p-6 space-y-3 text-slate-300 font-mono text-xs shadow-sm">
          <div className="text-white font-bold uppercase tracking-wider text-[11px] flex items-center justify-between">
            <span>Ground Rules &amp; Spec Governance</span>
            <span className="text-slate-400 font-normal">Apache 2.0 License</span>
          </div>

          <ul className="space-y-2 text-slate-400 font-sans text-xs leading-relaxed">
            <li className="flex items-start gap-2">
              <span className="text-[#6366f1] font-bold font-mono">•</span>
              <span><strong className="text-slate-200 font-mono">The emerge.yaml spec is frozen-by-default:</strong> Versioned via <code className="text-slate-200 font-mono">schema_version</code> and schema-validated. Spec changes require an RFC issue first.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#6366f1] font-bold font-mono">•</span>
              <span><strong className="text-slate-200 font-mono">Mock Mode First:</strong> The runtime executes with <code className="text-slate-200 font-mono">PAYMENT_MODE=mock</code> and zero proprietary cloud dependencies.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-[#6366f1] font-bold font-mono">•</span>
              <span><strong className="text-slate-200 font-mono">Standardized DIDs:</strong> User agents use <code className="text-slate-200 font-mono">did:orcha:agent:*</code>, platform tools use <code className="text-slate-200 font-mono">did:orcha:system:*</code>.</span>
            </li>
          </ul>
        </div>

        {/* Action Row */}
        <div className="flex flex-wrap gap-4 items-center pt-2">
          <a
            href="https://github.com/azank1/orcha/blob/main/CONTRIBUTING.md"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs font-semibold px-4 py-2.5 rounded-lg bg-[#6366f1] text-white hover:bg-[#4f52c8] transition-all flex items-center gap-2 shadow-sm"
          >
            <BookOpen className="w-4 h-4" /> Read CONTRIBUTING.md
          </a>

          <a
            href="https://github.com/azank1/orcha/issues/new?labels=rfc"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs font-medium px-4 py-2.5 rounded-lg border border-[var(--line)] text-[var(--text)] hover:border-[var(--faint)] bg-[var(--card-bg)] transition-all flex items-center gap-2 shadow-sm"
          >
            <GitPullRequest className="w-4 h-4 text-[#6366f1]" /> Open a Bridge PR / RFC
          </a>

          <a
            href="https://discord.gg/orcha"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs font-medium px-4 py-2.5 rounded-lg border border-[var(--line)] text-[var(--text)] hover:border-[var(--faint)] bg-[var(--card-bg)] transition-all flex items-center gap-2 shadow-sm"
          >
            <MessageSquare className="w-4 h-4 text-[#6366f1]" /> Join Discord
          </a>
        </div>

      </div>
    </section>
  );
};
