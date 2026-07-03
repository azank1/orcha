/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_SANDBOX_MODE?: string
  readonly VITE_MANIFEST_PATH?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
