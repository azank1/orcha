import { type KeyboardEvent, useRef, useEffect } from 'react'
import type { PendingArtifact } from '../../types'
import { ArtifactChip } from '../chat/ArtifactChip'
import { cn } from './cn'

interface InputBarProps {
  value: string
  onChange: (v: string) => void
  onSubmit: (v: string, artifactIds: string[]) => void
  onFileSelected?: (file: File) => void
  pendingArtifacts?: PendingArtifact[]
  onRemoveArtifact?: (artifactId: string) => void
  placeholder?: string
  disabled?: boolean
  isRunning?: boolean
  onStop?: () => void
  size?: 'home' | 'chat'
  className?: string
}

export function InputBar({
  value,
  onChange,
  onSubmit,
  onFileSelected,
  pendingArtifacts = [],
  onRemoveArtifact,
  placeholder,
  disabled,
  isRunning = false,
  onStop,
  size = 'home',
  className,
}: InputBarProps) {
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const el = inputRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [value])

  const readyArtifactIds = pendingArtifacts
    .filter((a) => !a.uploading && !a.error)
    .map((a) => a.artifact_id)

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (value.trim() || readyArtifactIds.length > 0) {
        onSubmit(value.trim(), readyArtifactIds)
      }
    }
  }

  const handleSend = () => {
    if (value.trim() || readyArtifactIds.length > 0) {
      onSubmit(value.trim(), readyArtifactIds)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && onFileSelected) {
      onFileSelected(file)
    }
    // Reset so the same file can be re-selected
    e.target.value = ''
  }

  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      {pendingArtifacts.length > 0 && (
        <div className="flex flex-wrap gap-1.5 px-1">
          {pendingArtifacts.map((artifact) => (
            <ArtifactChip
              key={artifact.artifact_id}
              artifact={artifact}
              onRemove={onRemoveArtifact ?? (() => {})}
            />
          ))}
        </div>
      )}

      <div
        className={cn(
          'relative flex items-end bg-surface-elevated border border-surface-borderLight rounded-lg',
          'focus-within:border-brand-primary focus-within:shadow-blue transition-all duration-150',
          size === 'home' ? 'min-h-14 px-4 py-2' : 'min-h-[52px] px-4 py-1.5',
        )}
      >
        {/* Paperclip button */}
        {onFileSelected && (
          <>
            <input
              ref={fileInputRef}
              type="file"
              className="sr-only"
              onChange={handleFileChange}
              accept=".pdf,.docx,.doc,.txt,.md,.csv,.json,.yaml,.yml,.png,.jpg,.jpeg,.gif,.webp,.mp3,.wav,.mp4"
              aria-label="Attach file"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
              aria-label="Attach file"
              className={cn(
                'mr-2 shrink-0 flex items-center justify-center rounded-md text-text-secondary',
                'hover:text-text-body hover:bg-surface-overlay transition-colors',
                'disabled:opacity-40 disabled:cursor-not-allowed',
                size === 'home' ? 'size-10 text-lg' : 'size-9 text-base',
              )}
            >
              📎
            </button>
          </>
        )}

        <textarea
          ref={inputRef}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder ?? 'Describe a task for your agent hive…'}
          disabled={disabled}
          rows={1}
          aria-label="Message input"
          className={cn(
            'flex-1 bg-transparent resize-none outline-none border-none text-body-md text-text-body',
            'placeholder:text-text-disabled leading-6 py-1 overflow-hidden',
            size === 'home' ? 'max-h-48' : 'max-h-32',
          )}
        />
        <button
          onClick={isRunning ? onStop : handleSend}
          disabled={
            isRunning
              ? !onStop
              : disabled || (!value.trim() && readyArtifactIds.length === 0)
          }
          aria-label={isRunning ? 'Stop execution' : 'Send message'}
          className={cn(
            'ml-2 shrink-0 flex items-center justify-center rounded-md bg-brand-primary text-white',
            'transition-colors duration-150 hover:bg-brand-primary-hover',
            'disabled:opacity-40 disabled:cursor-not-allowed disabled:shadow-none',
            size === 'home' ? 'size-10 text-lg shadow-blue' : 'size-9 text-base',
          )}
        >
          {isRunning ? '■' : '↑'}
        </button>
      </div>
    </div>
  )
}
