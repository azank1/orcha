/** Default lead-gen agent base URL when `VITE_LEAD_GEN_URL` is unset. No trailing slash. */
export const DEFAULT_LEAD_GEN_BASE_URL = 'http://localhost:4567'

/** Base URL from `import.meta.env.VITE_LEAD_GEN_URL`, or {@link DEFAULT_LEAD_GEN_BASE_URL}. */
export function leadGenBaseUrl(): string {
  const raw = import.meta.env.VITE_LEAD_GEN_URL
  if (typeof raw === 'string' && raw.trim() !== '') {
    return raw.replace(/\/$/, '')
  }
  return DEFAULT_LEAD_GEN_BASE_URL
}
