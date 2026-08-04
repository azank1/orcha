import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'motion/react';
import { ArrowRight, BookOpen, Copy, Check } from 'lucide-react';
import { AsciiMoonField } from './AsciiMoonField';
import { TypedWord } from './TypedWord';
import { hero } from '../data/siteConfig';
import { SANDBOX_URL } from '../config/sandbox';

const fadeUp = {
  hidden: { opacity: 0, y: 18 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.55, ease: [0.22, 1, 0.36, 1] },
  }),
};

const CopyChip: React.FC<{ text: string; label?: string }> = ({ text, label }) => {
  const [copied, setCopied] = useState(false);
  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };
  return (
    <button
      onClick={copy}
      className="inline-flex items-center gap-3 border border-[var(--line-dark)] px-3 py-2 text-xs text-[var(--muted-dark)] hover:text-[var(--fg)] hover:border-white/40 transition-colors"
    >
      {label && <span className="text-[var(--faint)]">{label}</span>}
      <code>{text}</code>
      {copied ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5 opacity-50" />}
    </button>
  );
};

export const SplitHero: React.FC = () => {
  return (
    <section className="relative min-h-[92vh] bg-[var(--bg)] text-[var(--fg)] border-b border-[var(--line-dark)] overflow-hidden">
      <div className="max-w-[1440px] mx-auto grid grid-cols-1 lg:grid-cols-[40%_60%] min-h-[92vh]">
        {/* Left editorial panel */}
        <div className="flex flex-col justify-center px-6 sm:px-10 lg:px-14 py-16 lg:py-0 gap-7">
          <motion.h1
            custom={0}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="font-display text-[clamp(2.6rem,6vw,4.6rem)] leading-[1.04] tracking-tight"
          >
            {hero.titleLines.map((line, i) => (
              <span key={i} className="block">
                {line}
              </span>
            ))}
          </motion.h1>

          <motion.div custom={2} initial="hidden" animate="visible" variants={fadeUp} className="text-sm">
            <span className="text-[var(--faint)] mr-2">&gt;</span>
            <TypedWord className="text-[var(--muted-dark)]" />
          </motion.div>

          <motion.p
            custom={3}
            initial="hidden"
            animate="visible"
            variants={fadeUp}
            className="text-sm text-[var(--muted-dark)] leading-relaxed max-w-md"
          >
            {hero.leadText}
          </motion.p>

          <motion.div custom={4} initial="hidden" animate="visible" variants={fadeUp} className="flex flex-wrap items-center gap-3 pt-1">
            <a
              href={SANDBOX_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center gap-3 bg-white text-black text-xs font-semibold pl-5 pr-2 py-2 hover:bg-neutral-200 transition-colors"
            >
              <span className="block overflow-hidden h-[1.2em]">
                <span className="flex flex-col leading-[1.2em] transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                  <span>Launch the sandbox</span>
                  <span>Launch the sandbox</span>
                </span>
              </span>
              <span className="w-6 h-6 bg-black text-white flex items-center justify-center transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:rotate-[-45deg]">
                <ArrowRight className="w-3.5 h-3.5" />
              </span>
            </a>
            <Link
              to="/docs"
              className="inline-flex items-center gap-2 border border-[var(--line-dark)] text-xs px-5 py-2.5 text-[var(--muted-dark)] hover:text-[var(--fg)] hover:border-white/40 transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" />
              Documentation
            </Link>
          </motion.div>

          <motion.div custom={5} initial="hidden" animate="visible" variants={fadeUp} className="pt-3">
            <CopyChip text="git clone github.com/solvent-metaorcha/orcha" label="$" />
          </motion.div>
        </div>

        {/* Right ASCII moon field */}
        <div className="relative border-t lg:border-t-0 lg:border-l border-[var(--line-dark)] min-h-[420px]">
          <AsciiMoonField className="absolute inset-0 w-full h-full" />
          <span className="absolute bottom-4 right-5 text-[10px] uppercase tracking-[0.14em] text-[var(--faint)]">
            fig. 01 — the runtime
          </span>
        </div>
      </div>
    </section>
  );
};
