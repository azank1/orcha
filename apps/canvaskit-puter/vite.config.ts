import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base: './' so the built bundle works when hosted under a Puter app subpath.
export default defineConfig({
  base: './',
  plugins: [react()],
})
