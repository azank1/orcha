import { type ButtonHTMLAttributes } from 'react'
import { cn } from './cn'

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'accent'
type Size = 'sm' | 'md' | 'lg'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant
  size?: Size
  loading?: boolean
}

const variantClasses: Record<Variant, string> = {
  primary:
    'bg-brand-primary text-white border-transparent hover:bg-brand-primary-hover',
  secondary:
    'bg-surface-elevated text-brand-primary border-surface-border hover:bg-surface-overlay',
  ghost:
    'bg-transparent text-text-body border-surface-border hover:bg-surface-overlay',
  danger:
    'bg-semantic-errorDim text-semantic-error border-[#3D1212] hover:bg-[#3D1010]',
  accent:
    'bg-brand-secondary-dim text-brand-secondary border-[#005060] hover:bg-[#003A42]',
}

const sizeClasses: Record<Size, string> = {
  sm: 'h-8 px-3 text-xs',
  md: 'h-10 px-4 text-label',
  lg: 'h-11 px-5 text-body-md',
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading,
  disabled,
  className,
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 rounded-md border font-medium transition-colors duration-150',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 focus-visible:ring-offset-surface-canvas',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    >
      {loading ? (
        <span className="size-4 rounded-full border-2 border-current border-t-transparent animate-spin" aria-hidden="true" />
      ) : null}
      {children}
    </button>
  )
}
