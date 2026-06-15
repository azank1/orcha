import { useEffect } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider } from '@tanstack/react-query'

import { Home } from './pages/Home'
import { Chat } from './pages/Chat'
import { AuthCallback } from './pages/AuthCallback'
import { Workflows } from './pages/Workflows'
import { AgentLibrary } from './pages/AgentLibrary'
import { RegisterAgent } from './pages/RegisterAgent'
import { Settings } from './pages/Settings'
import { Login } from './pages/Login'

import { useAuthStore } from './store/auth'
import { useSettingsStore } from './store/settings'
import { queryClient } from './lib/queryClient'

function AppRoutes() {
  const initFromStorage = useAuthStore((s) => s.initFromStorage)
  const loadLocalPrefs = useSettingsStore((s) => s.loadLocalPrefs)
  const isDevMode = useSettingsStore((s) => s.isDevMode)

  useEffect(() => {
    initFromStorage()
    loadLocalPrefs()
  }, [initFromStorage, loadLocalPrefs])

  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/chat/:sessionId" element={<Chat />} />
      <Route path="/workflows" element={<Workflows />} />
      {isDevMode && (
        <>
          <Route path="/agents" element={<AgentLibrary />} />
          <Route path="/agents/register" element={<RegisterAgent />} />
        </>
      )}
      {/* Redirect /agents to settings if dev mode is off */}
      {!isDevMode && (
        <Route path="/agents/*" element={<Navigate to="/settings" replace />} />
      )}
      <Route path="/settings" element={<Settings />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </QueryClientProvider>
  )
}
