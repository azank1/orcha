import React, { useState, useEffect } from 'react';
import { motion } from 'motion/react';
import { McpLogo, A2aLogo, ComputerUseLogo } from './ProtocolIcons';
import { SANDBOX_URL } from '../config/sandbox';

interface FleetAgent {
  name: string;
  did: string;
  protocol: string;
  health: string;
  last_check: string | null;
}

const PROTOCOL_ICONS: Record<string, React.ReactNode> = {
  MCP: <McpLogo className="w-4 h-4" />,
  A2A: <A2aLogo className="w-4 h-4" />,
  COMPUTER_USE: <ComputerUseLogo className="w-4 h-4" />,
};

const PROTOCOL_COLORS: Record<string, string> = {
  MCP: '#6366f1',
  A2A: '#3ecf8e',
  COMPUTER_USE: '#e5c07b',
};

const HEALTH_COLORS: Record<string, string> = {
  HEALTHY: 'var(--ok)',
  DEGRADED: 'var(--warn)',
  UNHEALTHY: 'var(--err)',
  UNKNOWN: 'var(--faint)',
};

export const FleetGrid: React.FC = () => {
  const [agents, setAgents] = useState<FleetAgent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    const fetchFleet = async () => {
      try {
        const res = await fetch(`${SANDBOX_URL}/api/v1/sandbox/fleet`);
        if (!res.ok) throw new Error(`status ${res.status}`);
        const data = await res.json();
        if (!cancelled && data.status === 'live') {
          setAgents(data.agents || []);
        }
      } catch {
        if (!cancelled) setAgents([]);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetchFleet();
    const id = setInterval(fetchFleet, 300000);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  if (loading) {
    return (
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="h-20 rounded-lg border border-[var(--line)] bg-[var(--card-bg)] animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (agents.length === 0) return null;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-[var(--muted)] uppercase tracking-wider">
          Live Fleet · {agents.length} agents
        </span>
        <span className="font-mono text-[11px] text-[var(--faint)]">
          polling every 5m
        </span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {agents.map((agent, idx) => (
          <motion.div
            key={agent.did}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05, duration: 0.3 }}
            className="group p-3 rounded-lg border border-[var(--line)] bg-[var(--card-bg)] hover:border-[#6366f1] transition-all cursor-default"
          >
            <div className="flex items-center justify-between mb-2">
              <span
                className="w-6 h-6 rounded-md flex items-center justify-center"
                style={{
                  backgroundColor: `${PROTOCOL_COLORS[agent.protocol] || '#6366f1'}15`,
                  color: PROTOCOL_COLORS[agent.protocol] || '#6366f1',
                }}
              >
                {PROTOCOL_ICONS[agent.protocol] || <McpLogo className="w-4 h-4" />}
              </span>
              <span
                className="w-2 h-2 rounded-full"
                style={{ backgroundColor: HEALTH_COLORS[agent.health] || 'var(--faint)' }}
                title={agent.health}
              />
            </div>

            <div className="font-mono text-[11px] font-semibold text-[var(--text)] truncate leading-tight">
              {agent.name}
            </div>
            <div className="font-mono text-[9px] text-[var(--faint)] truncate leading-tight mt-0.5">
              {agent.protocol}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
};
