import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Github, Menu, X } from 'lucide-react';
import { DiscordMark } from './DiscordMark';
import { nav, GITHUB_URL, DISCORD_URL } from '../data/siteConfig';

export const Navbar: React.FC = () => {
  const [open, setOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  const go = (href: string) => {
    setOpen(false);
    if (href.startsWith('/#')) {
      const id = href.slice(2);
      if (location.pathname !== '/') {
        navigate('/');
        setTimeout(() => document.getElementById(id)?.scrollIntoView({ behavior: 'auto' }), 60);
      } else {
        document.getElementById(id)?.scrollIntoView({ behavior: 'auto' });
      }
    } else {
      navigate(href);
    }
  };

  return (
    <header className="sticky top-0 z-40 bg-black/85 backdrop-blur-md border-b border-[var(--line-dark)]">
      <div className="max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-3 hover:opacity-70 transition-opacity">
            <img src="/brand/glyph-bare.svg" alt="Orcha" className="w-6 h-6 brand-white" />
            <span className="font-display text-lg tracking-tight">Orcha</span>
          </Link>

          <nav className="hidden md:flex items-center gap-8">
            {nav.links.map((l) => (
              <button
                key={l.label}
                onClick={() => go(l.href)}
                className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted-dark)] hover:text-[var(--fg)] transition-colors"
              >
                {l.label}
              </button>
            ))}
          </nav>

          <div className="hidden md:flex items-center gap-3">
            <a
              href={DISCORD_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] border border-[var(--line-dark)] px-4 py-2 text-[var(--muted-dark)] hover:text-[var(--fg)] hover:border-white/40 transition-colors"
            >
              <DiscordMark className="w-3.5 h-3.5" />
              Discord
            </a>
            <a
              href={GITHUB_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] border border-[var(--line-dark)] px-4 py-2 text-[var(--muted-dark)] hover:text-[var(--fg)] hover:border-white/40 transition-colors"
            >
              <Github className="w-3.5 h-3.5" />
              GitHub
            </a>
          </div>

          <button
            onClick={() => setOpen(!open)}
            className="md:hidden p-2 text-[var(--muted-dark)] hover:text-[var(--fg)]"
            aria-label="Toggle menu"
          >
            {open ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {open && (
        <div className="md:hidden border-t border-[var(--line-dark)] bg-black px-6 py-4 space-y-1">
          {nav.links.map((l) => (
            <button
              key={l.label}
              onClick={() => go(l.href)}
              className="block w-full text-left text-xs uppercase tracking-[0.14em] py-3 text-[var(--muted-dark)] hover:text-[var(--fg)]"
            >
              {l.label}
            </button>
          ))}
          <a
            href={DISCORD_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs uppercase tracking-[0.14em] py-3 text-[var(--muted-dark)] hover:text-[var(--fg)]"
          >
            <DiscordMark className="w-3.5 h-3.5" />
            Discord
          </a>
          <a
            href={GITHUB_URL}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs uppercase tracking-[0.14em] py-3 text-[var(--muted-dark)] hover:text-[var(--fg)]"
          >
            <Github className="w-3.5 h-3.5" />
            GitHub
          </a>
        </div>
      )}
    </header>
  );
};
