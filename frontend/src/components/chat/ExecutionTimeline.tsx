import type { ToolInvocationTrace } from '../../types'
import { isComputerUseTrace } from '../../lib/computerUse'
import { ToolRunCard } from './ToolRunCard'
import { ComputerUseViewport } from './ComputerUseViewport'

/** Tool / agent run row for the interleaved chat timeline */
export function ToolTimelineRow({ trace }: { readonly trace: ToolInvocationTrace }) {
  return (
    <li className="list-none animate-tool-enter">
      <ToolRunCard trace={trace} />
      {isComputerUseTrace(trace) && <ComputerUseViewport trace={trace} />}
    </li>
  )
}
