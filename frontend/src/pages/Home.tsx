import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { NavBar } from '../components/layout/NavBar'
import { Sidebar } from '../components/layout/Sidebar'
import { SessionListPanel } from '../components/layout/SessionListPanel'
import { InputBar } from '../components/ui/InputBar'
import { Logo } from '../components/ui/Logo'
import { cn } from '../components/ui/cn'
import { sessions } from '../api/client'
import { useSessionStore } from '../store/session'
import { useSessionSidebarStore } from '../store/sessionSidebar'
import { useAuthStore } from '../store/auth'
import { useSSE } from '../hooks/useSSE'
import { sessionTitleFromMessage } from '../lib/sessionTitle'
import { queryClient } from '../lib/queryClient'

const SAMPLE_PROMPTS = [
  'Check inbox for urgent emails',
  'Find senior engineer roles',
  'Research AI agent trends',
  'Security scan on my domain',
]

export function Home() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const sessionSidebarOpen = useSessionSidebarStore((s) => s.isOpen)
  const { setSessionId, addMessage, reset } = useSessionStore()
  const { streamResponse } = useSSE()

  const handleSubmit = async (message: string, _artifactIds: string[] = []) => {
    if (!isAuthenticated) {
      navigate('/login')
      return
    }
    setLoading(true)
    try {
      reset()
      const title = sessionTitleFromMessage(message)
      const { session_id } = await sessions.create({ title })
      setSessionId(session_id)
      addMessage({
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        timestamp: Date.now(),
      })
      navigate(`/chat/${session_id}`)
      const res = await sessions.sendMessage(session_id, message)
      if (res.ok) await streamResponse(res)
      void queryClient.invalidateQueries({ queryKey: ['sessions'] })
      void queryClient.invalidateQueries({ queryKey: ['transcript', session_id] })
    } catch {
      // Error surfaced by fetch / SSE consumers if needed
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-surface-canvas flex flex-col">
      <NavBar />
      <Sidebar />
      {isAuthenticated ? <SessionListPanel /> : null}

      {/* Glow background */}
      <div
        className="fixed pointer-events-none"
        style={{
          width: 700,
          height: 500,
          left: '50%',
          top: 100,
          transform: 'translateX(-50%)',
          background: 'radial-gradient(ellipse at center, rgba(59,110,248,0.07) 0%, rgba(7,7,12,0) 70%)',
          borderRadius: '50%',
        }}
        aria-hidden="true"
      />

      {/* Content */}
      <main
        className={cn(
          'flex flex-1 flex-col items-center justify-center px-4 pt-14 transition-[margin-left] duration-200 ease-out motion-reduce:transition-none',
          isAuthenticated && sessionSidebarOpen && 'ml-80',
          !isAuthenticated || !sessionSidebarOpen ? 'ml-16' : null,
        )}
      >
        {/* Logo badge */}
        <div className="size-16 flex items-center justify-center rounded-xl bg-brand-primary-dim border border-[rgba(59,110,248,0.35)] mb-6">
          <Logo size={36} />
        </div>

        {/* Headline */}
        <h1 className="text-[38px] font-bold text-text-heading text-center leading-tight max-w-[760px] mb-4">
          What can I help you orchestrate?
        </h1>
        <p className="text-body-lg text-text-secondary text-center max-w-[560px] mb-8">
          I'm your SuperAgent — I discover, compose, and run agents to complete complex tasks end-to-end.
        </p>

        {/* Prompt input */}
        <div className="w-full max-w-[680px] mb-4">
          <InputBar
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            placeholder="Describe a task for your agent hive…"
            disabled={loading}
            size="home"
          />
        </div>

        {/* Sample chips */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 max-w-[760px]">
          {SAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt}
              onClick={() => handleSubmit(prompt)}
              disabled={loading}
              className="h-9 px-3 rounded-md bg-surface-overlay border border-surface-border text-[12px] text-text-secondary hover:text-text-body hover:border-surface-borderLight transition-colors duration-150 disabled:opacity-50"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Gate note */}
        {!isAuthenticated && (
          <p className="mt-4 text-[12px] text-text-disabled text-center">
            Sign in required to start a session
          </p>
        )}
      </main>
    </div>
  )
}
