import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ChevronLeft, ChevronRight, Layout, CheckCircle2, ArrowUpRight } from 'lucide-react';

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

const iconClass = 'w-5 h-5';

const McpLogo: React.FC = () => (
  <svg fill="currentColor" role="img" viewBox="0 0 24 24" className={iconClass} aria-label="Model Context Protocol">
    <path d="M13.85 0a4.16 4.16 0 0 0-2.95 1.217L1.456 10.66a.835.835 0 0 0 0 1.18.835.835 0 0 0 1.18 0l9.442-9.442a2.49 2.49 0 0 1 3.541 0 2.49 2.49 0 0 1 0 3.541L8.59 12.97l-.1.1a.835.835 0 0 0 0 1.18.835.835 0 0 0 1.18 0l.1-.098 7.03-7.034a2.49 2.49 0 0 1 3.542 0l.049.05a2.49 2.49 0 0 1 0 3.54l-8.54 8.54a1.96 1.96 0 0 0 0 2.755l1.753 1.753a.835.835 0 0 0 1.18 0 .835.835 0 0 0 0-1.18l-1.753-1.753a.266.266 0 0 1 0-.394l8.54-8.54a4.185 4.185 0 0 0 0-5.9l-.05-.05a4.16 4.16 0 0 0-2.95-1.218c-.2 0-.401.02-.6.048a4.17 4.17 0 0 0-1.17-3.552A4.16 4.16 0 0 0 13.85 0m0 3.333a.84.84 0 0 0-.59.245L6.275 10.56a4.186 4.186 0 0 0 0 5.902 4.186 4.186 0 0 0 5.902 0L19.16 9.48a.835.835 0 0 0 0-1.18.835.835 0 0 0-1.18 0l-6.985 6.984a2.49 2.49 0 0 1-3.54 0 2.49 2.49 0 0 1 0-3.54l6.983-6.985a.835.835 0 0 0 0-1.18.84.84 0 0 0-.59-.245" />
  </svg>
);

const A2aLogo: React.FC = () => (
  <svg viewBox="0 0 860 860" fill="none" className={iconClass} aria-label="Agent2Agent">
    <circle cx="544" cy="307" r="27" fill="currentColor" />
    <circle cx="154" cy="307" r="27" fill="currentColor" />
    <circle cx="706" cy="307" r="27" fill="currentColor" />
    <circle cx="316" cy="307" r="27" fill="currentColor" />
    <path
      d="M336.5 191.003H162C97.6588 191.003 45.5 243.162 45.5 307.503C45.5 371.844 97.6442 424.003 161.985 424.003C206.551 424.003 256.288 424.003 296.5 424.003C487.5 424.003 374 191.005 569 191.001C613.886 191 658.966 191 698.025 191C762.366 191.001 814.5 243.16 814.5 307.501C814.5 371.843 762.34 424.003 697.998 424.003H523.5"
      stroke="currentColor"
      strokeWidth="48"
      strokeLinecap="round"
    />
    <path
      d="M256 510.002C270.359 510.002 282 521.643 282 536.002C282 550.361 270.359 562.002 256 562.002H148C133.641 562.002 122 550.361 122 536.002C122 521.643 133.641 510.002 148 510.002H256ZM712 510.002C726.359 510.002 738 521.643 738 536.002C738 550.361 726.359 562.002 712 562.002H360C345.641 562.002 334 550.361 334 536.002C334 521.643 345.641 510.002 360 510.002H712Z"
      fill="currentColor"
    />
    <path
      d="M444 628.002C458.359 628.002 470 639.643 470 654.002C470 668.361 458.359 680.002 444 680.002H100C85.6406 680.002 74 668.361 74 654.002C74 639.643 85.6406 628.002 100 628.002H444ZM548 628.002C562.359 628.002 574 639.643 574 654.002C574 668.361 562.359 680.002 548 680.002C533.641 680.002 522 668.361 522 654.002C522 639.643 533.641 628.002 548 628.002ZM760 628.002C774.359 628.002 786 639.643 786 654.002C786 668.361 774.359 680.002 760 680.002H652C637.641 680.002 626 668.361 626 654.002C626 639.643 637.641 628.002 652 628.002H760Z"
      fill="currentColor"
    />
  </svg>
);

const LangChainLogo: React.FC = () => (
  <svg fill="currentColor" role="img" viewBox="0 0 24 24" className={iconClass} aria-label="LangChain">
    <path d="M13.796 0a6.93 6.93 0 0 0-4.91 2.019L5.451 5.455l3.273 3.27 3.432-3.432a2.284 2.284 0 0 1 3.277 0 2.28 2.28 0 0 1 0 3.275L12 12.001l3.273 3.273 3.433-3.435c2.692-2.692 2.692-7.127 0-9.82A6.92 6.92 0 0 0 13.796 0m-5.07 8.728-3.433 3.434c-2.692 2.693-2.692 7.126 0 9.819A6.92 6.92 0 0 0 10.203 24a6.93 6.93 0 0 0 4.911-2.02l3.432-3.432-3.271-3.272-3.433 3.433a2.284 2.284 0 0 1-3.277 0 2.28 2.28 0 0 1 0-3.276L12 12z" />
  </svg>
);

// No official mark exists for computer-use — hand-drawn monitor + cursor,
// same stroke style as the lucide icons used elsewhere on the page.
const ComputerUseLogo: React.FC = () => (
  <svg
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={iconClass}
    aria-label="Computer use"
  >
    <rect x="2" y="3" width="20" height="14" rx="2" />
    <line x1="8" y1="21" x2="16" y2="21" />
    <line x1="12" y1="17" x2="12" y2="21" />
    <path d="m9.5 6.5 4.95 4.95-2.83.35-1.42 2.48z" fill="currentColor" stroke="none" />
  </svg>
);

const PlusLogo: React.FC = () => (
  <span className="flex items-center justify-center w-7 h-7 rounded-md border border-dashed border-[var(--faint)] text-[var(--muted)] font-mono text-sm leading-none">
    +
  </span>
);

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
    <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[var(--line)] pb-4">
          <div>
            <div className="font-mono text-xs text-[#6366f1] font-bold uppercase tracking-wider flex items-center gap-2">
              <Layout className="w-3.5 h-3.5" />
              Protocol Architecture Showcase
            </div>
            <h3 className="font-display font-bold text-xl sm:text-2xl text-[var(--text)]">
              Multi-Agent Protocol Capabilities
            </h3>
            <p className="text-xs sm:text-sm text-[var(--muted)] mt-1">
              the first two bridges are MCP and A2A — the harness doesn't care what ships next.
            </p>
          </div>

          {/* Controls */}
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs text-[var(--faint)] mr-2 hidden sm:inline">
              0{activeSlideIndex + 1} / 0{SLIDES.length}
            </span>
            <button
              onClick={() => setActiveSlideIndex((prev) => (prev - 1 + SLIDES.length) % SLIDES.length)}
              className="p-2 rounded-lg border border-[var(--line)] bg-[var(--card-bg)] hover:border-[#6366f1] text-[var(--text)] transition-colors"
              aria-label="Previous Slide"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              onClick={() => setActiveSlideIndex((prev) => (prev + 1) % SLIDES.length)}
              className="p-2 rounded-lg border border-[var(--line)] bg-[var(--card-bg)] hover:border-[#6366f1] text-[var(--text)] transition-colors"
              aria-label="Next Slide"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Carousel Slide Card */}
        <div
          onMouseEnter={() => setIsPaused(true)}
          onMouseLeave={() => setIsPaused(false)}
          className={`relative min-h-[320px] rounded-2xl border bg-[var(--card-bg)] p-6 sm:p-8 shadow-sm overflow-hidden flex flex-col justify-between ${
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
              className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-center"
            >
              {/* Left Content */}
              <div className="lg:col-span-5 space-y-4">
                <div
                  className={`inline-flex items-center gap-2 font-mono text-xs font-semibold px-2.5 py-1 rounded-md ${
                    currentSlide.invitation
                      ? 'border border-dashed border-[var(--line)] text-[var(--muted)]'
                      : 'uppercase bg-[#6366f1]/10 text-[#6366f1] border border-[#6366f1]/30'
                  }`}
                >
                  <span className={currentSlide.invitation ? '' : 'text-[#6366f1]'}>{currentSlide.icon}</span>
                  <span>{currentSlide.badge}</span>
                </div>

                <div className="space-y-1">
                  <h4
                    className={`font-display font-bold text-xl sm:text-2xl ${
                      currentSlide.invitation ? 'text-[var(--muted)]' : 'text-[var(--text)]'
                    }`}
                  >
                    {currentSlide.title}
                  </h4>
                  <p className="text-xs sm:text-sm text-[var(--muted)] leading-relaxed">
                    {currentSlide.subtitle}
                  </p>
                </div>

                {currentSlide.highlights.length > 0 && (
                  <ul className="space-y-2 pt-2 font-mono text-xs">
                    {currentSlide.highlights.map((h, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-[var(--text)]">
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#6366f1] flex-shrink-0" />
                        <span>{h}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Right Code Block / Invitation CTAs */}
              {currentSlide.codeSnippet ? (
                <div className="lg:col-span-7 rounded-xl border border-slate-800 bg-[#070A10] p-4 shadow-inner overflow-x-auto">
                  <div className="flex items-center justify-between font-mono text-[11px] text-slate-400 border-b border-slate-800 pb-2 mb-3">
                    <span>{currentSlide.codeLabel}</span>
                    <span className="text-[#6366f1]">Python 3.11</span>
                  </div>
                  <pre className="font-mono text-xs text-slate-200 leading-relaxed custom-scrollbar">
                    <code>{currentSlide.codeSnippet}</code>
                  </pre>
                </div>
              ) : (
                <div className="lg:col-span-7 rounded-xl border border-dashed border-[var(--line)] p-4 sm:p-6 space-y-3">
                  {currentSlide.ctas?.map((cta) => (
                    <a
                      key={cta.href}
                      href={cta.href}
                      target="_blank"
                      rel="noreferrer"
                      className="flex items-center justify-between gap-2 font-mono text-xs text-[var(--muted)] hover:text-[#6366f1] border border-dashed border-[var(--line)] hover:border-[#6366f1] rounded-lg px-4 py-3 transition-colors"
                    >
                      <span>{cta.label}</span>
                      <ArrowUpRight className="w-3.5 h-3.5 flex-shrink-0" />
                    </a>
                  ))}
                </div>
              )}
            </motion.div>
          </AnimatePresence>

          {/* Dots Indicator */}
          <div className="flex items-center justify-center gap-2 pt-6">
            {SLIDES.map((slide, idx) => (
              <button
                key={slide.id}
                onClick={() => setActiveSlideIndex(idx)}
                className={`h-2 rounded-full transition-all ${
                  idx === activeSlideIndex
                    ? 'w-8 bg-[#6366f1]'
                    : 'w-2 bg-[var(--line)] hover:bg-[var(--faint)]'
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
