import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {expect, test, type Page} from '@playwright/test';

// Opt in only after demo promotion. Explicit IDs make a stale resident worker,
// old canonical binding or accidental fallback fail instead of blessing it.
const expected: Record<string, string> = JSON.parse(process.env.LAB_REVIEW_EXPECTED_DEMOS || '{}');
const scenarios = ['photography', 'boardgames', 'dreamjob'];
for (const [scenario, run] of Object.entries(expected)) {
  if (!scenarios.includes(scenario) || !/^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$/.test(run)) {
    throw new Error('LAB_REVIEW_EXPECTED_DEMOS must map known scenarios to explicit canonical UUIDs.');
  }
}
const titles = ['Choose a test persona', 'Create a situation', 'Build and connect the agent',
  'Run the application', 'Investigate execution', 'Evaluate behaviour', 'Optimize model routing',
  'Configure behavioural safeguards', 'Deploy with controlled access'];

async function stage(page: Page, step: number) {
  const current = Number((await page.getByTestId('step-counter').innerText()).match(/Step (\d+)/)?.[1]);
  for (let index = 0; index < Math.abs(step - current); index++) {
    await page.getByRole('button', {name: current < step ? 'Next →' : '← Back', exact: true}).click();
  }
  await expect(page.getByTestId('step-counter')).toHaveText(`Step ${step} of 9`);
}

for (const scenario of scenarios) test(`${scenario}: verify the promoted original, teaching flow and capture inventory without execution`, async ({page}) => {
  test.skip(!expected[scenario], 'Supply LAB_REVIEW_EXPECTED_DEMOS after the reviewed demo is explicitly promoted.');
  const runId = expected[scenario];
  const output = resolve('..', '.private', 'review', `native-ui-${new Date().toISOString().replaceAll(/[:.]/g, '-')}`, scenario);
  mkdirSync(output, {recursive: true});
  const requests: {method: string; path: string; scenario: string | null}[] = [];
  const screenshots: {file: string; sha256: string}[] = [];
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.setViewportSize({width: 1800, height: 1100});
  await page.route('**/api/**', async route => {
    const request = route.request(), url = new URL(request.url());
    requests.push({method: request.method(), path: url.pathname, scenario: url.searchParams.get('scenario_id')});
    expect(request.method()).toBe('GET');
    expect(['/api/journey/lesson', '/api/journey/demo-persona', '/api/journey/metadata', '/api/journey/execution']).toContain(url.pathname);
    await route.continue();
  });
  const response = (action: string) => page.waitForResponse(value => {
    const url = new URL(value.url());
    return url.pathname === `/api/journey/${action}` && url.searchParams.get('scenario_id') === scenario;
  });
  const lessonRead = response('lesson'), personaRead = response('demo-persona'), inventoryRead = response('metadata');
  await page.goto('/');
  if (scenario !== 'photography') await page.getByLabel('Scenario', {exact: true}).selectOption(scenario);
  const [lessonResponse, personaResponse, inventoryResponse] = await Promise.all([lessonRead, personaRead, inventoryRead]);
  for (const value of [lessonResponse, personaResponse, inventoryResponse]) expect(value.ok()).toBe(true);
  const [lesson, persona, inventory] = await Promise.all([lessonResponse.json(), personaResponse.json(), inventoryResponse.json()]);
  expect(lesson.run_id).toBe(runId);
  expect(lesson.state).toBe('recorded');
  expect(lesson.inference_calls_for_inspection).toBe(0);
  expect(lesson.trace.run.status).toBe('completed');
  expect(lesson.trace.run.cleanup_confirmed).toBe(true);
  expect(persona.available).toBe(true);
  const lock = JSON.parse(readFileSync(resolve('..', 'recordings', scenario, runId, 'source-lock.json'), 'utf8'));
  expect(persona.original_sha256).toBe(lock.original_sha256);
  expect(inventory.run_id).toBe(runId);
  expect(inventory.available).toBe(true);
  expect(inventory.inference_calls_for_inspection).toBe(0);
  expect(inventory.rows.length).toBeGreaterThanOrEqual(51);
  expect(inventory.rows.filter((row: Record<string, unknown>) => !['exists', 'not-used'].includes(String(row.status)))).toEqual([]);
  await expect(page.getByTestId('selected-persona')).toBeVisible();
  await expect(page.getByTestId('record-state')).toContainText(runId.slice(0, 8));

  for (const audience of ['Simplified', 'Detailed']) {
    await page.getByRole('button', {name: audience, exact: true}).click();
    await stage(page, 1);
    for (let step = 1; step <= 9; step++) {
      await expect(page.locator('.step-title')).toHaveText(titles[step - 1]);
      await expect(page.getByTestId('journey-panel').getByRole('alert')).toHaveCount(0);
      await expect(page.getByTestId('journey-panel').locator('.component-reference, .operation-path')).toHaveCount(0);
      if (step < 9) await page.getByRole('button', {name: 'Next →', exact: true}).click();
    }
  }

  await stage(page, 4);
  const facts = page.getByTestId('scenario-facts');
  if (scenario === 'dreamjob') {
    await page.getByRole('button', {name: 'Turn 2', exact: true}).click();
    await expect(facts.getByText("This turn's Fabric result", {exact: true})).toHaveCount(0);
    await expect(facts).toContainText('Advisor model calls: 0');
    await expect(facts).toContainText('There is no Fabric invocation or new course lookup');
    await page.getByRole('button', {name: 'Turn 3', exact: true}).click();
  }
  await expect(facts.getByText("This turn's Fabric result", {exact: true})).toHaveCount(1);
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  const config = page.getByTestId('journey-panel').getByRole('link', {name: 'its effective settings ↗', exact: true});
  await expect(config).toHaveAttribute('href', new RegExp(`/recordings/captures/${scenario}/${runId}/`));
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'build_config ↗', exact: true})).toHaveAttribute('href', /github\.com\/syseeker\/persona-simulation-lab\/blob\/[^/]+\/src\/learning_lab\/fabric_target\.py#L\d+$/);
  async function capture(file: string) {
    const path = resolve(output, file);
    await page.screenshot({path});
    screenshots.push({file, sha256: createHash('sha256').update(readFileSync(path)).digest('hex')});
  }
  await capture('01-fabric-configuration.png');
  await page.getByRole('button', {name: /5\s+Metadata/}).click();
  await expect(page.getByRole('columnheader', {name: 'YAML / JSON file', exact: true})).toBeVisible();
  await expect(page.locator('.run-identity')).toContainText(runId);
  await expect(page.locator('tr[data-requirement]')).toHaveCount(new Set(inventory.rows.filter((row:Record<string,any>)=>!row.condition_id||row.condition_purpose==='baseline').map((row:Record<string,any>)=>row.id)).size);
  if (inventory.conditions.length>1) {
    await page.getByRole('combobox',{name:'Condition',exact:true}).selectOption('*');
    await expect(page.locator('tr[data-requirement]')).toHaveCount(new Set(inventory.rows.map((row:Record<string,any>)=>row.id)).size);
  }
  await expect(page.locator('.metadata-page a[href^="/home/"], .metadata-page a[href^="file:"]')).toHaveCount(0);
  await capture('02-metadata.png');
  expect(errors).toEqual([]);
  writeFileSync(resolve(output, 'manifest.json'), JSON.stringify({schema: 'citizen-native-ui-review/v1',
    captured_at: new Date().toISOString(), scenario_id: scenario, expected_run_id: runId,
    verified_original_hash: persona.original_sha256, lessons: 18, metadata_rows: inventory.rows.length,
    requests, screenshots}, null, 2) + '\n');
  console.log(`Native UI review: ${output}`);
});
