import type {
  AgentInfo,
  Artifact,
  ChecklistTask,
  ChecklistTaskStatus,
  Interrupt,
  InterruptType,
  SessionStatusResponse,
} from '../types'
import { coerceTokenCount } from './coerceTokenCount'

const STEP_STATUS: Record<string, ChecklistTaskStatus> = {
  pending: 'pending',
  in_progress: 'running',
  done: 'done',
  failed: 'failed',
}

function mapChecklist(raw: unknown): ChecklistTask[] {
  if (!raw || typeof raw !== 'object') return []
  const tc = raw as Record<string, unknown>
  const steps = tc.steps
  if (!Array.isArray(steps)) return []
  const out: ChecklistTask[] = []
  for (const s of steps) {
    if (!s || typeof s !== 'object') continue
    const o = s as Record<string, unknown>
    const id = String(o.step_id ?? '')
    const label = String(o.description ?? '')
    const st = String(o.status ?? 'pending')
    const status = STEP_STATUS[st] ?? 'pending'
    out.push({ id, label, status })
  }
  return out
}

function mapAgents(raw: unknown): AgentInfo[] {
  if (!Array.isArray(raw)) return []
  return raw.map((c) => {
    const o = (c && typeof c === 'object' ? c : {}) as Record<string, unknown>
    const protocol = String(o.protocol_type ?? '').toLowerCase()
    const type: AgentInfo['type'] =
      protocol === 'mcp' ? 'mcp' : protocol === 'a2a' ? 'a2a' : 'native'
    return {
      agent_id: String(o.agent_id ?? ''),
      name: String(o.agent_name ?? o.agent_id ?? 'Agent'),
      type,
      status: 'pending',
    }
  })
}

function mapArtifacts(record: Record<string, unknown>): Artifact[] {
  return Object.entries(record).map(([key, v]) => {
    const o = (v && typeof v === 'object' ? v : {}) as Record<string, unknown>
    const aid = String(o.artifact_id ?? key)
    const mime = String(o.mime_type ?? 'application/octet-stream')
    const label = String(
      o.filename ?? o.name ?? o.description ?? aid,
    )
    return {
      artifact_id: aid,
      name: label,
      type: mime,
    }
  })
}

function mapActiveInterrupt(raw: unknown): Interrupt | null {
  if (!raw || typeof raw !== 'object') return null
  const p = raw as Record<string, unknown>
  const id = String(p.interrupt_id ?? '')
  if (!id) return null
  const VALID_TYPES = new Set<InterruptType>([
    'AUTH_CALLBACK', 'AUTH_FORM_SUBMISSION', 'AGENT_OAUTH_CALLBACK',
    'HITL_APPROVAL', 'HITL_CLARIFICATION', 'AGENT_CLARIFICATION',
    'CRM_SETUP',
    'INSUFFICIENT_CREDITS',
  ])
  const rawType = String(p.interrupt_type ?? '')
  const interrupt_type: InterruptType = VALID_TYPES.has(rawType as InterruptType)
    ? (rawType as InterruptType)
    : 'HITL_CLARIFICATION'
  const metadata = p.metadata && typeof p.metadata === 'object'
    ? (p.metadata as Record<string, unknown>)
    : {}
  return {
    interrupt_id: id,
    interrupt_type,
    message: String(p.message ?? ''),
    metadata,
  }
}

/** Maps GET /sessions/:id/status JSON into store-ready slices. */
export function mapSessionStatusResponse(data: SessionStatusResponse) {
  const interrupt = mapActiveInterrupt(data.active_interrupt)
  return {
    agents: mapAgents(data.pnd_candidates),
    checklist: mapChecklist(data.task_checklist),
    artifacts: mapArtifacts(
      data.artifacts && typeof data.artifacts === 'object'
        ? (data.artifacts as Record<string, unknown>)
        : {},
    ),
    interrupts: interrupt ? [interrupt] : [],
    tokenUsage: {
      input: 0,
      output: 0,
      total: coerceTokenCount(data.estimated_token_count),
    },
  }
}
