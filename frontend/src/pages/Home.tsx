import { useEffect, useState } from 'react'
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

const M2_DEMO_GOAL =
  'Show me my portfolio performance, search for NVDA earnings coverage, and screenshot the Alpaca dashboard'

const SAMPLE_PROMPTS: { label: string; message: string }[] = [
  {
    label: 'Portfolio dashboard',
    message: 'Show me my portfolio performance and top holdings',
  },
  {
    label: '3-protocol demo (portfolio + search + screenshot)',
    message: M2_DEMO_GOAL,
  },
  {
    label: 'NVDA earnings search',
    message: 'Search for NVDA earnings coverage this week',
  },
  {
    label: 'Research AI agent frameworks',
    message: 'Research AI agent frameworks and summarize trends',
  },
]

const SANDBOX_MODE = import.meta.env.VITE_SANDBOX_MODE === 'true'

export function Home() {
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [guestBootstrapping, setGuestBootstrapping] = useState(SANDBOX_MODE)
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const guestLogin = useAuthStore((s) => s.guestLogin)
  const sessionSidebarOpen = useSessionSidebarStore((s) => s.isOpen)
  const { setSessionId, addMessage, reset } = useSessionStore()
  const { streamResponse } = useSSE()

  useEffect(() => {
    if (!SANDBOX_MODE || isAuthenticated) {
      setGuestBootstrapping(false)
      return
    }
    let cancelled = false
    ;(async () => {
      try {
        await guestLogin()
      } catch {
        /* fall through to sign-in prompt */
      } finally {
        if (!cancelled) setGuestBootstrapping(false)
      }
    })()
    return () => {
      cancelled = true
    }
  }, [guestLogin, isAuthenticated])

  const handleSubmit = async (message: string, _artifactIds: string[] = []) => {
    if (!isAuthenticated) {
      if (SANDBOX_MODE) {
        try {
          await guestLogin()
        } catch {
          navigate('/login')
          return
        }
      } else {
        navigate('/login')
        return
      }
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
        <p className="text-body-lg text-text-secondary text-center max-w-[600px] mb-8">
          Type a goal. Orcha discovers the right agents, composes them across MCP, A2A, and COMPUTER_USE,
          and renders the result as a live dashboard — not a chat reply.
        </p>

        {/* Prompt input */}
        <div className="w-full max-w-[680px] mb-4">
          <InputBar
            value={input}
            onChange={setInput}
            onSubmit={handleSubmit}
            placeholder="Describe a task for your agent hive…"
            disabled={loading || guestBootstrapping}
            size="home"
          />
        </div>

        {/* Sample chips */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 max-w-[760px]">
          {SAMPLE_PROMPTS.map((prompt) => (
            <button
              key={prompt.message}
              onClick={() => handleSubmit(prompt.message)}
              disabled={loading || guestBootstrapping}
              className="h-9 px-3 rounded-md bg-surface-overlay border border-surface-border text-[12px] text-text-secondary hover:text-text-body hover:border-surface-borderLight transition-colors duration-150 disabled:opacity-50"
            >
              {prompt.label}
            </button>
          ))}
        </div>

        {SANDBOX_MODE && (
          <p className="mt-4 text-[12px] text-text-disabled text-center max-w-[560px]">
            Sandbox uses pre-seeded demo agents. Portfolio numbers are illustrative — not connected
            to your accounts.
          </p>
        )}

        {/* Agents footnote */}
        <p className="mt-6 text-[11px] text-text-disabled text-center">
          {'→ powered by '}
          <a href="/agents" className="underline underline-offset-2 hover:text-text-secondary transition-colors">
            live agents
          </a>
        </p>

        {/* Gate note */}
        {!isAuthenticated && (
          <p className="mt-3 text-[12px] text-text-disabled text-center">
            {SANDBOX_MODE && guestBootstrapping
              ? 'Starting guest demo session…'
              : SANDBOX_MODE
                ? 'Try a goal — no account needed'
                : 'Sign in required to start a session'}
          </p>
        )}
      </main>
    </div>
  )
}
