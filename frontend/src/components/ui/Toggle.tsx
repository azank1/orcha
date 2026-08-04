import { cn } from './cn'

interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
  label?: string
  description?: string
  id?: string
}

export function Toggle({ checked, onChange, disabled, label, description, id }: ToggleProps) {
  const toggleId = id ?? 'toggle'

  return (
    <label
      htmlFor={toggleId}
      className={cn(
        'flex items-center gap-3 cursor-pointer select-none',
        disabled && 'opacity-50 cursor-not-allowed',
      )}
    >
      {(label || description) && (
        <span className="flex-1">
          {label && <span className="block text-body-md font-semibold text-text-heading">{label}</span>}
          {description && <span className="block text-caption text-text-secondary mt-0.5">{description}</span>}
        </span>
      )}
      <button
        id={toggleId}
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={cn(
          'relative inline-flex h-6 w-11 shrink-0 rounded-full border-2 border-transparent transition-colors duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary focus-visible:ring-offset-2 focus-visible:ring-offset-surface-canvas',
          checked ? 'bg-brand-primary' : 'bg-surface-border',
        )}
      >
        <span
          className={cn(
            'pointer-events-none inline-block size-5 rounded-full shadow transition-transform duration-200',
            checked ? 'translate-x-5 bg-white' : 'translate-x-0 bg-surface-muted',
          )}
        />
      </button>
    </label>
  )
}
