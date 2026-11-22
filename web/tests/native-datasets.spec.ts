import {expect, test} from '@playwright/test';

test('installed HF and NGC profiles retain read-only browsing, filters and original-field inspection', async ({page}) => {
  test.setTimeout(120000);
  const allowed = ['/api/journey/lesson', '/api/journey/demo-persona', '/api/journey/metadata',
    '/api/local-datasets', '/api/persona-options', '/api/personas'];
  const requests: {method: string; path: string}[] = [];
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.route('**/api/**', async route => {
    const request = route.request(), url = new URL(request.url());
    requests.push({method: request.method(), path: url.pathname});
    expect(request.method()).toBe('GET');
    expect(allowed).toContain(url.pathname);
    await route.continue();
  });
  const nextPage = (source: string, offset = 0) => page.waitForResponse(response => {
    const url = new URL(response.url());
    return url.pathname === '/api/personas' && url.searchParams.get('source') === source
      && Number(url.searchParams.get('offset') || 0) === offset;
  });
  await page.goto('/');
  await page.getByRole('button', {name: /4\s+Datasets/}).click();
  await expect(page.getByTestId('dataset-snapshot')).toHaveCount(2);
  await page.getByLabel('Search schema fields', {exact: true}).fill('openness');
  await expect(page.getByTestId('dataset-schema').locator('tr[data-field]')).toHaveCount(1);
  await expect(page.getByTestId('dataset-schema')).toContainText('NGC only');
  const catalogueRead = page.waitForResponse(response => new URL(response.url()).pathname === '/api/local-datasets');
  const firstRead = nextPage('hf-profile-only');
  await page.getByRole('tab', {name: 'Explore profiles', exact: true}).click();
  const catalogueResponse = await catalogueRead;
  expect(catalogueResponse.ok()).toBe(true);
  const catalogue = await catalogueResponse.json();
  expect(catalogue.inference_calls).toBe(0);
  expect(catalogue.datasets.map((dataset: {source: string}) => dataset.source).sort()).toEqual(['hf-profile-only', 'ngc']);
  let response = await firstRead;

  for (const source of ['hf-profile-only', 'ngc']) {
    if (source === 'ngc') {
      const pending = nextPage(source);
      await page.getByRole('button', {name: /NGC Extended/}).click();
      response = await pending;
    }
    expect(response.ok()).toBe(true);
    const initial = await response.json();
    expect(initial.dataset.source).toBe(source);
    expect(initial.dataset.ready).toBe(true);
    expect(initial.inference_calls).toBe(0);
    expect(initial.offset).toBe(0);
    expect(initial.records.length).toBe(10);
    await expect(page.getByTestId('profile-snapshot').locator('tr[data-profile-row]')).toHaveCount(initial.records.length);
    await expect(page.getByRole('alert')).toHaveCount(0);
    const geography = source === 'ngc' ? 'district' : 'planning_area';
    const suitableIndex = initial.records.findIndex((record: {profile: Record<string, unknown>}) => {
      const profile = record.profile;
      return Number.isInteger(profile.age) && Number(profile.age) >= 18 && Number(profile.age) <= 120
        && typeof profile[geography] === 'string' && typeof profile.education_level === 'string'
        && typeof profile.occupation === 'string' && profile.occupation.length > 0;
    });
    expect(suitableIndex).toBeGreaterThanOrEqual(0);
    const selected = initial.records[suitableIndex], profile = selected.profile;
    await page.getByRole('button', {name: `Inspect profile ${suitableIndex + 1}`, exact: true}).click();
    await expect(page.locator('[data-profile-field="age"] dd')).toHaveText(String(profile.age));
    await page.getByText('Source revision and original-row hash', {exact: true}).click();
    await expect(page.locator('.row-provenance')).toContainText(selected.original_profile_sha256);
    if (source === 'ngc') {
      expect(initial.dataset.ocean_fields).toHaveLength(5);
      await expect(page.locator('[data-profile-field="openness"]')).toBeVisible();
    } else {
      expect(initial.dataset.ocean_fields).toHaveLength(0);
      await expect(page.locator('[data-profile-field="openness"]')).toHaveCount(0);
    }

    const secondRead = nextPage(source, 10);
    await page.getByRole('button', {name: 'Next page →', exact: true}).click();
    const secondResponse = await secondRead;
    expect(secondResponse.ok()).toBe(true);
    const second = await secondResponse.json();
    expect(second.offset).toBe(10);
    expect(second.inference_calls).toBe(0);
    expect(second.records.length).toBe(10);
    const priorIds = new Set(initial.records.map((record: {source_id: string}) => record.source_id));
    expect(second.records.some((record: {source_id: string}) => priorIds.has(record.source_id))).toBe(false);

    await page.getByLabel('Minimum age', {exact: true}).fill(String(profile.age));
    await page.getByLabel('Maximum age', {exact: true}).fill(String(profile.age));
    await page.getByLabel(source === 'ngc' ? 'District' : 'Planning area', {exact: true}).selectOption(profile[geography]);
    await page.getByLabel('Education level', {exact: true}).selectOption(profile.education_level);
    // Derive a search term from a currently loaded source field; no source
    // values are embedded in the test or written to public output.
    const keyword = String(profile.occupation).match(/\p{L}+/gu)?.find(word => word.length >= 3);
    expect(Boolean(keyword)).toBe(true);
    await page.getByLabel('Search profile text', {exact: true}).fill(keyword!);
    const filteredRead = nextPage(source);
    await page.getByRole('button', {name: 'Apply filters', exact: true}).click();
    const filteredResponse = await filteredRead;
    expect(filteredResponse.ok()).toBe(true);
    const filtered = await filteredResponse.json();
    expect(filtered.inference_calls).toBe(0);
    expect(filtered.total).toBeGreaterThan(0);
    expect(filtered.total).toBeLessThan(initial.total);
    expect(filtered.records.every((record: {profile: Record<string, unknown>}) => record.profile.age === profile.age
      && record.profile[geography] === profile[geography] && record.profile.education_level === profile.education_level)).toBe(true);
    await expect(page.getByTestId('profile-snapshot').locator('tr[data-profile-row]')).toHaveCount(filtered.records.length);
    const clearedRead = nextPage(source);
    await page.getByRole('button', {name: 'Clear filters', exact: true}).click();
    const clearedResponse = await clearedRead;
    expect(clearedResponse.ok()).toBe(true);
    const cleared = await clearedResponse.json();
    expect(cleared.total).toBe(initial.total);
    expect(cleared.records[0].original_profile_sha256).toBe(initial.records[0].original_profile_sha256);
    expect(cleared.inference_calls).toBe(0);
  }
  expect(errors).toEqual([]);
  expect(requests.filter(request => request.path === '/api/personas').length).toBeGreaterThanOrEqual(8);
  expect(requests.every(request => request.method === 'GET')).toBe(true);
});
