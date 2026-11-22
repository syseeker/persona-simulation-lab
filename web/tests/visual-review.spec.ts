import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {expect, test} from '@playwright/test';

test('capture the real read-only guide for visual developer review', async ({page}) => {
  const output = resolve('..', '.private', 'review', `w2-ui-${new Date().toISOString().replaceAll(/[:.]/g, '-')}`);
  mkdirSync(output, {recursive: true});
  const requests: {method: string; path: string}[] = [], screenshots: {file: string; sha256: string}[] = [];
  await page.setViewportSize({width: 1800, height: 1100});
  // Only the fixed-recording readers reach the local worker. No live readiness,
  // inference, simulation, registration, deployment or recovery request can run.
  await page.route('**/api/**', async route => {
    const request = route.request(), url = new URL(request.url());
    requests.push({method: request.method(), path: url.pathname});
    expect(request.method()).toBe('GET');
    expect(['/api/journey/lesson', '/api/journey/demo-persona', '/api/journey/metadata']).toContain(url.pathname);
    await route.continue();
  });
  async function capture(file: string) {
    const path = resolve(output, file);
    await page.screenshot({path});
    screenshots.push({file, sha256: createHash('sha256').update(readFileSync(path)).digest('hex')});
  }
  await page.goto('/');
  await expect(page.getByTestId('selected-persona').or(page.getByTestId('scenario-facts').locator('.unavailable'))).toBeVisible();
  await page.getByRole('button', {name: 'Next →', exact: true}).click();
  await page.getByRole('button', {name: 'Next →', exact: true}).click();
  await expect(page.locator('.step-title')).toHaveText('Build and connect the agent');
  await capture('01-simplified-lesson-3.png');
  await page.getByRole('button', {name: 'Inspect Citizen advisor', exact: true}).click();
  await expect(page.locator('.step-title')).toHaveText('Citizen advisor');
  await expect(page.getByTestId('scenario-facts')).toHaveCount(0);
  await capture('02-concept-citizen-advisor.png');
  await page.getByRole('button', {name: 'Explain Citizen advisor: Connect the selected agent', exact: true}).click();
  await expect(page.locator('.step-title')).toHaveText('Connect the selected agent');
  await capture('03-action-connect-agent.png');
  await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  await expect(page.locator('.step-title')).toHaveText('Build the typed FabricConfig');
  await capture('04-detailed-fabric-configuration.png');
  await page.getByRole('button', {name: /5\s+Metadata/}).click();
  await expect(page.getByRole('heading', {name: 'Metadata', exact: true})).toBeVisible();
  await expect(page.getByRole('columnheader', {name: 'YAML / JSON file', exact: true})).toBeVisible();
  await expect(page.getByRole('status')).toHaveCount(0);
  await capture('05-metadata.png');
  writeFileSync(resolve(output, 'manifest.json'), JSON.stringify({schema: 'citizen-ui-review/v1',
    captured_at: new Date().toISOString(), source: 'current local guide and its tagged fixed recordings',
    viewport: {width: 1800, height: 1100}, scenario_id: 'photography', requests, screenshots}, null, 2) + '\n');
  expect(requests.length).toBeGreaterThan(0);
  expect(requests.every(request => request.method === 'GET')).toBe(true);
  console.log(`Visual review screenshots: ${output}`);
});
