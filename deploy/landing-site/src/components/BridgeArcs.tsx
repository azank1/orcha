import React, { useEffect, useRef } from 'react';

/**
 * Subtle "bridging" backdrop: thin dashed arcs slowly drawing themselves
 * between the left and right edges of the section. Monochrome, very light.
 * Renders a single static set of arcs under prefers-reduced-motion.
 */
export const BridgeArcs: React.FC<{ className?: string; stroke?: string }> = ({
  className = '',
  stroke = '#0a0a0a',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    let raf = 0;
    let width = 0;
    let height = 0;
    let dpr = 1;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = Math.max(1, Math.floor(width * dpr));
      canvas.height = Math.max(1, Math.floor(height * dpr));
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    // Arc definitions: pairs of edge points + arch height, phase-offset.
    const ARCS = 7;
    const arcs = Array.from({ length: ARCS }, (_, i) => ({
      y: 0.18 + (i / ARCS) * 0.68 + (i % 2 ? 0.03 : -0.03),
      lift: 0.10 + ((i * 37) % 40) / 100, // 0.10..0.50 of height
      phase: i * 0.9,
      speed: 0.05 + ((i * 13) % 10) / 220,
    }));

    const draw = (t: number) => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);
      ctx.lineWidth = 1;

      for (const a of arcs) {
        const y0 = a.y * height;
        const cpY = y0 - a.lift * height;
        // slow breathing opacity per arc
        const breathe = 0.5 + 0.5 * Math.sin(t * 0.4 + a.phase);
        ctx.strokeStyle = stroke;
        ctx.globalAlpha = 0.06 + breathe * 0.075;
        ctx.setLineDash([3, 7]);
        ctx.lineDashOffset = -(t * 6 * a.speed * 10 + a.phase * 20);

        ctx.beginPath();
        ctx.moveTo(-10, y0);
        ctx.quadraticCurveTo(width / 2, cpY, width + 10, y0);
        ctx.stroke();

        // tiny node dots at both banks
        ctx.setLineDash([]);
        ctx.globalAlpha = 0.14 + breathe * 0.1;
        ctx.fillStyle = stroke;
        ctx.beginPath();
        ctx.arc(2, y0, 1.5, 0, Math.PI * 2);
        ctx.arc(width - 2, y0, 1.5, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1;
    };

    if (reduced) {
      draw(0);
    } else {
      const start = performance.now();
      const loop = (now: number) => {
        draw((now - start) / 1000);
        raf = requestAnimationFrame(loop);
      };
      raf = requestAnimationFrame(loop);
    }

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
    };
  }, [stroke]);

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />;
};
