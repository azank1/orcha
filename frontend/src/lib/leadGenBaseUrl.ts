/** Default Lightsail lead-gen agent when `VITE_LEAD_GEN_URL` is unset. No trailing slash. */
export const DEFAULT_LEAD_GEN_BASE_URL =
  'https://metaorcha-agent-lead-gen-agent.ngsqnf87wnek6.us-east-1.cs.amazonlightsail.com'

/** Base URL from `import.meta.env.VITE_LEAD_GEN_URL`, or {@link DEFAULT_LEAD_GEN_BASE_URL}. */
export function leadGenBaseUrl(): string {
  const raw = import.meta.env.VITE_LEAD_GEN_URL
  if (typeof raw === 'string' && raw.trim() !== '') {
    return raw.replace(/\/$/, '')
  }
  return DEFAULT_LEAD_GEN_BASE_URL
}
