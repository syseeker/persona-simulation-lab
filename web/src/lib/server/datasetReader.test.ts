import { beforeEach, expect, test, vi } from 'vitest';
import { datasetWorker, readDatasetCatalogue, readDatasetOptions, readDatasetPage } from './datasetReader.ts';

beforeEach(() => vi.restoreAllMocks());

test('only delegates explicit read operations with bounded profile filters', async () => {
  const request = vi.spyOn(datasetWorker, 'request').mockResolvedValue({ inference_calls: 0 });
  await readDatasetCatalogue();
  await readDatasetOptions(new URLSearchParams('source=ngc'));
  await readDatasetPage(new URLSearchParams('source=ngc&search=retail&age_min=30&age_max=60&planning_area=Yishun&education_level=Diploma&offset=10&limit=10'));
  expect(request.mock.calls).toEqual([
    ['dataset_catalogue'], ['persona_facets', { source: 'ngc' }],
    ['browse_personas', { source: 'ngc', search: 'retail', age_min: 30, age_max: 60, planning_area: 'Yishun', education_level: 'Diploma', offset: 10, limit: 10 }]
  ]);
});

test.each([
  'source=../../private', 'source=ngc&source=hf-profile-only', 'path=/tmp/data.parquet',
  'method=start_run', 'limit=21', 'limit=1.5', 'offset=-1', 'age_min=40&age_max=30',
  `search=${'x'.repeat(201)}`, 'source=en_US'
])('rejects unsupported inputs before starting a worker: %s', async query => {
  const request = vi.spyOn(datasetWorker, 'request').mockResolvedValue({});
  await expect(readDatasetPage(new URLSearchParams(query))).rejects.toThrow();
  expect(request).not.toHaveBeenCalled();
});

test('filter options reject worker methods and paths before delegation', async () => {
  const request = vi.spyOn(datasetWorker, 'request').mockResolvedValue({});
  await expect(readDatasetOptions(new URLSearchParams('source=ngc&method=platform_action'))).rejects.toThrow();
  expect(request).not.toHaveBeenCalled();
});
