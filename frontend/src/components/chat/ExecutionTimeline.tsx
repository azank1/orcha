import type { ToolInvocationTrace } from '../../types'
import { ToolRunCard } from './ToolRunCard'

/** Tool / agent run row for the interleaved chat timeline */
export function ToolTimelineRow({ trace }: { readonly trace: ToolInvocationTrace }) {
  return (
    <li className="list-none animate-tool-enter">
      <ToolRunCard trace={trace} />
    </li>
  )
}
