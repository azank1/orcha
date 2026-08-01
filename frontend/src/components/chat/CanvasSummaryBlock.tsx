import { useState } from 'react'
import { ChatMarkdown } from './ChatMarkdown'

/**
 * Collapsed summary block shown instead of a full agent message bubble
 * when the response appears after a canvas has already been rendered.
 * The canvas is the primary output; this text is supplementary.
 */
export function CanvasSummaryBlock({ content }: { content: string }) {
  const [expanded, setExpanded] = useState(false)

  if (!content.trim()) return null

  // Extract first sentence as the preview label
  const firstSentence = content.split(/[.\n]/)[0]?.trim() ?? ''
  const preview = firstSentence.length > 80 ? firstSentence.slice(0, 80) + '…' : firstSentence

  return (
    <div className="flex justify-start">
      <div className="max-w-[560px] w-full">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="flex w-full items-center gap-2 rounded-lg border border-surface-borderLight bg-surface-base px-3 py-2 text-left transition-colors hover:bg-surface-overlay"
          aria-expanded={expanded}
        >
          <span className="shrink-0 text-[11px] text-semantic-success" aria-hidden>✓</span>
          <span className="flex-1 truncate text-[12px] text-text-secondary">{preview || 'Agent summary'}</span>
          <span className="shrink-0 text-[11px] text-text-disabled">{expanded ? '▲' : '▼'}</span>
        </button>
        {expanded && (
          <div className="mt-1 rounded-lg border border-surface-borderLight bg-surface-base px-4 py-3">
            <ChatMarkdown tone="agent">{content}</ChatMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}
