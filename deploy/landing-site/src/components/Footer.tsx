import React from 'react';
import { Link } from 'react-router-dom';
import { Github } from 'lucide-react';
import { AsciiMoonField } from './AsciiMoonField';
import { DiscordMark } from './DiscordMark';
import { footer, GITHUB_URL, DISCORD_URL } from '../data/siteConfig';

export const Footer: React.FC = () => {
  return (
    <footer className="relative bg-[var(--bg)] text-[var(--fg)] overflow-hidden">
      {/* Subtle ASCII backdrop */}
      <div className="absolute inset-0 opacity-[0.18] pointer-events-none">
        <AsciiMoonField speed={0.03} interactive={false} className="w-full h-full" />
      </div>

      <div className="relative max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 pt-20 pb-10">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 pb-16">
          <div className="md:col-span-6">
            <div className="flex items-center gap-3 mb-6">
              <img src="/brand/glyph-bare.svg" alt="Orcha" className="w-8 h-8 brand-white" />
              <span className="font-display text-2xl tracking-tight">Orcha</span>
            </div>
            <p className="text-xs text-[var(--muted-dark)] max-w-sm leading-relaxed">
              The open-source harness for multi-protocol AI agent orchestration — MCP, A2A, computer-use.
              Released under Apache 2.0. Maintained by its contributors, not a company.
            </p>
            <p className="text-[11px] text-[var(--faint)] mt-4">did:orcha:system:superagent · RFC 0001</p>
          </div>

          <div className="md:col-span-6 grid grid-cols-2 gap-8 text-xs">
            <div className="space-y-3">
              <span className="text-[10px] uppercase tracking-[0.14em] text-[var(--faint)] block">Runtime</span>
              <ul className="space-y-2 text-[var(--muted-dark)]">
                <li><Link to="/#observation" className="hover:text-[var(--fg)] transition-colors">Sandbox</Link></li>
                <li><Link to="/#plugins" className="hover:text-[var(--fg)] transition-colors">Plugins</Link></li>
                <li><Link to="/plugins/canvaskit" className="hover:text-[var(--fg)] transition-colors">CanvasKit</Link></li>
                <li><Link to="/docs" className="hover:text-[var(--fg)] transition-colors">Orcha SDK</Link></li>
              </ul>
            </div>
            <div className="space-y-3">
              <span className="text-[10px] uppercase tracking-[0.14em] text-[var(--faint)] block">Community</span>
              <ul className="space-y-2 text-[var(--muted-dark)]">
                <li>
                  <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer" className="hover:text-[var(--fg)] transition-colors inline-flex items-center gap-1.5">
                    <Github className="w-3 h-3" /> GitHub
                  </a>
                </li>
                <li>
                  <a href={DISCORD_URL} target="_blank" rel="noopener noreferrer" className="hover:text-[var(--fg)] transition-colors inline-flex items-center gap-1.5">
                    <DiscordMark className="w-3 h-3" /> Discord
                  </a>
                </li>
                <li><Link to="/roadmap" className="hover:text-[var(--fg)] transition-colors">Roadmap</Link></li>
                <li><Link to="/contributing" className="hover:text-[var(--fg)] transition-colors">Contributing</Link></li>
              </ul>
            </div>
          </div>
        </div>

        <div className="border-t border-[var(--line-dark)] pt-6 text-[11px] text-[var(--faint)]">
          <span>{footer.copyrightText}</span>
        </div>
      </div>
    </footer>
  );
};
