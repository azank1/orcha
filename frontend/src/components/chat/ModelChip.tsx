import { useByokStore } from '../../store/byok'

/**
 * Composer model chip — shows "hosted" or the BYOK model id; click opens the
 * onboarding modal. A dot indicates a system prompt is set.
 */
export function ModelChip() {
  const mode = useByokStore((s) => s.mode)
  const model = useByokStore((s) => s.model)
  const systemPrompt = useByokStore((s) => s.systemPrompt)
  const openOnboarding = useByokStore((s) => s.openOnboarding)

  return (
    <button
      type="button"
      onClick={openOnboarding}
      aria-label="Model and instructions settings"
      title="Model & instructions"
      className="flex h-7 items-center gap-1.5 rounded-full border border-surface-border bg-surface-elevated px-2.5 text-[11px] font-medium text-text-secondary transition-colors hover:border-surface-borderLight hover:text-text-body focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-primary"
    >
      {systemPrompt.trim() && (
        <span className="size-1.5 rounded-full bg-brand-primary" aria-hidden="true" />
      )}
      <span className="max-w-[220px] truncate">{mode === 'byok' ? model : 'hosted'}</span>
    </button>
  )
}
