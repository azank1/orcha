import type { ChatMessage } from '../../types'
import { cn } from '../ui/cn'
import { ChatMarkdown } from './ChatMarkdown'

interface MessageBubbleProps {
  readonly message: ChatMessage
}

export function MessageBubble({ message }: Readonly<MessageBubbleProps>) {
  if (message.role === 'error') {
    return (
      <div className="mx-12 flex items-start gap-2 rounded-sm border border-semantic-error/30 bg-semantic-errorDim px-3.5 py-2.5">
        <span className="mt-px shrink-0 text-[13px] text-semantic-error">⚠</span>
        <p className="text-[12px] font-medium text-semantic-error">{message.content}</p>
      </div>
    )
  }

  if (message.role === 'system') {
    return (
      <div className="mx-12 rounded-sm border border-surface-border bg-surface-overlay px-3.5 py-2.5 text-[12px] font-medium text-text-secondary">
        <ChatMarkdown tone="system">{message.content}</ChatMarkdown>
      </div>
    )
  }

  const isUser = message.role === 'user'

  return (
    <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
      <div
        className={cn(
          'max-w-[560px] rounded-lg px-4 py-3.5 text-body-md',
          isUser
            ? 'border border-[rgba(59,110,248,0.25)] bg-brand-primary-dim text-brand-primary-light'
            : 'bg-surface-elevated text-text-body',
        )}
        aria-label={isUser ? 'Your message' : 'Assistant message'}
      >
        <ChatMarkdown tone={isUser ? 'user' : 'agent'}>{message.content}</ChatMarkdown>
        {isUser &&
          message.attachedArtifacts &&
          message.attachedArtifacts.length > 0 && (
            <ul
              className="mt-2.5 flex flex-wrap gap-1.5 p-0 m-0 list-none"
              aria-label="Attached files"
            >
              {message.attachedArtifacts.map((a) => (
                <li key={a.artifact_id} className="list-none">
                  <span
                    className="inline-flex max-w-full items-center gap-1 rounded-md border border-surface-borderLight bg-surface-overlay px-2 py-1 text-caption text-text-body"
                    title={a.mime_type}
                  >
                    <span aria-hidden>📎</span>
                    <span className="truncate max-w-[200px]">{a.filename}</span>
                  </span>
                </li>
              ))}
            </ul>
          )}
        {message.streaming && (
          <span
            className="ml-0.5 inline-block h-4 w-0.5 animate-pulse bg-brand-primary align-text-bottom"
            aria-hidden
          />
        )}
      </div>
    </div>
  )
}
