import type { ChecklistTask, ChecklistTaskStatus } from '../../types'
import { cn } from '../ui/cn'

const stateConfig: Record<
  ChecklistTaskStatus,
  { bg: string; border: string; icon: string; iconColor: string; textColor: string }
> = {
  done: {
    bg: 'bg-semantic-successDim',
    border: 'border-transparent',
    icon: '✓',
    iconColor: 'text-semantic-success',
    textColor: 'text-text-secondary',
  },
  running: {
    bg: 'bg-brand-primary-dim',
    border: 'border-[rgba(59,110,248,0.2)]',
    icon: '◐',
    iconColor: 'text-brand-primary',
    textColor: 'text-text-body',
  },
  pending: {
    bg: 'bg-surface-overlay',
    border: 'border-transparent',
    icon: '○',
    iconColor: 'text-surface-muted',
    textColor: 'text-text-secondary',
  },
  failed: {
    bg: 'bg-semantic-errorDim',
    border: 'border-[rgba(239,68,68,0.2)]',
    icon: '✕',
    iconColor: 'text-semantic-error',
    textColor: 'text-text-secondary',
  },
}

interface ChecklistRowProps {
  task: ChecklistTask
  className?: string
}

export function ChecklistRow({ task, className }: ChecklistRowProps) {
  const cfg = stateConfig[task.status]

  return (
    <div
      className={cn(
        'flex items-center gap-2 h-9 px-3 rounded-sm border',
        cfg.bg,
        cfg.border,
        className,
      )}
    >
      <span className={cn('text-[13px] leading-none shrink-0', cfg.iconColor)} aria-hidden="true">
        {cfg.icon}
      </span>
      <span className={cn('text-label truncate', cfg.textColor)}>{task.label}</span>
    </div>
  )
}
