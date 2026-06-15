import type { ToolInvocationTrace } from '../../types'
import { ToolRunCard } from './ToolRunCard'

/** Tool / agent run row for the interleaved chat timeline */
export function ToolTimelineRow({ trace }: { readonly trace: ToolInvocationTrace }) {
  return (
    <li className="list-none border-l-2 border-surface-borderLight pl-4 ml-2">
      <ToolRunCard trace={trace} />
    </li>
  )
}
