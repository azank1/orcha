import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { ArrowRight, Zap, Search, Layers, Monitor, Globe, Mail, FileText, Database } from 'lucide-react';

interface AgentNode {
  id: string;
  name: string;
  protocol: 'MCP' | 'A2A' | 'COMPUTER_USE';
  capability: string;
  icon: React.ReactNode;
  x: number;
  y: number;
}

interface Edge {
  from: number;
  to: number;
}

const AGENT_POOL: Record<string, AgentNode[]> = {
  portfolio: [
    { id: 'did:orcha:agent:finance-dashboard', name: 'finance-dashboard', protocol: 'MCP', capability: 'get_portfolio_dashboard', icon: <Database className="w-3.5 h-3.5" />, x: 50, y: 50 },
  ],
  scrape: [
    { id: 'did:orcha:agent:web-scraper', name: 'web-scraper', protocol: 'A2A', capability: 'scrape', icon: <Globe className="w-3.5 h-3.5" />, x: 30, y: 40 },
    { id: 'did:orcha:agent:search-agent', name: 'search-agent', protocol: 'MCP', capability: 'search', icon: <Search className="w-3.5 h-3.5" />, x: 70, y: 40 },
  ],
  research: [
    { id: 'did:orcha:agent:web-scraper', name: 'web-scraper', protocol: 'A2A', capability: 'scrape', icon: <Globe className="w-3.5 h-3.5" />, x: 25, y: 40 },
    { id: 'did:orcha:agent:notion-research', name: 'notion-research', protocol: 'A2A', capability: 'research', icon: <FileText className="w-3.5 h-3.5" />, x: 75, y: 40 },
    { id: 'did:orcha:agent:finance-dashboard', name: 'finance-dashboard', protocol: 'MCP', capability: 'get_portfolio_dashboard', icon: <Database className="w-3.5 h-3.5" />, x: 50, y: 75 },
  ],
  lead: [
    { id: 'did:orcha:agent:lead-gen-agent', name: 'lead-gen', protocol: 'A2A', capability: 'generate_leads', icon: <Mail className="w-3.5 h-3.5" />, x: 50, y: 50 },
  ],
  browser: [
    { id: 'did:orcha:agent:computer-use-agent', name: 'computer-use', protocol: 'COMPUTER_USE', capability: 'screenshot', icon: <Monitor className="w-3.5 h-3.5" />, x: 50, y: 50 },
  ],
  default: [
    { id: 'did:orcha:agent:search-agent', name: 'search-agent', protocol: 'MCP', capability: 'search', icon: <Search className="w-3.5 h-3.5" />, x: 25, y: 40 },
    { id: 'did:orcha:agent:web-scraper', name: 'web-scraper', protocol: 'A2A', capability: 'scrape', icon: <Globe className="w-3.5 h-3.5" />, x: 75, y: 40 },
    { id: 'did:orcha:agent:finance-dashboard', name: 'finance-dashboard', protocol: 'MCP', capability: 'get_portfolio_dashboard', icon: <Database className="w-3.5 h-3.5" />, x: 50, y: 75 },
  ],
};

const PROTOCOL_COLORS: Record<string, string> = {
  MCP: '#6366f1',
  A2A: '#3ecf8e',
  COMPUTER_USE: '#e5c07b',
};

function planGoal(goal: string): { nodes: AgentNode[]; edges: Edge[] } {
  const lower = goal.toLowerCase();
  let key = 'default';
  if (lower.includes('portfolio') || lower.includes('finance') || lower.includes('stock')) key = 'portfolio';
  else if (lower.includes('scrape') || lower.includes('crawl') || lower.includes('extract')) key = 'scrape';
  else if (lower.includes('research') || lower.includes('analyze') || lower.includes('report')) key = 'research';
  else if (lower.includes('lead') || lower.includes('email') || lower.includes('outreach')) key = 'lead';
  else if (lower.includes('browser') || lower.includes('screenshot') || lower.includes('click') || lower.includes('ui')) key = 'browser';

  const nodes = AGENT_POOL[key];
  const edges: Edge[] = [];
  for (let i = 0; i < nodes.length - 1; i++) {
    edges.push({ from: i, to: i + 1 });
  }
  if (nodes.length === 3) {
    edges.push({ from: 0, to: 2 });
    edges.push({ from: 1, to: 2 });
  }
  return { nodes, edges };
}

export const GoalDecomposition: React.FC = () => {
  const [goal, setGoal] = useState('');
  const [plan, setPlan] = useState<{ nodes: AgentNode[]; edges: Edge[] } | null>(null);
  const [isAnimating, setIsAnimating] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!goal.trim()) return;
    setIsAnimating(true);
    setPlan(null);
    // Small delay to reset animation
    setTimeout(() => {
      setPlan(planGoal(goal));
      setIsAnimating(false);
    }, 100);
  };

  const handleExample = (example: string) => {
    setGoal(example);
    setIsAnimating(true);
    setPlan(null);
    setTimeout(() => {
      setPlan(planGoal(example));
      setIsAnimating(false);
    }, 100);
  };

  return (
    <div className="space-y-4">
      {/* Input Pill */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="flex items-center bg-[var(--card-bg)] border border-[var(--line)] rounded-full pl-4 pr-1.5 py-1.5 shadow-sm hover:border-[#6366f1] transition-colors focus-within:border-[#6366f1] focus-within:ring-1 focus-within:ring-[#6366f1]/30">
          <Zap className="w-4 h-4 text-[#6366f1] shrink-0" />
          <input
            ref={inputRef}
            type="text"
            value={goal}
            onChange={(e) => setGoal(e.target.value)}
            placeholder="try a goal — e.g. research nvidia and build a portfolio"
            className="flex-1 bg-transparent border-none outline-none px-3 py-1.5 font-mono text-xs text-[var(--text)] placeholder:text-[var(--faint)]"
          />
          <button
            type="submit"
            className="bg-[#6366f1] text-white rounded-full p-2 hover:bg-[#4f52c8] transition-colors shrink-0"
          >
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>

      {/* Example chips */}
      <div className="flex flex-wrap gap-2">
        {['portfolio', 'scrape wikipedia', 'research ai', 'lead gen', 'browser screenshot'].map((ex) => (
          <button
            key={ex}
            onClick={() => handleExample(ex)}
            className="font-mono text-[11px] px-2.5 py-1 rounded-full border border-[var(--line)] text-[var(--muted)] hover:border-[#6366f1] hover:text-[#6366f1] transition-colors"
          >
            {ex}
          </button>
        ))}
      </div>

      {/* DAG Visualization */}
      <AnimatePresence mode="wait">
        {plan && (
          <motion.div
            key={goal}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.3 }}
            className="relative bg-[var(--card-bg)] border border-[var(--line)] rounded-xl p-4 overflow-hidden"
          >
            <div className="flex items-center justify-between mb-3">
              <span className="font-mono text-[11px] text-[var(--muted)] uppercase tracking-wider">
                visual demo — not a live run
              </span>
              <Layers className="w-3.5 h-3.5 text-[#6366f1]" />
            </div>

            <div className="relative h-[180px] w-full">
              {/* Edges */}
              <svg className="absolute inset-0 w-full h-full pointer-events-none">
                {plan.edges.map((edge, idx) => {
                  const from = plan.nodes[edge.from];
                  const to = plan.nodes[edge.to];
                  return (
                    <motion.line
                      key={idx}
                      x1={`${from.x}%`}
                      y1={`${from.y}%`}
                      x2={`${to.x}%`}
                      y2={`${to.y}%`}
                      stroke="var(--line)"
                      strokeWidth="1.5"
                      strokeDasharray="4 4"
                      initial={{ pathLength: 0, opacity: 0 }}
                      animate={{ pathLength: 1, opacity: 1 }}
                      transition={{ delay: 0.2 + idx * 0.1, duration: 0.4 }}
                    />
                  );
                })}
              </svg>

              {/* Nodes */}
              {plan.nodes.map((node, idx) => (
                <motion.div
                  key={node.id}
                  initial={{ opacity: 0, scale: 0.8 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: idx * 0.15, duration: 0.3, ease: 'easeOut' }}
                  className="absolute transform -translate-x-1/2 -translate-y-1/2"
                  style={{ left: `${node.x}%`, top: `${node.y}%` }}
                >
                  <div
                    className="flex flex-col items-center gap-1.5 p-2.5 rounded-lg border bg-[var(--bg)] shadow-md min-w-[100px]"
                    style={{ borderColor: PROTOCOL_COLORS[node.protocol] }}
                  >
                    <div
                      className="w-7 h-7 rounded-md flex items-center justify-center"
                      style={{ backgroundColor: `${PROTOCOL_COLORS[node.protocol]}20`, color: PROTOCOL_COLORS[node.protocol] }}
                    >
                      {node.icon}
                    </div>
                    <div className="text-center">
                      <div className="font-mono text-[11px] font-semibold text-[var(--text)] leading-tight">
                        {node.name}
                      </div>
                      <div className="font-mono text-[9px] text-[var(--faint)] leading-tight">
                        {node.protocol}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            {/* Step summary */}
            <div className="mt-3 pt-3 border-t border-[var(--line)] space-y-1">
              {plan.nodes.map((node, idx) => (
                <motion.div
                  key={node.id}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.3 + idx * 0.1 }}
                  className="flex items-center gap-2 font-mono text-[11px]"
                >
                  <span className="text-[var(--faint)]">0{idx + 1}</span>
                  <span className="text-[var(--text)]">{node.capability}</span>
                  <span className="text-[var(--faint)]">→</span>
                  <span style={{ color: PROTOCOL_COLORS[node.protocol] }}>{node.protocol}</span>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
