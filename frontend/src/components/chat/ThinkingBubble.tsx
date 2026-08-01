import { useEffect, useRef, useState } from 'react'

interface ThinkingBubbleProps {
  content: string
  streaming: boolean
}

/**
 * Shows the orchestrator's ReAct reasoning as a collapsible "Thinking" block —
 * like Claude's extended thinking. Collapsed by default while streaming;
 * when streaming ends and content is empty (pure tool-call turn), renders nothing.
 */
export function ThinkingBubble({ content, streaming }: ThinkingBubbleProps) {
  const [expanded, setExpanded] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom of content while streaming
  useEffect(() => {
    if (streaming && expanded && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [content, streaming, expanded])

  // When streaming finishes with no content, render nothing
  if (!streaming && !content.trim()) return null

  return (
    <div className="flex justify-start">
      <div className="max-w-[560px] w-full">
        <button
          type="button"
          onClick={() => setExpanded((v) => !v)}
          className="flex w-full items-center gap-2 rounded-lg border border-surface-borderLight bg-surface-base px-3 py-2 text-left transition-colors hover:bg-surface-overlay"
          aria-expanded={expanded}
        >
          {/* Animated thinking dots or static checkmark */}
          {streaming ? (
            <span className="flex shrink-0 items-center gap-0.5" aria-hidden>
              <span className="size-[5px] rounded-full bg-text-disabled opacity-50 animate-pulse-dot" />
              <span className="size-[5px] rounded-full bg-text-disabled opacity-65 animate-pulse-dot" />
              <span className="size-[5px] rounded-full bg-text-disabled opacity-80 animate-pulse-dot" />
            </span>
          ) : (
            <span className="shrink-0 text-[11px] text-text-disabled" aria-hidden>✓</span>
          )}
          <span className="flex-1 text-[12px] font-medium text-text-secondary">
            {streaming ? 'Thinking…' : 'Thought for a moment'}
          </span>
          <span className="shrink-0 text-[11px] text-text-disabled" aria-hidden>
            {expanded ? '▲' : '▼'}
          </span>
        </button>

        {expanded && (
          <div
            ref={scrollRef}
            className="mt-1 max-h-48 overflow-y-auto rounded-lg border border-surface-borderLight bg-surface-base px-3 py-2 scrollbar-thin"
          >
            <p className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-text-secondary">
              {content}
              {streaming && (
                <span className="ml-0.5 inline-block h-3 w-0.5 animate-pulse bg-text-disabled align-text-bottom" aria-hidden />
              )}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
