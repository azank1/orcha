import React, { useEffect, useRef } from 'react';

interface AsciiMoonFieldProps {
  /** Glyph ramp from lightest to densest, e.g. ' .:-=+*#%@' */
  glyphs?: string;
  /** Rotations per second-ish factor; 0 = static frame */
  speed?: number;
  /** Pointer reactivity (tilt + spin follow the mouse) */
  interactive?: boolean;
  /** Glyph color (CSS) — defaults to currentColor via inherit */
  color?: string;
  className?: string;
}

/**
 * Canvas-rendered rotating ASCII sphere ("the moon"). Monochrome, Fragment Mono.
 * Renders one static frame under prefers-reduced-motion or speed=0.
 */
export const AsciiMoonField: React.FC<AsciiMoonFieldProps> = ({
  glyphs = ' .:-=+*#%@',
  speed = 0.12,
  interactive = true,
  color = '#ffffff',
  className = '',
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouse = useRef({ x: 0.5, y: 0.5 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Sample the sphere on a lat/long grid.
    const points: { x: number; y: number; z: number }[] = [];
    const LAT_STEP = 14;
    const LON_STEP = 14;
    for (let lat = -90; lat <= 90; lat += LAT_STEP) {
      const latRad = (lat * Math.PI) / 180;
      const ring = Math.cos(latRad);
      const lonCount = Math.max(6, Math.round((360 / LON_STEP) * ring));
      for (let i = 0; i < lonCount; i++) {
        const lonRad = ((i / lonCount) * 360 * Math.PI) / 180;
        points.push({
          x: ring * Math.cos(lonRad),
          y: Math.sin(latRad),
          z: ring * Math.sin(lonRad),
        });
      }
    }

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

    const onMouse = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouse.current = {
        x: (e.clientX - rect.left) / Math.max(rect.width, 1),
        y: (e.clientY - rect.top) / Math.max(rect.height, 1),
      };
    };
    if (interactive) window.addEventListener('mousemove', onMouse);

    const cell = Math.max(10, Math.floor(Math.min(width, height) / 34));

    const draw = (t: number) => {
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, width, height);
      ctx.font = `${cell}px 'Fragment Mono', 'IBM Plex Mono', monospace`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';

      const cx = width / 2;
      const cy = height / 2;
      const R = Math.min(width, height) * 0.42;

      const spin = t * speed + (interactive ? (mouse.current.x - 0.5) * 1.6 : 0);
      const tilt = 0.42 + (interactive ? (mouse.current.y - 0.5) * 0.5 : 0);

      const cosS = Math.cos(spin);
      const sinS = Math.sin(spin);
      const cosT = Math.cos(tilt);
      const sinT = Math.sin(tilt);

      const n = glyphs.length - 1;
      for (const p of points) {
        // rotate around Y (spin), then X (tilt)
        const x1 = p.x * cosS + p.z * sinS;
        const z1 = -p.x * sinS + p.z * cosS;
        const y2 = p.y * cosT - z1 * sinT;
        const z2 = p.y * sinT + z1 * cosT;

        if (z2 <= -0.15) continue; // back hemisphere: skip

        const px = cx + x1 * R;
        const py = cy - y2 * R;
        const depth = (z2 + 1) / 2; // 0..1
        const idx = Math.max(0, Math.min(n, Math.round(depth * n)));
        const g = glyphs[idx];
        if (g === ' ') continue;
        ctx.globalAlpha = 0.25 + depth * 0.75;
        ctx.fillStyle = color;
        ctx.fillText(g, px, py);
      }
      ctx.globalAlpha = 1;
    };

    if (reduced || speed === 0) {
      draw(1.7);
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
      if (interactive) window.removeEventListener('mousemove', onMouse);
    };
  }, [glyphs, speed, interactive, color]);

  return <canvas ref={canvasRef} className={className} aria-hidden="true" />;
};
