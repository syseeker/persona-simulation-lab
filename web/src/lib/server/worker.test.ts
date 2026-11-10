import { afterEach, expect, test } from 'vitest';
import { WorkerClient, type Operation } from './worker';

const clients: WorkerClient[] = [];
function client() { const value = new WorkerClient(); clients.push(value); return value; }
afterEach(() => { for (const item of clients.splice(0)) item.close(); });

test('correlates independent requests to one persistent worker', async () => {
  const worker = client();
  const [status, catalogue, again] = await Promise.all([
    worker.request<{ catalogue_count: number }>('status'), worker.request<unknown[]>('catalogue'),
    worker.request<{ catalogue_count: number }>('status')
  ]);
  expect(status.catalogue_count).toBe(12);
  expect(catalogue).toHaveLength(12);
  expect(again.catalogue_count).toBe(status.catalogue_count);
});

test('rejects invalid operations without losing the worker', async () => {
  const worker = client();
  await expect(worker.request('invalid' as Operation)).rejects.toThrow();
  await expect(worker.request('status')).resolves.toHaveProperty('version', '0.1.0');
});
