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
import { OwlPreview } from './pages/OwlPreview'

import { useAuthStore } from './store/auth'
import { useSettingsStore } from './store/settings'
import { useByokStore } from './store/byok'
import { OnboardingModal } from './components/modals/OnboardingModal'
import { queryClient } from './lib/queryClient'

function AppRoutes() {
  const initFromStorage = useAuthStore((s) => s.initFromStorage)
  const loadLocalPrefs = useSettingsStore((s) => s.loadLocalPrefs)
  const isDevMode = useSettingsStore((s) => s.isDevMode)
  const openOnboarding = useByokStore((s) => s.openOnboarding)

  useEffect(() => {
    initFromStorage()
    loadLocalPrefs()
  }, [initFromStorage, loadLocalPrefs])

  // Dual-mode theming: applied on the root element so body + fixed overlays
  // resolve the CSS custom properties too.
  useEffect(() => {
    document.documentElement.dataset.mode = isDevMode ? 'developer' : 'user'
  }, [isDevMode])

  // First-visit onboarding (model choice + optional system prompt).
  useEffect(() => {
    if (!localStorage.getItem('orcha_onboarded')) openOnboarding()
  }, [openOnboarding])

  return (
    <>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/auth/callback" element={<AuthCallback />} />
        <Route path="/chat/:sessionId" element={<Chat />} />
        <Route path="/workflows" element={<Workflows />} />
        {/* Agent Library + Register are core developer surfaces — always available. */}
        <Route path="/agents" element={<AgentLibrary />} />
        <Route path="/agents/register" element={<RegisterAgent />} />
        <Route path="/settings" element={<Settings />} />
        {/* Dev-only playground for the Metis owl mascot — never mounted in production. */}
        {import.meta.env.DEV && <Route path="/dev/owl" element={<OwlPreview />} />}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <OnboardingModal />
    </>
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
