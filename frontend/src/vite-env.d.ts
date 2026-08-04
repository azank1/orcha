/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the lead-gen agent (tool-settings, CRM OAuth, etc.). No trailing slash. */
  readonly VITE_LEAD_GEN_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
