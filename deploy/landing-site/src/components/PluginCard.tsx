import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowUpRight } from 'lucide-react';
import { ProtocolLogo } from './ProtocolLogo';
import { BridgeItem } from '../data/siteConfig';

// Demo clips — real captures from the live sandbox. Each maps to a file in
// src/assets/proof/; fall back to the original multi-protocol captures.
import pluginMcp from '../assets/proof/plugin-mcp.mp4';
import pluginA2a from '../assets/proof/plugin-a2a.mp4';
import pluginComputerUse from '../assets/proof/plugin-computer-use.mp4';
import pluginCanvaskit from '../assets/proof/plugin-canvaskit.mp4';

const CLIPS: Record<string, string> = {
  'plugin-mcp': pluginMcp,
  'plugin-a2a': pluginA2a,
  'plugin-computer-use': pluginComputerUse,
  'plugin-canvaskit': pluginCanvaskit,
};

interface Props {
  item: BridgeItem;
  index: number;
}

/**
 * Flip card: front = protocol mark + name, back = real demo capture.
 * Hover flips on desktop, tap flips on touch.
 */
export const PluginCard: React.FC<Props> = ({ item, index }) => {
  const [flipped, setFlipped] = useState(false);

  return (
    <div
      className="group [perspective:1200px]"
      onMouseLeave={() => setFlipped(false)}
    >
      <div
        className={`relative aspect-[3/4] transition-transform duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] [transform-style:preserve-3d] ${
          flipped ? '[transform:rotateY(180deg)]' : 'group-hover:[transform:rotateY(180deg)]'
        }`}
      >
        {/* Front — mark + name */}
        <button
          onClick={() => setFlipped(true)}
          className="absolute inset-0 bg-black border border-[var(--line-dark)] hover:border-white/40 transition-colors flex flex-col items-center justify-center gap-6 [backface-visibility:hidden]"
          aria-label={`${item.name} — flip to watch`}
        >
          <span className="absolute top-3 left-3 text-[10px] tracking-[0.14em] text-white/40">
            {item.code}
          </span>
          <ProtocolLogo logo={item.logo} className="w-14 h-14 text-white/85" />
          <span className="font-display text-lg text-white">{item.name}</span>
        </button>

        {/* Back — demo capture */}
        <div className="absolute inset-0 bg-black border border-white/25 [backface-visibility:hidden] [transform:rotateY(180deg)] overflow-hidden">
          <video
            src={CLIPS[item.clip]}
            autoPlay
            muted
            loop
            playsInline
            className="w-full h-full object-cover opacity-90"
          />
          <Link
            to={`/plugins/${item.slug}`}
            onClick={(e) => e.stopPropagation()}
            className="absolute bottom-3 left-3 inline-flex items-center gap-1.5 bg-black/80 border border-white/25 px-3 py-1.5 text-[10px] uppercase tracking-[0.12em] text-white hover:bg-white hover:text-black transition-colors"
          >
            {item.name}
            <ArrowUpRight className="w-3 h-3" />
          </Link>
        </div>
      </div>
      <p className="mt-3 text-[11px] text-[var(--muted-light)] leading-relaxed px-0.5">
        {item.status}
      </p>
      <span className="sr-only">{index}</span>
    </div>
  );
};

/** Fifth card — contribution. Same container, no clip. */
export const ContributeCard: React.FC = () => {
  const [flipped, setFlipped] = useState(false);
  return (
    <div className="group [perspective:1200px]" onMouseLeave={() => setFlipped(false)}>
      <div
        className={`relative aspect-[3/4] transition-transform duration-700 ease-[cubic-bezier(0.22,1,0.36,1)] [transform-style:preserve-3d] ${
          flipped ? '[transform:rotateY(180deg)]' : 'group-hover:[transform:rotateY(180deg)]'
        }`}
      >
        <button
          onClick={() => setFlipped(true)}
          className="absolute inset-0 bg-black border border-dashed border-white/25 hover:border-white/50 transition-colors flex flex-col items-center justify-center gap-5 [backface-visibility:hidden]"
          aria-label="Build your own plugin"
        >
          <span className="absolute top-3 left-3 text-[10px] tracking-[0.14em] text-white/40">05</span>
          <span className="font-display text-5xl text-white/70">+</span>
          <span className="font-display text-lg text-white">Build your own</span>
        </button>

        <div className="absolute inset-0 bg-black border border-white/25 [backface-visibility:hidden] [transform:rotateY(180deg)] p-5 flex flex-col justify-between">
          <p className="text-[11px] text-[var(--muted-dark)] leading-relaxed">
            A new protocol is a handler subclass and a manifest entry — under fifty lines of Python.
            The dispatch table is open.
          </p>
          <div className="flex flex-col gap-2">
            <Link
              to="/docs"
              className="inline-flex items-center justify-center gap-1.5 border border-white/25 px-3 py-2 text-[10px] uppercase tracking-[0.12em] text-white hover:bg-white hover:text-black transition-colors"
            >
              Read the docs
            </Link>
            <Link
              to="/contributing"
              className="inline-flex items-center justify-center gap-1.5 bg-white text-black px-3 py-2 text-[10px] uppercase tracking-[0.12em] font-semibold hover:bg-neutral-200 transition-colors"
            >
              Contribute a plugin
              <ArrowUpRight className="w-3 h-3" />
            </Link>
          </div>
        </div>
      </div>
      <p className="mt-3 text-[11px] text-[var(--muted-light)] leading-relaxed px-0.5">
        The dispatch table is open — ship the next bridge.
      </p>
    </div>
  );
};
