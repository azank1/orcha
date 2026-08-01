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
    <section id="proof" className="py-24 sm:py-32 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-6 sm:px-8 lg:px-12 space-y-12">

        <div className="space-y-4 max-w-3xl">
          <div className="text-sm text-[#6366f1] uppercase tracking-widest font-semibold">
            watch it work
          </div>
          <h2 className="font-display font-bold text-3xl sm:text-4xl tracking-tight text-[var(--text)]">
            Captured from the live sandbox.
          </h2>
          <p className="text-lg text-[var(--muted)] leading-relaxed">
            No mockups, no staged demos. Real runs, real verdicts.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
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
                <div className="absolute bottom-4 left-4 flex items-center h-10 w-10 group-hover:w-[160px] rounded-full bg-[#6366f1] overflow-hidden transition-all duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] shadow-lg">
                  <Play className="w-4 h-4 shrink-0 ml-[12px] text-white fill-current" />
                  <span className="ml-2 text-sm font-semibold uppercase tracking-wider text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                    watch
                  </span>
                </div>
              </div>
              <div className="p-5 space-y-2">
                <h3 className="font-display font-bold text-base text-[var(--text)]">
                  {card.title}
                </h3>
                <p className="text-sm text-[var(--muted)] leading-relaxed">
                  {card.caption}
                </p>
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
};
