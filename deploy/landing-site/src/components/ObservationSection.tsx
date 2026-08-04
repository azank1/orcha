import React, { useEffect, useState } from 'react';
import { motion } from 'motion/react';
import { ArrowRight } from 'lucide-react';
import { RunReplayTerminal } from './RunReplayTerminal';
import { observation } from '../data/siteConfig';
import { OPEN_SANDBOX_EVENT } from './SandboxDock';
import { SANDBOX_STATUS_URL } from '../config/sandbox';
import devRunClip from '../assets/proof/dev-run.mp4';

const useSandboxLive = (): boolean => {
  const [live, setLive] = useState(false);
  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await fetch(SANDBOX_STATUS_URL);
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data = await res.json();
        if (!cancelled) setLive(data.status === 'live');
      } catch {
        if (!cancelled) setLive(false);
      }
    };
    poll();
    const id = setInterval(poll, 60000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);
  return live;
};

export const ObservationSection: React.FC = () => {
  const live = useSandboxLive();

  return (
    <section id="observation" className="bg-[var(--bg)] text-[var(--fg)] border-b border-[var(--line-dark)]">
      <div className="max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 py-20 lg:py-28">
        <motion.div
          initial={{ opacity: 0, y: 18 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-wrap items-end justify-between gap-6 mb-12"
        >
          <div>
            <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted-dark)] mb-3">
              Sandbox
            </p>
            <h2 className="font-display text-[clamp(1.8rem,4vw,3rem)] leading-tight">
              {observation.sectionLabel}
            </h2>
          </div>
          {live && (
            <span className="text-[11px] text-[var(--muted-dark)] flex items-center gap-2">
              <span className="w-1.5 h-1.5 bg-white inline-block status-dot" />
              {observation.statusText}
            </span>
          )}
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-start">
          <motion.div
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <RunReplayTerminal />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 18 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-80px' }}
            transition={{ duration: 0.6, delay: 0.08, ease: [0.22, 1, 0.36, 1] }}
            className="border border-[var(--line-dark)] p-8 sm:p-10 flex flex-col gap-6"
          >
            <p className="text-sm text-[var(--muted-dark)] leading-relaxed max-w-md">
              Guest access, no signup. Pick a model or bring your own key, run a goal across
              MCP, A2A and computer-use, watch every step verify, download the audit.
            </p>
            <div>
              <button
                onClick={() => window.dispatchEvent(new CustomEvent(OPEN_SANDBOX_EVENT))}
                className="group inline-flex items-center gap-3 bg-white text-black text-xs font-semibold pl-5 pr-2 py-2 hover:bg-neutral-200 transition-colors"
              >
                <span className="block overflow-hidden h-[1.2em]">
                  <span className="flex flex-col leading-[1.2em] transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                    <span>Open the live sandbox</span>
                    <span>Open the live sandbox</span>
                  </span>
                </span>
                <span className="w-6 h-6 bg-black text-white flex items-center justify-center transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:rotate-[-45deg]">
                  <ArrowRight className="w-3.5 h-3.5" />
                </span>
              </button>
            </div>
            <div className="border border-[var(--line-dark)] overflow-hidden">
              <video
                src={devRunClip}
                autoPlay
                muted
                loop
                playsInline
                className="w-full block"
              />
              <p className="text-[10px] text-[var(--muted-dark)] px-3 py-2 border-t border-[var(--line-dark)]">
                captured from a live guest run · 2026-08-03
              </p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
