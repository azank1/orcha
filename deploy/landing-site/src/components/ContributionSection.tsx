import React from 'react';
import { GitPullRequest, MessageSquare, BookOpen, Terminal, Layers, ShieldCheck, Cpu } from 'lucide-react';
import { DISCORD_URL } from '../data/siteConfig';

export const ContributionSection: React.FC = () => {
  return (
    <section id="contribute" className="py-16 border-b border-black/10 bg-[var(--paper)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-[11px] uppercase tracking-[0.12em] text-[var(--muted-light)] font-semibold">
            Open Source Ecosystem
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--ink)]">
            Grow at the edges, freeze the core
          </h2>
          <p className="text-[var(--muted-light)] text-xs sm:text-sm max-w-3xl leading-relaxed">
            Handlers are pluggable: anyone can add a protocol bridge — LangGraph, OpenAPI, gRPC, ACP, or custom RPCs — without prior discussion.
          </p>
          <p className="text-[var(--muted-light)] text-xs sm:text-sm max-w-3xl leading-relaxed">
            No waitlist. No black box. The runtime, the bridges and the audit trail are Apache 2.0 — read them, fork them, run them. Bridge authors are named in the handler docs, spec changes go through public RFC, and commit rights are earned by contribution.
          </p>
        </div>

        {/* 4 Contribution Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          
          <div className="bg-white border border-black/10 p-5 rounded-xl space-y-3 flex flex-col justify-between shadow-sm transition-colors hover:border-black/40">
            <div className="space-y-2">
              <span className="font-mono text-[10.5px] uppercase tracking-wider text-[var(--muted-light)] block font-semibold flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5" /> Highest Leverage
              </span>
              <h3 className="font-display font-bold text-base text-[var(--ink)]">
                Write a Protocol Bridge
              </h3>
              <p className="text-xs text-[var(--muted-light)] leading-relaxed">
                Pluggable protocol handlers unlock entire agent ecosystems. Create a subclass of <code className="text-[var(--ink)]">AgentHandler</code> to orchestrate LangGraph, n8n, OpenAPI, gRPC, or custom RPCs.
              </p>
            </div>
            <code className="font-mono text-[11px] text-[var(--ink)] bg-[var(--paper)] px-3 py-2 rounded border border-black/10 block truncate">
              templates/your-first-bridge/
            </code>
          </div>

          <div className="bg-white border border-black/10 p-5 rounded-xl space-y-3 flex flex-col justify-between shadow-sm transition-colors hover:border-black/40">
            <div className="space-y-2">
              <span className="font-mono text-[10.5px] uppercase tracking-wider text-[var(--muted-light)] block font-semibold flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5" /> Grow the Fleet
              </span>
              <h3 className="font-display font-bold text-base text-[var(--ink)]">
                Ship an Example Agent
              </h3>
              <p className="text-xs text-[var(--muted-light)] leading-relaxed">
                Add specialized agents with <code className="text-[var(--ink)]">emerge.yaml</code> manifests specifying capability scopes and DIDs (<code className="text-[var(--ink)]">did:orcha:agent:*</code>).
              </p>
            </div>
            <code className="font-mono text-[11px] text-[var(--ink)] bg-[var(--paper)] px-3 py-2 rounded border border-black/10 block truncate">
              templates/your-first-agent/
            </code>
          </div>

          <div className="bg-white border border-black/10 p-5 rounded-xl space-y-3 flex flex-col justify-between shadow-sm transition-colors hover:border-black/40">
            <div className="space-y-2">
              <span className="font-mono text-[10.5px] uppercase tracking-wider text-[var(--muted-light)] block font-semibold flex items-center gap-1.5">
                <Terminal className="w-3.5 h-3.5" /> Native Output
              </span>
              <h3 className="font-display font-bold text-base text-[var(--ink)]">
                Build CanvasKit UI
              </h3>
              <p className="text-xs text-[var(--muted-light)] leading-relaxed">
                Build declarative UI dashboard primitives for agent outputs so runs render structured visual widgets instead of chat bubbles.
              </p>
            </div>
            <code className="font-mono text-[11px] text-[var(--ink)] bg-[var(--paper)] px-3 py-2 rounded border border-black/10 block truncate">
              frontend/src/components/canvas/
            </code>
          </div>

          <div className="bg-white border border-black/10 p-5 rounded-xl space-y-3 flex flex-col justify-between shadow-sm transition-colors hover:border-black/40">
            <div className="space-y-2">
              <span className="font-mono text-[10.5px] uppercase tracking-wider text-[var(--muted-light)] block font-semibold flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5" /> Audit Engine
              </span>
              <h3 className="font-display font-bold text-base text-[var(--ink)]">
                Execution Observer
              </h3>
              <p className="text-xs text-[var(--muted-light)] leading-relaxed">
                Extend the <code className="text-[var(--ink)]">ExecutionObserver</code> seam and validator reference code to improve protocol attestation and run evidence.
              </p>
            </div>
            <code className="font-mono text-[11px] text-[var(--ink)] bg-[var(--paper)] px-3 py-2 rounded border border-black/10 block truncate">
              services/validator/
            </code>
          </div>

        </div>

        {/* How Bridges Work Callout Box */}
        <div className="bg-white border border-black/10 rounded-xl p-6 space-y-4 shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-black/10 pb-3">
            <div>
              <h3 className="font-display font-bold text-base text-[var(--ink)]">
                Writing a Bridge Component (3-Step Quick Contract)
              </h3>
              <p className="text-xs text-[var(--muted-light)]">
                Any protocol can become an Orcha handler in under 50 lines of Python.
              </p>
            </div>
            <span className="font-mono text-[11px] text-[var(--muted-light)] w-fit">
              No prior discussion needed
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
            <div className="p-3.5 rounded-lg bg-[var(--paper)] border border-black/10 space-y-1.5">
              <div className="text-[var(--ink)] font-semibold">1. Subclass AgentHandler</div>
              <p className="text-[var(--muted-light)] text-[11px] leading-relaxed">
                Create <code className="text-[var(--ink)] font-mono">handlers/langgraph_handler.py</code> extending <code className="text-[var(--ink)] font-mono">AgentHandler</code>.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-[var(--paper)] border border-black/10 space-y-1.5">
              <div className="text-[var(--ink)] font-semibold">2. Implement send_task()</div>
              <p className="text-[var(--muted-light)] text-[11px] leading-relaxed">
                Receive task payloads as a dict, return execution strings; prefix hard errors with <code className="text-[var(--ink)] font-mono">Error:</code>.
              </p>
            </div>

            <div className="p-3.5 rounded-lg bg-[var(--paper)] border border-black/10 space-y-1.5">
              <div className="text-[var(--ink)] font-semibold">3. Register Protocol</div>
              <p className="text-[var(--muted-light)] text-[11px] leading-relaxed">
                Add dispatch mapping in <code className="text-[var(--ink)] font-mono">middleware/pipeline.py</code> and registry adapter for <code className="text-[var(--ink)] font-mono">emerge.yaml</code>.
              </p>
            </div>
          </div>
        </div>

        {/* Ground Rules & Spec Governance */}
        <div className="bg-[#050505] border border-[var(--line-dark)] rounded-xl p-5 sm:p-6 space-y-3 text-neutral-300 font-mono text-xs shadow-sm">
          <div className="text-white font-bold uppercase tracking-wider text-[11px] flex items-center justify-between">
            <span>Ground Rules &amp; Spec Governance</span>
            <span className="text-[var(--muted-dark)] font-normal">Apache 2.0 License</span>
          </div>

          <ul className="space-y-2 text-[var(--muted-dark)] text-xs leading-relaxed">
            <li className="flex items-start gap-2">
              <span className="text-white font-bold font-mono">•</span>
              <span><strong className="text-neutral-200 font-mono">The emerge.yaml spec is frozen-by-default:</strong> Versioned via <code className="text-neutral-200 font-mono">schema_version</code> and schema-validated. Spec changes require an RFC issue first.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-white font-bold font-mono">•</span>
              <span><strong className="text-neutral-200 font-mono">Mock Mode First:</strong> The runtime executes with <code className="text-neutral-200 font-mono">PAYMENT_MODE=mock</code> and zero proprietary cloud dependencies.</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-white font-bold font-mono">•</span>
              <span><strong className="text-neutral-200 font-mono">Standardized DIDs:</strong> User agents use <code className="text-neutral-200 font-mono">did:orcha:agent:*</code>, platform tools use <code className="text-neutral-200 font-mono">did:orcha:system:*</code>.</span>
            </li>
          </ul>
        </div>

        {/* Action Row */}
        <div className="flex flex-wrap gap-4 items-center pt-2">
          <a
            href="https://github.com/solvent-metaorcha/orcha/blob/main/CONTRIBUTING.md"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs font-semibold px-4 py-2.5 rounded-lg bg-[var(--ink)] text-white hover:bg-black/80 transition-all flex items-center gap-2 shadow-sm"
          >
            <BookOpen className="w-4 h-4" /> Read CONTRIBUTING.md
          </a>

          <a
            href="https://github.com/solvent-metaorcha/orcha/issues/new?labels=rfc"
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs font-medium px-4 py-2.5 rounded-lg border border-black/10 text-[var(--ink)] hover:border-black/40 bg-white transition-all flex items-center gap-2 shadow-sm"
          >
            <GitPullRequest className="w-4 h-4" /> Open a Bridge PR / RFC
          </a>

          <a
            href={DISCORD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="font-mono text-xs font-medium px-4 py-2.5 rounded-lg border border-black/10 text-[var(--ink)] hover:border-black/40 bg-white transition-all flex items-center gap-2 shadow-sm"
          >
            <MessageSquare className="w-4 h-4" /> Join Discord
          </a>
        </div>

      </div>
    </section>
  );
};
