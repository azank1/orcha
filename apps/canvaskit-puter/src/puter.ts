import type { UIManifest } from './types/canvas'
import { SAMPLE_MANIFEST } from './sample-manifest'

// ── puter.js client adapter ──────────────────────────────────────────────────
// puter.js is loaded via the CDN <script> in index.html and exposes a global
// `window.puter`. This module is the ONLY place that touches it, so the AGPL
// boundary is explicit: we call the Puter *client SDK* as a black box and never
// link/fork Puter core. If the SDK is absent (app opened outside Puter) every
// path degrades gracefully to the bundled SAMPLE_MANIFEST.

// Minimal structural type for the subset of puter.js we use. Loosely typed on
// purpose — the SDK ships no types and we only need FS read/write + KV.
interface PuterLike {
  auth?: {
    isSignedIn?: () => boolean
    signIn?: () => Promise<unknown>
  }
  fs?: {
    read?: (path: string) => Promise<Blob | string>
    write?: (path: string, data: string) => Promise<unknown>
  }
  kv?: {
    get?: (key: string) => Promise<unknown>
    set?: (key: string, value: string) => Promise<unknown>
  }
}

declare global {
  interface Window {
    puter?: PuterLike
  }
}

export type ManifestSource = 'puter-fs' | 'puter-kv' | 'mock'

export interface LoadResult {
  manifest: UIManifest
  source: ManifestSource
  detail: string
}

const MANIFEST_PATH =
  import.meta.env.VITE_MANIFEST_PATH ?? '~/orcha/latest-dashboard.json'
const KV_KEY = 'orcha:latest-dashboard'

export function hasPuter(): boolean {
  return typeof window !== 'undefined' && !!window.puter
}

function isManifest(value: unknown): value is UIManifest {
  return (
    !!value &&
    typeof value === 'object' &&
    Array.isArray((value as UIManifest).components)
  )
}

function parseManifest(raw: string): UIManifest | null {
  try {
    const parsed = JSON.parse(raw)
    return isManifest(parsed) ? parsed : null
  } catch {
    return null
  }
}

async function readFromFs(puter: PuterLike): Promise<UIManifest | null> {
  if (!puter.fs?.read) return null
  const blob = await puter.fs.read(MANIFEST_PATH)
  const text = typeof blob === 'string' ? blob : await blob.text()
  return parseManifest(text)
}

async function readFromKv(puter: PuterLike): Promise<UIManifest | null> {
  if (!puter.kv?.get) return null
  const value = await puter.kv.get(KV_KEY)
  if (value == null) return null
  const text = typeof value === 'string' ? value : JSON.stringify(value)
  return parseManifest(text)
}

/**
 * Load the current dashboard manifest. Tries the user's Puter filesystem first,
 * then Puter KV, then falls back to the bundled sample. Never throws.
 */
export async function loadManifest(): Promise<LoadResult> {
  const puter = typeof window !== 'undefined' ? window.puter : undefined
  if (!puter) {
    return {
      manifest: SAMPLE_MANIFEST,
      source: 'mock',
      detail: 'puter.js not present — rendering bundled sample manifest',
    }
  }

  try {
    if (puter.auth?.isSignedIn && !puter.auth.isSignedIn() && puter.auth.signIn) {
      await puter.auth.signIn()
    }
  } catch {
    // Sign-in cancelled/unavailable — still try reads, then fall back.
  }

  try {
    const fromFs = await readFromFs(puter)
    if (fromFs) {
      return { manifest: fromFs, source: 'puter-fs', detail: MANIFEST_PATH }
    }
  } catch {
    // fall through to KV
  }

  try {
    const fromKv = await readFromKv(puter)
    if (fromKv) {
      return { manifest: fromKv, source: 'puter-kv', detail: KV_KEY }
    }
  } catch {
    // fall through to mock
  }

  return {
    manifest: SAMPLE_MANIFEST,
    source: 'mock',
    detail: 'no manifest found in Puter FS/KV yet — rendering bundled sample',
  }
}

/**
 * Write a manifest into the user's Puter filesystem. Used by the "load sample
 * into Puter" PoC button and, later, by an Orcha post-run hook (the v2 automated
 * write). Returns true on success.
 */
export async function writeManifest(manifest: UIManifest): Promise<boolean> {
  const puter = typeof window !== 'undefined' ? window.puter : undefined
  if (!puter?.fs?.write) return false
  try {
    if (puter.auth?.isSignedIn && !puter.auth.isSignedIn() && puter.auth.signIn) {
      await puter.auth.signIn()
    }
    await puter.fs.write(MANIFEST_PATH, JSON.stringify(manifest, null, 2))
    return true
  } catch {
    return false
  }
}
