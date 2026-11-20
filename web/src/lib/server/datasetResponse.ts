import { json } from '@sveltejs/kit';
import { DatasetQueryError } from '#dataset-reader';
export async function datasetResponse(read: () => Promise<unknown>) {
  try {
    return json(await read(), { headers: { 'Cache-Control': 'no-store' } });
  } catch (error) {
    const invalid = error instanceof DatasetQueryError;
    return json({ error: invalid ? error.message : 'The local dataset reader is unavailable. Configure LAB_ROOT for this checkout, install its environment and datasets, then retry.' },
      { status: invalid ? 400 : 503, headers: { 'Cache-Control': 'no-store' } });
  }
}
