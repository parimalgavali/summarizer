import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests-e2e',
  fullyParallel: false,
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:6701',
    trace: 'on-first-retry',
    // Sent with API requests when the backend has API_KEY set
    ...(process.env.API_KEY && { extraHTTPHeaders: { 'X-API-Key': process.env.API_KEY } }),
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});