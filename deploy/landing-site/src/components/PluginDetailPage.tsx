import React, { useEffect } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowUpRight } from 'lucide-react';
import { ProtocolLogo } from './ProtocolLogo';
import { CanvasKitShowcase } from './CanvasKitShowcase';
import { bridges } from '../data/siteConfig';

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

export const PluginDetailPage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const item = bridges.find((b) => b.slug === slug);

  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [slug]);

  if (!item) {
    return (
      <div className="bg-[var(--paper)] text-[var(--ink)] min-h-[60vh] flex flex-col items-center justify-center gap-4">
        <p className="text-sm text-[var(--muted-light)]">Plugin not found in the registry.</p>
        <Link to="/" className="text-xs underline underline-offset-4">
          Return to the runtime
        </Link>
      </div>
    );
  }

  return (
    <div className="bg-[var(--paper)] text-[var(--ink)]">
      <article className="max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 py-14 lg:py-20">
        <Link
          to="/#plugins"
          className="inline-flex items-center gap-2 text-[11px] uppercase tracking-[0.14em] text-[var(--muted-light)] hover:text-[var(--ink)] transition-colors mb-12"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          All plugins
        </Link>

        <div className="grid grid-cols-1 lg:grid-cols-[38%_1fr] gap-10 lg:gap-16">
          <div>
            <div className="sticky top-24 space-y-3">
              <div className="relative aspect-[3/4] bg-black overflow-hidden">
                <video
                  src={CLIPS[item.clip]}
                  autoPlay
                  muted
                  loop
                  playsInline
                  className="absolute inset-0 w-full h-full object-cover"
                />
                <span className="absolute top-3 left-3 text-[10px] uppercase tracking-[0.14em] text-white/70 bg-black/60 px-2 py-1">
                  {item.code} · live capture
                </span>
              </div>
              <div className="flex items-center gap-3 text-[var(--muted-light)]">
                <ProtocolLogo logo={item.logo} className="w-6 h-6" />
                <span className="text-[11px] uppercase tracking-[0.12em]">{item.name}</span>
              </div>
            </div>
          </div>

          <div>
            <h1 className="font-display text-[clamp(1.9rem,4vw,3.2rem)] leading-[1.1] mb-8">
              {item.article.title}
            </h1>

            <dl className="border-y border-black/10 divide-y divide-black/10 text-xs mb-10">
              <div className="grid grid-cols-[110px_1fr] gap-4 py-3">
                <dt className="text-[var(--muted-light)] uppercase tracking-[0.1em] text-[10px] pt-0.5">Handler</dt>
                <dd className="font-medium break-all">{item.handler}</dd>
              </div>
              <div className="grid grid-cols-[110px_1fr] gap-4 py-3">
                <dt className="text-[var(--muted-light)] uppercase tracking-[0.1em] text-[10px] pt-0.5">Stack</dt>
                <dd>{item.stack}</dd>
              </div>
              <div className="grid grid-cols-[110px_1fr] gap-4 py-3">
                <dt className="text-[var(--muted-light)] uppercase tracking-[0.1em] text-[10px] pt-0.5">Surface</dt>
                <dd>{item.address}</dd>
              </div>
            </dl>

            <div className="space-y-5 max-w-2xl">
              {item.article.paragraphs.map((p, i) => (
                <p key={i} className="text-sm leading-[1.85] text-[var(--ink)]">
                  {p}
                </p>
              ))}
            </div>

            <a
              href={item.ctaHref}
              target="_blank"
              rel="noopener noreferrer"
              className="group inline-flex items-center gap-3 mt-10 bg-black text-white text-xs font-semibold pl-5 pr-2 py-2 hover:bg-neutral-800 transition-colors"
            >
              <span className="block overflow-hidden h-[1.2em]">
                <span className="flex flex-col leading-[1.2em] transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:-translate-y-1/2">
                  <span>{item.ctaText}</span>
                  <span>{item.ctaText}</span>
                </span>
              </span>
              <span className="w-6 h-6 bg-white text-black flex items-center justify-center transition-transform duration-500 ease-[cubic-bezier(0.25,0.1,0.25,1)] group-hover:rotate-[-45deg]">
                <ArrowUpRight className="w-3.5 h-3.5" />
              </span>
            </a>
          </div>
        </div>

        {item.slug === 'canvaskit' && (
          <div className="mt-20 border-t border-black/10 pt-14">
            <CanvasKitShowcase />
          </div>
        )}
      </article>
    </div>
  );
};
