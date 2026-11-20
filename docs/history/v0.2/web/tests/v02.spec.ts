import { expect, test, type Page } from '@playwright/test';
import { mkdir } from 'node:fs/promises';
import path from 'node:path';

// Every real model-workload request in this file must explicitly be offline.
// Fabric and MCP are real local integrations; structured dataset/eval fixtures below are labelled.
test.beforeEach(async ({ page }) => {
  for (const operation of ['chat', 'runs']) {
    await page.route(`**/api/${operation}`, async route => {
      if (route.request().method() === 'POST') expect(route.request().postDataJSON().mode).toBe('demo');
      await route.continue();
    });
  }
  await page.route('**/api/workbench', route => route.abort('blockedbyclient'));
});

async function nav(page: Page, label: string) {
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: new RegExp(label) }).click();
}

async function screenshots(page: Page, name: string) {
  const destination = path.resolve(process.cwd(), '../runs/browser-v02');
  await mkdir(destination, { recursive: true });
  await page.screenshot({ path: path.join(destination, name + '-desktop.png'), fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: path.join(destination, name + '-mobile.png'), fullPage: true });
}

test('one offline guided story retains native evidence across lessons without another simulation', async ({ page }) => {
  // The readiness fixture prevents a local developer's key from choosing Live
  // during hydration. The story/harness/MCP/evidence below are real offline execution.
  await page.route('**/api/status', route => route.fulfill({ json: {
    nim_key_present: false, proxy_configured: false, inference_configured: false,
    model: 'offline-readiness-fixture', catalogue_count: 12, snapshot_date: '2026-11-10', personas_audited: false
  } }));
  let starts = 0;
  page.on('request', request => { if (request.method() === 'POST' && request.url().endsWith('/api/runs')) starts++; });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Follow the whole application' })).toBeVisible();
  await expect(page.getByLabel('Teaching story')).toHaveValue('photography');
  await expect(page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: /Guided walkthrough/ })).toBeEnabled();
  await page.getByLabel('Story inference').selectOption('demo');
  await page.getByRole('button', { name: 'Start one offline citizen story' }).click();
  await expect(page.getByRole('region', { name: 'Course facts CC-001' })).toBeVisible({ timeout: 30000 });
  await expect(page.getByText('completed', { exact: true }).first()).toBeVisible();
  await page.getByRole('button', { name: /Follow the evidence/ }).click();
  const evidence = page.getByRole('region', { name: 'Backend evidence' });
  await expect(evidence.getByRole('button', { name: 'Copy local run folder', exact: true })).toBeVisible();
  await expect(evidence.getByLabel('Native Relay scopes')).toBeVisible();
  await expect(evidence.getByRole('heading', { name: 'Model calls and routing', exact: true })).toBeVisible();
  const modelCall = evidence.locator('details.lab-check-row').filter({ has: page.locator('summary').filter({ hasText: /Call 1\b/ }) }).first();
  await modelCall.locator('summary').click();
  await expect(modelCall.getByText(/Requested alias:/)).toBeVisible();
  await evidence.getByRole('button', { name: 'Timeline', exact: true }).click();
  await expect(evidence.getByRole('button', { name: 'Timeline', exact: true })).toHaveAttribute('aria-pressed', 'true');
  await evidence.getByText(/Saved artifacts ·/).click();
  await expect(evidence.locator('.artifact-row').filter({ hasText: /relay\.jsonl/ }).first()).toBeVisible();
  await evidence.getByRole('button', { name: 'Read artifact', exact: true }).first().click();
  await expect(evidence.locator('.raw-artifact')).toBeVisible();
  await page.getByRole('button', { name: /Inside Fabric/ }).click();
  await expect(evidence.getByText('Resolved execution plan', { exact: true })).toBeVisible();
  await evidence.getByText('Runtime and invocation lifecycle', { exact: true }).click();
  await expect(evidence.getByText(/runtime_started/).first()).toBeVisible();
  await screenshots(page, 'guided-evidence');
  await page.getByRole('button', { name: /Evaluate with Helix/ }).click();
  await page.getByRole('button', { name: 'Evaluate saved replies', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Inspectable Helix evaluation' }).getByText('Applicable checks passed')).toBeVisible();
  expect(starts).toBe(1);
});

for (const engine of ['direct', 'relay', 'fabric']) {
  test(`board-game no-match is an honest offline answer through ${engine}`, async ({ page }) => {
    await page.goto('/');
    await nav(page, 'Try the advisor');
    await page.getByLabel('INFERENCE', { exact: true }).selectOption('demo');
    await page.getByLabel('ADVISOR RUNTIME').selectOption(engine);
    await page.getByLabel('Your learning goal').fill('Hello, I want to learn how to play board games.');
    await page.getByRole('button', { name: 'Send learning goal' }).click();
    await expect(page.locator('.message').last()).toContainText('no suitable match', { timeout: 30000 });
    await expect(page.locator('.message').last()).not.toContainText('[ERROR');
    await expect(page.getByRole('heading', { name: 'From the catalogue' })).toHaveCount(0);
    await expect(page.getByRole('heading', { name: 'Behind this reply' })).toBeVisible();
  });
}

const fixtureRecords = Array.from({ length: 45 }, (_, index) => ({
  source_id: 'fabricated-' + index, source: 'hf-profile-only', source_revision: 'fabricated-browser-fixture',
  original_profile_sha256: 'fixture-hash-' + index, kind: 'original',
  profile: { uuid: 'fabricated-' + index, age: 20 + index, occupation: 'Fabricated occupation ' + index,
    planning_area: 'Fixture area', career_goals_and_ambitions: 'A fabricated browser test ambition' }
}));

async function fixtureDatasets(page: Page) {
  const metadata = { source: 'hf-profile-only', name: 'Fabricated HF browser fixture', ready: true, row_count: 45,
    revision: 'fabricated-browser-fixture', notice: 'Fabricated test data, not actual Nemotron source records', license: 'Fixture only',
    columns: [{ name: 'uuid', type: 'string' }, { name: 'occupation', type: 'string' }], ocean_fields: [] };
  await page.route('**/api/datasets', route => route.fulfill({ json: { datasets: [metadata,
    { ...metadata, source: 'ngc', name: 'Singapore NGC Extended fixture', ready: false, row_count: 0,
      notice: 'Fabricated unavailable Singapore Extended test fixture', reason: 'Singapore NGC asset is not installed',
      setup: 'Configure access to the Singapore Extended source.', source_url: 'https://example.org/fixture' }] } }));
  await page.route('**/api/dataset-browse', route => {
    const body = route.request().postDataJSON();
    return route.fulfill({ json: { dataset: metadata, records: fixtureRecords.slice(body.offset, body.offset + body.limit),
      offset: body.offset, limit: body.limit, total: 45, has_more: body.offset + body.limit < 45, inference_calls: 0 } });
  });
  await page.route('**/api/persona-sample', route => route.fulfill({ json: {
    source_ids: ['fabricated-39'], rows: [fixtureRecords[39].profile], records: [fixtureRecords[39]], seed: 123,
    sampling: 'Fabricated test selection', matched_profiles: 45, inference_calls: 0 } }));
  await page.route('**/api/persona-lock', route => {
    const ids = route.request().postDataJSON().source_ids;
    return route.fulfill({ json: { source_ids: ids, records: fixtureRecords.filter(item => ids.includes(item.source_id)),
      rows: fixtureRecords.filter(item => ids.includes(item.source_id)).map(item => item.profile), inference_calls: 0 } });
  });
  await page.route('**/api/workbench-history', route => route.fulfill({ json: [] }));
}

test('dataset explorer pages, inspects, randomises and locks source inputs without inference', async ({ page }) => {
  await fixtureDatasets(page);
  const previous = { run_id: 'aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa', status: 'completed', calls: 1,
    story: { title: 'Earlier saved story fixture' }, spec: { story_id: 'baking', mode: 'demo' }, episodes: [], events: [] };
  await page.route('**/api/run?*', route => route.fulfill({ json: previous }));
  let modelWorkloads = 0;
  page.on('request', request => { if (request.method() === 'POST' && /\/api\/(chat|runs|workbench)$/.test(request.url())) modelWorkloads++; });
  await page.goto('/?story_run=' + previous.run_id);
  await expect(page.getByRole('heading', { name: 'Earlier saved story fixture' })).toBeVisible();
  await nav(page, 'Data workbench');
  await expect(page.getByText('45 matching source records', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Next records', exact: true }).click();
  await page.getByRole('button', { name: 'Inspect original fields', exact: true }).first().click();
  await expect(page.getByText('Original profile · fabricated-20', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Random profile', exact: true }).click();
  await expect(page.getByText('Original profile · fabricated-39', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Use 1 locked profile in simulation' }).click();
  await expect(page.getByRole('heading', { name: 'Locked source input' })).toBeVisible();
  await expect(page.getByText('fabricated-39', { exact: true })).toBeVisible();
  await expect(page).not.toHaveURL(/story_run=/);
  await expect(page.getByRole('heading', { name: 'Earlier saved story fixture' })).toHaveCount(0);
  expect(modelWorkloads).toBe(0);
  await nav(page, 'Data workbench');
  await page.getByRole('button', { name: /Singapore NGC Extended fixture/ }).click();
  await expect(page.getByText('Singapore NGC asset is not installed')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Random profile', exact: true })).toBeDisabled();
  expect(modelWorkloads).toBe(0);
});

test('custom generation fields retain types, preserve original data and select one saved row for a story', async ({ page }) => {
  await fixtureDatasets(page);
  let generation: any;
  const rows = [0, 1].map(index => ({ generated_id: 'generated-fixture-' + index, kind: 'enriched-source',
    hypothesis: true, source_id: fixtureRecords[index].source_id, profile: fixtureRecords[index].profile,
    scenario: null, generated_fields: { last_drawn_salary_sgd: 5000 + index, favourite_brands: ['Fixture Brand'] },
    lineage: { source_id: fixtureRecords[index].source_id, source_distribution: 'hf-profile-only',
      source_revision: 'fabricated-browser-fixture' } }));
  await page.route('**/api/workbench', route => {
    generation = route.request().postDataJSON();
    return route.fulfill({ json: { job_id: 'fabricated-job', status: 'completed', calls: 4, budget: 120,
      spec: generation, result: { status: 'completed', operation: 'columns', records: rows,
        config_sha256: 'fabricated-config', warnings: [], notice: 'Fabricated test generation; no model was called' } } });
  });
  await page.goto('/');
  await nav(page, 'Data workbench');
  await page.getByRole('button', { name: 'Add salary example', exact: true }).click();
  await page.getByRole('button', { name: 'Add favourite brands example', exact: true }).click();
  await page.getByLabel('Data Designer operation').selectOption('columns');
  await page.getByLabel('Preview rows').fill('2');
  await page.getByRole('button', { name: 'Preview generation configuration', exact: true }).click();
  await expect(page.locator('pre').filter({ hasText: 'last_drawn_salary_sgd' }).first()).toContainText('text-list');
  await page.getByRole('button', { name: 'Generate live preview', exact: true }).click();
  await expect(page.getByLabel('Preview row to use')).toBeVisible();
  expect(generation.fields.map((field: any) => [field.name, field.type])).toEqual([
    ['last_drawn_salary_sgd', 'decimal'], ['favourite_brands', 'text-list']
  ]);
  expect(generation.fields[0].minimum).toBe(0);
  await page.getByLabel('Preview row to use').selectOption('fabricated-1');
  await expect(page.getByText('Selected row and its provenance')).toBeVisible();
  await screenshots(page, 'data-workbench');
  await page.getByRole('button', { name: 'Use generated data in the guided story', exact: true }).click();
  await expect(page.getByText('Saved Data Designer input · fabricated-job.', { exact: false })).toBeVisible();
  await expect(page.getByText('fabricated-1', { exact: true })).toBeVisible();
});

test('an invalid saved advisor answer cannot hide behind an aggregate passing score', async ({ page }) => {
  const runId = 'aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa', episode = 'bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb';
  const run: any = { run_id: runId, status: 'completed_with_failures', started_at: '2026-11-17T01:00:00Z', calls: 1,
    source_notice: 'Fabricated failed-answer browser fixture', spec: { mode: 'demo', engine: 'fabric', source: 'hf-profile-only', personas: 1, strategies: ['concise'] },
    episodes: [{ episode_id: episode, status: 'failed', strategy: 'concise', error: 'Fabricated turn-limit fixture' }],
    events: [{ type: 'episode_started', episode_id: episode, strategy: 'concise' },
      { type: 'message', role: 'user', episode_id: episode, content: 'Fixture question' },
      { type: 'message', role: 'assistant', episode_id: episode, content: '[ERROR: Max turns (10) exceeded]' }] };
  const evaluation = { engine: 'NeMo Helix Evals SDK', details: { summary: { concise: { criteria: 1, passed: 0, failed: 1, errors: 0, not_applicable: 1 } }, rows: [
    { case_id: episode + ':1', episode_id: episode, turn: 1, condition: 'concise', criterion: 'answer_validity', status: 'fail', expected: 'true', output: 'false',
      reason: 'Fabricated fixture: a turn-limit error is not a public answer.', evidence: { answer_excerpt: '[ERROR: Max turns (10) exceeded]' } },
    { case_id: episode + ':1', episode_id: episode, turn: 1, condition: 'concise', criterion: 'fee_caution', status: 'not_applicable', output: null,
      reason: 'No valid public answer exists to assess.' }] }, row_scores: [{ score: 0, fixture: true }] };
  await page.route('**/api/runs*', route => route.fulfill({ json: [run] }));
  await page.route('**/api/run?*', route => route.fulfill({ json: run }));
  await page.route('**/api/evaluate', route => { run.evaluation = evaluation; return route.fulfill({ json: evaluation }); });
  await page.goto('/?run=' + runId);
  await page.getByRole('button', { name: 'Evaluate saved replies', exact: true }).click();
  const checks = page.getByRole('region', { name: 'Inspectable Helix evaluation' });
  await expect(checks.getByText('0 / 1', { exact: true })).toBeVisible();
  await expect(checks.getByText('1 failed', { exact: true })).toBeVisible();
  await checks.getByLabel('Criterion rows').selectOption('attention');
  await expect(checks.getByText('1 of 2 saved criterion rows')).toBeVisible();
  await checks.locator('summary').filter({ hasText: 'answer validity' }).click();
  await expect(checks.getByText('Observed: false', { exact: true })).toBeVisible();
  await expect(checks.getByText('Fabricated fixture: a turn-limit error is not a public answer.')).toBeVisible();
});

test('deployment UI reports unavailable readiness without registering or deploying', async ({ page }) => {
  const operations: string[] = [];
  await page.route('**/api/profiles', route => route.fulfill({ json: { profiles: [
    { id: 'openshell', label: 'OpenShell fabricated readiness fixture', configured: false, status: 'not_probed' }
  ] } }));
  await page.route('**/api/platform', route => {
    const operation = route.request().postDataJSON().operation; operations.push(operation);
    expect(operation).toBe('status');
    return route.fulfill({ json: { ready: false, error: 'Fabricated fixture: no Platform or OpenShell service is available.' } });
  });
  await page.goto('/');
  await nav(page, 'Deploy the agent');
  await expect(page.getByRole('button', { name: 'Deploy with OpenShell', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Check Platform readiness', exact: true }).click();
  await expect(page.getByText('Platform not ready', { exact: true })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Native Platform result' }).getByText('Fabricated fixture: no Platform or OpenShell service is available.', { exact: false })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Deploy with OpenShell', exact: true })).toBeDisabled();
  expect(operations).toEqual(['status']);
});

test('an in-flight advisor reply keeps its harness and routing controls frozen', async ({ page }) => {
  let releaseReply!: () => void;
  const replyGate = new Promise<void>(resolve => releaseReply = resolve);
  await page.route('**/api/chat', async route => {
    expect(route.request().postDataJSON().mode).toBe('demo');
    await replyGate;
    await route.fulfill({ json: { session_id: 'dddddddd-dddd-4ddd-8ddd-dddddddddddd',
      content: 'Fabricated delayed offline reply for the selected Deep Agents harness.',
      matches: [], engine: 'fabric', calls: 0, turns: 1 } });
  });
  await page.goto('/');
  await nav(page, 'Try the advisor');
  await page.getByLabel('INFERENCE', { exact: true }).selectOption('demo');
  await page.getByLabel('ADVISOR RUNTIME').selectOption('fabric');
  await page.getByLabel('Your learning goal').fill('photography');
  const submitted = page.waitForRequest(request => request.method() === 'POST' && request.url().endsWith('/api/chat'));
  await page.getByRole('button', { name: 'Send learning goal' }).click();
  await submitted;
  await expect(page.getByRole('combobox', { name: 'Fabric harness', exact: true })).toBeDisabled();
  await expect(page.getByRole('combobox', { name: 'Model routing', exact: true })).toBeDisabled();
  await expect(page.getByLabel('ADVISOR RUNTIME')).toBeDisabled();
  releaseReply();
  await expect(page.locator('.message').last()).toContainText('Fabricated delayed offline reply');
  await expect(page.getByRole('combobox', { name: 'Fabric harness', exact: true })).toBeEnabled();
  await expect(page.getByRole('combobox', { name: 'Model routing', exact: true })).toBeEnabled();
  await page.getByRole('combobox', { name: 'Fabric harness', exact: true }).selectOption('hermes');
  await expect(page.locator('.message')).toHaveCount(0);
});

test('deployment trace inspection uses the saved session and leaving closes it once without inference', async ({ page }) => {
  const session = 'fixture-saved-platform-session';
  const operations: { operation: string; arguments: any }[] = [];
  await page.route('**/api/status', route => route.fulfill({ json: { managed_session: null,
    nim_key_present: false, inference_configured: false, catalogue_count: 12 } }));
  await page.route('**/api/profiles', route => route.fulfill({ json: { profiles: [] } }));
  await page.route('**/api/platform', route => {
    const body = route.request().postDataJSON(); operations.push(body);
    if (body.operation === 'sessions_create') return route.fulfill({ json: {
      session: { name: session, notice: 'Fabricated session fixture; no Platform was contacted' },
      deployment: { frozen_preferences: { goal: 'photography', budget_sgd: 50, days: [5] } }
    } });
    if (body.operation === 'logs') return route.fulfill({ json: { job_id: 'fixture-log-job',
      operation: 'logs', status: 'completed', calls: 0, usage: [], result: {
        notice: 'Fabricated native Intake browser fixture; no Platform or model was called',
        intake: { status: 'fabricated-fixture', traces: [{ trace_id: 'fixture-trace' }],
          spans: [{ span_id: 'fixture-one' }, { span_id: 'fixture-two' }] },
        runtime_session_logs: { status: 'fabricated-fixture', stdout: 'Fabricated runtime MCP evidence' }
      } } });
    expect(body.operation).toBe('sessions_close');
    return route.fulfill({ json: { closed: true, fixture: true } });
  });
  await page.goto('/');
  await nav(page, 'Deploy the agent');
  await page.getByLabel('Saved Platform job ID').fill('44444444-4444-4444-8444-444444444444');
  await page.getByRole('button', { name: 'Create a fresh Platform session', exact: true }).click();
  await expect(page.getByLabel('Platform session', { exact: true })).toHaveValue(session);
  await expect(page.getByLabel('Trusted learning goal')).toBeDisabled();
  await expect(page.getByLabel('Saved Platform job ID')).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Read saved operation', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Undeploy this demo', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Read deployment logs and native trace', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Native managed trace', exact: true })).toBeVisible();
  await expect(page.getByText('1 traces', { exact: true })).toBeVisible();
  await expect(page.getByText('2 spans', { exact: true })).toBeVisible();
  await page.getByText('Saved operation and model-call ledger', { exact: true }).click();
  await expect(page.getByText('0 model calls', { exact: true })).toBeVisible();
  expect(operations.find(item => item.operation === 'logs')?.arguments.session_id).toBe(session);
  await screenshots(page, 'deployment-native-trace');
  await nav(page, 'Guided walkthrough');
  await expect.poll(() => operations.filter(item => item.operation === 'sessions_close').length).toBe(1);
  expect(operations.find(item => item.operation === 'sessions_close')?.arguments.name).toBe(session);
  expect(operations.map(item => item.operation)).toEqual(['sessions_create', 'logs', 'sessions_close']);
});

test('deployment runtime is explicit, preserves custom names and never falls back after a Docker failure', async ({ page }) => {
  // Every operation is a labelled browser fixture; no Platform or model is contacted.
  const operations: { operation: string; arguments: any; target: string }[] = [];
  let created = 0, releaseDeploy!: () => void;
  const deploymentGate = new Promise<void>(resolve => releaseDeploy = resolve);
  await page.route('**/api/status', route => route.fulfill({ json: { managed_session: null,
    nim_key_present: false, inference_configured: false, catalogue_count: 12 } }));
  await page.route('**/api/profiles', route => route.fulfill({ json: { profiles: [] } }));
  await page.route('**/api/platform', async route => {
    const body = route.request().postDataJSON(); operations.push(body);
    if (body.operation === 'status') return route.fulfill({ json: { ready: true, notice: 'Fabricated reachable Platform fixture' } });
    if (body.operation === 'deploy') {
      await deploymentGate;
      return route.fulfill({ status: 503, json: { error: 'Fabricated Docker runtime unavailable; no deployment occurred.' } });
    }
    if (body.operation === 'sessions_create') return route.fulfill({ json: {
      session: { name: 'fixture-context-session-' + ++created }, deployment: { frozen_preferences: null }
    } });
    if (body.operation === 'sessions_close') return route.fulfill({ json: { closed: true, fixture: true } });
    expect(body.operation).toBe('logs');
    return route.fulfill({ json: { fixture: true, notice: 'Fabricated saved log result; no native records requested.' } });
  });
  await page.goto('/');
  await nav(page, 'Deploy the agent');
  const runtime = page.getByRole('combobox', { name: 'Deployment runtime', exact: true });
  const harness = page.getByRole('combobox', { name: 'Packaged harness', exact: true });
  const connection = page.getByRole('combobox', { name: 'Platform connection', exact: true });
  const name = page.getByLabel('Deployment name', { exact: true });
  await expect(runtime).toHaveValue('openshell');
  await expect(name).toHaveValue('sg-learning-demo');
  await harness.selectOption('hermes');
  await runtime.selectOption('docker');
  await expect(name).toHaveValue('sg-learning-hermes-docker');
  await name.fill('my-reviewed-deployment');
  await runtime.selectOption('openshell');
  await runtime.selectOption('docker');
  await expect(name).toHaveValue('my-reviewed-deployment');
  await page.getByRole('button', { name: 'Check Platform readiness', exact: true }).click();
  const deploy = page.getByRole('button', { name: 'Deploy with Docker', exact: true });
  await expect(deploy).toBeEnabled();
  const submitted = page.waitForRequest(request => request.method() === 'POST'
    && request.url().endsWith('/api/platform') && request.postDataJSON().operation === 'deploy');
  await deploy.click(); await submitted;
  await expect(runtime).toBeDisabled();
  await expect(harness).toBeDisabled();
  await expect(connection).toBeDisabled();
  releaseDeploy();
  await expect(page.getByRole('alert')).toContainText('Fabricated Docker runtime unavailable');
  const attempts = operations.filter(item => item.operation === 'deploy');
  expect(attempts).toHaveLength(1);
  expect(attempts[0].arguments).toMatchObject({ mode: 'docker', name: 'my-reviewed-deployment',
    agent: 'singapore-learning-advisor-hermes', image: 'persona-lab-hermes:0.2.0' });
  await screenshots(page, 'deployment-runtime');

  // A closed session remains inspectable until its deployment context changes.
  for (const changeContext of [
    async () => { await name.fill('another-reviewed-deployment'); await name.blur(); },
    async () => { await harness.selectOption('deepagents'); },
    async () => { await connection.selectOption('remote'); },
    async () => { await runtime.selectOption('openshell'); }
  ]) {
    await page.getByRole('button', { name: 'Create a fresh Platform session', exact: true }).click();
    const session = page.getByLabel('Platform session', { exact: true });
    await expect(session).toHaveValue(/fixture-context-session-/);
    const identity = await session.inputValue();
    await expect(runtime).toBeDisabled();
    await page.getByRole('button', { name: 'Close conversation session', exact: true }).click();
    await expect(session).toHaveValue('');
    const logs = page.getByRole('button', { name: 'Read deployment logs and native trace', exact: true });
    const read = async () => {
      const previous = operations.filter(item => item.operation === 'logs').length;
      await logs.click();
      await expect.poll(() => operations.filter(item => item.operation === 'logs').length).toBe(previous + 1);
      await expect(logs).toBeEnabled();
      return operations.filter(item => item.operation === 'logs').at(-1)!;
    };
    expect((await read()).arguments.session_id).toBe(identity);
    await changeContext();
    expect((await read()).arguments).not.toHaveProperty('session_id');
  }
  expect(operations.filter(item => item.operation === 'deploy')).toHaveLength(1);
});

test('saved failed Platform evidence reopens its ledger without restoring a live session', async ({ page }) => {
  const identity = '44444444-4444-4444-8444-444444444444';
  const operations: any[] = [];
  await page.route('**/api/status', route => route.fulfill({ json: { managed_session: null,
    nim_key_present: false, inference_configured: false, catalogue_count: 12 } }));
  await page.route('**/api/profiles', route => route.fulfill({ json: { profiles: [] } }));
  await page.route('**/api/platform', route => {
    const body = route.request().postDataJSON(); operations.push(body);
    if (body.operation === 'job') {
      expect(body.job_id).toBe(identity);
      return route.fulfill({ json: { job_id: identity, operation: 'invoke', target: 'remote',
        status: 'failed', calls: 2, conversation_turns: 1,
        story_reference: { run_id: '11111111-1111-4111-8111-111111111111', episode_id: '22222222-2222-4222-8222-222222222222', condition_id: identity },
        error: 'Fabricated saved invocation failure; no current operation was invoked.',
        usage: [{ call: 1, status: 'error', role: 'assistant', fixture: true }],
        result: { notice: 'Fabricated historical failed-job browser fixture',
          session_identity: { resource_name: 'persona-lab/fixture-closed-session' },
          response: { model: 'persona-lab/fixture-closed-deployment' } }
      } });
    }
    expect(body.operation).toBe('logs');
    return route.fulfill({ json: { notice: 'Fabricated native log lookup fixture',
      intake: { status: 'no_records_observed', traces: [], spans: [] } } });
  });
  await page.goto('/');
  await nav(page, 'Deploy the agent');
  const saved = page.getByRole('region', { name: 'Saved Platform operation', exact: true });
  await saved.getByLabel('Saved Platform job ID').fill(identity);
  await saved.getByRole('button', { name: 'Read saved operation', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Fabricated saved invocation failure');
  await page.getByText('Saved operation and model-call ledger', { exact: true }).click();
  await expect(page.getByText('2 model calls', { exact: true })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Open source saved experiment', exact: true })).toHaveAttribute('href', '/?run=11111111-1111-4111-8111-111111111111&view=conversation');
  await expect(page.locator('pre').filter({ hasText: 'conversation_turns' })).toContainText('"status": "failed"');
  await expect(page.getByLabel('Platform session', { exact: true })).toHaveValue('');
  await expect(page.getByRole('button', { name: 'Invoke deployed agent · live calls', exact: true })).toBeDisabled();
  await expect(saved.getByText(/No active conversation has been restored/)).toBeVisible();
  await expect(page.getByRole('combobox', { name: 'Platform connection', exact: true })).toHaveValue('remote');
  await expect(page.getByLabel('Deployment name', { exact: true })).toHaveValue('persona-lab/fixture-closed-deployment');
  expect(operations.map(item => item.operation)).toEqual(['job']);

  await page.getByRole('button', { name: 'Read deployment logs and native trace', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Native managed trace', exact: true })).toBeVisible();
  expect(operations[1]).toMatchObject({ target: 'remote', operation: 'logs', arguments: {
    name: 'persona-lab/fixture-closed-deployment', session_id: 'persona-lab/fixture-closed-session'
  } });
  await nav(page, 'Guided walkthrough');
  expect(operations.map(item => item.operation)).toEqual(['job', 'logs']);
});

test('failed session cleanup requires explicit recovery and confirmed native proof before releasing the guard', async ({ page }) => {
  // Deliberately failed/partial/confirmed browser fixtures; no runtime is stopped.
  const session = 'fixture-session-that-cannot-drain';
  const operations: any[] = [];
  let retained: any = null, recoveries = 0;
  await page.route('**/api/status', route => route.fulfill({ json: { managed_session: retained,
    nim_key_present: false, inference_configured: false, catalogue_count: 12 } }));
  await page.route('**/api/profiles', route => route.fulfill({ json: { profiles: [] } }));
  await page.route('**/api/platform', route => {
    const body = route.request().postDataJSON(); operations.push(body);
    if (body.operation === 'status') return route.fulfill({ json: { ready: true, fixture: true } });
    if (body.operation === 'sessions_create') return route.fulfill({ json: {
      session: { name: session }, deployment: { frozen_preferences: { goal: 'photography', budget_sgd: 50, days: [5] } }
    } });
    if (body.operation === 'sessions_close') return route.fulfill({ json: {
      job_id: 'fixture-failed-close', operation: 'sessions_close', status: 'failed', calls: 0,
      error: 'Fabricated close failure: native runtime could not drain.',
      result: { runtime_cleanup_confirmed: false, session: { status: 'active' }, fixture: true }
    } });
    expect(body.operation).toBe('sessions_recover');
    recoveries++;
    const confirmed = recoveries >= 3;
    return route.fulfill({ json: { job_id: 'fixture-recovery-' + recoveries, operation: 'sessions_recover',
      status: recoveries === 1 ? 'failed' : 'completed', calls: 0,
      ...(recoveries === 1 ? { error: 'Fabricated recovery rejection: native absence is not confirmed.' } : {}),
      result: { runtime_cleanup_confirmed: confirmed, deployment_removed: confirmed,
        session: { status: confirmed ? 'closed' : 'active' },
        proof_source: 'fabricated-authenticated-native-proof-fixture' }
    } });
  });
  await page.goto('/');
  await nav(page, 'Deploy the agent');
  await page.getByRole('button', { name: 'Check Platform readiness', exact: true }).click();
  await page.getByRole('button', { name: 'Create a fresh Platform session', exact: true }).click();
  await expect(page.getByLabel('Platform session', { exact: true })).toHaveValue(session);
  await page.getByRole('button', { name: 'Close conversation session', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Fabricated close failure');
  const recover = page.getByRole('button', { name: 'Stop failed deployment and close session', exact: true });
  const guardHeld = async () => {
    await expect(page.getByLabel('Platform session', { exact: true })).toHaveValue(session);
    await expect(page.getByRole('button', { name: 'Create a fresh Platform session', exact: true })).toBeDisabled();
    await expect(page.getByRole('button', { name: 'Invoke deployed agent · live calls', exact: true })).toBeDisabled();
    await expect(recover).toBeVisible();
  };
  await guardHeld();
  expect(recoveries).toBe(0);
  await expect(page.getByRole('region', { name: 'Failed deployment recovery' })).toContainText('all its sessions');
  await recover.click();
  await expect(page.getByRole('alert')).toContainText('Fabricated recovery rejection');
  await guardHeld();
  await recover.click();
  await expect(page.getByRole('alert')).toContainText('Native recovery has not confirmed');
  await guardHeld();
  await screenshots(page, 'deployment-recovery');
  await recover.click();
  await expect(page.getByLabel('Platform session', { exact: true })).toHaveValue('');
  await expect(recover).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Create a fresh Platform session', exact: true })).toBeEnabled();
  await expect(page.getByRole('button', { name: 'Deploy with OpenShell', exact: true })).toBeDisabled();
  await expect(page.getByRole('region', { name: 'Native Platform result' })).toContainText('fabricated-authenticated-native-proof-fixture');
  expect(recoveries).toBe(3);

  // A retained remote guard exposes the same explicit action after a reload.
  retained = { session_name: 'fixture-retained-remote-session', invocation_state: 'uncertain',
    scope: ['remote', 'https://example.invalid', 'fixture-workspace'] };
  await page.reload();
  await nav(page, 'Deploy the agent');
  await expect(recover).toBeVisible();
  await expect(page.getByRole('button', { name: 'Create a fresh Platform session', exact: true })).toBeDisabled();
  expect(recoveries).toBe(3);
  await recover.click();
  await expect(recover).toHaveCount(0);
  expect(operations.at(-1)).toMatchObject({ operation: 'sessions_recover', target: 'remote',
    arguments: { name: 'fixture-retained-remote-session' } });
  expect(operations.filter(item => item.operation === 'invoke')).toHaveLength(0);
  expect(operations.filter(item => item.operation === 'sessions_close')).toHaveLength(1);
  expect(recoveries).toBe(4);
});
