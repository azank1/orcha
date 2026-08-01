import { create } from 'zustand'

const STORAGE_KEY = 'pref_sessionSidebarOpen'

function readInitialOpen(): boolean {
  if (globalThis.window === undefined) return true
  const raw = globalThis.localStorage.getItem(STORAGE_KEY)
  if (raw === null) return true
  return raw === 'true'
}

interface SessionSidebarState {
  isOpen: boolean
  setOpen: (open: boolean) => void
  toggle: () => void
}

export const useSessionSidebarStore = create<SessionSidebarState>((set, get) => ({
  isOpen: readInitialOpen(),

  setOpen: (open) => {
    globalThis.localStorage.setItem(STORAGE_KEY, String(open))
    set({ isOpen: open })
  },

  toggle: () => {
    const next = !get().isOpen
    globalThis.localStorage.setItem(STORAGE_KEY, String(next))
    set({ isOpen: next })
  },
}))
