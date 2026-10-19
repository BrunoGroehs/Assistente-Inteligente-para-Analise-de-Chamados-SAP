import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  // Proxy apenas para npm run dev isolado; vercel dev usa as regras de vercel.json.
  server: { proxy: { '/api': { target: 'http://127.0.0.1:8000', changeOrigin: false } } },
  test: { include: ['src/**/*.test.{ts,tsx}'], environment: 'jsdom', setupFiles: ['./src/test-setup.ts'], globals: true },
})
