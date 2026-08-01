import type { MarkdownCardSpec } from '../../types/canvas'

export function MarkdownCard({ spec }: { spec: MarkdownCardSpec }) {
  return (
    <div className="flex flex-col gap-1.5 rounded-xl bg-surface-overlay border border-surface-border px-5 py-4 shadow-sm">
      {spec.title && (
        <span className="text-[10px] font-semibold uppercase tracking-widest text-text-secondary">
          {spec.title}
        </span>
      )}
      <p className="whitespace-pre-wrap text-[13px] leading-relaxed text-text-secondary">
        {spec.body}
      </p>
    </div>
  )
}
