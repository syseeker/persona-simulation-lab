import { defineConfig } from '@playwright/test';
const configuredURL = process.env.LAB_REVIEW_BASE_URL;
const baseURL = configuredURL || 'http://127.0.0.1:4173';
const target = new URL(baseURL);
if (target.protocol !== 'http:' || !['127.0.0.1', 'localhost'].includes(target.hostname)) {
  throw new Error('LAB_REVIEW_BASE_URL must be a loopback HTTP URL.');
}
const port = target.port || '80';
export default defineConfig({
  testDir: './tests', workers: 1, timeout: 60000,
  use: { baseURL, screenshot: 'only-on-failure' },
  webServer: { command: `npm run dev -- --port ${port} --strictPort`, url: baseURL,
    reuseExistingServer: !configuredURL && !process.env.CI, timeout: 30000 }
});
