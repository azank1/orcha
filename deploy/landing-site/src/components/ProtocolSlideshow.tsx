import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ChevronLeft, ChevronRight, Layout, CheckCircle2, ArrowUpRight } from 'lucide-react';
import { McpLogo, A2aLogo, LangChainLogo, ComputerUseLogo, PlusLogo } from './ProtocolIcons';

interface Cta {
  label: string;
  href: string;
}

interface Slide {
  id: string;
  badge: string;
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  codeSnippet?: string;
  codeLabel?: string;
  highlights: string[];
  ctas?: Cta[];
  invitation?: boolean;
}

const SLIDES: Slide[] = [
  {
    id: 'mcp-bridge',
    badge: 'bridge 01 · tools',
    title: 'MCP — tools and resources',
    subtitle: 'The tool servers everyone already runs, composed into the run.',
    icon: <McpLogo />,
    codeLabel: 'handlers/mcp_handler.py',
    codeSnippet: `await handler.call_tool(
    agent_id="did:orcha:agent:finance-dashboard",
    capability_id="get_portfolio_dashboard",
    args={}, transport=transport,   # SSE or stdio
)`,
    highlights: [
      'SSE + stdio transports',
      'capabilities harvested from the live endpoint at registration',
      'credential vault + auth cascade'
    ]
  },
  {
    id: 'a2a-bridge',
    badge: 'bridge 02 · agents',
    title: 'A2A — independent agent services',
    subtitle: 'Agents running elsewhere, called as peers — ACP manifests route here too.',
    icon: <A2aLogo />,
    codeLabel: 'handlers/a2a_handler.py',
    codeSnippet: `await handler.send_task(
    agent_id="did:orcha:agent:web-scraper",
    task="summarize en.wikipedia.org/wiki/Nvidia",
    transport=transport, state=state, call_id=call_id,
)`,
    highlights: [
      'agent-card discovery',
      'ACP accepted, routed as A2A',
      'async task + HITL resume'
    ]
  },
  {
    id: 'computer-use',
    badge: 'bridge 03 · no API needed',
    title: 'Computer use — the long tail',
    subtitle: 'Software with no API gets driven, not rewritten.',
    icon: <ComputerUseLogo />,
    codeLabel: 'handlers/computer_use_handler.py',
    codeSnippet: `await handler.execute(
    args={"action": "screenshot", "target": "dashboard"},
    transport=transport, call_id=call_id,
)`,
    highlights: [
      'backend env-swappable (COMPUTER_USE_BACKEND)',
      'mock by default, OSS-clean',
      'screenshots land as run artifacts'
    ]
  },
  {
    id: 'langgraph-bridge',
    badge: 'bridge 04 · your framework',
    title: 'LangGraph, OpenAPI, n8n — one class each',
    subtitle: 'A bridge answers one question: given a task and a transport, call the remote agent and return text.',
    icon: <LangChainLogo />,
    codeLabel: 'handlers/base.py',
    codeSnippet: `class LangGraphHandler(AgentHandler):
    async def execute(self, args, transport, **kw) -> str:
        return await call_your_service(transport["endpoint"], args)`,
    highlights: [
      'planning, auth, verification, payments inherited',
      'one handler = one weekend PR'
    ]
  },
  {
    id: 'your-bridge',
    badge: 'bridge 05 · yours',
    title: 'Your protocol here.',
    subtitle: 'One handler class unlocks every agent that speaks it. The template is a single file.',
    icon: <PlusLogo />,
    highlights: [],
    ctas: [
      {
        label: 'templates/your-first-bridge/',
        href: 'https://github.com/azank1/orcha/tree/main/templates/your-first-bridge'
      },
      {
        label: 'bridge guide',
        href: 'https://github.com/azank1/orcha/blob/main/docs/bridges.md'
      }
    ],
    invitation: true
  }
];

export const ProtocolSlideshow: React.FC = () => {
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (isPaused) return;
    const interval = setInterval(() => {
      setActiveSlideIndex((prev) => (prev + 1) % SLIDES.length);
    }, 6000);
    return () => clearInterval(interval);
  }, [isPaused]);

  const currentSlide = SLIDES[activeSlideIndex];

  return (
    <section className="py-24 sm:py-32 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 space-y-12">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--line)] pb-6">
          <div className="space-y-2">
            <div className="text-sm text-[#6366f1] font-semibold uppercase tracking-wider flex items-center gap-2">
              <Layout className="w-4 h-4" />
              Protocol Architecture
            </div>
            <h3 className="font-display font-bold text-3xl sm:text-4xl text-[var(--text)]">
              Multi-Agent Protocol Capabilities
            </h3>
            <p className="text-lg text-[var(--muted)]">
              the first two bridges are MCP and A2A — the harness doesn't care what ships next.
            </p>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            <span className="text-sm text-[var(--faint)] mr-2 hidden sm:inline">
              0{activeSlideIndex + 1} / 0{SLIDES.length}
            </span>
            <button
              onClick={() => setActiveSlideIndex((prev) => (prev - 1 + SLIDES.length) % SLIDES.length)}
              className="p-2.5 rounded-full border border-[var(--line)] bg-[var(--card-bg)] hover:border-[#6366f1] text-[var(--text)] transition-colors"
              aria-label="Previous Slide"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <button
              onClick={() => setActiveSlideIndex((prev) => (prev + 1) % SLIDES.length)}
              className="p-2.5 rounded-full border border-[var(--line)] bg-[var(--card-bg)] hover:border-[#6366f1] text-[var(--text)] transition-colors"
              aria-label="Next Slide"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Carousel Slide Card */}
        <div
          onMouseEnter={() => setIsPaused(true)}
          onMouseLeave={() => setIsPaused(false)}
          className={`relative min-h-[360px] rounded-2xl border bg-[var(--card-bg)] p-8 sm:p-10 shadow-sm overflow-hidden flex flex-col justify-between ${
            currentSlide.invitation ? 'border-dashed border-[var(--line)]' : 'border-[var(--line)]'
          }`}
        >
          <AnimatePresence mode="wait">
            <motion.div
              key={currentSlide.id}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.4, ease: 'easeInOut' }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center"
            >
              {/* Left Content */}
              <div className="lg:col-span-5 space-y-5">
                <div
                  className={`inline-flex items-center gap-2 text-sm font-semibold px-3 py-1.5 rounded-full ${
                    currentSlide.invitation
                      ? 'border border-dashed border-[var(--line)] text-[var(--muted)]'
                      : 'uppercase bg-[#6366f1]/10 text-[#6366f1] border border-[#6366f1]/30'
                  }`}
                >
                  <span className={currentSlide.invitation ? '' : 'text-[#6366f1]'}>{currentSlide.icon}</span>
                  <span>{currentSlide.badge}</span>
                </div>

                <div className="space-y-2">
                  <h4
                    className={`font-display font-bold text-2xl sm:text-3xl ${
                      currentSlide.invitation ? 'text-[var(--muted)]' : 'text-[var(--text)]'
                    }`}
                  >
                    {currentSlide.title}
                  </h4>
                  <p className="text-base text-[var(--muted)] leading-relaxed">
                    {currentSlide.subtitle}
                  </p>
                </div>

                {currentSlide.highlights.length > 0 && (
                  <ul className="space-y-3 pt-3">
                    {currentSlide.highlights.map((h, idx) => (
                      <li key={idx} className="flex items-center gap-3 text-sm text-[var(--text)]">
                        <CheckCircle2 className="w-4 h-4 text-[#6366f1] flex-shrink-0" />
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Right Code Block / Invitation CTAs */}
              {currentSlide.codeSnippet ? (
                <div className="lg:col-span-7 rounded-xl border border-slate-800 bg-[#070A10] p-5 shadow-inner overflow-x-auto">
                  <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-800 pb-3 mb-4">
                    <span>{currentSlide.codeLabel}</span>
                    <span className="text-[#6366f1]">Python 3.11</span>
                  </div>
                  <pre className="font-mono text-sm text-slate-200 leading-relaxed custom-scrollbar">
                    <code>{currentSlide.codeSnippet}</code>
                  </pre>
                </div>
              ) : (
                <div className="lg:col-span-7 rounded-xl border border-dashed border-[var(--line)] p-6 space-y-4">
                  {currentSlide.ctas?.map((cta) => (
                    <a
                      key={cta.href}
                      href={cta.href}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between gap-3 text-sm text-[var(--muted)] hover:text-[#6366f1] border border-dashed border-[var(--line)] hover:border-[#6366f1] rounded-xl px-5 py-4 transition-colors"
                    >
                      <span>{cta.label}</span>
                      <ArrowUpRight className="w-4 h-4 flex-shrink-0" />
                    </a>
                  ))}
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Dots Indicator */}
          <div className="flex items-center justify-center gap-2 pt-8">
            {SLIDES.map((slide, idx) => (
              <button
                key={slide.id}
                onClick={() => setActiveSlideIndex(idx)}
                className={`h-2.5 rounded-full transition-all ${
                  idx === activeSlideIndex
                    ? 'w-10 bg-[#6366f1]'
                    : 'w-2.5 bg-[var(--line)] hover:bg-[var(--faint)]'
                }`}
                aria-label={`Go to slide ${idx + 1}`}
              />
            ))}
          </div>
        </div>

      </div>
    </section>
  );
};
