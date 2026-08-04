import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'motion/react';
import { Minus, X, TerminalSquare } from 'lucide-react';
import { SANDBOX_URL, SANDBOX_HOST } from '../config/sandbox';

type DockState = 'pill' | 'open';

export const OPEN_SANDBOX_EVENT = 'orcha:open-sandbox';

/**
 * Site-wide sandbox dock: a floating pill that expands into a windowed
 * live-sandbox frame. Stays mounted across routes; state survives navigation.
 */
export const SandboxDock: React.FC = () => {
  const [state, setState] = useState<DockState>('pill');

  useEffect(() => {
    const open = () => setState('open');
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setState('pill');
    };
    window.addEventListener(OPEN_SANDBOX_EVENT, open);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener(OPEN_SANDBOX_EVENT, open);
      window.removeEventListener('keydown', onKey);
    };
  }, []);

  return (
    <>
      {/* Floating pill */}
      <AnimatePresence>
        {state === 'pill' && (
          <motion.button
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 16 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
            onClick={() => setState('open')}
            className="fixed bottom-5 right-5 z-[70] flex items-center gap-2.5 bg-white text-black text-xs font-semibold pl-4 pr-5 py-3 hover:bg-neutral-200 transition-colors shadow-[0_8px_30px_rgba(0,0,0,0.5)]"
          >
            <TerminalSquare className="w-4 h-4" />
            Run a goal
            <span className="w-1.5 h-1.5 bg-black inline-block status-dot" />
          </motion.button>
        )}
      </AnimatePresence>

      {/* Expanded window */}
      <AnimatePresence>
        {state === 'open' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 z-[70] bg-black/70 backdrop-blur-sm flex items-center justify-center p-4 sm:p-8"
            onClick={() => setState('pill')}
          >
            <motion.div
              initial={{ scale: 0.96, y: 12, opacity: 0 }}
              animate={{ scale: 1, y: 0, opacity: 1 }}
              exit={{ scale: 0.96, y: 12, opacity: 0 }}
              transition={{ duration: 0.35, ease: [0.22, 1, 0.36, 1] }}
              className="w-[min(1100px,94vw)] h-[78vh] bg-black border border-white/25 flex flex-col shadow-[0_24px_80px_rgba(0,0,0,0.7)]"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between px-4 py-2.5 border-b border-[var(--line-dark)]">
                <span className="text-[11px] text-[var(--muted-dark)] uppercase tracking-[0.12em] flex items-center gap-2">
                  <span className="w-1.5 h-1.5 bg-white inline-block status-dot" />
                  {SANDBOX_HOST}
                </span>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setState('pill')}
                    className="p-1.5 text-[var(--muted-dark)] hover:text-white transition-colors"
                    aria-label="Minimize"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => setState('pill')}
                    className="p-1.5 text-[var(--muted-dark)] hover:text-white transition-colors"
                    aria-label="Close"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
              <iframe
                src={SANDBOX_URL}
                title="Orcha live sandbox"
                className="flex-1 w-full bg-[#050505]"
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
};
