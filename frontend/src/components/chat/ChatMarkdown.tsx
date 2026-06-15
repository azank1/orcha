import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { Components } from 'react-markdown'
import { cn } from '../ui/cn'

type ChatMarkdownTone = 'user' | 'agent' | 'system'

function markdownComponents(tone: ChatMarkdownTone): Components {
  const codeSurface = tone === 'user' ? 'bg-black/25' : 'bg-surface-overlay'

  return {
    p: ({ children }) => (
      <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>
    ),
    ul: ({ children }) => (
      <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0">{children}</ul>
    ),
    ol: ({ children }) => (
      <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0">{children}</ol>
    ),
    li: ({ children }) => <li className="leading-relaxed">{children}</li>,
    a: ({ href, children }) => (
      <a
        href={href}
        target="_blank"
        rel="noopener noreferrer"
        className="font-medium underline decoration-1 underline-offset-2"
      >
        {children}
      </a>
    ),
    code: ({ className, children }) => {
      const inline = !className
      if (inline) {
        return (
          <code
            className={cn(
              'rounded-sm px-1 py-0.5 font-mono text-caption',
              codeSurface,
            )}
          >
            {children}
          </code>
        )
      }
      return (
        <code className={cn('block whitespace-pre font-mono text-caption', className)}>
          {children}
        </code>
      )
    },
    pre: ({ children }) => (
      <pre
        className={cn(
          'mb-2 overflow-x-auto rounded-md p-3 font-mono text-caption last:mb-0',
          codeSurface,
        )}
      >
        {children}
      </pre>
    ),
    strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
    em: ({ children }) => <em className="italic">{children}</em>,
    h1: ({ children }) => (
      <h1 className="mb-2 mt-3 text-h3 font-semibold first:mt-0">{children}</h1>
    ),
    h2: ({ children }) => (
      <h2 className="mb-2 mt-3 text-label font-semibold first:mt-0">{children}</h2>
    ),
    h3: ({ children }) => (
      <h3 className="mb-1 mt-2 text-label font-semibold first:mt-0">{children}</h3>
    ),
    blockquote: ({ children }) => (
      <blockquote className="mb-2 border-l-2 border-surface-muted pl-3 text-text-secondary last:mb-0">
        {children}
      </blockquote>
    ),
    hr: () => <hr className="my-3 border-surface-border" />,
    table: ({ children }) => (
      <div className="mb-2 max-w-full overflow-x-auto last:mb-0">
        <table className="w-full border-collapse text-left text-caption">{children}</table>
      </div>
    ),
    thead: ({ children }) => <thead className="border-b border-surface-border">{children}</thead>,
    th: ({ children }) => (
      <th className="px-2 py-1.5 font-semibold text-text-heading">{children}</th>
    ),
    td: ({ children }) => <td className="border-t border-surface-border px-2 py-1.5">{children}</td>,
  }
}

interface ChatMarkdownProps {
  readonly tone: ChatMarkdownTone
  readonly children: string
}

export function ChatMarkdown({ tone, children }: Readonly<ChatMarkdownProps>) {
  return (
    <div className="min-w-0 break-words">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents(tone)}>
        {children}
      </ReactMarkdown>
    </div>
  )
}
