import React from 'react';
import { motion } from 'motion/react';
import { PluginCard, ContributeCard } from './PluginCard';
import { BridgeArcs } from './BridgeArcs';
import { bridges } from '../data/siteConfig';

export const PluginDirectory: React.FC = () => {
  return (
    <section id="plugins" className="relative bg-[var(--paper)] text-[var(--ink)] border-b border-black/10 overflow-hidden">
      <BridgeArcs className="absolute inset-0 w-full h-full pointer-events-none" />
      <div className="relative max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 py-20 lg:py-28">
        <div className="mb-12">
          <h2 className="font-display text-[clamp(1.8rem,4vw,3rem)] leading-tight">
            Bridges
          </h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6 lg:gap-7">
          {bridges.map((b, i) => (
            <motion.div
              key={b.slug}
              initial={{ opacity: 0, y: 16 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-60px' }}
              transition={{ duration: 0.5, delay: i * 0.07, ease: [0.22, 1, 0.36, 1] }}
            >
              <PluginCard item={b} index={i} />
            </motion.div>
          ))}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: '-60px' }}
            transition={{ duration: 0.5, delay: bridges.length * 0.07, ease: [0.22, 1, 0.36, 1] }}
          >
            <ContributeCard />
          </motion.div>
        </div>
      </div>
    </section>
  );
};
