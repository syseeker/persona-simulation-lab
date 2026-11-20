import type { RequestHandler } from './$types';
import { readDatasetCatalogue } from '#dataset-reader';
import { datasetResponse } from '#lib/server/datasetResponse.ts';
export const GET: RequestHandler = () => datasetResponse(readDatasetCatalogue);
