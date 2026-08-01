import React, { useEffect, useRef } from 'react';

// Slow-drifting indigo-on-zinc gradient mesh behind the hero, hand-rolled on
// a 2D canvas (no shader deps). Renders one static frame under
// prefers-reduced-motion, pauses while the tab is hidden.
export const HeroShaderCanvas: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Pre-rendered film-grain tile, drawn once and stamped at low opacity.
    const grain = document.createElement('canvas');
    grain.width = grain.height = 128;
    const gctx = grain.getContext('2d');
    if (gctx) {
      const img = gctx.createImageData(128, 128);
      for (let i = 0; i < img.data.length; i += 4) {
        const v = Math.random() * 255;
        img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
        img.data[i + 3] = 14;
      }
      gctx.putImageData(img, 0, 0);
    }

    // Blobs ease between anchor positions on a ~30s period.
    const PERIOD = 30000;
    const blobs = [
      { color: '99,102,241', alpha: 0.16, ax: 0.22, ay: 0.28, bx: 0.38, by: 0.45, r: 0.55, phase: 0 },
      { color: '79,70,229', alpha: 0.12, ax: 0.78, ay: 0.20, bx: 0.62, by: 0.55, r: 0.60, phase: 2.1 },
      { color: '99,102,241', alpha: 0.09, ax: 0.50, ay: 0.85, bx: 0.68, by: 0.62, r: 0.50, phase: 4.2 },
    ];

    let raf = 0;
    let running = true;

    const resize = () => {
      const parent = canvas.parentElement;
      if (!parent) return;
      canvas.width = parent.clientWidth;
      canvas.height = parent.clientHeight;
    };

    const draw = (now: number) => {
      const { width: w, height: h } = canvas;
      if (!w || !h) return;
      ctx.fillStyle = '#0b0b0e';
      ctx.fillRect(0, 0, w, h);
      const t = (now % PERIOD) / PERIOD;
      for (const b of blobs) {
        // cosine ease between the two anchors, offset per blob
        const k = 0.5 - 0.5 * Math.cos(2 * Math.PI * t + b.phase);
        const x = (b.ax + (b.bx - b.ax) * k) * w;
        const y = (b.ay + (b.by - b.ay) * k) * h;
        const rad = b.r * Math.max(w, h);
        const grad = ctx.createRadialGradient(x, y, 0, x, y, rad);
        grad.addColorStop(0, `rgba(${b.color},${b.alpha})`);
        grad.addColorStop(1, 'rgba(11,11,14,0)');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, w, h);
      }
      ctx.drawImage(grain, 0, 0, w, h);
    };

    const loop = (now: number) => {
      if (!running) return;
      draw(now);
      raf = requestAnimationFrame(loop);
    };

    const onVisibility = () => {
      if (document.hidden) {
        running = false;
        cancelAnimationFrame(raf);
      } else if (!running && !reduced) {
        running = true;
        raf = requestAnimationFrame(loop);
      }
    };

    resize();
    if (reduced) {
      draw(0); // single static frame
    } else {
      raf = requestAnimationFrame(loop);
      document.addEventListener('visibilitychange', onVisibility);
    }
    window.addEventListener('resize', resize);

    return () => {
      running = false;
      cancelAnimationFrame(raf);
      document.removeEventListener('visibilitychange', onVisibility);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden="true"
      className="hero-shader pointer-events-none absolute inset-0 z-0 h-full w-full opacity-60"
    />
  );
};
