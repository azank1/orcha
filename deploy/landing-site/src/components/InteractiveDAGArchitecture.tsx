import React, { useState } from 'react';
import { ARCHITECTURE_SERVICES } from '../data/orchaData';

export const InteractiveDAGArchitecture: React.FC = () => {
  const [activeNode, setActiveNode] = useState<string | null>(null);

  return (
    <section id="arch" className="py-16 border-b border-[var(--line)] bg-[var(--bg)] transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Section Header */}
        <div className="space-y-2">
          <div className="font-mono text-xs text-[#6366f1] uppercase tracking-widest font-semibold">
            Architecture
          </div>
          <h2 className="font-display font-bold text-2xl sm:text-3xl tracking-tight text-[var(--text)]">
            Neutral ground between agents
          </h2>
          <p className="text-[var(--muted)] text-xs sm:text-sm max-w-2xl leading-relaxed">
            Orcha is a harness, not an agent: plan → route → dispatch → verify → normalize → render. Agents stay external and independent.
          </p>
        </div>

        {/* Interactive Architecture SVG Diagram */}
        <div className="bg-[var(--card-bg)] border border-[var(--line)] rounded-xl p-6 shadow-xl overflow-x-auto transition-colors">
          <div className="min-w-[800px]">
            <svg
              viewBox="0 0 1000 300"
              className="w-full h-auto block select-none"
              aria-label="Orcha Architecture Diagram"
            >
              <defs>
                <filter id="whiteGlow" x="-20%" y="-20%" width="140%" height="140%">
                  <feDropShadow dx="0" dy="2" stdDeviation="4" floodColor="#ffffff" floodOpacity="0.15" />
                </filter>
              </defs>

              {/* Connected Edge Paths */}
              <path
                className={`svg-edge ${activeNode === 'goal' || activeNode === 'registry' ? 'svg-edge-hi' : ''}`}
                d="M 128 150 L 232 150"
              />
              <path
                className={`svg-edge ${activeNode === 'registry' || activeNode === 'pnd' ? 'svg-edge-hi' : ''}`}
                d="M 352 150 L 456 150"
              />
              <path
                className={`svg-edge ${activeNode === 'pnd' || activeNode === 'superagent' ? 'svg-edge-hi' : ''}`}
                d="M 576 150 L 680 150"
              />
              <path
                className={`svg-edge ${activeNode === 'superagent' || activeNode === 'mcp' ? 'svg-edge-hi' : ''}`}
                d="M 790 130 L 850 62"
              />
              <path
                className={`svg-edge ${activeNode === 'superagent' || activeNode === 'a2a' ? 'svg-edge-hi' : ''}`}
                d="M 790 150 L 850 150"
              />
              <path
                className={`svg-edge ${activeNode === 'superagent' || activeNode === 'cu' ? 'svg-edge-hi' : ''}`}
                d="M 790 170 L 850 238"
              />

              {/* Node 1: Goal */}
              <g
                className="cursor-pointer"
                onMouseEnter={() => setActiveNode('goal')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <rect
                  className={`svg-node ${activeNode === 'goal' ? 'svg-node-hi' : ''}`}
                  x="18"
                  y="122"
                  width="110"
                  height="56"
                  rx="8"
                />
                <text className="svg-txt" x="73" y="146" textAnchor="middle">
                  Goal
                </text>
                <text className="svg-sub" x="73" y="163" textAnchor="middle">
                  natural language
                </text>
              </g>

              {/* Node 2: Registry */}
              <g
                className="cursor-pointer"
                onMouseEnter={() => setActiveNode('registry')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <rect
                  className={`svg-node ${activeNode === 'registry' ? 'svg-node-hi' : ''}`}
                  x="232"
                  y="122"
                  width="120"
                  height="56"
                  rx="8"
                />
                <text className="svg-txt" x="292" y="146" textAnchor="middle">
                  Registry
                </text>
                <text className="svg-sub" x="292" y="163" textAnchor="middle">
                  :8000 · manifests
                </text>
              </g>

              {/* Node 3: Plan & Discover */}
              <g
                className="cursor-pointer"
                onMouseEnter={() => setActiveNode('pnd')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <rect
                  className={`svg-node ${activeNode === 'pnd' ? 'svg-node-hi' : ''}`}
                  x="456"
                  y="122"
                  width="120"
                  height="56"
                  rx="8"
                />
                <text className="svg-txt" x="516" y="146" textAnchor="middle">
                  Plan + Discover
                </text>
                <text className="svg-sub" x="516" y="163" textAnchor="middle">
                  :8001 · vector + LLM
                </text>
              </g>

              {/* Node 4: SuperAgent */}
              <g
                className="cursor-pointer"
                onMouseEnter={() => setActiveNode('superagent')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <rect
                  className={`svg-node ${activeNode === 'superagent' ? 'svg-node-hi' : ''}`}
                  x="680"
                  y="122"
                  width="110"
                  height="56"
                  rx="8"
                />
                <text className="svg-txt" x="735" y="146" textAnchor="middle">
                  SuperAgent
                </text>
                <text className="svg-sub" x="735" y="163" textAnchor="middle">
                  :8002 · LangGraph
                </text>
              </g>

              {/* Node 5: MCP Handler */}
              <g
                className="cursor-pointer"
                onMouseEnter={() => setActiveNode('mcp')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <rect
                  className={`svg-node ${activeNode === 'mcp' ? 'svg-node-hi' : ''}`}
                  x="850"
                  y="34"
                  width="132"
                  height="56"
                  rx="8"
                />
                <text className="svg-txt" x="916" y="58" textAnchor="middle">
                  MCP handler
                </text>
                <text className="svg-sub" x="916" y="75" textAnchor="middle">
                  tools + resources
                </text>
              </g>

              {/* Node 6: A2A Handler */}
              <g
                className="cursor-pointer"
                onMouseEnter={() => setActiveNode('a2a')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <rect
                  className={`svg-node ${activeNode === 'a2a' ? 'svg-node-hi' : ''}`}
                  x="850"
                  y="122"
                  width="132"
                  height="56"
                  rx="8"
                />
                <text className="svg-txt" x="916" y="146" textAnchor="middle">
                  A2A handler
                </text>
                <text className="svg-sub" x="916" y="163" textAnchor="middle">
                  + ACP alias route
                </text>
              </g>

              {/* Node 7: Computer-Use Handler */}
              <g
                className="cursor-pointer"
                onMouseEnter={() => setActiveNode('cu')}
                onMouseLeave={() => setActiveNode(null)}
              >
                <rect
                  className={`svg-node ${activeNode === 'cu' ? 'svg-node-hi' : ''}`}
                  x="850"
                  y="210"
                  width="132"
                  height="56"
                  rx="8"
                />
                <text className="svg-txt" x="916" y="234" textAnchor="middle">
                  Computer-use
                </text>
                <text className="svg-sub" x="916" y="251" textAnchor="middle">
                  screens + input
                </text>
              </g>
            </svg>
          </div>
        </div>

        {/* Microservices Breakdown Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {ARCHITECTURE_SERVICES.map((svc, idx) => (
            <div
              key={idx}
              className="bg-[var(--card-bg)] border border-[var(--line)] p-5 rounded-xl space-y-2 flex flex-col justify-between shadow-sm transition-colors"
            >
              <div>
                <span className="font-mono text-xs font-bold text-[#6366f1] block mb-1">
                  {svc.port}
                </span>
                <h4 className="font-display font-semibold text-sm text-[var(--text)]">
                  {svc.name}
                </h4>
                <p className="text-xs text-[var(--muted)] mt-2 leading-relaxed">
                  {svc.description}
                </p>
              </div>
              <div className="pt-3 border-t border-[var(--line)] font-mono text-[10.5px] text-[var(--faint)]">
                {svc.protocol}
              </div>
            </div>
          ))}
        </div>

      </div>
    </section>
  );
};
