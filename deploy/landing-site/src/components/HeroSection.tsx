import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { REAL_RUN_REPLAY, ReplayLine, CAPTURED_AT } from '../data/realRunReplay';
import { HeroShaderCanvas } from './HeroShaderCanvas';
import { Play, Copy, Check, ArrowRight, BookOpen } from 'lucide-react';

const replayLineColor = (cls?: ReplayLine['cls']): string => {
  if (cls === 'ok') return 'text-[var(--ok)]';
  if (cls === 'cm') return 'text-slate-500';
  return 'text-slate-300';
};

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.12, duration: 0.5, ease: [0.22, 1, 0.36, 1] },
  }),
};

interface HeroSectionProps {
  onLaunchSandbox?: () => void;
  onExploreDocs?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onLaunchSandbox, onExploreDocs }) => {
  const [displayedLines, setDisplayedLines] = useState<ReplayLine[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [currentCharIndex, setCurrentCharIndex] = useState(0);
  const [isTyping, setIsTyping] = useState(true);
  const [copiedGit, setCopiedGit] = useState(false);
  const [copiedUvx, setCopiedUvx] = useState(false);
  const [activeStep, setActiveStep] = useState<number | null>(null);

  useEffect(() => {
    if (currentLineIndex >= REAL_RUN_REPLAY.length) {
      setIsTyping(false);
      return;
    }

    const currentLine = REAL_RUN_REPLAY[currentLineIndex];

    if (currentCharIndex < currentLine.t.length) {
      const timer = setTimeout(() => {
        setCurrentCharIndex((prev) => prev + 1);
      }, 15 + Math.random() * 15);
      return () => clearTimeout(timer);
    } else {
      const delayTimer = setTimeout(() => {
        setDisplayedLines((prev) => [
          ...prev,
          { ...currentLine, t: currentLine.t }
        ]);
        setCurrentLineIndex((prev) => prev + 1);
        setCurrentCharIndex(0);
      }, currentLine.d || 300);
      return () => clearTimeout(delayTimer);
    }
  }, [currentLineIndex, currentCharIndex]);

  const handleCopyGit = () => {
    navigator.clipboard.writeText('git clone github.com/azank1/orcha');
    setCopiedGit(true);
    setTimeout(() => setCopiedGit(false), 2000);
  };

  const handleCopyUvx = () => {
    navigator.clipboard.writeText('uvx emerge init my-agent');
    setCopiedUvx(true);
    setTimeout(() => setCopiedUvx(false), 2000);
  };

  const pipelineSteps = [
    { id: 'goal', label: 'User Goal', desc: 'Natural language goal in', num: '01' },
    { id: 'gate', label: '3-Tier Gate', desc: 'Auth, DID & scope verification', num: '02' },
    { id: 'superagent', label: 'SuperAgent', desc: 'LLM + pgvector DAG planner', num: '03' },
    { id: 'dispatch', label: 'Protocol Dispatch', desc: 'MCP | A2A | Computer-use', num: '04' },
    { id: 'canvaskit', label: 'CanvasKit Output', desc: 'Live visual dashboard', num: '05' },
  ];

  return (
    <section id="hero" className="relative overflow-hidden pt-16 pb-24 sm:pt-24 sm:pb-32 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <HeroShaderCanvas />

      <div className="relative z-10 max-w-7xl mx-auto px-6 sm:px-8 lg:px-12">

        {/* Hero Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-16 items-center">

          {/* Left Text & CTA */}
          <div className="lg:col-span-5 space-y-8">

            <motion.h1
              custom={0}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="font-display font-bold text-5xl sm:text-6xl lg:text-7xl tracking-tight leading-[1.05] text-[var(--text)]"
            >
              One goal in. Verified multi-agent run out.
            </motion.h1>

            <motion.p
              custom={1}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="text-lg sm:text-xl text-[var(--muted)] leading-relaxed max-w-xl"
            >
              Open-source runtime for multi-protocol agent orchestration.
            </motion.p>

            {/* CTAs */}
            <motion.div
              custom={2}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="flex flex-wrap items-center gap-4 pt-4"
            >
              {onLaunchSandbox && (
                <button
                  onClick={onLaunchSandbox}
                  className="group font-sans text-sm font-semibold pl-6 pr-2 py-2.5 rounded-full bg-[#6366f1] text-white hover:bg-[#4f52c8] transition-all flex items-center gap-3 shadow-lg"
                >
                  <span className="block overflow-hidden h-[1.2em]">
                    <span className="flex flex-col leading-[1.2em] transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                      <span>Launch Sandbox</span>
                      <span>Launch Sandbox</span>
                    </span>
                  </span>
                  <span className="w-8 h-8 rounded-full bg-white flex items-center justify-center transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:rotate-[-45deg]">
                    <ArrowRight className="w-4 h-4 text-[#6366f1]" />
                  </span>
                </button>
              )}

              {onExploreDocs && (
                <button
                  onClick={onExploreDocs}
                  className="font-sans text-sm font-semibold px-6 py-2.5 rounded-full border border-[var(--line)] bg-[var(--card-bg)] text-[var(--text)] hover:border-[#6366f1] transition-all flex items-center gap-2"
                >
                  <BookOpen className="w-4 h-4" />
                  Documentation
                </button>
              )}
            </motion.div>

            {/* Quickstart */}
            <motion.div
              custom={3}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="pt-4 space-y-3"
            >
              <div
                onClick={handleCopyGit}
                className="inline-flex items-center gap-3 px-4 py-2.5 rounded-lg bg-[var(--card-bg)] border border-[var(--line)] hover:border-[#6366f1] cursor-pointer transition-all group"
              >
                <span className="text-[#6366f1] font-mono text-sm">$</span>
                <code className="text-sm text-[var(--text)] font-mono">git clone github.com/azank1/orcha</code>
                {copiedGit ? (
                  <Check className="w-4 h-4 text-[#6366f1]" />
                ) : (
                  <Copy className="w-4 h-4 text-[var(--faint)] group-hover:text-[var(--text)] transition-colors" />
                )}
              </div>

              <div
                onClick={handleCopyUvx}
                className="inline-flex items-center gap-3 px-4 py-2.5 rounded-lg bg-[var(--card-bg)] border border-[var(--line)] hover:border-[#6366f1] cursor-pointer transition-all group ml-0 sm:ml-3"
              >
                <span className="text-[var(--muted)] text-sm">Quickstart:</span>
                <code className="text-sm text-[var(--text)] font-mono">uvx emerge init my-agent</code>
                {copiedUvx ? (
                  <span className="text-xs text-[#6366f1] font-semibold">Copied</span>
                ) : (
                  <Copy className="w-4 h-4 text-[var(--faint)] group-hover:text-[var(--text)] transition-colors" />
                )}
              </div>
            </motion.div>

          </div>

          {/* Right Live Terminal Box */}
          <motion.div
            custom={2}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="lg:col-span-7"
          >
            <div className="bg-[#080C14] border border-[var(--line)] rounded-2xl overflow-hidden font-mono text-sm shadow-2xl">

              {/* Titlebar */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-[#0c0f17]">
                <div className="flex items-center gap-2 text-sm text-slate-300 font-semibold">
                  <span className="w-2 h-2 rounded-full bg-[#6366f1]"></span>
                  ~/orcha · runtime live
                </div>
                <div className="text-xs text-slate-400">v1.0-active</div>
              </div>

              {/* Terminal Screen Output */}
              <div className="p-5 sm:p-6 min-h-[280px] space-y-2 leading-relaxed bg-[#080C14]">
                {displayedLines.map((line, idx) => (
                  <div key={idx} className="flex items-start gap-2">
                    <span className={`${replayLineColor(line.cls)} font-mono leading-relaxed`}>{line.t}</span>
                  </div>
                ))}

                {isTyping && currentLineIndex < REAL_RUN_REPLAY.length && (
                  <div className="flex items-start gap-2">
                    <span className={`${replayLineColor(REAL_RUN_REPLAY[currentLineIndex].cls)} font-mono`}>
                      {REAL_RUN_REPLAY[currentLineIndex].t.slice(0, currentCharIndex)}
                    </span>
                    <span className="w-2 h-4 bg-[#6366f1] inline-block animate-pulse"></span>
                  </div>
                )}
              </div>

              <div className="px-5 py-2.5 border-t border-slate-800 bg-[#0c0f17] text-xs text-slate-400 flex justify-between items-center">
                <span>Handlers: MCP · A2A · Computer-Use</span>
                <span className="text-slate-400">verified</span>
              </div>

            </div>
            <p className="mt-3 text-xs text-[var(--faint)]">
              captured from a live run · {CAPTURED_AT}
            </p>
          </motion.div>

        </div>

        {/* Execution Flow */}
        <motion.div
          custom={4}
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          className="mt-20 sm:mt-24"
        >
          <div className="flex items-center justify-between mb-6">
            <span className="text-sm font-semibold uppercase tracking-wider text-[var(--text)]">
              Execution Flow
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            {pipelineSteps.map((step, index) => (
              <div
                key={step.id}
                onMouseEnter={() => setActiveStep(index)}
                onMouseLeave={() => setActiveStep(null)}
                className={`p-5 rounded-xl border transition-all cursor-pointer relative group ${
                  activeStep === index
                    ? 'border-[#6366f1] bg-[#6366f1]/10'
                    : 'border-[var(--line)] bg-[var(--card-bg)] hover:border-[var(--faint)]'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <span className="w-6 h-6 rounded-full bg-[#6366f1] text-white flex items-center justify-center text-xs font-bold">
                    {step.num}
                  </span>
                  {index < pipelineSteps.length - 1 && (
                    <ArrowRight className="w-4 h-4 text-[#6366f1] hidden md:block opacity-40 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>

                <div className="font-display font-bold text-sm text-[var(--text)] mb-1 group-hover:text-[#6366f1] transition-colors">
                  {step.label}
                </div>

                <p className="text-xs text-[var(--muted)] leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </motion.div>

      </div>
    </section>
  );
};
