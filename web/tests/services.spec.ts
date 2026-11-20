import { expect, test } from '@playwright/test';

test('the integrated guide starts no execution operation on entry', async ({ page }) => {
  const apiRequests: string[] = [];
  // A regression must fail without starting a worker or a workload from the landing.
  await page.route('**/api/**', async route => {
    apiRequests.push(route.request().url());
    if (route.request().url().includes('/api/journey/list')) {
      await route.fulfill({json:{runs:[],scenario_id:'photography'}});
    } else await route.abort('blockedbyclient');
  });

  await page.goto('/');
  await expect(page).toHaveTitle('Building Citizen Apps with NeMo · Integration Guide');
  await expect(page.getByRole('button', {name:'Simulate a Session',exact:true})).toBeEnabled();
  await expect(page.getByRole('button', {name:'Trace a Request',exact:true})).toHaveAttribute('aria-pressed','true');
  await page.waitForLoadState('networkidle');
  expect(apiRequests.every(url=>url.includes('/api/journey/list'))).toBe(true);
});

test('retained metadata routes reach the real local worker without inference', async ({ request }) => {
  const [statusResponse, catalogueResponse] = await Promise.all([
    request.get('/api/status'),
    request.get('/api/catalogue')
  ]);
  expect(statusResponse.ok()).toBe(true);
  expect(catalogueResponse.ok()).toBe(true);

  const status = await statusResponse.json();
  const catalogue = await catalogueResponse.json();
  expect(typeof status.version).toBe('string');
  expect(status.catalogue_count).toBeGreaterThan(0);
  expect(Array.isArray(catalogue)).toBe(true);
  expect(catalogue).toHaveLength(status.catalogue_count);
  for (const course of catalogue) {
    expect(typeof course.id).toBe('string');
    expect(typeof course.title).toBe('string');
    expect(typeof course.source_url).toBe('string');
  }
});

test('the HTTP boundary rejects unknown operations and invalid shapes before workloads', async ({ request }) => {
  const unknown = await request.get('/api/service-smoke-unknown');
  expect(unknown.status()).toBe(404);
  expect(await unknown.json()).toEqual({ error: 'Unknown operation' });

  // An array is rejected by the HTTP route before worker.request can be called.
  const invalid = await request.post('/api/chat', { data: [] });
  expect(invalid.status()).toBe(400);
  expect(await invalid.json()).toEqual({ error: 'Expected an object' });
});
