import type { RequestHandler } from './$types';
import { readDatasetOptions } from '#dataset-reader';
import { datasetResponse } from '#lib/server/datasetResponse.ts';
export const GET: RequestHandler = ({ url }) => datasetResponse(() => readDatasetOptions(url.searchParams));
