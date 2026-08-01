import { files } from '../../api/client'
import { getAccessToken } from '../../api/client'

interface ArtifactCardProps {
  artifactId: string
  filename: string
  mimeType: string
  sizeBytes: number
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes}B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
}

function fileIcon(mimeType: string): string {
  if (mimeType.startsWith('image/')) return '🖼️'
  if (mimeType.startsWith('audio/')) return '🎵'
  if (mimeType.startsWith('video/')) return '🎬'
  if (mimeType === 'application/pdf') return '📕'
  if (mimeType.includes('word') || mimeType.includes('document')) return '📝'
  if (mimeType === 'text/csv') return '📊'
  return '📄'
}

export function ArtifactCard({ artifactId, filename, mimeType, sizeBytes }: ArtifactCardProps) {
  const downloadUrl = files.download(artifactId)

  const handleDownload = async (e: React.MouseEvent) => {
    e.preventDefault()
    const token = getAccessToken()
    const res = await fetch(downloadUrl, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    })
    if (!res.ok) return
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex items-center gap-3 px-3 py-2.5 rounded-md bg-surface-overlay border border-surface-border max-w-xs">
      <span className="text-xl shrink-0">{fileIcon(mimeType)}</span>
      <div className="flex-1 min-w-0">
        <p className="text-label text-text-body truncate">{filename}</p>
        <p className="text-caption font-mono text-text-disabled">{formatBytes(sizeBytes)}</p>
      </div>
      <button
        onClick={handleDownload}
        aria-label={`Download ${filename}`}
        className="shrink-0 h-7 px-2 rounded-md bg-brand-primary text-white text-[11px] font-medium hover:bg-brand-primary-hover transition-colors"
      >
        ↓
      </button>
    </div>
  )
}
