import { useNavigate } from 'react-router-dom'
import { useSessionStore } from '../../store/session'
import { Badge } from '../ui/Badge'
import { StatusDot } from '../ui/Badge'

/** Entry point to agent registration + this session's discovered fleet. */
export function AgentsTab() {
  const navigate = useNavigate()
  const agents = useSessionStore((s) => s.agents)

  return (
    <div className="px-3">
      <p className="px-1 mb-2 text-[10px] font-semibold text-text-disabled tracking-caps uppercase">
        Register Agent
      </p>
      <p className="px-1 mb-2 font-mono text-[10px] text-text-secondary">
        Ship your own agent — upload an emerge.yaml and it joins the fleet the
        planner can route to.
      </p>
      <button
        onClick={() => navigate('/agents/register')}
        className="h-7 px-2.5 rounded-sm border border-surface-borderLight bg-surface-overlay font-mono text-[10px] text-text-body hover:border-brand-primary transition-colors"
      >
        open registration →
      </button>

      <p className="px-1 mt-4 mb-2 text-[10px] font-semibold text-text-disabled tracking-caps uppercase">
        Session Fleet
      </p>
      {agents.length === 0 ? (
        <p className="px-1 font-mono text-caption text-text-disabled">
          No agents discovered yet.
        </p>
      ) : (
        <div className="flex flex-col gap-1.5">
          {agents.map((agent) => (
            <div
              key={agent.agent_id}
              className="flex items-center gap-2 rounded-md border border-surface-border bg-surface-overlay px-2.5 py-2"
            >
              <StatusDot status={agent.status} />
              <span className="min-w-0 flex-1 truncate font-mono text-[11px] text-text-body">
                {agent.name}
              </span>
              <Badge variant={agent.type} className="h-5 px-1.5 text-[9px]" />
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
