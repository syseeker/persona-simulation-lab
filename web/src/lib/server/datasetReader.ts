/** Read-only dataset boundary shared with the external Integration Guide.
 * Browser inputs select a distribution and bounded filters, never a path or worker method.
 */
import { WorkerClient } from './worker.ts';

const globalReader = globalThis as typeof globalThis & { personaDatasetReader?: WorkerClient };
export const datasetWorker = globalReader.personaDatasetReader ??= new WorkerClient(undefined, { datasetsOnly: true });
process.once('SIGTERM', () => datasetWorker.close());
process.once('SIGINT', () => datasetWorker.close());

export class DatasetQueryError extends Error {}

function queryValues(query: URLSearchParams, allowed: string[]) {
  for (const key of query.keys()) {
    if (!allowed.includes(key)) throw new DatasetQueryError('Unknown dataset filter.');
    if (query.getAll(key).length !== 1) throw new DatasetQueryError('Repeated dataset filters are not supported.');
  }
  const source = query.get('source') ?? 'hf-profile-only';
  if (!['hf-profile-only', 'ngc'].includes(source)) throw new DatasetQueryError('Choose HF public or Singapore NGC Extended.');
  return { source };
}

export async function readDatasetCatalogue() {
  return datasetWorker.request('dataset_catalogue');
}

export async function readDatasetOptions(query: URLSearchParams) {
  return datasetWorker.request('persona_facets', queryValues(query, ['source']));
}

export async function readDatasetPage(query: URLSearchParams) {
  const params: Record<string, unknown> = queryValues(query,
    ['source', 'search', 'offset', 'limit', 'age_min', 'age_max', 'planning_area', 'occupation', 'education_level']);
  for (const [name, min, max, fallback] of [
    ['offset', 0, 1_000_000, 0], ['limit', 1, 20, 10], ['age_min', 18, 120, null], ['age_max', 18, 120, null]
  ] as const) {
    const raw = query.get(name);
    if (raw === null || raw === '') { if (fallback !== null) params[name] = fallback; continue; }
    if (!/^\d+$/.test(raw) || Number(raw) < min || Number(raw) > max) {
      throw new DatasetQueryError(`${name} must be an integer from ${min} to ${max}.`);
    }
    params[name] = Number(raw);
  }
  if (params.age_min !== undefined && params.age_max !== undefined && Number(params.age_min) > Number(params.age_max)) {
    throw new DatasetQueryError('Minimum age must not exceed maximum age.');
  }
  for (const [name, limit] of [['search', 200], ['planning_area', 100], ['occupation', 150], ['education_level', 150]] as const) {
    const value = query.get(name)?.trim();
    if (value && value.length > limit) throw new DatasetQueryError(`${name} is too long.`);
    if (value) params[name] = value;
  }
  return datasetWorker.request('browse_personas', params);
}
