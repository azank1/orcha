import { create } from 'zustand'
import type { UserSettings } from '../types'

interface SettingsState {
  userSettings: UserSettings | null
  isDevMode: boolean
  // localStorage-only prefs
  appearance: 'dark' | 'light'
  language: string
  timezone: string
  defaultModel: string

  setUserSettings: (s: UserSettings) => void
  setDevMode: (v: boolean) => void
  setAppearance: (v: 'dark' | 'light') => void
  setLanguage: (v: string) => void
  setTimezone: (v: string) => void
  setDefaultModel: (v: string) => void
  loadLocalPrefs: () => void
}

export const useSettingsStore = create<SettingsState>((set) => ({
  userSettings: null,
  isDevMode: false,
  appearance: 'dark',
  language: 'en',
  timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
  defaultModel: 'claude-sonnet',

  setUserSettings: (s) => set({ userSettings: s, isDevMode: s.is_dev_mode }),
  setDevMode: (v) => set({ isDevMode: v }),

  setAppearance: (v) => {
    localStorage.setItem('pref_appearance', v)
    set({ appearance: v })
  },
  setLanguage: (v) => {
    localStorage.setItem('pref_language', v)
    set({ language: v })
  },
  setTimezone: (v) => {
    localStorage.setItem('pref_timezone', v)
    set({ timezone: v })
  },
  setDefaultModel: (v) => {
    localStorage.setItem('pref_defaultModel', v)
    set({ defaultModel: v })
  },

  loadLocalPrefs: () => {
    const appearance = (localStorage.getItem('pref_appearance') as 'dark' | 'light') ?? 'dark'
    const language = localStorage.getItem('pref_language') ?? 'en'
    const timezone = localStorage.getItem('pref_timezone') ?? Intl.DateTimeFormat().resolvedOptions().timeZone
    const defaultModel = localStorage.getItem('pref_defaultModel') ?? 'claude-sonnet'
    set({ appearance, language, timezone, defaultModel })
  },
}))
