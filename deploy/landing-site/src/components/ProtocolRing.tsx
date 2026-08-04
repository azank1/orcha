import React, { useEffect, useRef, useState } from 'react';
import { MoveHorizontal } from 'lucide-react';
import { ProtocolLogo, ProtocolLogoKey } from './ProtocolLogo';
import { SANDBOX_URL } from '../config/sandbox';

const PROTOCOL_ITEMS: { logo: ProtocolLogoKey; name: string }[] = [
  { logo: 'mcp', name: 'MCP' },
  { logo: 'a2a', name: 'A2A' },
  { logo: 'a2ui', name: 'A2UI' },
  { logo: 'langgraph', name: 'LangGraph' },
  { logo: 'openapi', name: 'OpenAPI' },
  { logo: 'grpc', name: 'gRPC' },
  { logo: 'computer-use', name: 'Computer-Use' },
  { logo: 'canvaskit', name: 'CanvasKit' },
];

const FLEET_LOGO: Record<string, ProtocolLogoKey> = {
  MCP: 'mcp',
  A2A: 'a2a',
  ACP: 'a2a',
  COMPUTER_USE: 'computer-use',
};

interface FleetAgent {
  name: string;
  protocol: string;
}

/**
 * Protocol knowledge index — a draggable 3D ring of the protocols and
 * integrations the harness speaks, plus the live sandbox fleet.
 */
export const ProtocolRing: React.FC = () => {
  const [rotation, setRotation] = useState(0);
  const [hintVisible, setHintVisible] = useState(true);
  const [fleet, setFleet] = useState<FleetAgent[]>([]);
  const drag = useRef<{ startX: number; startRot: number } | null>(null);
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  useEffect(() => {
    let cancelled = false;
    const fetchFleet = async () => {
      try {
        const res = await fetch(`${SANDBOX_URL}/api/v1/sandbox/fleet`);
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data = await res.json();
        if (!cancelled && data.status === 'live') {
          setFleet(data.agents || []);
        }
      } catch {
        /* fleet absent — ring shows protocols only */
      }
    };
    fetchFleet();
    const id = setInterval(fetchFleet, 300000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  useEffect(() => {
    if (reduced) return;
    let raf = 0;
    let last = performance.now();
    const loop = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      if (!drag.current) setRotation((r) => r + dt * 3.5);
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [reduced]);

  const onPointerDown = (e: React.PointerEvent) => {
    drag.current = { startX: e.clientX, startRot: rotation };
    setHintVisible(false);
  };
  const onPointerMove = (e: React.PointerEvent) => {
    if (!drag.current) return;
    setRotation(drag.current.startRot + (e.clientX - drag.current.startX) * 0.25);
  };
  const onPointerUp = () => {
    drag.current = null;
  };

  const items = [
    ...PROTOCOL_ITEMS,
    ...fleet.map((a) => ({
      logo: FLEET_LOGO[a.protocol] ?? 'openapi',
      name: a.name,
    })),
  ];
  const step = 360 / items.length;
  const radius = Math.max(380, Math.round((items.length * 170) / (2 * Math.PI)) + 40);

  return (
    <section id="protocols" className="bg-[var(--bg)] text-[var(--fg)] border-b border-[var(--line-dark)] overflow-hidden">
      <div className="max-w-[1440px] mx-auto px-6 sm:px-10 lg:px-14 py-20 lg:py-28">
        <div className="mb-4">
          <p className="text-[11px] uppercase tracking-[0.14em] text-[var(--muted-dark)] mb-3">
            Knowledge index
          </p>
          <h2 className="font-display text-[clamp(1.8rem,4vw,3rem)] leading-tight">
            Speaks your protocol
          </h2>
        </div>

        <div
          className="relative h-[380px] sm:h-[420px] mt-8 select-none cursor-grab active:cursor-grabbing"
          style={{ perspective: '1400px' }}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerLeave={onPointerUp}
        >
          <div
            className="absolute inset-0 flex items-center justify-center"
            style={{
              transformStyle: 'preserve-3d',
              transform: `rotateY(${rotation}deg)`,
              transition: drag.current ? 'none' : 'transform 0.1s linear',
            }}
          >
            {items.map((item, i) => (
              <div
                key={item.name}
                className="absolute w-[150px] sm:w-[170px]"
                style={{
                  transform: `rotateY(${i * step}deg) translateZ(${radius}px)`,
                  transformStyle: 'preserve-3d',
                  backfaceVisibility: 'hidden',
                }}
              >
                <div className="border border-[var(--line-dark)] bg-black aspect-square flex flex-col items-center justify-center gap-4">
                  <ProtocolLogo logo={item.logo} className="w-10 h-10 text-white/80" />
                  <span className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-dark)] truncate max-w-full px-2 text-center">
                    {item.name}
                  </span>
                </div>
              </div>
            ))}
          </div>

          {hintVisible && (
            <div className="absolute bottom-2 right-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.14em] text-[var(--faint)] pointer-events-none">
              <MoveHorizontal className="w-4 h-4" />
              drag
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
