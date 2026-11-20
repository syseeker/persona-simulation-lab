import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { journeyWorker } from '#lib/server/journey.ts';

const reads: Record<string, string[]> = {
  presets: [], readiness: [], list: ['scenario_id'], get: ['run_id'], trace: ['run_id'],
  source: ['component', 'module'], artifacts: ['run_id'], artifact: ['run_id', 'artifact_id'],
  lesson: ['scenario_id'], 'demo-persona': ['scenario_id']
};
const writes = new Set(['sample', 'start', 'cancel', 'recover']);
const headers = { 'Cache-Control': 'no-store' };

export const GET: RequestHandler = async ({ params, url }) => {
  if (!(params.action in reads)) return json({ error: 'Unknown read operation' }, { status: 404, headers });
  const args: Record<string, string> = { action: params.action };
  for (const key of url.searchParams.keys()) {
    if (!reads[params.action].includes(key) || url.searchParams.getAll(key).length !== 1) {
      return json({ error: 'Unexpected or repeated guide parameter' }, { status: 400, headers });
    }
    const value = url.searchParams.get(key)!;
    if (value.length > 200) return json({ error: 'Guide parameter is too long' }, { status: 400, headers });
    args[key] = value;
  }
  try {
    return json(await journeyWorker.request('journey', args), { headers });
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Guide read failed' }, { status: 400, headers });
  }
};

export const POST: RequestHandler = async ({ params, request, url }) => {
  if (!writes.has(params.action)) return json({ error: 'Unknown write operation' }, { status: 404, headers });
  const origin = request.headers.get('origin');
  if (origin && origin !== url.origin) return json({ error: 'Use the local application origin' }, { status: 403, headers });
  try {
    const raw = await request.text();
    if (raw.length > 16000) return json({ error: 'Request is too large' }, { status: 413, headers });
    const body = JSON.parse(raw);
    if (!body || typeof body !== 'object' || Array.isArray(body) || 'action' in body) throw new Error('Expected guide parameters');
    return json(await journeyWorker.request('journey', { action: params.action, ...body }), { headers });
  } catch (error) {
    return json({ error: error instanceof Error ? error.message : 'Guide operation failed' }, { status: 400, headers });
  }
};
