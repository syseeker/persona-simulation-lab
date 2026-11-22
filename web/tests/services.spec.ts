import { expect, test } from '@playwright/test';

test('the integrated guide starts no execution operation on entry', async ({ page }) => {
  const apiRequests: string[] = [];
  // A regression must fail without starting a worker or a workload from the landing.
  await page.route('**/api/**', async route => {
    apiRequests.push(route.request().url());
    expect(route.request().method()).toBe('GET');
    if (route.request().url().includes('/api/journey/lesson')) {
      await route.fulfill({json:{state:'unavailable',scenario_id:'photography',trace:null,artifacts:[],sources:{}}});
    } else if (route.request().url().includes('/api/journey/demo-persona')) {
      await route.fulfill({json:{available:false,notice:'Offline test: source unavailable'}});
    } else if (route.request().url().includes('/api/journey/metadata')) {
      await route.fulfill({json:{schema:'citizen-guide-metadata/v1',scenario_id:'photography',run_id:null,
        available:false,rows:[],conditions:[],inference_calls_for_inspection:0}});
    } else await route.abort('blockedbyclient');
  });

  await page.goto('/');
  await expect(page).toHaveTitle('Building Citizen Apps with NeMo · Integration Guide');
  await expect(page.getByRole('button', {name:'Simulate a Session',exact:true})).toBeEnabled();
  await expect(page.getByRole('button', {name:'Trace a Request',exact:true})).toHaveAttribute('aria-pressed','true');
  await page.waitForLoadState('networkidle');
  expect(apiRequests.every(url=>/\/api\/journey\/(lesson|demo-persona|metadata)\?scenario_id=photography$/.test(url))).toBe(true);
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
  for(const path of ['/api/journey/lesson?scenario_id=photography&run_id=arbitrary', '/api/journey/demo-persona?path=.env', '/api/journey/lesson?scenario_id=photography&scenario_id=boardgames']){
    expect((await request.get(path)).status()).toBe(400);
  }
  expect((await request.post('/api/journey/lesson',{data:{scenario_id:'photography'}})).status()).toBe(404);
});
