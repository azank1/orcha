import type { RunPhase } from '../../store/session'

interface StreamingDotsProps {
  phase?: RunPhase
  agentName?: string | null
}

function phaseLabel(phase: RunPhase, agentName: string | null | undefined): string {
  if (phase === 'planning') return 'Planning your goal…'
  if (phase === 'executing') {
    const name = agentName ? agentName.replace(/-agent$/, '').replace(/-/g, ' ') : null
    return name ? `Running ${name}…` : 'Calling agent…'
  }
  return 'SuperAgent is thinking…'
}


export function StreamingDots({ phase, agentName }: StreamingDotsProps) {
  return (
    <div className="flex items-center gap-2 py-1">
      <div className="flex items-center gap-[3px]">
        <span className="size-[5px] rounded-full bg-text-disabled opacity-50 animate-pulse-dot" aria-hidden="true" />
        <span className="size-[5px] rounded-full bg-text-disabled opacity-65 animate-pulse-dot" aria-hidden="true" />
        <span className="size-[5px] rounded-full bg-text-disabled opacity-80 animate-pulse-dot" aria-hidden="true" />
      </div>
      <span className="text-[12px] text-text-disabled">
        {phaseLabel(phase ?? null, agentName)}
      </span>
    </div>
  )
}
