import { expect, test } from '@playwright/test';

test('advisor finds a sourced class through the real worker and MCP server', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Your next chapter starts here.' })).toBeVisible();
  await page.getByRole('button', { name: 'Try a photography class' }).click();
  await page.getByLabel('Budget, before funding').fill('50');
  await page.getByRole('button', { name: 'Send learning goal' }).click();
  await expect(page.locator('.message').last()).toContainText('CC-001');
  await expect(page.getByRole('link', { name: 'View official listing' }).first()).toHaveAttribute('href', /onepa.gov.sg/);
});

test('simulation saves replies and Helix scores them', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /02.*Run a simulation/ }).click();
  await page.getByRole('button', { name: 'Start simulation' }).click();
  await expect(page.getByText('1 of 1 episodes saved')).toBeVisible({ timeout: 30000 });
  await page.getByRole('button', { name: 'Inspect conversation' }).click();
  await expect(page.locator('.message').last()).toContainText('SF-005');
  await page.getByRole('button', { name: 'Evaluate saved replies' }).click();
  await expect(page.getByText('4 of 4 checks passed')).toBeVisible({ timeout: 30000 });
  await page.getByRole('button', { name: 'Trace sources', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Source persona' })).toContainText('no source persona was sampled');
  await expect(page.getByRole('region', { name: 'Course facts SF-005' })).toContainText('Project Management');
  await page.getByText('Saved tool steps (1)', { exact: true }).click();
  await expect(page.locator('.tool-step')).toContainText('search_courses');
});

test('narrow screens remain usable and model-supplied HTML stays inert', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route('**/api/chat', route => route.fulfill({ json: {
    session_id: '00000000-0000-0000-0000-000000000000',
    content: '<img src=x onerror="window.injected=true"><script>window.injected=true</script>**Safe answer**', matches: []
  } }));
  await page.goto('/');
  await page.getByLabel('Your learning goal').fill('photography');
  await page.getByRole('button', { name: 'Send learning goal' }).click();
  await expect(page.getByText('Safe answer')).toBeVisible();
  expect(await page.evaluate(() => (window as typeof window & { injected?: boolean }).injected)).toBeUndefined();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});

test('history filters match the selected mode and traced sources belong to the selected episode', async ({ page }) => {
  const runId = '11111111-1111-4111-8111-111111111111';
  const episodeId = '22222222-2222-4222-8222-222222222222';
  const live = { run_id: runId, status: 'completed', started_at: '2026-11-11T01:00:00Z', calls: 2,
    source_notice: 'Fabricated test inputs', spec: { mode: 'live', engine: 'direct', source: 'hf-profile-only', personas: 1, strategies: ['concise'] },
    episodes: [{ episode_id: episodeId, status: 'completed', strategy: 'concise' }],
    events: [{ type: 'episode_started', episode_id: episodeId, persona_index: 0, strategy: 'concise' },
      { type: 'message', role: 'assistant', episode_id: episodeId, content: 'A live fixture reply' }] };
  const demo = { ...live, run_id: '33333333-3333-4333-8333-333333333333', spec: { ...live.spec, mode: 'demo' } };
  await page.route('**/api/runs*', route => route.fulfill({ json: [live, demo] }));
  await page.route('**/api/run?*', route => route.fulfill({ json: live }));
  await page.route('**/api/trace?*', route => route.fulfill({ json: {
    version: 1, run_id: runId, episode_id: episodeId, mode: 'live', status: 'completed', source_notice: 'Fabricated profile',
    source: { distribution: 'hf-profile-only', revision: 'fixture' }, profile: { age: 30, occupation: 'Fabricated role', career_goals_and_ambitions: 'Learn event coordination' },
    scenario: { theme: { description: 'Explore professional learning' }, strategy: 'concise' }, snapshot: { available: true, integrity_matches: true },
    turns: [{ number: 1, user: 'Find a course', assistant: 'Try SF-005', tools: [{ name: 'search_courses', arguments: { goal: 'coordination' }, result: { matches: [] } }],
      course_references: [{ id: 'SF-005', seen_in_tool_result: false, course: { id: 'SF-005', title: 'Fabricated fixture course', provider: 'Example provider', source_url: 'https://example.org/course', price_min_sgd: null, price_max_sgd: null, extra_cost_sgd: null, cost_note: 'Confirm costs', schedule_note: 'Unknown intake', prerequisite_note: 'Confirm entry requirements', funding_note: 'Unknown eligibility' } }] }], notices: []
  } }));
  await page.goto('/');
  await page.getByLabel('INFERENCE', { exact: true }).selectOption('live');
  await page.getByRole('button', { name: /03.*Review results/ }).click();
  await expect(page.getByLabel('SHOW EXPERIMENTS')).toHaveValue('live');
  await expect(page.locator('[data-run-mode="live"]')).toHaveCount(1);
  await expect(page.locator('[data-run-mode="demo"]')).toHaveCount(0);
  await page.locator(`[data-run-id="${runId}"]`).click();
  await page.getByRole('button', { name: 'Trace sources', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Source persona' })).toContainText('Learn event coordination');
  await expect(page.getByRole('region', { name: 'Application scenario' })).toContainText('Explore professional learning');
  await expect(page.getByRole('region', { name: 'Course facts SF-005' })).toContainText('use in a saved tool result is unconfirmed');
  await page.getByLabel('SHOW EXPERIMENTS').selectOption('demo');
  await expect(page.locator('[data-run-mode="live"]')).toHaveCount(0);
  await expect(page.locator('[data-run-mode="demo"]')).toHaveCount(1);
  await expect(page.getByText('Learn event coordination')).toHaveCount(0);
  await page.getByLabel('SHOW EXPERIMENTS').selectOption('all');
  await expect(page.locator('[data-run-mode]')).toHaveCount(2);
});
