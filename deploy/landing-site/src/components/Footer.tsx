import React from 'react';
import { Github } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-[var(--bg)] border-t border-[var(--line)] py-12 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        <div className="grid grid-cols-1 md:grid-cols-12 gap-8">
          
          {/* Brand & Mission */}
          <div className="md:col-span-5 space-y-3">
            <div className="flex items-center gap-2 font-display font-bold text-lg text-[var(--text)]">
              <span className="w-2.5 h-2.5 bg-[#6366f1] rounded-[2px] inline-block"></span>
              Orcha
            </div>
            <p className="text-xs text-[var(--muted)] max-w-sm leading-relaxed">
              The open source harness for multi-protocol AI agent orchestration (MCP, A2A, computer use). Released under Apache 2.0.
            </p>
            <div className="font-mono text-[11px] text-[var(--faint)]">
              did:orcha:system:superagent · RFC 0001
            </div>
          </div>

          {/* Quick Links */}
          <div className="md:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-6 font-mono text-xs">
            
            <div className="space-y-3">
              <span className="text-[var(--text)] font-semibold uppercase tracking-wider block">Runtime</span>
              <ul className="space-y-2 text-[var(--muted)]">
                <li><a href="#playground" className="hover:text-[var(--text)] transition-colors">Sandbox</a></li>
                <li><a href="#verified-runs" className="hover:text-[var(--text)] transition-colors">Verified Runs</a></li>
                <li><a href="#canvaskit" className="hover:text-[var(--text)] transition-colors">CanvasKit</a></li>
                <li><a href="#sdk" className="hover:text-[var(--text)] transition-colors">Emerge SDK</a></li>
              </ul>
            </div>

            <div className="space-y-3">
              <span className="text-[var(--text)] font-semibold uppercase tracking-wider block">Architecture</span>
              <ul className="space-y-2 text-[var(--muted)]">
                <li><a href="#arch" className="hover:text-[var(--text)] transition-colors">Neutral Ground</a></li>
                <li><a href="#sdk" className="hover:text-[var(--text)] transition-colors">emerge.yaml 1.1</a></li>
                <li><a href="https://github.com/azank1/orcha" target="_blank" rel="noopener noreferrer" className="hover:text-[var(--text)] transition-colors">RFC 0001 Spec</a></li>
              </ul>
            </div>

            <div className="space-y-3">
              <span className="text-[var(--text)] font-semibold uppercase tracking-wider block">Community</span>
              <ul className="space-y-2 text-[var(--muted)]">
                <li><a href="https://github.com/azank1/orcha" target="_blank" rel="noopener noreferrer" className="hover:text-[var(--text)] transition-colors flex items-center gap-1"><Github className="w-3 h-3" /> GitHub Repo</a></li>
                <li><a href="#roadmap" className="hover:text-[var(--text)] transition-colors">Honest Roadmap</a></li>
                <li><a href="#contribute" className="hover:text-[var(--text)] transition-colors">Contributing</a></li>
                <li><a href="https://discord.gg/orcha" target="_blank" rel="noopener noreferrer" className="hover:text-[var(--text)] transition-colors">Discord</a></li>
              </ul>
            </div>

          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-8 border-t border-[var(--line)] flex flex-col sm:flex-row items-center justify-between font-mono text-xs text-[var(--faint)] gap-4">
          <div>
            © {new Date().getFullYear()} Orcha Open Source Contributors. Licensed under Apache 2.0.
              <br /><span className="font-mono text-[11px] text-[var(--faint)]">receipts, not traces — per-step verdicts, exportable evidence.</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-[var(--muted)]">PAYMENT_MODE=mock</span>
            <span className="text-[var(--muted)]">v1.0.0</span>
          </div>
        </div>

      </div>
    </footer>
  );
};
