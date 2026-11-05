// @ts-check
import { defineConfig, devices } from '@playwright/test';

const FRONTEND_URL = 'http://127.0.0.1:5173';

/**
 * Playwright E2E config — exercita a integração real React + Flask.
 * O webServer sobe o Flask com banco isolado (e2e_server.py) e o Vite.
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: FRONTEND_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  ],
  webServer: [
    {
      // Backend Flask com banco de dados isolado e descartável.
      command: '.venv/bin/python e2e_server.py',
      cwd: 'api',
      url: 'http://127.0.0.1:5000/api/restaurantes',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: { DATABASE: '/tmp/sabor-e2e.db', E2E_PORT: '5000', APP_ENV: 'development' },
    },
    {
      // Frontend Vite (proxy /api -> 127.0.0.1:5000).
      command: 'npm run dev -- --host 127.0.0.1 --port 5173 --strictPort',
      url: FRONTEND_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
