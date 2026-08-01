import React, { useState, useEffect } from 'react';
import { Github, Star, FileText, MessageSquare, Menu, X, Sun, Moon, Terminal, MapPin, GitPullRequest, Home, Sparkles } from 'lucide-react';
import { SANDBOX_URL, SANDBOX_STATUS_URL } from '../config/sandbox';

interface SandboxStatus {
  status: string;
  runs_today: number;
  agents_fleet: number;
}

const STATUS_URL = SANDBOX_STATUS_URL;

// Small live-status chip: renders only while the gateway reports "live";
// silent (renders nothing) on fetch failure or any non-live status.
const LiveStatusChip: React.FC = () => {
  const [status, setStatus] = useState<SandboxStatus | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetch(STATUS_URL);
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data: SandboxStatus = await res.json();
        if (!cancelled) setStatus(data.status === 'live' ? data : null);
      } catch {
        if (!cancelled) setStatus(null);
      }
    };
    poll();
    const id = setInterval(poll, 60000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (!status) return null;

  return (
    <span className="text-xs text-[var(--muted)] flex items-center gap-1.5">
      <span className="w-1.5 h-1.5 rounded-full bg-[var(--ok)] inline-block"></span>
      live · {status.runs_today} runs today
    </span>
  );
};

interface NavbarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  theme?: 'dark' | 'light';
  onToggleTheme?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  activeTab,
  setActiveTab,
  theme = 'dark',
  onToggleTheme
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: <Home className="w-4 h-4" /> },
    { id: 'docs', label: 'Documentation', icon: <FileText className="w-4 h-4" /> },
    { id: 'playground', label: 'Sandbox', icon: <Terminal className="w-4 h-4" /> },
    { id: 'roadmap', label: 'Roadmap', icon: <MapPin className="w-4 h-4" /> },
    { id: 'contributing', label: 'Contributing', icon: <GitPullRequest className="w-4 h-4" /> }
  ];

  return (
    <header className="sticky top-0 z-50 bg-[var(--bg)]/80 backdrop-blur-xl border-b border-[var(--line)]/50 transition-colors">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">
        <div className="flex items-center justify-between h-16">

          {/* Left: Logo */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab('overview')}
              className="flex items-center gap-2 font-display font-bold text-xl tracking-tight text-[var(--text)] hover:opacity-80 transition-opacity"
            >
              <span className="w-2.5 h-2.5 bg-[#6366f1] rounded-[2px] inline-block"></span>
              Orcha
            </button>
          </div>

          {/* Center: Main Tab Navigation */}
          <nav className="hidden md:flex items-center gap-1 bg-[var(--card-bg)]/80 p-1.5 rounded-full border border-[var(--line)]">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              if (item.id === 'playground') {
                return (
                  <a
                    key={item.id}
                    href={SANDBOX_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm px-4 py-2 rounded-full flex items-center gap-2 transition-all relative text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg)]"
                  >
                    {item.icon}
                    <span>{item.label}</span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded-full font-semibold uppercase bg-[#6366f1]/15 text-[#6366f1]">live</span>
                  </a>
                );
              }
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`text-sm px-4 py-2 rounded-full flex items-center gap-2 transition-all relative ${
                    isActive
                      ? 'bg-[#6366f1] text-white font-semibold shadow-sm'
                      : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg)]'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Right: Theme Toggle & GitHub */}
          <div className="hidden md:flex items-center gap-4">
            <LiveStatusChip />
            <button
              onClick={onToggleTheme}
              className="text-sm border border-[var(--line)] hover:border-[#6366f1] bg-[var(--card-bg)] text-[var(--text)] px-3 py-2 rounded-full flex items-center gap-2 transition-all"
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Theme`}
            >
              {theme === 'dark' ? (
                <>
                  <Sun className="w-4 h-4 text-amber-400" />
                  <span className="text-sm font-medium">Light</span>
                </>
              ) : (
                <>
                  <Moon className="w-4 h-4 text-indigo-600" />
                  <span className="text-sm font-medium">Dark</span>
                </>
              )}
            </button>

            <a
              href="https://github.com/azank1/orcha"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm border border-[var(--line)] hover:border-[#6366f1] bg-[var(--card-bg)] text-[var(--text)] px-4 py-2 rounded-full flex items-center gap-2 transition-all group"
            >
              <Github className="w-4 h-4 text-[var(--muted)] group-hover:text-[var(--text)]" />
              <Star className="w-4 h-4 text-amber-400 fill-amber-400/20" />
              <span>GitHub</span>
            </a>
          </div>

          {/* Mobile Menu Toggle */}
          <div className="flex items-center gap-2 md:hidden">
            <button
              onClick={onToggleTheme}
              className="p-2 text-[var(--text)] border border-[var(--line)] rounded-full bg-[var(--card-bg)]"
              title="Toggle Theme"
            >
              {theme === 'dark' ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5 text-indigo-600" />}
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-[var(--muted)] hover:text-[var(--text)] border border-[var(--line)] rounded-full bg-[var(--card-bg)]"
              aria-label="Toggle Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[var(--line)] bg-[var(--card-bg)] px-6 pt-4 pb-6 space-y-2">
          {navItems.map((item) => item.id === 'playground' ? (
            <a
              key={item.id}
              href={SANDBOX_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full text-left text-sm px-4 py-3 rounded-full flex items-center justify-between transition-colors text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg)]"
              onClick={() => setMobileMenuOpen(false)}
            >
              <span className="flex items-center gap-2">{item.icon}{item.label}</span>
              <span className="text-[10px] font-semibold uppercase text-[#6366f1]">live</span>
            </a>
          ) : (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setMobileMenuOpen(false);
              }}
              className={`w-full text-left text-sm px-4 py-3 rounded-full flex items-center justify-between transition-colors ${
                activeTab === item.id
                  ? 'bg-[#6366f1] text-white font-semibold'
                  : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg)]'
              }`}
            >
              <span className="flex items-center gap-2">
                {item.icon}
                {item.label}
              </span>
            </button>
          ))}

          <div className="pt-4 border-t border-[var(--line)] flex items-center justify-between">
            <a
              href="https://github.com/azank1/orcha"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-[#6366f1]"
            >
              <Github className="w-4 h-4" />
              Star on GitHub
            </a>
          </div>
        </div>
      )}
    </header>
  );
};
