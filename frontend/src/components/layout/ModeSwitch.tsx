import { cn } from '../ui/cn'
import { useSettingsStore } from '../../store/settings'

interface ModeSwitchProps {
  /** horizontal for top bars, vertical for the slim icon sidebar */
  direction?: 'horizontal' | 'vertical'
}

const OPTIONS = ['User', 'Developer'] as const

export function ModeSwitch({ direction = 'horizontal' }: ModeSwitchProps) {
  const isDevMode = useSettingsStore((s) => s.isDevMode)
  const setDevMode = useSettingsStore((s) => s.setDevMode)
  const vertical = direction === 'vertical'

  return (
    <div
      role="group"
      aria-label="Interface mode"
      className={cn(
        'relative flex rounded-full border border-surface-border bg-surface-base p-0.5 font-medium',
        vertical ? 'w-14 flex-col text-[10px]' : 'h-8 text-[12px]',
      )}
    >
      {/* Sliding thumb (transition defined in index.css under no-preference) */}
      <span
        aria-hidden="true"
        className={cn(
          'mode-thumb absolute rounded-full border border-surface-borderLight bg-surface-elevated shadow-sm',
          vertical
            ? 'inset-x-0.5 top-0.5 h-[calc(50%-2px)]'
            : 'inset-y-0.5 left-0.5 w-[calc(50%-2px)]',
          isDevMode && (vertical ? 'translate-y-full' : 'translate-x-full'),
        )}
      />
      {OPTIONS.map((label) => {
        const active = (label === 'Developer') === isDevMode
        return (
          <button
            key={label}
            type="button"
            aria-pressed={active}
            onClick={() => setDevMode(label === 'Developer')}
            className={cn(
              'relative z-10 flex items-center justify-center rounded-full transition-colors duration-150',
              'focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary',
              vertical ? 'h-7 w-full' : 'h-full px-3',
              active ? 'text-text-heading' : 'text-text-secondary hover:text-text-body',
            )}
          >
            {label}
          </button>
        )
      })}
    </div>
  )
}
