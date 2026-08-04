import type { AgentInfo } from '../../types'
import { Badge, StatusDot } from '../ui/Badge'
import { cn } from '../ui/cn'

interface AgentCardProps {
  agent: AgentInfo
  className?: string
}

export function AgentCard({ agent, className }: AgentCardProps) {
  const badgeVariant = agent.type === 'mcp' ? 'mcp' : agent.type === 'a2a' ? 'a2a' : 'native'

  return (
    <div
      className={cn(
        'flex items-center h-[54px] px-3 rounded-md bg-surface-overlay border border-surface-border',
        className,
      )}
    >
      <div className="flex-1 min-w-0">
        <p className="text-label font-medium text-text-body truncate">{agent.name}</p>
      </div>
      <Badge variant={badgeVariant} className="mx-2 h-5 text-[10px] px-1.5 shrink-0" />
      <StatusDot status={agent.status} />
    </div>
  )
}
