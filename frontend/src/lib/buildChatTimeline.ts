import type { ChatMessage, ToolInvocationTrace } from '../types'
import type { CanvasEntry } from '../types/canvas'

export type ChatTimelineItem =
  | { kind: 'message'; msg: ChatMessage }
  | { kind: 'tool'; trace: ToolInvocationTrace }
  | { kind: 'canvas'; entry: CanvasEntry }

function orderForMessage(msg: ChatMessage, index: number): number {
  if (msg.sortIndex != null) return msg.sortIndex
  return msg.timestamp * 1000 + index
}

function orderForTool(trace: ToolInvocationTrace, index: number): number {
  if (trace.sortIndex != null) return trace.sortIndex
  if (trace.startedAt != null) return trace.startedAt * 1000 + index
  return Number.MAX_SAFE_INTEGER - 10000 + index
}

/** Merge user / agent messages, tool runs, and canvas manifests in SSE arrival order. */
export function buildChatTimeline(
  messages: ChatMessage[],
  toolTrace: ToolInvocationTrace[],
  canvases: CanvasEntry[] = [],
): ChatTimelineItem[] {
  type Row = ChatTimelineItem & { order: number }
  const rows: Row[] = [
    ...messages.map((msg, i) => ({
      kind: 'message' as const,
      msg,
      order: orderForMessage(msg, i),
    })),
    ...toolTrace.map((trace, i) => ({
      kind: 'tool' as const,
      trace,
      order: orderForTool(trace, i),
    })),
    ...canvases.map((entry) => ({
      kind: 'canvas' as const,
      entry,
      order: entry.sortIndex,
    })),
  ]
  rows.sort((a, b) => a.order - b.order)
  return rows.map((r) => {
    if (r.kind === 'message') return { kind: 'message', msg: r.msg }
    if (r.kind === 'canvas') return { kind: 'canvas', entry: r.entry }
    return { kind: 'tool', trace: r.trace }
  })
}
