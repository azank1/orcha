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
    <span className="font-mono text-[11px] text-[var(--muted)] flex items-center gap-1.5">
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
  theme = 'light',
  onToggleTheme
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const navItems = [
    { id: 'overview', label: 'Overview', icon: <Home className="w-3.5 h-3.5" /> },
    { id: 'docs', label: 'Documentation', icon: <FileText className="w-3.5 h-3.5" />, badge: 'System Docs' },
    { id: 'playground', label: 'Sandbox', icon: <Terminal className="w-3.5 h-3.5" /> },
    { id: 'roadmap', label: 'Roadmap', icon: <MapPin className="w-3.5 h-3.5" /> },
    { id: 'contributing', label: 'Contributing', icon: <GitPullRequest className="w-3.5 h-3.5" /> }
  ];

  return (
    <header className="sticky top-0 z-50 bg-[var(--bg)]/80 backdrop-blur-xl border-b border-[var(--line)]/50 transition-colors shadow-[0_1px_0_0_rgba(255,255,255,0.03)_inset]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          
          {/* Left: Logo */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setActiveTab('overview')}
              className="flex items-center gap-2 font-mono font-bold text-lg tracking-tight text-[var(--text)] hover:opacity-80 transition-opacity"
            >
              <span className="w-2.5 h-2.5 bg-[#6366f1] rounded-[2px] inline-block"></span>
              Orcha
            </button>
          </div>

          {/* Center: Main Tab Navigation */}
          <nav className="hidden md:flex items-center gap-1 bg-[var(--card-bg)]/80 p-1 rounded-lg border border-[var(--line)]">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              if (item.id === 'playground') {
                return (
                  <a
                    key={item.id}
                    href={SANDBOX_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="font-mono text-xs px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-all relative text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg)]"
                  >
                    {item.icon}
                    <span>{item.label}</span>
                    <span className="text-[9px] px-1.5 py-0.2 rounded font-mono uppercase bg-[#6366f1]/15 text-[#6366f1]">live</span>
                  </a>
                );
              }
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`font-mono text-xs px-3 py-1.5 rounded-md flex items-center gap-1.5 transition-all relative ${
                    isActive
                      ? 'bg-[#6366f1] text-white font-semibold shadow-sm'
                      : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg)]'
                  }`}
                >
                  {item.icon}
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className={`text-[9px] px-1.5 py-0.2 rounded font-mono uppercase ${
                      isActive ? 'bg-white/20 text-white' : 'bg-[#6366f1]/15 text-[#6366f1]'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* Right: Theme Toggle & GitHub */}
          <div className="hidden md:flex items-center gap-3">
            <LiveStatusChip />
            <button
              onClick={onToggleTheme}
              className="font-mono text-xs border border-[var(--line)] hover:border-[#6366f1] bg-[var(--card-bg)] text-[var(--text)] px-2.5 py-1.5 rounded-md flex items-center gap-1.5 transition-all shadow-sm"
              title={`Switch to ${theme === 'dark' ? 'Light' : 'Dark'} Theme`}
            >
              {theme === 'dark' ? (
                <>
                  <Sun className="w-3.5 h-3.5 text-amber-400" />
                  <span className="text-[11px] font-medium">Light</span>
                </>
              ) : (
                <>
                  <Moon className="w-3.5 h-3.5 text-indigo-600" />
                  <span className="text-[11px] font-medium">Dark</span>
                </>
              )}
            </button>

            <a
              href="https://github.com/azank1/orcha"
              target="_blank"
              rel="noopener noreferrer"
              className="font-mono text-xs border border-[var(--line)] hover:border-[#6366f1] bg-[var(--card-bg)] text-[var(--text)] px-3 py-1.5 rounded-md flex items-center gap-2 transition-all group shadow-sm"
            >
              <Github className="w-3.5 h-3.5 text-[var(--muted)] group-hover:text-[var(--text)]" />
              <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400/20" />
              <span>GitHub</span>
            </a>
          </div>

          {/* Mobile Menu Toggle */}
          <div className="flex items-center gap-2 md:hidden">
            <button
              onClick={onToggleTheme}
              className="p-1.5 text-[var(--text)] border border-[var(--line)] rounded bg-[var(--card-bg)]"
              title="Toggle Theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-indigo-600" />}
            </button>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 text-[var(--muted)] hover:text-[var(--text)] border border-[var(--line)] rounded bg-[var(--card-bg)]"
              aria-label="Toggle Menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>

        </div>
      </div>

      {/* Mobile Menu */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-[var(--line)] bg-[var(--card-bg)] px-4 pt-3 pb-5 space-y-2">
          {navItems.map((item) => item.id === 'playground' ? (
            <a
              key={item.id}
              href={SANDBOX_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full text-left font-mono text-xs px-3 py-2 rounded-md flex items-center justify-between transition-colors text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg)]"
              onClick={() => setMobileMenuOpen(false)}
            >
              <span className="flex items-center gap-2">{item.icon}{item.label}</span>
              <span className="text-[9px] font-mono uppercase text-[#6366f1]">live</span>
            </a>
          ) : (
            <button
              key={item.id}
              onClick={() => {
                setActiveTab(item.id);
                setMobileMenuOpen(false);
              }}
              className={`w-full text-left font-mono text-xs px-3 py-2 rounded-md flex items-center justify-between transition-colors ${
                activeTab === item.id
                  ? 'bg-[#6366f1] text-white font-semibold'
                  : 'text-[var(--muted)] hover:text-[var(--text)] hover:bg-[var(--bg)]'
              }`}
            >
              <span className="flex items-center gap-2">
                {item.icon}
                {item.label}
              </span>
              {item.badge && (
                <span className="text-[10px] bg-white/20 text-white px-1.5 py-0.5 rounded">
                  {item.badge}
                </span>
              )}
            </button>
          ))}
          
          <div className="pt-2 border-t border-[var(--line)] flex items-center justify-between">
            <a
              href="https://github.com/azank1/orcha"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 font-mono text-xs text-[#6366f1]"
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
