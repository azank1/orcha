import { useState } from 'react'
import type { Artifact } from '../../types'
import { files, getAccessToken } from '../../api/client'
import { useSessionStore } from '../../store/session'
import { AgentCard } from '../agents/AgentCard'
import { ChecklistRow } from '../agents/ChecklistRow'
import { MetaStatsGrid } from '../ui/MetaStatsGrid'
import { Button } from '../ui/Button'
import { cn } from '../ui/cn'

type Tab = 'Agents' | 'Tasks' | 'Logs' | 'Meta' | 'Artifacts'
const TABS: Tab[] = ['Agents', 'Tasks', 'Logs', 'Meta', 'Artifacts']

export function RightPanel() {
  const [activeTab, setActiveTab] = useState<Tab>('Agents')

  const agents = useSessionStore((s) => s.agents)
  const checklist = useSessionStore((s) => s.checklist)
  const artifacts = useSessionStore((s) => s.artifacts)
  const interrupts = useSessionStore((s) => s.interrupts)
  const tokenUsage = useSessionStore((s) => s.tokenUsage)
  const elapsedSeconds = useSessionStore((s) => s.elapsedSeconds)
  const sessionLogs = useSessionStore((s) => s.sessionLogs)
  const sessionId = useSessionStore((s) => s.sessionId)
  const openSaveWorkflow = useSessionStore((s) => s.openSaveWorkflowModal)

  const stats = [
    { label: 'Tokens', value: tokenUsage.total > 0 ? `${tokenUsage.total.toLocaleString()}` : '—' },
    { label: 'Elapsed', value: elapsedSeconds > 0 ? `${elapsedSeconds}s` : '—' },
    { label: 'Credits', value: '—' },
    { label: 'Model', value: 'claude-sonnet' },
  ]

  return (
    <aside
      className="flex flex-col w-80 bg-surface-base border-l border-surface-border h-full"
      aria-label="Session details"
    >
      {/* Panel header */}
      <div className="h-14 px-4 flex items-center bg-surface-elevated border-b border-surface-border shrink-0">
        <span className="text-label font-semibold text-text-heading">Session Details</span>
        {interrupts.length > 0 && (
          <span className="ml-2 size-4 rounded-full bg-semantic-warning text-[9px] text-text-inverse flex items-center justify-center font-bold">
            {interrupts.length}
          </span>
        )}
      </div>

      {/* Tab bar */}
      <div className="flex items-center gap-1 px-2 py-1.5 bg-surface-elevated border-b border-surface-border shrink-0">
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            aria-selected={activeTab === tab}
            role="tab"
            className={cn(
              'flex-1 h-8 rounded-sm text-[11px] transition-colors duration-150',
              activeTab === tab
                ? 'bg-brand-primary-dim text-brand-primary-light font-medium'
                : 'text-text-secondary hover:text-text-body',
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin py-3">
        {activeTab === 'Agents' && (
          <div>
            <p className="px-4 mb-2 text-[10px] font-semibold text-text-disabled tracking-caps uppercase">
              Active Agents
            </p>
            {agents.length === 0 ? (
              <p className="px-4 text-caption text-text-disabled">No agents yet</p>
            ) : (
              <div className="flex flex-col gap-2 px-3">
                {agents.map((agent) => (
                  <AgentCard key={agent.agent_id} agent={agent} />
                ))}
              </div>
            )}

            {checklist.length > 0 && (
              <>
                <p className="px-4 mt-4 mb-2 text-[10px] font-semibold text-text-disabled tracking-caps uppercase">
                  Task Checklist
                </p>
                <div className="flex flex-col gap-1.5 px-3">
                  {checklist.map((task) => (
                    <ChecklistRow key={task.id} task={task} />
                  ))}
                </div>
              </>
            )}

            <div className="mt-4 px-3">
              <MetaStatsGrid stats={stats} />
            </div>
          </div>
        )}

        {activeTab === 'Tasks' && (
          <div>
            <p className="px-4 mb-2 text-[10px] font-semibold text-text-disabled tracking-caps uppercase">
              Task Checklist
            </p>
            {checklist.length === 0 ? (
              <p className="px-4 text-caption text-text-disabled">No tasks yet</p>
            ) : (
              <div className="flex flex-col gap-1.5 px-3">
                {checklist.map((task) => (
                  <ChecklistRow key={task.id} task={task} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'Meta' && (
          <div className="px-3">
            <MetaStatsGrid stats={stats} className="mb-3" />
          </div>
        )}

        {activeTab === 'Artifacts' && (
          <div className="px-3">
            {artifacts.length === 0 ? (
              <p className="text-caption text-text-disabled">No artifacts yet</p>
            ) : (
              <div className="flex flex-col gap-2">
                {artifacts.map((a) => (
                  <ArtifactPanelRow key={a.artifact_id} artifact={a} />
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === 'Logs' && (
          <div className="px-3">
            {sessionLogs.length === 0 ? (
              <p className="font-mono text-caption text-text-disabled">No logs yet</p>
            ) : (
              <ul className="flex flex-col gap-2" aria-label="Session activity log">
                {sessionLogs.map((entry) => (
                  <li
                    key={entry.id}
                    className="rounded-md border border-surface-border bg-surface-overlay px-2.5 py-2 font-mono text-caption text-text-secondary"
                  >
                    <span className="text-text-disabled">
                      {new Date(entry.timestamp).toLocaleTimeString(undefined, {
                        hour: '2-digit',
                        minute: '2-digit',
                        second: '2-digit',
                      })}
                    </span>{' '}
                    <span className="text-text-body">{entry.message}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {/* Save Workflow CTA */}
      {sessionId && (
        <div className="p-3 border-t border-surface-border shrink-0">
          <Button
            variant="primary"
            className="w-full"
            onClick={openSaveWorkflow}
          >
            💾 Save as Workflow
          </Button>
        </div>
      )}
    </aside>
  )
}

// ── Artifact panel row ─────────────────────────────────────────────────────────

function ArtifactPanelRow({ artifact }: { artifact: Artifact }) {
  const handleDownload = async () => {
    const token = getAccessToken()
    const url = files.download(artifact.artifact_id)
    try {
      const res = await fetch(url, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) return
      const blob = await res.blob()
      const blobUrl = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = blobUrl
      a.download = artifact.name
      a.click()
      URL.revokeObjectURL(blobUrl)
    } catch {
      // ignore
    }
  }

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-md bg-surface-overlay border border-surface-border">
      <span className="text-sm shrink-0">
        {artifact.type?.startsWith('image/') ? '🖼️' : artifact.type === 'application/pdf' ? '📕' : '📄'}
      </span>
      <div className="flex-1 min-w-0">
        <p className="text-label text-text-body truncate">{artifact.name}</p>
        <p className="text-caption text-text-disabled truncate">{artifact.type}</p>
      </div>
      <button
        onClick={handleDownload}
        aria-label={`Download ${artifact.name}`}
        className="shrink-0 size-7 flex items-center justify-center rounded-md hover:bg-surface-muted text-text-secondary hover:text-text-body transition-colors text-sm"
        title="Download"
      >
        ↓
      </button>
    </div>
  )
}
