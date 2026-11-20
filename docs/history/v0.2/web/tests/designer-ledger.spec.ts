import { expect, test, type Page } from '@playwright/test';

// Browser-only, fabricated saved-job fixtures. Every API request is intercepted;
// these tests never invoke the worker, an SDK, a model, or live generation.
async function savedDesignerFixture(page: Page, job: Record<string, unknown>) {
  const calls = { modelWorkloads: 0, savedJobReads: 0 };
  await page.route('**/api/**', async route => {
    const request = route.request();
    const operation = new URL(request.url()).pathname.split('/').pop();
    if (request.method() === 'POST') {
      if (['chat', 'runs', 'workbench', 'platform'].includes(operation ?? '')) calls.modelWorkloads++;
      return route.fulfill({ status: 400, json: { error: 'Fabricated ledger fixture forbids runtime operations' } });
    }
    if (operation === 'status') return route.fulfill({ json: {
      nim_key_present: false, ngc_key_present: false, proxy_configured: false,
      model: 'fabricated-ledger-fixture', catalogue_count: 0, personas_audited: false
    } });
    if (operation === 'datasets') return route.fulfill({ json: { datasets: [{
      source: 'hf-profile-only', name: 'Fabricated unavailable dataset fixture', ready: false,
      row_count: 0, columns: [], ocean_fields: [], revision: 'browser-fixture-only',
      notice: 'Fabricated browser data; no actual persona records', reason: 'Not needed for saved-ledger inspection'
    }] } });
    if (operation === 'workbench-history') return route.fulfill({ json: [job] });
    if (operation === 'workbench-job') {
      calls.savedJobReads++;
      expect(new URL(request.url()).searchParams.get('job_id')).toBe(job.job_id);
      return route.fulfill({ json: job });
    }
    return route.fulfill({ json: [] });
  });
  await page.goto('/');
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: /Data workbench/ }).click();
  await page.getByText('Reopen a saved generation job', { exact: true }).click();
  await page.getByRole('button', { name: /columns ·/ }).click();
  const ledger = page.getByRole('region', { name: 'Saved Designer model-call ledger' });
  await expect(ledger).toBeVisible();
  return { calls, ledger };
}

const fixtureJob = {
  job_id: 'fabricated-designer-ledger-job', status: 'failed', calls: 3, budget: 120,
  started_at: '2026-11-17T01:00:00Z', spec: { operation: 'columns' }, result: null,
  error: 'Fabricated generation failure retained for browser coverage'
};

test('saved Designer ledger shows actual recorded fields, unknown usage and errors without generation (fixture)', async ({ page }) => {
  const { calls, ledger } = await savedDesignerFixture(page, {
    ...fixtureJob,
    usage: [
      { call: 1, role: 'designer', mode: 'live', status: 'completed', model: 'fabricated-configured-model',
        requested_model: 'fabricated-support-alias', selected_model: 'fabricated-provider-model',
        latency_ms: 20, usage: { prompt_tokens: 41, completion_tokens: 7, total_tokens: 48 } },
      { call: 2, role: 'designer', mode: 'live', status: 'failed', requested_model: 'fabricated-support-alias',
        error_type: 'FabricatedProviderError', http_status: 429, usage: null,
        provider_error: { message: '<img src=x onerror="window.ledgerMarkupExecuted=true">Fabricated provider failure' } },
      { call: 3, role: 'designer', mode: 'live', status: 'cancelled',
        usage: { input_tokens: 0, output_tokens: 3 } }
    ]
  });
  await expect(ledger).toContainText('Admitted calls: 3 · job cap: 120 · 3 saved records from job.usage');
  await ledger.getByText('Inspect saved model calls · 3 records', { exact: true }).click();
  const first = ledger.locator('details.lab-check-row').filter({ has: page.locator('summary strong', { hasText: /^Call 1$/ }) });
  await first.locator('summary').first().click();
  await expect(first).toContainText('Role: designer');
  await expect(first).toContainText('completed');
  await expect(first.locator('div').filter({ has: page.locator('dt', { hasText: /^Requested model \/ alias$/ }) })).toContainText('fabricated-support-alias');
  await expect(first).toContainText('fabricated-provider-model');
  await expect(first.locator('div').filter({ has: page.locator('dt', { hasText: /^Input tokens$/ }) })).toContainText('41');
  await expect(first.locator('div').filter({ has: page.locator('dt', { hasText: /^Total tokens$/ }) })).toContainText('48');

  const failed = ledger.locator('details.lab-check-row').filter({ has: page.locator('summary strong', { hasText: /^Call 2$/ }) });
  await failed.locator('summary').first().click();
  await expect(failed).toContainText('failed');
  await expect(failed).toContainText('FabricatedProviderError');
  await expect(failed).toContainText('HTTP status: 429');
  await expect(failed).toContainText('Fabricated provider failure');
  await expect(failed.locator('div').filter({ has: page.locator('dt', { hasText: /^Input tokens$/ }) })).toContainText('Unknown (not recorded)');
  await expect(failed.locator('div').filter({ has: page.locator('dt', { hasText: /^Selected provider model$/ }) })).toContainText('Unknown (not recorded)');
  await expect(failed.locator('img')).toHaveCount(0);
  expect(await page.evaluate(() => (window as unknown as Record<string, unknown>).ledgerMarkupExecuted)).toBeUndefined();

  const cancelled = ledger.locator('details.lab-check-row').filter({ has: page.locator('summary strong', { hasText: /^Call 3$/ }) });
  await cancelled.locator('summary').first().click();
  await expect(cancelled).toContainText('cancelled');
  await expect(cancelled.locator('div').filter({ has: page.locator('dt', { hasText: /^Input tokens$/ }) }).locator('dd')).toHaveText('0');
  await expect(cancelled.locator('div').filter({ has: page.locator('dt', { hasText: /^Output tokens$/ }) }).locator('dd')).toHaveText('3');
  await expect(cancelled.locator('div').filter({ has: page.locator('dt', { hasText: /^Total tokens$/ }) })).toContainText('Unknown (not recorded)');
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  expect(calls).toEqual({ modelWorkloads: 0, savedJobReads: 1 });
});

test('a missing saved Designer ledger is explicit and never backfilled (fixture)', async ({ page }) => {
  const { calls, ledger } = await savedDesignerFixture(page, { ...fixtureJob, calls: 4 });
  await expect(ledger).toContainText('Admitted calls: 4');
  await expect(ledger).toContainText('0 saved records from job.usage');
  await expect(ledger).toContainText('No model-call records were saved for this job. Token usage is unknown');
  await expect(ledger.locator('details.lab-check-row')).toHaveCount(0);
  expect(calls).toEqual({ modelWorkloads: 0, savedJobReads: 1 });
});

test('Designer ledger rendering remains bounded while preserving saved count (fixture)', async ({ page }) => {
  const usage = Array.from({ length: 121 }, (_, index) => ({
    call: index + 1, role: 'fabricated-designer', status: 'completed',
    requested_model: 'fabricated-alias', usage: null
  }));
  const { calls, ledger } = await savedDesignerFixture(page, { ...fixtureJob, calls: 121, usage });
  await expect(ledger).toContainText('Showing the first 120 of 121 saved records');
  await ledger.getByText('Inspect saved model calls · 121 records', { exact: true }).click();
  await expect(ledger.locator('details.lab-check-row')).toHaveCount(120);
  await expect(ledger.locator('summary strong').filter({ hasText: /^Call 120$/ })).toBeVisible();
  await expect(ledger.locator('summary strong').filter({ hasText: /^Call 121$/ })).toHaveCount(0);
  expect(calls).toEqual({ modelWorkloads: 0, savedJobReads: 1 });
});
