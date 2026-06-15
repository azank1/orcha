import { cn } from './cn'

type BadgeVariant = 'mcp' | 'a2a' | 'native' | 'active' | 'pending' | 'failed' | 'running'

interface BadgeProps {
  variant: BadgeVariant
  className?: string
  children?: React.ReactNode
}

const variantClasses: Record<BadgeVariant, string> = {
  mcp: 'bg-brand-primary-dim text-brand-primary border-[#1A3060]',
  a2a: 'bg-brand-secondary-dim text-brand-secondary border-[#005060]',
  native: 'bg-semantic-purpleDim text-semantic-purple border-[#2D1A60]',
  active: 'bg-semantic-successDim text-semantic-success border-[#0A4A26]',
  pending: 'bg-semantic-warningDim text-semantic-warning border-[#2D2000]',
  failed: 'bg-semantic-errorDim text-semantic-error border-[#3D1212]',
  running: 'bg-[#0A1230] text-brand-primary-light border-[#1A2248]',
}

const defaultLabels: Record<BadgeVariant, string> = {
  mcp: 'MCP',
  a2a: 'A2A',
  native: 'Native',
  active: 'Active',
  pending: 'Pending',
  failed: 'Failed',
  running: 'Running',
}

export function Badge({ variant, className, children }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center h-[26px] px-[10px] rounded-xs border',
        'text-caption font-semibold tracking-[0.6px] uppercase',
        variantClasses[variant],
        className,
      )}
    >
      {children ?? defaultLabels[variant]}
    </span>
  )
}

interface StatusDotProps {
  status: 'running' | 'done' | 'pending'
  className?: string
}

const dotColors: Record<StatusDotProps['status'], string> = {
  running: 'bg-brand-primary animate-glow-pulse',
  done: 'bg-semantic-success',
  pending: 'bg-surface-muted',
}

export function StatusDot({ status, className }: StatusDotProps) {
  return (
    <span
      className={cn('inline-block size-2 rounded-full', dotColors[status], className)}
      aria-label={status}
    />
  )
}
