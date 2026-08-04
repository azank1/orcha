import type { PendingArtifact } from '../../types'
import { cn } from '../ui/cn'

interface ArtifactChipProps {
  artifact: PendingArtifact
  onRemove: (artifactId: string) => void
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}

export function ArtifactChip({ artifact, onRemove }: ArtifactChipProps) {
  return (
    <div
      className={cn(
        'inline-flex items-center gap-1.5 h-7 pl-2.5 pr-1 rounded-full border text-[12px]',
        artifact.error
          ? 'border-semantic-error bg-semantic-errorDim text-semantic-error'
          : 'border-surface-border bg-surface-overlay text-text-body',
      )}
    >
      {artifact.uploading ? (
        <span className="animate-pulse">⏳</span>
      ) : artifact.error ? (
        <span>⚠</span>
      ) : (
        <span>📎</span>
      )}
      <span className="max-w-[140px] truncate">{artifact.filename}</span>
      {!artifact.uploading && !artifact.error && (
        <span className="font-mono text-text-disabled">{formatBytes(artifact.size_bytes)}</span>
      )}
      {artifact.error && <span className="text-[11px]">{artifact.error}</span>}
      <button
        onClick={() => onRemove(artifact.artifact_id)}
        aria-label={`Remove ${artifact.filename}`}
        className="size-5 flex items-center justify-center rounded-full hover:bg-surface-muted text-text-secondary hover:text-text-body transition-colors"
      >
        ×
      </button>
    </div>
  )
}
