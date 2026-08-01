/**
 * Base URL of a deployed lead-gen agent. There is no public default —
 * set `VITE_LEAD_GEN_URL` to your own deployment (see `agents/lead-gen-agent/`).
 */
export const DEFAULT_LEAD_GEN_BASE_URL = ''

/** Base URL from `import.meta.env.VITE_LEAD_GEN_URL`, or {@link DEFAULT_LEAD_GEN_BASE_URL}. */
export function leadGenBaseUrl(): string {
  const raw = import.meta.env.VITE_LEAD_GEN_URL
  if (typeof raw === 'string' && raw.trim() !== '') {
    return raw.replace(/\/$/, '')
  }
  return DEFAULT_LEAD_GEN_BASE_URL
}
