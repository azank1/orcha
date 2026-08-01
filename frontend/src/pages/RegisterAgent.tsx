import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Sidebar } from '../components/layout/Sidebar'
import { Button } from '../components/ui/Button'
import { Badge } from '../components/ui/Badge'
import { Logo } from '../components/ui/Logo'
import { devAgents } from '../api/client'
import type { RegisterAgentResponse } from '../types'

interface ParsedManifest {
  name?: string
  description?: string
  protocol_type?: 'mcp' | 'a2a'
  version?: string
  auth_required?: boolean
  capabilities?: string[]
}

function parseYaml(text: string): ParsedManifest {
  const lines = text.split('\n')
  const get = (key: string) => {
    const line = lines.find((l) => l.trimStart().startsWith(`${key}:`))
    return line ? line.split(':').slice(1).join(':').trim() : undefined
  }
  return {
    name: get('name'),
    description: get('description'),
    protocol_type: (get('protocol_type') ?? get('type')) as 'mcp' | 'a2a' | undefined,
    version: get('version'),
    auth_required: get('auth_required') === 'true',
  }
}

export function RegisterAgent() {
  const navigate = useNavigate()
  const [file, setFile] = useState<File | null>(null)
  const [yamlText, setYamlText] = useState('')
  const [manifest, setManifest] = useState<ParsedManifest | null>(null)
  const [result, setResult] = useState<RegisterAgentResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [registering, setRegistering] = useState(false)
  const [dragging, setDragging] = useState(false)
  const [editingYaml, setEditingYaml] = useState(false)

  const handleFile = useCallback((f: File) => {
    setFile(f)
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      setYamlText(text)
      setManifest(parseYaml(text))
    }
    reader.readAsText(f)
  }, [])

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  const handleRegister = async () => {
    if (!file) return
    setRegistering(true)
    setError(null)
    try {
      const uploadFile = new File([yamlText], file.name, { type: 'text/yaml' })
      const res = await devAgents.register(uploadFile)
      setResult(res)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Registration failed')
    } finally {
      setRegistering(false)
    }
  }

  return (
    <div className="flex h-screen bg-surface-canvas overflow-hidden">
      <Sidebar />

      <main className="flex-1 ml-16 overflow-y-auto scrollbar-thin">
        {/* Header */}
        <div className="h-16 flex flex-col justify-center px-6 border-b border-surface-border bg-surface-base sticky top-0 z-10">
          <h1 className="text-h2 text-text-heading">Register Agent</h1>
          <nav className="text-[12px] text-text-secondary mt-0.5" aria-label="Breadcrumb">
            <button onClick={() => navigate('/agents')} className="hover:text-text-body transition-colors">My Agents</button>
            <span className="mx-1">/</span>
            <span>Register</span>
          </nav>
        </div>

        {result ? (
          <div className="max-w-xl mx-auto mt-16 px-6">
            <div className="p-6 rounded-lg bg-surface-elevated border border-semantic-successDim text-center">
              <p className="text-3xl mb-3">✅</p>
              <h2 className="text-h3 text-text-heading mb-1">Agent Registered!</h2>
              <p className="text-body-md text-text-secondary mb-2">{result.data.name} v{result.data.version}</p>
              <p className="text-caption text-text-disabled mb-4">
                Tools: {result.data.capabilities_harvested.tools} · Resources: {result.data.capabilities_harvested.resources} · Prompts: {result.data.capabilities_harvested.prompts}
              </p>
              <Button onClick={() => navigate('/agents')}>Back to Agent Library</Button>
            </div>
          </div>
        ) : (
          <div className="flex gap-16 px-10 py-10 max-w-[1200px] min-w-0 overflow-hidden">
            {/* LEFT: Form */}
            <div className="w-[540px] shrink-0 flex flex-col gap-5">
              <p className="text-caption font-medium text-text-secondary">Step 1 of 2 — Upload emerge.yaml</p>

              {!file ? (
                /* Drop zone */
                <div
                  onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                  onDragLeave={() => setDragging(false)}
                  onDrop={handleDrop}
                  className={`flex flex-col items-center justify-center gap-2 h-[140px] rounded-lg border-2 border-dashed transition-colors cursor-pointer ${dragging ? 'border-brand-primary bg-brand-primary-dim/30' : 'border-surface-borderLight bg-surface-elevated'}`}
                >
                  <span className="text-3xl" aria-hidden="true">📎</span>
                  <p className="text-body-md text-text-secondary">Drop emerge.yaml here or click to browse</p>
                  <label className="cursor-pointer">
                    <span className="flex items-center justify-center h-[34px] px-4 rounded-md bg-surface-overlay border border-surface-borderLight text-label text-text-body hover:bg-surface-muted/10 transition-colors">
                      Browse
                    </span>
                    <input
                      type="file"
                      accept=".yaml,.yml"
                      className="hidden"
                      aria-label="Upload emerge.yaml"
                      onChange={(e) => {
                        const f = e.target.files?.[0]
                        if (f) handleFile(f)
                      }}
                    />
                  </label>
                </div>
              ) : (
                /* Selected chip */
                <div className="flex items-center h-11 px-3 rounded-md bg-semantic-successDim border border-[#0A4A26]">
                  <span className="text-label font-medium text-semantic-success flex-1 truncate">
                    📄 {file.name}
                  </span>
                  <button
                    onClick={() => { setFile(null); setManifest(null); setYamlText('') }}
                    aria-label="Remove file"
                    className="text-text-secondary hover:text-text-body text-lg ml-2"
                  >
                    ×
                  </button>
                </div>
              )}

              {/* Parsed fields */}
              {manifest && (
                <div className="flex flex-col gap-3">
                  <p className="text-body-lg font-semibold text-text-heading">Agent Information</p>
                  <Field label="Agent Name" value={manifest.name ?? '—'} />
                  <Field label="Protocol Type" value={manifest.protocol_type ? (
                    <Badge variant={manifest.protocol_type === 'mcp' ? 'mcp' : 'a2a'} />
                  ) : '—'} />
                  <Field label="Version" value={manifest.version ?? '—'} />
                  <Field label="Description" value={manifest.description ?? '—'} textarea />
                  <Field label="Auth Required" value={manifest.auth_required ? 'Yes' : 'No'} />
                </div>
              )}

              {error && <p className="text-caption text-semantic-error">{error}</p>}

              <Button
                onClick={handleRegister}
                loading={registering}
                disabled={!file}
                className="w-full h-11"
              >
                Register Agent
              </Button>
            </div>

            {/* RIGHT: Preview card */}
            <div className="flex-1 min-w-0">
              {manifest ? (
                <div className="rounded-lg bg-surface-elevated border border-surface-border p-6 flex flex-col gap-4 overflow-hidden">
                  <div className="flex items-center gap-3">
                    <div className="size-11 rounded-[10px] bg-brand-primary-dim flex items-center justify-center">
                      <Logo size={28} />
                    </div>
                    <div className="flex-1">
                      <p className="text-body-lg font-semibold text-text-heading">{manifest.name ?? 'Agent'}</p>
                    </div>
                    {manifest.protocol_type && (
                      <Badge variant={manifest.protocol_type === 'mcp' ? 'mcp' : 'a2a'} />
                    )}
                  </div>

                  {manifest.description && (
                    <p className="text-body-md text-text-secondary">{manifest.description}</p>
                  )}

                  <div className="border-t border-surface-border" />

                  {yamlText && (
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <p className="text-[12px] font-semibold text-text-disabled tracking-caps uppercase">emerge.yaml</p>
                        <button
                          onClick={() => setEditingYaml((v) => !v)}
                          className="text-[11px] text-brand-primary-light hover:text-text-body transition-colors"
                        >
                          {editingYaml ? 'Done' : 'Edit'}
                        </button>
                      </div>
                      {editingYaml ? (
                        <textarea
                          className="w-full p-3 rounded-md bg-surface-canvas text-[12px] font-mono text-brand-primary-light border border-brand-primary/40 focus:outline-none focus:border-brand-primary resize-y min-h-[160px] scrollbar-thin"
                          value={yamlText}
                          onChange={(e) => {
                            setYamlText(e.target.value)
                            setManifest(parseYaml(e.target.value))
                          }}
                          spellCheck={false}
                        />
                      ) : (
                        <pre className="p-3 rounded-md bg-surface-canvas text-[12px] font-mono text-brand-primary-light overflow-x-auto max-h-40 scrollbar-thin">
                          {yamlText.slice(0, 500)}{yamlText.length > 500 ? '…' : ''}
                        </pre>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center h-64 rounded-lg border border-dashed border-surface-border text-text-disabled text-body-md">
                  Upload a file to preview
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

function Field({
  label,
  value,
  textarea,
}: {
  label: string
  value: React.ReactNode
  textarea?: boolean
}) {
  return (
    <div className="flex flex-col gap-1">
      <span className="text-[12px] font-medium text-text-secondary">{label}</span>
      {textarea ? (
        <div className="min-h-[72px] px-3 py-2 rounded-md bg-surface-elevated border border-surface-border text-label text-text-body">
          {value}
        </div>
      ) : (
        <div className="h-10 flex items-center px-3 rounded-md bg-surface-elevated border border-surface-border text-label text-text-body">
          {value}
        </div>
      )}
    </div>
  )
}
