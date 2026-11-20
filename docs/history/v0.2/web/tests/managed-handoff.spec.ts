import { expect, test, type Page } from '@playwright/test';

const runId = '11111111-1111-4111-8111-111111111111';
const episodeId = '22222222-2222-4222-8222-222222222222';
const firstInput = 'Fixture first public learner input: I want a sourced class.';

function savedRun(preferences: any, harness = 'deepagents') {
  return { run_id: runId, status: 'completed', started_at: '2026-11-17T01:00:00Z', calls: 2,
    source_notice: 'Fabricated saved-story browser fixture; no source resident or model call',
    catalogue_sha256: 'fixture-original-catalogue-hash', story: { id: 'baking', title: 'Fixture saved citizen story' },
    spec: { mode: 'demo', engine: 'fabric', harness, model_route: 'fixed', story_id: 'baking',
      source: 'hf-profile-only', personas: 1, strategies: ['concise'] },
    episodes: [{ episode_id: episodeId, status: 'completed', strategy: 'concise', preferences,
      source_id: 'fixture-source-identity' }],
    events: [{ type: 'episode_started', episode_id: episodeId, strategy: 'concise', preferences,
      source_id: 'fixture-source-identity' },
    { type: 'message', episode_id: episodeId, role: 'user', content: firstInput },
    { type: 'message', episode_id: episodeId, role: 'assistant', content: 'Fixture previous reply; never restored as memory.' }] };
}

async function fixtureApplication(page: Page, run: ReturnType<typeof savedRun>) {
  const posts: any[] = [];
  await page.route('**/api/**', async route => {
    const request = route.request(), url = new URL(request.url());
    const operation = url.pathname.split('/').at(-1);
    if (request.method() === 'POST') {
      const body = request.postDataJSON(); posts.push({ endpoint: operation, ...body });
      expect(operation).toBe('platform');
      if (body.operation === 'sessions_create') return route.fulfill({ json: {
        session: { name: 'fixture-new-managed-session' }, deployment: { frozen_preferences: null }
      } });
      if (body.operation === 'invoke') return route.fulfill({ json: { job_id: 'fixture-invoke-job',
        operation: 'invoke', status: 'failed', calls: 0,
        error: 'Fabricated invocation fixture; no runtime or model was contacted.', result: { fixture: true } } });
      expect(body.operation).toBe('sessions_close');
      return route.fulfill({ json: { closed: true, fixture: true } });
    }
    const fixtures: Record<string, unknown> = {
      status: { nim_key_present: false, inference_configured: false, managed_session: null, catalogue_count: 0 },
      catalogue: [], stories: [{ id: 'baking', title: 'Fixture saved citizen story', lesson: 'Fixture only', expected: 'Fixture only' }],
      profiles: { profiles: [] }, runs: [run], run,
      source: { purpose: 'Fabricated source reference', content: 'Fixture source only', notice: 'No SDK loaded' }
    };
    if (operation === 'trace') {
      const episode = url.searchParams.get('episode_id');
      return route.fulfill({ json: { version: 1, run_id: run.run_id, episode_id: episode, mode: 'demo', status: 'completed',
        source_notice: 'Fabricated trace fixture; no SDK called', source: {}, profile: {}, scenario: {}, snapshot: { available: false },
        turns: [{ number: 1, user: run.events.find((event: any) => event.episode_id === episode && event.role === 'user')?.content,
          assistant: 'Fabricated saved reply', tools: [], course_references: [] }], notices: [] } });
    }
    expect(Object.hasOwn(fixtures, operation!)).toBe(true);
    return route.fulfill({ json: fixtures[operation!] });
  });
  return posts;
}

async function guidedDeployment(page: Page) {
  await page.goto('/?story_run=' + runId);
  await expect(page.getByRole('heading', { name: 'Fixture saved citizen story', exact: true })).toBeVisible();
  await page.getByRole('region', { name: 'Guided walkthrough steps' }).getByRole('button', { name: /Deploy in OpenShell/ }).click();
  await page.getByRole('button', { name: 'Prepare saved story for deployment', exact: true }).click();
}

test('preparing a saved story is idle and creates a distinct managed condition without restoring memory', async ({ page }) => {
  const preferences = { goal: 'photography', budget_sgd: 50, days: [5], planning_area: null, known_skills: null, kind: null };
  const posts = await fixtureApplication(page, savedRun(preferences, 'hermes'));
  await guidedDeployment(page);
  const prepared = page.getByRole('region', { name: 'Prepared managed story', exact: true });
  await expect(prepared).toContainText(runId);
  await expect(prepared).toContainText(episodeId);
  await expect(prepared).toContainText('fixture-original-catalogue-hash');
  await expect(prepared).not.toContainText('Fixture previous reply');
  await expect(page.getByLabel('Deployed learner message')).toHaveValue(firstInput);
  await expect(page.getByLabel('Deployed learner message')).toBeDisabled();
  await expect(page.getByRole('combobox', { name: 'Packaged harness', exact: true })).toHaveValue('hermes');
  await expect(page.getByLabel('Platform session', { exact: true })).toHaveValue('');
  await expect(page.getByRole('button', { name: 'Invoke deployed agent · live calls', exact: true })).toBeDisabled();
  const original = await prepared.locator('.lab-path').innerText();
  await page.getByRole('combobox', { name: 'Packaged harness', exact: true }).selectOption('deepagents');
  await expect(prepared).toContainText('Explicit new condition');
  await expect(prepared.locator('.lab-path')).not.toHaveText(original);
  expect(posts).toEqual([]);
});

test('review handoff preserves all constraints, blocks a native preset mismatch and sends only explicit reference keys', async ({ page }) => {
  const preferences = { goal: 'baking', budget_sgd: 120, days: null, planning_area: 'Yishun', known_skills: ['mixing'], kind: 'community' };
  const posts = await fixtureApplication(page, savedRun(preferences));
  await page.goto('/?run=' + runId);
  await page.getByRole('button', { name: 'Prepare selected story for deployment', exact: true }).click();
  const prepared = page.getByRole('region', { name: 'Prepared managed story', exact: true });
  await expect(prepared).toContainText('does not match');
  await expect(page.getByLabel('Trusted learning goal')).toHaveValue('baking');
  await expect(page.getByLabel('Total budget in SGD')).toHaveValue('120');
  await expect(page.getByLabel('Saturday availability')).not.toBeChecked();
  await expect(page.getByRole('button', { name: 'Invoke deployed agent · live calls', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Create a fresh Platform session', exact: true })).toBeDisabled();
  expect(posts).toEqual([]);
  await page.getByRole('combobox', { name: 'Deployment runtime', exact: true }).selectOption('docker');
  await expect(prepared).not.toContainText('does not match');
  await expect(page.getByText(/live invocation remains unverified on this host/)).toBeVisible();
  expect(posts).toEqual([]);
  await page.getByRole('button', { name: 'Create a fresh Platform session', exact: true }).click();
  await expect(page.getByLabel('Platform session', { exact: true })).toHaveValue('fixture-new-managed-session');
  await page.getByRole('button', { name: 'Invoke deployed agent · live calls', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Fabricated invocation fixture');
  expect(posts.map(item => item.operation)).toEqual(['sessions_create', 'invoke']);
  const reference = posts[0].arguments.story_reference;
  expect(Object.keys(reference).sort()).toEqual(['condition_id', 'episode_id', 'run_id']);
  expect(reference).toMatchObject({ run_id: runId, episode_id: episodeId });
  expect(reference.condition_id).toMatch(/^[a-f0-9-]{36}$/);
  expect(posts[1].arguments).toMatchObject({ story_reference: reference, preferences, input: firstInput, model_route: 'fixed' });
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: /Guided walkthrough/ }).click();
  await expect.poll(() => posts.filter(item => item.operation === 'sessions_close').length).toBe(1);
});

test('missing original structured preferences stay missing and block a prepared invocation', async ({ page }) => {
  const run: any = savedRun({ goal: 'photography', budget_sgd: 50, days: [5] });
  delete run.events[0].preferences; // A summary is not a substitute for the original episode-start constraints.
  const posts = await fixtureApplication(page, run);
  await guidedDeployment(page);
  await expect(page.getByRole('region', { name: 'Prepared managed story' })).toContainText('Original structured preferences were not saved');
  await expect(page.getByRole('button', { name: 'Invoke deployed agent · live calls', exact: true })).toBeDisabled();
  await expect(page.getByRole('button', { name: 'Create a fresh Platform session', exact: true })).toBeDisabled();
  expect(posts).toEqual([]);
});

test('the second inspected conversation supplies the handoff episode and original first public input', async ({ page }) => {
  const secondId = '33333333-3333-4333-8333-333333333333';
  const secondInput = 'The second saved learner asks about Saturday photography.';
  const preferences = { goal: 'photography', budget_sgd: 50, days: [5] };
  const run: any = savedRun(preferences);
  run.episodes.push({ episode_id: secondId, status: 'completed', strategy: 'clarification-first', preferences, source_id: 'fixture-second-profile' });
  run.events.push({ type: 'episode_started', episode_id: secondId, strategy: 'clarification-first', preferences, source_id: 'fixture-second-profile' },
    { type: 'message', episode_id: secondId, role: 'user', content: secondInput });
  const posts = await fixtureApplication(page, run);
  await page.goto('/?run=' + runId);
  await page.getByRole('button', { name: 'Trace sources', exact: true }).click();
  await page.getByLabel('Conversation to trace', { exact: true }).selectOption(secondId);
  await expect(page.getByRole('region', { name: 'Turn 1', exact: true })).toContainText(secondInput);
  await page.getByRole('button', { name: 'Prepare selected story for deployment', exact: true }).click();
  const prepared = page.getByRole('region', { name: 'Prepared managed story', exact: true });
  await expect(prepared).toContainText(secondId);
  await expect(prepared).toContainText('fixture-second-profile');
  await expect(prepared).not.toContainText(firstInput);
  await expect(page.getByLabel('Deployed learner message')).toHaveValue(secondInput);
  expect(posts).toEqual([]);
  await page.getByRole('button', { name: 'Create a fresh Platform session', exact: true }).click();
  await expect(page.getByLabel('Platform session', { exact: true })).toHaveValue('fixture-new-managed-session');
  expect(posts[0].arguments.story_reference.episode_id).toBe(secondId);
  await page.getByRole('navigation', { name: 'Main navigation' }).getByRole('button', { name: /Guided walkthrough/ }).click();
});
