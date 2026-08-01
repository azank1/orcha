import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Sidebar } from '../components/layout/Sidebar'
import { Badge } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { devAgents } from '../api/client'
import type { AgentListItem } from '../types'
import { cn } from '../components/ui/cn'

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

function healthBadgeVariant(status: AgentListItem['health_status']) {
  if (status === 'healthy') return 'active'
  if (status === 'unhealthy') return 'failed'
  return 'pending'
}

export function AgentLibrary() {
  const navigate = useNavigate()
  const qc = useQueryClient()
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['dev-agents', page, typeFilter, statusFilter],
    queryFn: () => devAgents.list({ page, limit: 20, protocol: typeFilter, status: statusFilter }),
  })

  const deleteMut = useMutation({
    mutationFn: (id: string) => devAgents.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['dev-agents'] }),
  })

  const agents = data?.data.agents ?? []
  const pagination = data?.data.pagination

  const filtered = agents.filter((a) =>
    a.name.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="flex h-screen bg-surface-canvas overflow-hidden">
      <Sidebar />

      <main className="flex-1 ml-16 flex flex-col overflow-hidden">
        {/* Header */}
        <div className="h-16 flex items-center px-6 bg-surface-base border-b border-surface-border shrink-0">
          <h1 className="text-h2 text-text-heading flex-1">My Agents</h1>
          <Button onClick={() => navigate('/agents/register')}>
            + Register Agent
          </Button>
        </div>

        {/* Filter bar */}
        <div className="flex items-center gap-3 px-6 h-12 bg-surface-elevated border-b border-surface-border shrink-0">
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search agents…"
            aria-label="Search agents"
            className="w-60 h-8 px-3 rounded-md bg-surface-overlay border border-surface-border text-label text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary"
          />
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            aria-label="Filter by type"
            className="h-8 px-2 rounded-md bg-surface-overlay border border-surface-border text-label text-text-body focus:outline-none focus:border-brand-primary cursor-pointer"
          >
            <option value="">Type: All</option>
            <option value="mcp">MCP</option>
            <option value="a2a">A2A</option>
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            aria-label="Filter by status"
            className="h-8 px-2 rounded-md bg-surface-overlay border border-surface-border text-label text-text-body focus:outline-none focus:border-brand-primary cursor-pointer"
          >
            <option value="">Status: All</option>
            <option value="healthy">Healthy</option>
            <option value="unhealthy">Unhealthy</option>
            <option value="unknown">Unknown</option>
          </select>
        </div>

        {/* Table header */}
        <div className="flex items-center px-6 h-11 border-b border-surface-border bg-surface-canvas shrink-0">
          <span className="flex-[2] text-caption font-semibold text-text-disabled tracking-caps uppercase">Agent Name</span>
          <span className="w-24 text-caption font-semibold text-text-disabled tracking-caps uppercase">Type</span>
          <span className="w-24 text-caption font-semibold text-text-disabled tracking-caps uppercase">Status</span>
          <span className="flex-1 text-caption font-semibold text-text-disabled tracking-caps uppercase">Registered</span>
          <span className="w-24 text-caption font-semibold text-text-disabled tracking-caps uppercase">Actions</span>
        </div>

        {/* Table rows */}
        <div className="flex-1 overflow-y-auto scrollbar-thin divide-y divide-surface-border">
          {isLoading && (
            <div className="px-6 py-4 text-text-secondary text-body-md">Loading…</div>
          )}
          {!isLoading && filtered.length === 0 && (
            <div className="px-6 py-4 text-text-secondary text-body-md">No agents found.</div>
          )}
          {filtered.map((agent) => (
            <AgentRow
              key={agent.id}
              agent={agent}
              onDelete={() => deleteMut.mutate(agent.id)}
            />
          ))}
        </div>

        {/* Pagination */}
        {pagination && pagination.total_pages > 1 && (
          <div className="flex items-center justify-center gap-3 px-6 py-3 border-t border-surface-border shrink-0">
            <Button
              variant="ghost"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
            >
              ← Prev
            </Button>
            <span className="text-label text-text-secondary">
              Page {pagination.page} of {pagination.total_pages}
            </span>
            <Button
              variant="ghost"
              size="sm"
              disabled={page >= pagination.total_pages}
              onClick={() => setPage((p) => p + 1)}
            >
              Next →
            </Button>
          </div>
        )}
      </main>
    </div>
  )
}

function AgentRow({
  agent,
  onDelete,
}: {
  agent: AgentListItem
  onDelete: () => void
}) {
  return (
    <div
      className={cn(
        'flex items-center px-6 h-14 transition-colors duration-100',
        'hover:bg-surface-elevated',
      )}
    >
      {/* Name */}
      <div className="flex-[2] flex items-center gap-2.5 min-w-0">
        <div className="size-6 rounded-full bg-brand-primary-dim flex items-center justify-center shrink-0">
          <span className="text-[10px] text-brand-primary font-bold">A</span>
        </div>
        <span className="text-body-md font-medium text-text-heading truncate">{agent.name}</span>
      </div>

      {/* Type */}
      <div className="w-24">
        <Badge variant={agent.protocol_type === 'mcp' ? 'mcp' : 'a2a'} />
      </div>

      {/* Status */}
      <div className="w-24">
        <Badge variant={healthBadgeVariant(agent.health_status)}>
          {agent.health_status}
        </Badge>
      </div>

      {/* Registered */}
      <div className="flex-1">
        <span className="text-[12px] text-text-secondary">{formatDate(agent.indexed_at)}</span>
      </div>

      {/* Actions */}
      <div className="w-24 flex items-center gap-3">
        <button
          aria-label={`Delete ${agent.name}`}
          onClick={onDelete}
          className="text-surface-muted hover:text-semantic-error transition-colors"
          title="Deactivate"
        >
          <span className="text-sm">🗑</span>
        </button>
      </div>
    </div>
  )
}
