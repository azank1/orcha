import type { Artifact, ToolInvocationTrace } from '../types'

/**
 * Computer-use steps are dispatched with protocol 'computer_use' (see the
 * SuperAgent's invocation_start event + transcript tool_inputs). The name
 * fallback covers historical rows where the protocol field was not stored.
 */
export function isComputerUseTrace(trace: ToolInvocationTrace): boolean {
  if (trace.protocol?.toLowerCase() === 'computer_use') return true
  return /computer[-_ ]?use/i.test(trace.tool_name) || /computer[-_ ]?use/i.test(trace.agent_id)
}

export interface ComputerUseFrame {
  artifact_id: string
  /** 1-based step number parsed from the filename. */
  step: number
}

const FRAME_NAME_RE = /^computer-use-step-(\d+)\.png$/i

/**
 * Screenshot frames persisted by the computer-use backend are session
 * artifacts named `computer-use-step-{N}.png` (image/png) — see
 * services/superagent/handlers/computer_use_playwright.py. Returned sorted
 * by step so they can be played back as a flipbook.
 */
export function computerUseFrames(artifacts: Artifact[]): ComputerUseFrame[] {
  return artifacts
    .map((a) => {
      const m = FRAME_NAME_RE.exec(a.name)
      if (!m || !a.type.startsWith('image/')) return null
      return { artifact_id: a.artifact_id, step: Number(m[1]) }
    })
    .filter((f): f is ComputerUseFrame => f !== null)
    .sort((a, b) => a.step - b.step)
}
