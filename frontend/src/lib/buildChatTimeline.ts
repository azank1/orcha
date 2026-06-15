import type { ChatMessage, ToolInvocationTrace } from '../types'

export type ChatTimelineItem =
  | { kind: 'message'; msg: ChatMessage }
  | { kind: 'tool'; trace: ToolInvocationTrace }

function orderForMessage(msg: ChatMessage, index: number): number {
  if (msg.sortIndex != null) return msg.sortIndex
  return msg.timestamp * 1000 + index
}

function orderForTool(trace: ToolInvocationTrace, index: number): number {
  if (trace.sortIndex != null) return trace.sortIndex
  if (trace.startedAt != null) return trace.startedAt * 1000 + index
  return Number.MAX_SAFE_INTEGER - 10000 + index
}

/** Merge user / agent messages and tool runs in SSE arrival order (via sortIndex). */
export function buildChatTimeline(
  messages: ChatMessage[],
  toolTrace: ToolInvocationTrace[],
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
  ]
  rows.sort((a, b) => a.order - b.order)
  return rows.map((r) =>
    r.kind === 'message' ? { kind: 'message', msg: r.msg } : { kind: 'tool', trace: r.trace },
  )
}
