import { useState } from 'react'
import { useSessionStore } from '../../store/session'
import { workflows } from '../../api/client'
import { Button } from '../ui/Button'

export function SaveWorkflowModal() {
  const sessionId = useSessionStore((s) => s.sessionId)
  const isOpen = useSessionStore((s) => s.saveWorkflowModalOpen)
  const close = useSessionStore((s) => s.closeSaveWorkflowModal)

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  if (!isOpen) return null

  const handleSave = async () => {
    if (!name.trim() || !sessionId) return
    setSaving(true)
    setError(null)
    try {
      await workflows.create(sessionId, name.trim(), description.trim() || undefined)
      setSaved(true)
      setTimeout(() => {
        setSaved(false)
        setName('')
        setDescription('')
        close()
      }, 1500)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to save workflow')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center" role="dialog" aria-modal="true" aria-label="Save workflow">
      <div className="absolute inset-0 bg-surface-canvas/70" onClick={close} aria-hidden="true" />
      <div className="relative w-[420px] bg-surface-elevated border border-surface-border rounded-lg shadow-lg p-6 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <h2 className="text-h3 text-text-heading">Save as Workflow</h2>
          <button onClick={close} aria-label="Close" className="text-text-secondary hover:text-text-body text-lg">×</button>
        </div>

        {saved ? (
          <div className="flex items-center gap-2 text-semantic-success">
            <span>✓</span>
            <span className="text-body-md">Workflow saved!</span>
          </div>
        ) : (
          <>
            <div className="flex flex-col gap-1">
              <label htmlFor="wf-name" className="text-caption font-medium text-text-secondary">Workflow Name *</label>
              <input
                id="wf-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Gmail Inbox Management"
                className="h-10 px-3 rounded-md bg-surface-base border border-surface-borderLight text-label text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary"
              />
            </div>
            <div className="flex flex-col gap-1">
              <label htmlFor="wf-desc" className="text-caption font-medium text-text-secondary">Description (optional)</label>
              <textarea
                id="wf-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What does this workflow do?"
                rows={3}
                className="px-3 py-2 rounded-md bg-surface-base border border-surface-borderLight text-label text-text-body placeholder:text-text-disabled focus:outline-none focus:border-brand-primary resize-none"
              />
            </div>
            {error && <p className="text-caption text-semantic-error">{error}</p>}
            <div className="flex gap-2 justify-end">
              <Button variant="ghost" onClick={close}>Cancel</Button>
              <Button onClick={handleSave} loading={saving} disabled={!name.trim()}>Save Workflow</Button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
