import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { worker, type Operation } from '#lib/server/worker.ts';

export const GET: RequestHandler = async ({ params, url }) => {
  const operations: Record<string, Operation> = { status: 'status', catalogue: 'catalogue', runs: 'runs', run: 'get_run', trace: 'get_trace' };
  const operation = operations[params.operation];
  if (!operation) return json({ error: 'Unknown operation' }, { status: 404 });
  try {
    const args = operation === 'get_run' ? { run_id: url.searchParams.get('id') }
      : operation === 'get_trace' ? { run_id: url.searchParams.get('run_id'), episode_id: url.searchParams.get('episode_id') }
      : operation === 'runs' ? { mode: url.searchParams.get('mode') } : {};
    return json(await worker.request(operation, args));
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Operation failed' }, { status: 400 });
  }
};

export const POST: RequestHandler = async ({ params, request }) => {
  const operations: Record<string, Operation> = { chat: 'chat', runs: 'start_run', cancel: 'cancel_run', evaluate: 'evaluate_run' };
  const operation = operations[params.operation];
  if (!operation) return json({ error: 'Unknown operation' }, { status: 404 });
  try {
    const text = await request.text();
    if (text.length > 65536) return json({ error: 'Request is too large' }, { status: 413 });
    const body = JSON.parse(text);
    if (!body || typeof body !== 'object' || Array.isArray(body)) throw new Error('Expected an object');
    return json(await worker.request(operation, body));
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Operation failed' }, { status: 400 });
  }
};
