import type {
  AgentInfo,
  Artifact,
  ChecklistTask,
  Interrupt,
  SessionLogEntry,
  SessionStatusResponse,
} from '../types'
import { coerceTokenCount } from './coerceTokenCount'
import { mapSessionStatusResponse } from './mapSessionStatus'

export interface SessionDetailsSlice {
  agents: AgentInfo[]
  checklist: ChecklistTask[]
  artifacts: Artifact[]
  tokenUsage: { input: number; output: number; total: number }
  sessionLogs: SessionLogEntry[]
  interrupts?: Interrupt[]
}

/** Union PnD / discovery lists by agent_id; preserve richer runtime status from the client. */
export function mergeAgentsAdditive(prev: AgentInfo[], incoming: AgentInfo[]): AgentInfo[] {
  if (incoming.length === 0) return prev
  const map = new Map(prev.map((a) => [a.agent_id, { ...a }]))
  for (const a of incoming) {
    if (!a.agent_id) continue
    const ex = map.get(a.agent_id)
    if (ex) {
      map.set(a.agent_id, {
        ...a,
        name: a.name || ex.name,
        type: a.type,
        status: ex.status,
      })
    } else {
      map.set(a.agent_id, a)
    }
  }
  return Array.from(map.values())
}

/** Merge checklist steps by id; if the snapshot has no steps, keep the previous checklist. */
export function mergeChecklistAdditive(prev: ChecklistTask[], incoming: ChecklistTask[]): ChecklistTask[] {
  if (incoming.length === 0) return prev
  const map = new Map(prev.map((t) => [t.id, t]))
  for (const t of incoming) {
    if (t.id) map.set(t.id, t)
  }
  return Array.from(map.values())
}

/** Merge artifacts by id; empty snapshot does not clear SSE-accumulated artifacts. */
export function mergeArtifactsAdditive(prev: Artifact[], incoming: Artifact[]): Artifact[] {
  if (incoming.length === 0) return prev
  const map = new Map(prev.map((a) => [a.artifact_id, a]))
  for (const a of incoming) {
    map.set(a.artifact_id, a)
  }
  return Array.from(map.values())
}

/** Treat counts as monotonic session totals (status + SSE). */
export function mergeTokenUsageAdditive(
  prev: SessionDetailsSlice['tokenUsage'],
  incoming: SessionDetailsSlice['tokenUsage'],
): SessionDetailsSlice['tokenUsage'] {
  const pi = coerceTokenCount(prev.input)
  const po = coerceTokenCount(prev.output)
  const pt = coerceTokenCount(prev.total)
  const ii = coerceTokenCount(incoming.input)
  const io = coerceTokenCount(incoming.output)
  const it = coerceTokenCount(incoming.total)
  return {
    input: Math.max(pi, ii),
    output: Math.max(po, io),
    total: Math.max(pt, it),
  }
}

function parseActivityLogFromStatus(data: SessionStatusResponse): SessionLogEntry[] {
  const ext = data as SessionStatusResponse & {
    activity_log?: unknown
    session_logs?: unknown
  }
  const raw = ext.activity_log ?? ext.session_logs
  if (!Array.isArray(raw)) return []
  const out: SessionLogEntry[] = []
  for (const item of raw) {
    if (!item || typeof item !== 'object') continue
    const o = item as Record<string, unknown>
    const message = String(o.message ?? o.text ?? o.msg ?? '')
    if (!message) continue
    const id =
      typeof o.id === 'string' && o.id
        ? o.id
        : typeof o.entry_id === 'string' && o.entry_id
          ? o.entry_id
          : crypto.randomUUID()
    let ts = Date.now()
    if (typeof o.timestamp === 'number') ts = o.timestamp
    else if (typeof o.timestamp === 'string') {
      const n = Date.parse(o.timestamp)
      if (!Number.isNaN(n)) ts = n
    } else if (typeof o.at === 'string') {
      const n = Date.parse(o.at)
      if (!Number.isNaN(n)) ts = n
    }
    out.push({ id, timestamp: ts, message })
  }
  return out
}

/** Append API log lines; skip ids already present. */
export function mergeSessionLogsAdditive(prev: SessionLogEntry[], incoming: SessionLogEntry[]): SessionLogEntry[] {
  if (incoming.length === 0) return prev
  const seen = new Set(prev.map((e) => e.id))
  const next = [...prev]
  for (const e of incoming) {
    if (seen.has(e.id)) continue
    seen.add(e.id)
    next.push(e)
  }
  return next.sort((a, b) => a.timestamp - b.timestamp)
}

/**
 * Fold a GET /sessions/:id/status response into existing session details.
 * Agents, artifacts, and logs are additive; token totals only increase.
 * Checklist: merged when the API sends a checklist object; cleared when `task_checklist` is null.
 */
export function reduceSessionDetailsFromStatus(
  prev: SessionDetailsSlice,
  data: SessionStatusResponse,
): SessionDetailsSlice {
  const mapped = mapSessionStatusResponse(data)
  const fromApiLogs = parseActivityLogFromStatus(data)

  let checklist: ChecklistTask[]
  if (data.task_checklist === null) {
    checklist = []
  } else {
    checklist = mergeChecklistAdditive(prev.checklist, mapped.checklist)
  }

  return {
    agents: mergeAgentsAdditive(prev.agents, mapped.agents),
    checklist,
    artifacts: mergeArtifactsAdditive(prev.artifacts, mapped.artifacts),
    tokenUsage: mergeTokenUsageAdditive(prev.tokenUsage, mapped.tokenUsage),
    sessionLogs: mergeSessionLogsAdditive(prev.sessionLogs, fromApiLogs),
    interrupts: mapped.interrupts,
  }
}
