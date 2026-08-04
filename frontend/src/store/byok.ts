import { create } from 'zustand'
import { credentials } from '../api/client'
import { useSessionStore } from './session'

export type ByokMode = 'hosted' | 'byok'

export interface ByokConfig {
  mode: ByokMode
  baseUrl: string
  apiKey: string
  model: string
  systemPrompt: string
}

interface ByokState extends ByokConfig {
  onboardingOpen: boolean
  openOnboarding: () => void
  closeOnboarding: () => void
  saveConfig: (cfg: ByokConfig) => void
  /** Reset to hosted defaults, drop localStorage, and clear session BYOK state. */
  clearConfig: () => void
  /**
   * Push base_url/api_key/model as session-scoped '__llm__' credentials.
   * No-ops in hosted mode; best-effort (never throws). The API key is never
   * logged and is only sent to the credentials API.
   */
  applyToSession: (sessionId: string) => Promise<void>
}

const STORAGE_KEY = 'orcha_byok'

const DEFAULTS: ByokConfig = {
  mode: 'hosted',
  baseUrl: 'https://openrouter.ai/api/v1',
  apiKey: '',
  model: 'meta-llama/llama-3.1-8b-instruct',
  systemPrompt: '',
}

function loadStored(): ByokConfig {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULTS
    const parsed = JSON.parse(raw) as Partial<ByokConfig>
    return { ...DEFAULTS, ...parsed }
  } catch {
    return DEFAULTS
  }
}

export const useByokStore = create<ByokState>((set, get) => ({
  ...loadStored(),
  onboardingOpen: false,

  openOnboarding: () => set({ onboardingOpen: true }),
  closeOnboarding: () => set({ onboardingOpen: false }),

  saveConfig: (cfg) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(cfg))
    } catch {
      /* storage full / private mode — keep in-memory only */
    }
    set(cfg)
    if (cfg.mode !== 'byok') useSessionStore.getState().clearByokActive()
  },

  clearConfig: () => {
    try {
      localStorage.removeItem(STORAGE_KEY)
    } catch {
      /* private mode — in-memory reset is enough */
    }
    set({ ...DEFAULTS })
    useSessionStore.getState().clearByokActive()
  },

  applyToSession: async (sessionId) => {
    const { mode, baseUrl, apiKey, model } = get()
    if (mode !== 'byok' || !apiKey.trim()) return
    try {
      for (const [var_name, value] of [
        ['base_url', baseUrl],
        ['api_key', apiKey],
        ['model', model],
      ] as const) {
        if (!value.trim()) continue
        await credentials.set({
          agent_id: '__llm__',
          var_name,
          value: value.trim(),
          scope: 'session',
          session_id: sessionId,
        })
      }
      useSessionStore.getState().setByokActive(sessionId)
    } catch {
      /* best-effort — hosted fallback remains available */
    }
  },
}))
