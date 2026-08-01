import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { REAL_RUN_REPLAY, ReplayLine, CAPTURED_AT } from '../data/realRunReplay';
import { HeroShaderCanvas } from './HeroShaderCanvas';
import { GoalDecomposition } from './GoalDecomposition';
import { McpLogo, A2aLogo, ComputerUseLogo } from './ProtocolIcons';
import { Play, Copy, Check, ShieldCheck, Layers, ArrowRight, BookOpen } from 'lucide-react';

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
    <section id="hero" className="relative overflow-hidden pt-8 pb-16 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <HeroShaderCanvas />

      {/* Edge anchors */}
      <div className="absolute bottom-4 left-4 sm:left-8 font-mono text-[10px] text-[var(--faint)] z-20">
        apache 2.0
      </div>
      <div className="absolute bottom-4 right-4 sm:right-8 font-mono text-[10px] text-[var(--faint)] z-20">
        PAYMENT_MODE=mock
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">

        {/* Hero Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

          {/* Left Text & CTA */}
          <div className="lg:col-span-6 space-y-5">

            <motion.h1
              custom={0}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="font-display font-bold text-3xl sm:text-4xl lg:text-5xl tracking-tight leading-[1.12] text-[var(--text)]"
            >
              One goal in.{' '}
              <span className="inline-flex items-center gap-1.5 align-middle">
                <McpLogo className="w-6 h-6 sm:w-8 sm:h-8 text-[#6366f1]" />
                <A2aLogo className="w-6 h-6 sm:w-8 sm:h-8 text-[#3ecf8e]" />
                <ComputerUseLogo className="w-6 h-6 sm:w-8 sm:h-8 text-[#e5c07b]" />
              </span>{' '}
              Verified multi-agent run out.
            </motion.h1>

            <motion.p
              custom={1}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="font-mono text-xs text-[var(--muted)]"
            >
              plan → route → verify → render · MCP · A2A · COMPUTER_USE · apache 2.0
            </motion.p>

            {/* Interactive Goal Decomposition */}
            <motion.div
              custom={2}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="pt-2"
            >
              <GoalDecomposition />
            </motion.div>

            {/* CTAs */}
            <motion.div
              custom={3}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="space-y-3 pt-1"
            >

              <div className="flex flex-wrap items-center gap-3">
                {onExploreDocs && (
                  <button
                    onClick={onExploreDocs}
                    className="font-mono text-xs font-semibold px-4 py-3 rounded-md bg-[#6366f1] text-white hover:bg-[#4f52c8] transition-all flex items-center gap-2 shadow-md"
                  >
                    <BookOpen className="w-3.5 h-3.5" />
                    Explore System Docs
                  </button>
                )}

                {onLaunchSandbox && (
                  <button
                    onClick={onLaunchSandbox}
                    className="group font-mono text-xs font-semibold px-4 py-3 rounded-md bg-[var(--card-bg)] border border-[var(--line)] hover:border-[#6366f1] text-[var(--text)] transition-all flex items-center gap-2 shadow-sm"
                  >
                    <Play className="w-3.5 h-3.5 fill-current text-[#6366f1]" />
                    <span className="block overflow-hidden h-[1em]">
                      <span className="flex flex-col leading-[1em] transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                        <span>Launch Sandbox</span>
                        <span>Launch Sandbox</span>
                      </span>
                    </span>
                  </button>
                )}

                <button
                  onClick={handleCopyGit}
                  className="font-mono text-xs font-semibold px-4 py-3 rounded-md bg-[var(--card-bg)] border border-[var(--line)] hover:border-[#6366f1] text-[var(--text)] transition-all flex items-center gap-3 group shadow-sm"
                >
                  <span className="text-[#6366f1]">$</span>
                  <code>git clone github.com/azank1/orcha</code>
                  {copiedGit ? (
                    <Check className="w-4 h-4 text-[#6366f1] ml-1" />
                  ) : (
                    <Copy className="w-4 h-4 text-[var(--faint)] group-hover:text-[var(--text)] ml-1 transition-colors" />
                  )}
                </button>
              </div>

              {/* Quick Terminal Box */}
              <div className="pt-1">
                <div
                  onClick={handleCopyUvx}
                  className="inline-flex items-center gap-3 px-3.5 py-2 rounded-lg bg-[var(--card-bg)] border border-[var(--line)] hover:border-[#6366f1] cursor-pointer transition-all text-xs font-mono group shadow-sm"
                >
                  <span className="text-[var(--muted)]">Quickstart:</span>
                  <code className="text-[var(--text)]">uvx emerge init my-agent</code>
                  {copiedUvx ? (
                    <span className="text-[11px] text-[#6366f1] font-semibold">Copied</span>
                  ) : (
                    <Copy className="w-3.5 h-3.5 text-[var(--faint)] group-hover:text-[var(--text)]" />
                  )}
                </div>
              </div>

            </motion.div>

            {/* Quick feature tags */}
            <motion.div
              custom={4}
              initial="hidden"
              animate="visible"
              variants={fadeUp}
              className="pt-2 flex flex-wrap items-center gap-6 text-xs font-mono text-[var(--muted)]"
            >
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#6366f1]" /> PAYMENT_MODE=mock
              </span>
              <span className="flex items-center gap-1.5">
                <Layers className="w-4 h-4 text-[#6366f1]" /> LangGraph SuperAgent
              </span>
            </motion.div>

          </div>

          {/* Right Live Terminal Box */}
          <motion.div
            custom={2}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="lg:col-span-6"
          >
            <div className="bg-[#080C14] border border-[var(--line)] rounded-xl overflow-hidden font-mono text-xs shadow-xl">

              {/* Titlebar */}
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-slate-800 bg-[#0c0f17]">
                <div className="flex items-center gap-2 text-xs text-slate-300 font-semibold">
                  <span className="w-2 h-2 rounded-full bg-[#6366f1]"></span>
                  ~/orcha · runtime live
                </div>
                <div className="text-[11px] text-slate-400">v1.0-active</div>
              </div>

              {/* Terminal Screen Output */}
              <div className="p-4 sm:p-5 min-h-[240px] space-y-2 leading-relaxed bg-[#080C14]">
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

              <div className="px-4 py-2 border-t border-slate-800 bg-[#0c0f17] text-[11px] text-slate-400 flex justify-between items-center">
                <span>Handlers: MCP · A2A · Computer-Use</span>
                <span className="text-slate-400">verified</span>
              </div>

            </div>
            <p className="mt-2 font-mono text-[11px] text-[var(--faint)]">
              captured from a live run · {CAPTURED_AT}
            </p>
          </motion.div>

        </div>

        {/* Interactive Visual Pipeline */}
        <motion.div
          custom={5}
          initial="hidden"
          animate="visible"
          variants={fadeUp}
          className="bg-[var(--card-bg)] border border-[var(--line)] rounded-xl p-5 space-y-3 shadow-sm transition-colors"
        >
          <div className="flex items-center justify-between font-mono text-xs">
            <span className="text-[var(--text)] font-semibold uppercase tracking-wider">
              Execution Flow Architecture
            </span>

          </div>

          <div className="grid grid-cols-1 md:grid-cols-5 gap-3 pt-1">
            {pipelineSteps.map((step, index) => (
              <div
                key={step.id}
                onMouseEnter={() => setActiveStep(index)}
                onMouseLeave={() => setActiveStep(null)}
                className={`p-3.5 rounded-lg border transition-all cursor-pointer relative group ${
                  activeStep === index
                    ? 'border-[#6366f1] bg-[#6366f1]/10'
                    : 'border-[var(--line)] bg-[var(--bg)] hover:border-[var(--faint)]'
                }`}
              >
                <div className="flex items-center justify-between font-mono text-[10px] text-[var(--faint)] mb-1">
                  <span className="w-5 h-5 rounded-full bg-[#6366f1] text-white flex items-center justify-center text-[10px] font-bold">
                    {step.num}
                  </span>
                  {index < pipelineSteps.length - 1 && (
                    <ArrowRight className="w-3 h-3 text-[#6366f1] hidden md:block opacity-40 group-hover:opacity-100 transition-opacity" />
                  )}
                </div>

                <div className="font-display font-bold text-xs text-[var(--text)] mb-1 group-hover:text-[#6366f1] transition-colors">
                  {step.label}
                </div>

                <p className="text-[11px] text-[var(--muted)] leading-tight">
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
