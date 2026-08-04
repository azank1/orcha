import React from 'react';
import { motion } from 'motion/react';
import { manifesto } from '../data/siteConfig';
import runClip from '../assets/proof/card1-run.mp4';

export const Manifesto: React.FC = () => {
  return (
    <section className="bg-[var(--paper)] text-[var(--ink)] border-b border-black/10">
      <div className="max-w-[1440px] mx-auto grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-16 px-6 sm:px-10 lg:px-14 py-20 lg:py-28 items-center">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="border border-black/15 bg-black"
        >
          <video
            src={runClip}
            autoPlay
            muted
            loop
            playsInline
            className="w-full aspect-video object-cover opacity-90"
          />
        </motion.div>
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: '-80px' }}
          transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
        >
          <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted-light)] mb-6">
            Manifesto
          </p>
          <p className="text-sm sm:text-[15px] leading-[1.85] text-[var(--ink)] max-w-xl">
            {manifesto.text}
          </p>
        </motion.div>
      </div>
    </section>
  );
};
