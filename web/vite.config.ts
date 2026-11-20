import { sveltekit } from '@sveltejs/kit/vite';
import adapter from '@sveltejs/adapter-node';
import { defineConfig } from 'vitest/config';
import { resolve } from 'node:path';
export default defineConfig({
  plugins: [sveltekit({ adapter: adapter() })],
  resolve: { alias: { '#dataset-reader': resolve('src/lib/server/datasetReader.ts') } },
  test: { include: ['src/**/*.test.ts'], testTimeout: 30000 }
});
