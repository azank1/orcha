import React from 'react';
import { Play } from 'lucide-react';
import card1Run from '../assets/proof/card1-run.mp4';
import card2ComputerUse from '../assets/proof/card2-computer-use.mp4';
import card3Audit from '../assets/proof/card3-audit.mp4';

interface ProofCard {
  src: string;
  title: string;
  caption: string;
}

const PROOF_CARDS: ProofCard[] = [
  {
    src: card1Run,
    title: 'one goal, three protocols',
    caption: 'a portfolio + scrape + screenshot run completing live',
  },
  {
    src: card2ComputerUse,
    title: 'an agent driving a browser',
    caption: 'computer-use steps captured as screenshot artifacts',
  },
  {
    src: card3Audit,
    title: 'the run audit',
    caption: 'every run exports this evidence package',
  },
];

export const ProofCards: React.FC = () => {
  return (
    <section id="proof" className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
      <div className="space-y-2">
        <div className="font-mono text-xs text-[#6366f1] uppercase tracking-widest font-semibold">
          watch it work
        </div>
        <p className="text-[var(--muted)] text-xs sm:text-sm max-w-2xl leading-relaxed">
          Captured from the live sandbox — no mockups, no staged demos.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {PROOF_CARDS.map((card) => (
          <div
            key={card.title}
            className="group rounded-2xl border border-[var(--line)] bg-[var(--card-bg)] overflow-hidden shadow-sm transition-colors hover:border-[#6366f1]"
          >
            <div className="relative">
              <video
                src={card.src}
                autoPlay
                muted
                loop
                playsInline
                preload="metadata"
                className="w-full aspect-video object-cover bg-[#0b0b0e]"
              />
              {/* Expanding-circle reveal */}
              <div className="absolute bottom-3 left-3 flex items-center h-9 w-9 group-hover:w-[148px] rounded-full bg-[#6366f1] overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] shadow-md">
                <Play className="w-3.5 h-3.5 shrink-0 ml-[11px] text-white fill-current" />
                <span className="ml-2 font-mono text-[11px] font-semibold uppercase tracking-wider text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  watch
                </span>
              </div>
            </div>
            <div className="p-4 space-y-1">
              <h3 className="font-display font-bold text-sm text-[var(--text)]">
                {card.title}
              </h3>
              <p className="text-[11px] font-mono text-[var(--muted)] leading-relaxed">
                {card.caption}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
