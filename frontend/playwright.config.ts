import { defineConfig } from '@playwright/test'
import { resolve } from 'node:path'

if (process.env.RUN_REAL_USER_TESTS !== '1') {
  throw new Error('Estes testes usam Supabase/OpenRouter reais e consomem créditos. Defina RUN_REAL_USER_TESTS=1 para executá-los.')
}
const root = resolve(import.meta.dirname, '..')
const python = resolve(root, process.platform === 'win32' ? '.venv/Scripts/python.exe' : '.venv/bin/python')
export default defineConfig({
  testDir: './e2e', fullyParallel: true, workers: 2, retries: 0, timeout: 240_000,
  grep: process.env.USER_TEST_GREP ? new RegExp(process.env.USER_TEST_GREP) : undefined,
  expect: { timeout: 15_000 },
  outputDir: '../.local/playwright-results',
  reporter: [['list'], ['json', { outputFile: '../.local/playwright-real.json' }]],
  use: { baseURL: 'http://127.0.0.1:8011', channel: 'msedge', headless: true,
    viewport: { width: 1280, height: 900 }, locale: 'pt-BR', timezoneId: 'America/Sao_Paulo',
    trace: 'off', video: 'off', screenshot: 'off' },
  webServer: { command: `"${python}" -m uvicorn app:app --host 127.0.0.1 --port 8011`, cwd: root,
    url: 'http://127.0.0.1:8011/api/health', timeout: 90_000, reuseExistingServer: false,
    env: { APP_ENV: 'local', DEMO_ACCESS_CODE: '' } },
})
