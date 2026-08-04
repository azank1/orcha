import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

const root = path.dirname(fileURLToPath(import.meta.url))

/** Isolated Metis owl playground — imports locked mascot from main frontend. */
export default defineConfig({
  plugins: [react()],
  root,
  resolve: {
    alias: {
      '@metis': path.resolve(root, '../src/components/ui/metis'),
    },
  },
  server: {
    port: 3100,
    strictPort: true,
    open: '/',
  },
})
