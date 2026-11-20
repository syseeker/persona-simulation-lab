import type { RequestHandler } from './$types';
import { readDatasetPage } from '#dataset-reader';
import { datasetResponse } from '#lib/server/datasetResponse.ts';
export const GET: RequestHandler = ({ url }) => datasetResponse(() => readDatasetPage(url.searchParams));
