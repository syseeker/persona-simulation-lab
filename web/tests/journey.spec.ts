import {expect, test, type Page} from '@playwright/test';
import {readFileSync, readdirSync} from 'node:fs';
import {resolve} from 'node:path';
import {components, componentTitle, simpleBlocks} from '../src/lib/lessonArchitecture';

type Data = Record<string, any>;
const repo = 'https://github.com/syseeker/persona-simulation-lab';
// These immutable historical fixtures retain their original limitations after
// demo promotion. Synthetic branches below are offline browser test data only.
const demos: Record<string, string> = {
  photography: '7863c607-cb99-4a31-b60c-381bf2099f0e',
  boardgames: '938bdb3f-568e-442e-889f-fed046edf5a0',
  dreamjob: '8542330d-d6df-494e-8509-d81a5841d69e',
};
const lessonTitles = ['Choose a test persona', 'Create a situation', 'Build and connect the agent',
  'Run the application', 'Investigate execution', 'Evaluate behaviour', 'Optimize model routing',
  'Configure behavioural safeguards', 'Deploy with controlled access'];
const read = (path: string) => JSON.parse(readFileSync(resolve('..', path), 'utf8'));
const registry = read('src/learning_lab/capture_registry.json');

function sourceLinks(): Data {
  const result: Data = {};
  const source = readFileSync(resolve('..', 'src/learning_lab/guide_sources.py'), 'utf8');
  for (const match of source.matchAll(/^\s+'([^']+)': \('([^']+)', '([^']*)'\),?$/gm)) {
    const [, id, path, symbol] = match;
    const lines = readFileSync(resolve('..', path), 'utf8').split('\n');
    const line = symbol ? lines.findIndex(text => text.includes(symbol)) + 1 : 1;
    if (line > 0) result[id] = {available: true, path, symbol, line,
      url: `${repo}/blob/offline-source-fixture/${path}#L${line}`};
  }
  return result;
}

function recording(scenario: string): Data {
  const identity = demos[scenario];
  const folder = `recordings/${scenario}/${identity}`;
  const companion = `recordings/guide-context/${scenario}/${identity}`;
  const trace = read(`${folder}/trace.json`), extra: Data = {};
  for (const name of readdirSync(resolve('..', companion)).filter(name => name.endsWith('.json') && name !== 'manifest.json')) {
    extra[name] = read(`${companion}/${name}`);
  }
  for (const name of Object.keys(read(`${folder}/manifest.json`).files)) {
    if (name.endsWith('.json')) extra[name] = read(`${folder}/${name}`);
    else if (name.endsWith('.jsonl')) extra[name] = readFileSync(resolve('..', `${folder}/${name}`), 'utf8')
      .trim().split('\n').filter(Boolean).map(line => JSON.parse(line));
  }
  const artifacts = [
    ...Object.keys(read(`${folder}/manifest.json`).files).map(path => ({path,
      url: `${repo}/blob/offline-recording-fixture/${folder}/${path}`})),
    ...Object.keys(read(`${companion}/manifest.json`).files).map(path => ({path,
      url: `${repo}/blob/offline-companion-fixture/${companion}/${path}`})),
  ];
  return {state: 'recorded', scenario_id: scenario, run_id: identity, trace, context: extra,
    artifacts, sources: sourceLinks()};
}

function metadata(scenario: string): Data {
  const context = recording(scenario), condition = `${scenario}-offline-baseline`;
  return {schema: 'citizen-guide-metadata/v1', scenario_id: scenario, run_id: demos[scenario],
    available: true, inference_calls_for_inspection: 0,
    notice: 'Offline browser fixture: historical captures retain their original limitations.',
    conditions: [{id: condition, purpose: 'baseline', execution_status: context.trace.run.status}],
    rows: registry.requirements.map((requirement: Data) => {
      const applies = requirement.scenario_ids.includes(scenario);
      const filename = requirement.id === 'CAP-FAB-01' ? 'fabric-config.json' : null;
      const artifact = filename && context.artifacts.find((row: Data) => row.path === filename);
      return {...requirement, steps: requirement.lessons, filenames: filename ? [filename] : [],
        status: !applies ? 'not-used' : artifact ? 'exists' : 'unavailable',
        privacy: artifact ? 'projection' : 'unknown', condition_id: condition,
        condition_purpose: 'baseline', execution_status: context.trace.run.status,
        artifacts: artifact ? [{id: `offline-${requirement.id}`, path: artifact.path, url: artifact.url,
          privacy: 'projection', status: 'exists', kind: 'sanitized-configuration-projection', sha256: 'f'.repeat(64)}] : []};
    })};
}

async function stage(page: Page, step: number) {
  const current = Number((await page.getByTestId('step-counter').innerText()).match(/Step (\d+)/)?.[1]);
  const button = current < step ? 'Next →' : '← Back';
  for (let n = 0; n < Math.abs(step - current); n++) await page.getByRole('button', {name: button, exact: true}).click();
  await expect(page.getByTestId('step-counter')).toHaveText(`Step ${step} of 9`);
}

async function noRejectedClutter(page: Page) {
  const panel = page.getByTestId('journey-panel');
  await expect(panel.getByRole('heading', {name: 'Why this matters', exact: true})).toHaveCount(0);
  await expect(panel.getByRole('heading', {name: 'Check your implementation', exact: true})).toHaveCount(0);
  await expect(panel.locator('.operation-path, .concept-path, .component-reference, pre')).toHaveCount(0);
  await expect(panel.getByTestId('record-state')).toHaveCount(0);
  await expect(panel.getByText('All files in this run', {exact: true})).toHaveCount(0);
  await expect(panel).not.toContainText('inspect the matching proof');
  await expect(panel).not.toContainText('Committed code matches the recorded source hash');
}

test.use({viewport: {width: 1800, height: 1100}});
test.beforeEach(async ({page}) => {
  // Block unknown reads and every write before a real worker could receive it.
  await page.route('**/api/**', async route => {
    const request = route.request();
    expect(request.method()).toBe('GET');
    const url = new URL(request.url()), scenario = url.searchParams.get('scenario_id') || 'photography';
    if (url.pathname.endsWith('/lesson')) await route.fulfill({json: recording(scenario)});
    else if (url.pathname.endsWith('/metadata')) await route.fulfill({json: metadata(scenario)});
    else if (url.pathname.endsWith('/demo-persona')) await route.fulfill({json: {
      available: true, name: `${scenario} profile fixture`, source: 'ngc', revision: 'offline-original',
      fields: [{label: 'Age', value: 24}, {label: 'Interests', value: 'Learning'}], traits: [], original_sha256: 'f'.repeat(64),
    }});
    else throw new Error('Recorded guide attempted an unexpected operation: ' + url.pathname);
  });
});

test('all 27 scenario lessons have distinct audience explanations without repeated directories or execution', async ({page}) => {
  const errors: string[] = [], methods: string[] = [], introductions = new Map<string, string>();
  page.on('pageerror', error => errors.push(error.message));
  page.on('request', request => {if (request.url().includes('/api/journey/')) methods.push(request.method());});
  await page.goto('/');
  for (const audience of ['Simplified', 'Detailed']) {
    await page.getByRole('button', {name: audience, exact: true}).click();
    for (const scenario of Object.keys(demos)) {
      const choice = page.getByLabel('Scenario', {exact: true});
      if (await choice.inputValue() !== scenario) await choice.selectOption(scenario);
      for (let step = 1; step <= 9; step++) {
        await expect(page.locator('.step-title')).toHaveText(lessonTitles[step - 1]);
        const introduction = await page.locator('.teaching-introduction').innerText();
        const key = `${scenario}:${step}`;
        if (audience === 'Simplified') introductions.set(key, introduction);
        else expect(introduction).not.toBe(introductions.get(key));
        await noRejectedClutter(page);
        await expect(page.locator('.scenario-setup').getByTestId('record-state')).toContainText(demos[scenario].slice(0, 8));
        const panel = page.getByTestId('journey-panel');
        for (const other of Object.keys(demos).filter(id => id !== scenario)) {
          await expect(panel.locator(`a[href*="recordings/${other}/"], a[href*="recordings/guide-context/${other}/"]`)).toHaveCount(0);
        }
        if (step < 9) await page.getByRole('button', {name: 'Next →', exact: true}).click();
      }
    }
  }
  expect(errors).toEqual([]);
  expect(methods.length).toBeGreaterThan(0);
  expect(methods.every(method => method === 'GET')).toBe(true);
});

for (const scenario of Object.keys(demos)) test(`${scenario}: conceptual blocks and actions keep their own identity`, async ({page}) => {
  await page.goto('/');
  await page.getByLabel('Scenario', {exact: true}).selectOption(scenario);
  await stage(page, 3);
  const blocks = [...simpleBlocks(scenario), ...components.filter(component =>
    ['guardrails', 'openshell', 'platform'].includes(component.id)).map(component => ({
      id: component.id, title: component.simple, rows: component.operations,
    }))];
  for (const block of blocks) {
    await page.getByRole('button', {name: `Inspect ${block.title}`, exact: true}).click();
    await expect(page.locator('.step-title')).toHaveText(block.title);
    const introduction = await page.locator('.teaching-introduction').innerText();
    await expect(page.getByTestId('scenario-facts')).toHaveCount(0);
    for (const row of block.rows) {
      await page.getByRole('button', {name: `Explain ${block.title}: ${row.title}`, exact: true}).click();
      await expect(page.locator('.step-title')).toHaveText(row.title);
      expect(await page.locator('.teaching-introduction').innerText()).not.toBe(introduction);
      await expect(page.getByTestId('step-counter')).toHaveText('Step 3 of 9');
      await expect(page.getByTestId('scenario-facts')).toHaveCount(0);
      await noRejectedClutter(page);
    }
  }
});

for (const scenario of Object.keys(demos)) test(`${scenario}: technical library and operation selections match clicked titles`, async ({page}) => {
  await page.goto('/');
  await page.getByLabel('Scenario', {exact: true}).selectOption(scenario);
  await stage(page, 3);
  await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  for (const component of components) {
    const title = componentTitle(component.id, scenario);
    await page.getByRole('button', {name: `Inspect ${title}`, exact: true}).click();
    await expect(page.locator('.step-title')).toHaveText(title);
    const introduction = await page.locator('.teaching-introduction').innerText();
    for (const operation of component.operations) {
      await page.getByRole('button', {name: `Explain ${title}: ${operation.title}`, exact: true}).click();
      await expect(page.locator('.step-title')).toHaveText(operation.title);
      expect(await page.locator('.teaching-introduction').innerText()).not.toBe(introduction);
      await expect(page.getByTestId('step-counter')).toHaveText('Step 3 of 9');
      await expect(page.getByTestId('scenario-facts')).toHaveCount(0);
      await noRejectedClutter(page);
    }
  }
});

test('scenario summary owns recording state while the collapsed selector remains visible', async ({page}) => {
  await page.goto('/');
  await expect(page.getByTestId('selected-persona')).toContainText('photography profile fixture');
  await expect(page.locator('.scenario-setup').getByTestId('record-state')).toHaveCount(1);
  await stage(page, 2);
  await expect(page.getByTestId('scenario-facts')).toContainText('Supplied by this scenario');
  await expect(page.getByTestId('journey-panel').locator('.conversation-message')).toHaveCount(0);
  await expect(page.getByTestId('journey-panel')).not.toContainText('USERSIM WORDING · SAVED OPENING');
  await page.getByLabel('Toggle scenario summary', {exact: true}).click();
  await expect(page.getByLabel('Scenario', {exact: true})).toBeVisible();
  await expect(page.getByLabel('Scenario', {exact: true})).toHaveCount(1);
  await page.getByLabel('Scenario', {exact: true}).selectOption('boardgames');
  await expect(page.getByTestId('step-counter')).toHaveText('Step 1 of 9');
  await expect(page.getByTestId('selected-persona')).toContainText('boardgames profile fixture');
});

test('Fabric links precise calling code and real configuration without repeating architecture links', async ({page}) => {
  await page.goto('/'); await stage(page, 3);
  await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  const panel = page.getByTestId('journey-panel');
  await expect(panel.getByRole('link', {name: 'build_config ↗', exact: true})).toHaveAttribute('href', /\/src\/learning_lab\/fabric_target.py#L\d+$/);
  await expect(panel.getByRole('link', {name: 'The captured typed settings ↗', exact: true})).toHaveAttribute('href',
    `${repo}/blob/offline-recording-fixture/recordings/photography/${demos.photography}/fabric-config.json`);
  await expect(panel).toContainText('Neither public file is loaded as runtime input');
  await expect(panel.locator('a[href*="docs.nvidia.com/nemo/fabric"]')).toHaveCount(0);
  await page.getByRole('button', {name: 'Inspect NeMo Fabric', exact: true}).click();
  await expect(panel.locator('a[href*="docs.nvidia.com/nemo/fabric"]')).toHaveCount(1);
});

test('selected public turns show one native result or an application-only clarification', async ({page}) => {
  const fixture = recording('dreamjob');
  fixture.context['fabric-invocations.json'] = [
    {public_turn: 1, invocation_sequence: 1, runtime_status: 'succeeded', outcome: {status: 'valid'},
      output: {native_response_published: true}, tool_scope_uuids: []},
    {public_turn: 3, invocation_sequence: 2, runtime_status: 'succeeded', outcome: {status: 'valid'},
      output: {native_response_published: false}, tool_scope_uuids: []},
  ];
  fixture.context['application-turns.json'] = [{public_turn: 2, execution_kind: 'application_clarification',
    agent_invoked: false, inference_calls: 0, missing_constraints: ['budget_sgd', 'days']}];
  await page.route('**/api/journey/lesson?scenario_id=dreamjob', route => route.fulfill({json: fixture}));
  await page.goto('/'); await page.getByLabel('Scenario', {exact: true}).selectOption('dreamjob');
  await stage(page, 4); await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await page.getByRole('button', {name: 'Follow this step on the map →', exact: true}).click();
  const facts = page.getByTestId('scenario-facts');
  await expect(facts.getByText("This turn's Fabric result", {exact: true})).toHaveCount(1);
  await expect(facts).toContainText('The normalized response supplied the public reply above');
  await page.getByRole('button', {name: 'Turn 2', exact: true}).click();
  await expect(facts.getByText("This turn's Fabric result", {exact: true})).toHaveCount(0);
  await expect(facts).toContainText('Advisor model calls: 0');
  await expect(facts).toContainText('There is no Fabric invocation or new course lookup');
  await expect(facts).toContainText('training budget not stated');
  await expect(page.getByRole('note')).toContainText('No advisor model, Fabric invocation or course-tool call');
  for (const id of ['fabric', 'harness', 'mcp', 'relay']) {
    await expect(page.locator(`[data-component="${id}"]`)).toHaveAttribute('data-active', 'false');
  }
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Invoke with a RunRequest', exact: true}).click();
  await expect(page.getByRole('region', {name: 'Observed operation result'})).toContainText('No RunRequest was submitted');
  await page.getByRole('button', {name: /Back to step 4/}).click();
  await page.getByRole('button', {name: 'Turn 3', exact: true}).click();
  await expect(page.getByRole('note')).toHaveCount(0);
  await expect(facts.getByText("This turn's Fabric result", {exact: true})).toHaveCount(1);
  await expect(facts).toContainText('native proposal was preserved separately');
  await expect(facts).toContainText('training budget S$3000');
});

test('tool interpretation distinguishes empty search, error, details and comparison', async ({page}) => {
  const fixture = recording('boardgames');
  fixture.context['fabric-invocations.json'] = [{public_turn: 1, tool_scope_uuids: ['empty', 'error', 'detail', 'compare']}];
  fixture.trace.tools = [
    {name: 'search_courses', status: 'completed', scope_uuid: 'empty', arguments: {}, result: {matches: []}},
    {name: 'search_courses', status: 'completed', scope_uuid: 'error', arguments: {}, result: {error: 'Invalid study day', matches: []}},
    {name: 'get_course_details', status: 'completed', scope_uuid: 'detail', arguments: {}, result: {id: 'SF-001', title: 'Details fixture course', price_max_sgd: null}},
    {name: 'compare_courses', status: 'completed', scope_uuid: 'compare', arguments: {}, result: [
      {id: 'SF-001', title: 'Comparison fixture one', price_max_sgd: 100},
      {id: 'SF-002', title: 'Comparison fixture two', price_max_sgd: 200},
    ]},
  ];
  await page.route('**/api/journey/lesson?scenario_id=boardgames', route => route.fulfill({json: fixture}));
  await page.goto('/'); await page.getByLabel('Scenario', {exact: true}).selectOption('boardgames');
  await stage(page, 5);
  const facts = page.getByTestId('scenario-facts');
  await expect(facts).toContainText('completed successfully and found no matching catalogue entry');
  await expect(facts).toContainText('domain error: Invalid study day');
  await expect(facts).toContainText('Details fixture course · full fee unknown');
  await expect(facts).toContainText('Comparison fixture one');
  await expect(facts).toContainText('Comparison fixture two');
  fixture.context['fabric-invocations.json'] = [];
  await page.reload();
  await expect(facts).toContainText('no verified turn-to-invocation association');
  await expect(facts.locator('.tool-fact')).toHaveCount(0);
});

test('photography investigation explains recorded cost uncertainty and reveals exclusion reasons in Detailed', async ({page}) => {
  const fixture = recording('photography');
  // Preserve the actual historical native search result. This explicit turn
  // association is an offline presentation fixture, not fresh runtime proof.
  fixture.context['fabric-invocations.json'] = [{public_turn: 1,
    tool_scope_uuids: fixture.trace.tools.map((tool: Data) => tool.scope_uuid)}];
  await page.route('**/api/journey/lesson?scenario_id=photography', route => route.fulfill({json: fixture}));
  await page.goto('/'); await stage(page, 5);
  const facts = page.getByTestId('scenario-facts');
  await expect(facts).toContainText('Additional costs are unconfirmed');
  await expect(facts).toContainText('Other checkout costs are unconfirmed');
  await expect(facts).toContainText('5 other listings were excluded by the search constraints');
  await expect(facts).not.toContainText('Published class days conflict with availability');
  await expect(facts).not.toContainText('Search terms matched:');
  await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await expect(facts).toContainText('Additional costs are unconfirmed');
  await expect(facts).toContainText('Search terms matched: photo; photography; smartphone');
  await expect(facts).toContainText('CC-002: Published class days conflict with availability');
  await expect(facts).toContainText('CC-003: Published upper fee including known extras exceeds the budget');
});

test('overview, audience change and layout reset clear focus while retaining the lesson', async ({page}) => {
  await page.goto('/'); await expect(page.locator('.component-node.dim')).toHaveCount(0);
  await page.getByRole('button', {name: 'Follow this step on the map →', exact: true}).click();
  await expect(page.locator('.component-node.active')).toHaveCount(1);
  await expect(page.locator('[data-component="person"]')).toHaveAttribute('data-active', 'true');
  await expect(page.locator('[data-component="learner"]')).toHaveAttribute('data-active', 'false');
  await stage(page, 3);
  await page.getByRole('button', {name: 'Explain Citizen advisor: Connect the selected agent', exact: true}).click();
  await expect(page.locator('.step-title')).toHaveText('Connect the selected agent');
  await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await expect(page.locator('.step-title')).toHaveText('Build and connect the agent');
  await expect(page.locator('.component-node.dim')).toHaveCount(0);
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  await page.getByRole('button', {name: 'Reset layout', exact: true}).click();
  await expect(page.locator('.step-title')).toHaveText('Build and connect the agent');
  await expect(page.locator('.component-node.dim')).toHaveCount(0);
  await page.getByRole('button', {name: /2\s+Integration Map/}).click();
  await expect(page.locator('.component-node.dim')).toHaveCount(0);
});

test('semantic selection reloads but a foreign persisted action returns to its lesson', async ({page}) => {
  await page.goto('/'); await stage(page, 3);
  await page.getByRole('button', {name: 'Explain Citizen advisor: Connect the selected agent', exact: true}).click();
  await page.reload();
  await expect(page.locator('.step-title')).toHaveText('Connect the selected agent');
  await expect(page.getByTestId('step-counter')).toHaveText('Step 3 of 9');
  await page.evaluate(() => {
    const key = 'persona-lab-guide-wireframe:selection:v4';
    const saved = JSON.parse(localStorage.getItem(key)!);
    localStorage.setItem(key, JSON.stringify({...saved, selected: 'advisor', operationId: 'fabric.config'}));
  });
  await page.reload();
  await expect(page.locator('.step-title')).toHaveText('Build and connect the agent');
});

test('saved geometry, inspector resizing and reduced motion remain functional', async ({page}) => {
  await page.emulateMedia({reducedMotion: 'reduce'}); await page.goto('/');
  const node = page.locator('.svelte-flow__node[data-id="person"]');
  const box = await node.locator('header').boundingBox(); expect(box).not.toBeNull();
  await page.mouse.move(box!.x + 30, box!.y + 15); await page.mouse.down();
  await page.mouse.move(box!.x + 70, box!.y + 45, {steps: 8}); await page.mouse.up();
  const transform = await node.getAttribute('style');
  await page.getByRole('button', {name: 'Save layout', exact: true}).click();
  const divider = page.getByRole('separator'); await divider.focus(); await page.keyboard.press('ArrowLeft');
  const width = await divider.getAttribute('aria-valuenow');
  await page.reload(); await expect(node).toHaveAttribute('style', transform!);
  await expect(divider).toHaveAttribute('aria-valuenow', width!);
  await page.getByRole('button', {name: 'Follow this step on the map →', exact: true}).click();
  await stage(page, 2);
  const animations = await page.locator('.integration-edge.is-active .svelte-flow__edge-path')
    .evaluateAll(paths => paths.map(path => getComputedStyle(path).animationName));
  expect(animations.length).toBeGreaterThan(0);
  expect(animations.every(animation => animation === 'none')).toBe(true);
});

test('playback advances nine lessons using only recorded GET requests', async ({page}) => {
  const methods: string[] = [];
  page.on('request', request => {if (request.url().includes('/api/journey/')) methods.push(request.method());});
  await page.goto('/'); await page.clock.install();
  await page.getByRole('button', {name: 'Play', exact: true}).click();
  for (let step = 2; step <= 9; step++) {
    await page.clock.fastForward(4300);
    await expect(page.getByTestId('step-counter')).toHaveText(`Step ${step} of 9`);
  }
  await page.clock.fastForward(4300);
  await expect(page.getByRole('button', {name: 'Play', exact: true})).toHaveAttribute('aria-pressed', 'false');
  expect(methods.every(method => method === 'GET')).toBe(true);
});

test('missing originals or captures stay unavailable without substitute configuration links', async ({page}) => {
  await page.route('**/api/journey/lesson?**', route => route.fulfill({json: {state: 'unavailable', scenario_id: 'photography',
    trace: null, context: {}, artifacts: [], sources: {}, notice: 'The tagged demo is unavailable. No substitute.'}}));
  await page.route('**/api/journey/demo-persona?**', route => route.fulfill({json: {available: false,
    notice: 'No original matches this revision and hash. No substitute profile.'}}));
  await page.route('**/api/journey/metadata?**', route => route.fulfill({json: {...metadata('photography'), rows: []}}));
  await page.goto('/');
  await expect(page.getByTestId('scenario-facts')).toContainText('No original matches');
  await expect(page.getByTestId('selected-persona')).toHaveCount(0);
  await expect(page.getByTestId('journey-panel').locator('a[href*="recordings/"]')).toHaveCount(0);
  await stage(page, 3); await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  await expect(page.getByTestId('journey-panel').locator('.unavailable-reference')
    .filter({hasText: 'The captured typed settings'})).toHaveAttribute('title', /No matching public capture is available/);
  await expect(page.getByTestId('journey-panel').locator('a[href*="fabric_target.py"]')).toHaveCount(0);
});

test('project introduction and journey retain requested copy and a responsive chart', async ({page}) => {
  await page.goto('/'); await page.getByRole('button', {name: /1\s+Why NeMo Stack/}).click();
  await expect(page.locator('.application-story')).not.toContainText('Learning is the goal');
  await expect(page.locator('.header-note')).toHaveCount(0);
  await expect(page.getByText('Every lesson must answer:', {exact: true})).toHaveCount(1);
  await expect(page.getByText('What are we trying to achieve → which components cooperate → what does the application call → what configuration is used → what comes back → where is the proof?', {exact: true})).toHaveCount(1);
  const situationCard = page.locator('.lesson-card').filter({has: page.getByRole('heading', {name: 'Create a situation', exact: true})});
  await expect(situationCard.getByRole('link', {name: 'UserSim documentation ↗', exact: true})).toHaveCount(1);
  for (const width of [1800, 1000, 390]) {
    await page.setViewportSize({width, height: 1000});
    const chart = page.locator('.journey-chart'); await expect(chart.getByRole('button')).toHaveCount(9);
    expect(await chart.evaluate(element => element.scrollWidth <= element.clientWidth + 1)).toBe(true);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1)).toBe(true);
  }
});

test('switching scenarios keeps live ownership separate and starts or cancels no workload', async ({page}) => {
  const live = '11111111-1111-4111-8111-111111111111', methods: string[] = [];
  page.on('request', request => {if (request.url().includes('/api/')) methods.push(request.method());});
  await page.addInitScript(({live}) => localStorage.setItem('persona-lab-guide-wireframe:selection:v4',
    JSON.stringify({version: 5, page: 'map', scenarioId: 'photography', liveRuns: {photography: live}})), {live});
  await page.route('**/api/journey/readiness*', route => route.fulfill({json: {ready: false,
    native: {gateway: true, image: true}, proxy: {fixed_alias_available: true, support_alias_available: true}, active: {run_id: live}}}));
  await page.route('**/api/journey/trace*', route => route.fulfill({json: {
    run: {run_id: live, scenario_id: 'photography', status: 'running', stage: 'run', calls: 3, cleanup_confirmed: false},
    conversation: [{role: 'user', content: 'Public photography live fixture'}],
  }}));
  await page.goto('/');
  await page.getByRole('button', {name: 'Simulate a Session', exact: true}).click();
  await expect(page.getByTestId('live-session')).toContainText('Public photography live fixture');
  await page.getByLabel('Scenario', {exact: true}).selectOption('boardgames');
  await page.getByRole('button', {name: 'Simulate a Session', exact: true}).click();
  await expect(page.getByTestId('live-session')).not.toContainText('Public photography live fixture');
  await expect(page.getByTestId('live-session')).toContainText('NEW BOARD-GAMES CONDITION');
  await page.getByLabel('Scenario', {exact: true}).selectOption('photography');
  await page.getByRole('button', {name: 'Simulate a Session', exact: true}).click();
  await expect(page.getByTestId('live-session')).toContainText('Public photography live fixture');
  expect(methods.every(method => method === 'GET')).toBe(true);
});

test('dataset schemas, filtering, paging and original-field inspection remain read-only', async ({page}) => {
  const requests: URL[] = [];
  const dataset = {source: 'hf-profile-only', name: 'Offline HF fixture', revision: 'offline-r1', row_count: 21,
    ready: true, columns: [], ocean_fields: [], source_url: 'https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore'};
  await page.route('**/api/local-datasets', route => route.fulfill({json: {datasets: [dataset,
    {...dataset, source: 'ngc', name: 'Offline NGC fixture', ready: false, reason: 'Fixture NGC source not installed', ocean_fields: ['openness']}]}}));
  await page.route('**/api/persona-options?**', route => route.fulfill({json: {source: 'hf-profile-only',
    source_revision: 'offline-r1', geography_field: 'planning_area', row_count: 21,
    fields: {planning_area: [{value: 'Tampines', count: 21}], education_level: [{value: 'Diploma', count: 21}]}, inference_calls: 0}}));
  await page.route('**/api/personas?**', route => {
    expect(route.request().method()).toBe('GET');
    const url = new URL(route.request().url()); requests.push(url);
    const offset = Number(url.searchParams.get('offset') || 0);
    return route.fulfill({json: {dataset, offset, limit: 10, total: 21, has_more: offset < 20, inference_calls: 0,
      records: [{source_id: `offline-row-${offset + 1}`, source: 'hf-profile-only', source_revision: 'offline-r1',
        original_profile_sha256: 'f'.repeat(64), kind: 'original', profile: {age: 24, planning_area: 'Tampines',
          occupation: 'Offline retail fixture', education_level: 'Diploma', hobbies_and_interests: `Photography fixture ${offset + 1}`}}]}});
  });
  await page.goto('/'); await page.getByRole('button', {name: /4\s+Datasets/}).click();
  await expect(page.getByTestId('dataset-snapshot')).toHaveCount(2);
  await page.getByLabel('Search schema fields', {exact: true}).fill('openness');
  await expect(page.getByTestId('dataset-schema').locator('tr[data-field]')).toHaveCount(1);
  await expect(page.getByTestId('dataset-schema')).toContainText('NGC only');
  await page.getByRole('tab', {name: 'Explore profiles', exact: true}).click();
  await expect(page.getByTestId('profile-snapshot')).toContainText('Photography fixture 1');
  await page.getByLabel('Search profile text', {exact: true}).fill('photography');
  await page.getByLabel('Minimum age', {exact: true}).fill('20');
  await page.getByLabel('Planning area', {exact: true}).selectOption('Tampines');
  await page.getByRole('button', {name: 'Apply filters', exact: true}).click();
  await expect(page.getByTestId('profile-snapshot')).toContainText('Photography fixture 1');
  await page.getByRole('button', {name: 'Next page →', exact: true}).click();
  await expect(page.getByTestId('profile-snapshot')).toContainText('Photography fixture 11');
  await page.getByRole('button', {name: 'Inspect profile 11', exact: true}).click();
  await expect(page.getByRole('complementary', {name: 'Original profile details'})).toContainText('Photography fixture 11');
  expect(requests.at(-1)?.searchParams.get('search')).toBe('photography');
  expect(requests.at(-1)?.searchParams.get('age_min')).toBe('20');
  expect(requests.at(-1)?.searchParams.get('planning_area')).toBe('Tampines');
  expect(requests.at(-1)?.searchParams.get('offset')).toBe('10');
  await page.getByRole('button', {name: /NGC Extended/}).click();
  await expect(page.getByRole('alert')).toContainText('Fixture NGC source not installed');
  await expect(page.getByTestId('profile-snapshot')).toHaveCount(0);
});

test('Metadata distinguishes settings projections, private originals and missing captures', async ({page}) => {
  const inventory = metadata('photography');
  const base = inventory.rows.find((row: Data) => row.id === 'CAP-FAB-01');
  const record = recording('photography');
  const paths = ['fabric-plan.json', 'fabric-doctor.json'];
  const artifacts = paths.map((path, index) => ({id: `offline-report-${index}`, path,
    url: record.artifacts.find((artifact: Data) => artifact.path === path).url,
    privacy: 'public', status: 'exists', kind: 'native-response', sha256: 'f'.repeat(64)}));
  inventory.rows = [base,
    {...base, id: 'CAP-FAB-03', module: 'Fabric preparation', filenames: paths, privacy: 'public', artifacts},
    {...base, id: 'CAP-US-01', module: 'Resolved simulator inputs', filenames: ['resolved-inputs.json'], privacy: 'private',
      artifacts: [{id: 'opaque-private-original', privacy: 'private', status: 'exists', kind: 'native-input', sha256: 'f'.repeat(64)}]},
    {...base, id: 'CAP-US-04', module: 'Missing output', filenames: ['usersim-result.json'], status: 'missing', privacy: 'unknown', artifacts: []},
    {...base, id: 'CAP-DD-01', module: 'Unused Designer', filenames: [], status: 'not-used', privacy: 'unknown', artifacts: []},
  ];
  await page.route('**/api/journey/metadata?scenario_id=photography', route => route.fulfill({json: inventory}));
  await page.goto('/'); await stage(page, 3);
  await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await page.getByTestId('journey-panel').getByRole('button', {name: 'their reports ↗', exact: true}).click();
  await expect(page.getByRole('heading', {name: 'Metadata', exact: true})).toBeVisible();
  await expect(page.locator('tr[data-requirement]')).toHaveCount(1);
  await expect(page.locator('tr[data-requirement="CAP-FAB-03"]')).toContainText('Fabric preparation');
  const headings = await page.locator('.metadata-page thead th').allTextContents();
  expect(headings).toEqual(['Module', 'Steps', 'YAML / JSON file', 'Status', 'Location', 'Apply to scenario']);
  await page.getByRole('button', {name: 'Show all modules', exact: true}).click();
  await expect(page.locator('tr[data-requirement="CAP-FAB-01"]')).toContainText('PARTIAL');
  const privateRow = page.locator('tr[data-requirement="CAP-US-01"]');
  await expect(privateRow).toContainText('PRIVATE');
  await expect(privateRow).toContainText('No public link');
  await expect(privateRow.locator('a')).toHaveCount(0);
  await expect(page.locator('tr[data-requirement="CAP-US-04"]')).toContainText('NOT EXIST');
  await expect(page.locator('tr[data-requirement="CAP-DD-01"]')).toContainText('NOT USED');
  await expect(page.locator('.metadata-page a[href^="/home/"], .metadata-page a[href^="file:"]')).toHaveCount(0);
  const search = page.getByRole('searchbox', {name: 'Find a module, file or status', exact: true});
  await search.fill('PRIVATE');
  await expect(page.locator('tr[data-requirement]')).toHaveCount(1);
  await expect(page.locator('tr[data-requirement="CAP-US-01"]')).toBeVisible();
  await search.fill('NOT USED');
  await expect(page.locator('tr[data-requirement]')).toHaveCount(1);
  await expect(page.locator('tr[data-requirement="CAP-DD-01"]')).toBeVisible();
  await search.fill('PUBLIC');
  await expect(page.locator('tr[data-requirement]')).toHaveCount(1);
  await expect(page.locator('tr[data-requirement="CAP-FAB-03"]')).toBeVisible();
  await search.fill('');
  await expect(page.locator('tr[data-requirement]')).toHaveCount(5);
});

test('routing condition references follow the displayed condition and never borrow baseline proof', async ({page}) => {
  const fixture = recording('dreamjob'), inventory = metadata('dreamjob');
  const fixed = 'offline-fixed-comparison', missing = 'offline-missing-comparison';
  fixture.context['routing-comparison.json'] = {conditions: [
    {condition_id: fixed, label: 'Fixed fixture', purpose: 'Offline fixed comparison', status: 'failed',
      cleanup_confirmed: true, calls: 0, usage: [], native_decisions: []},
    {condition_id: missing, label: 'Missing fixture', purpose: 'Offline condition without a captured config', status: 'failed',
      cleanup_confirmed: true, calls: 0, usage: [], native_decisions: []},
  ]};
  const baseline = inventory.rows.find((row: Data) => row.id === 'CAP-FAB-01');
  const comparisonURL = `${repo}/blob/offline-condition-fixture/recordings/dreamjob/${demos.dreamjob}/fixed-typed-settings.json`;
  const aggregateURL = `${repo}/blob/offline-run-fixture/recordings/dreamjob/${demos.dreamjob}/routing-comparison.json`;
  const policyURL = `${repo}/blob/offline-run-fixture/recordings/dreamjob/${demos.dreamjob}/routing-configuration.json`;
  inventory.rows = inventory.rows.map((row: Data) => ['CAP-SW-01', 'CAP-SW-02'].includes(row.id) ? {...row,
    artifacts: [{...baseline.artifacts[0], url: row.id === 'CAP-SW-01' ? policyURL : aggregateURL,
      path: row.id === 'CAP-SW-01' ? 'routing-configuration.json' : 'routing-comparison.json'}]} : row);
  inventory.conditions.push({id: fixed, purpose: 'fixed-candidate', execution_status: 'failed'},
    {id: missing, purpose: 'switchyard', execution_status: 'failed'});
  inventory.rows.push({...baseline, condition_id: fixed, condition_purpose: 'fixed-candidate',
    artifacts: [{...baseline.artifacts[0], url: comparisonURL, path: 'fixed-typed-settings.json'}]});
  await page.route('**/api/journey/lesson?scenario_id=dreamjob', route => route.fulfill({json: fixture}));
  await page.route('**/api/journey/metadata?scenario_id=dreamjob', route => route.fulfill({json: inventory}));
  await page.goto('/'); await page.getByLabel('Scenario', {exact: true}).selectOption('dreamjob');
  await stage(page, 7); await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await expect(page.getByLabel('Routing comparison condition', {exact: true})).toHaveValue(fixed);
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'the comparison record ↗', exact: true})).toHaveAttribute('href', aggregateURL);
  await page.getByRole('button', {name: 'Explain NeMo Switchyard: Load candidates and routing policy', exact: true}).click();
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'The recorded routing configuration ↗', exact: true})).toHaveAttribute('href', policyURL);
  await page.getByRole('button', {name: /Back to step 7/}).click();
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'The captured typed settings ↗', exact: true})).toHaveAttribute('href', comparisonURL);
  await expect(page.getByTestId('journey-panel').locator('a[href*="framework-config.json"]')).toHaveCount(0);
  await page.getByRole('button', {name: /Back to step 7/}).click();
  await page.getByLabel('Routing comparison condition', {exact: true}).selectOption(missing);
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'the comparison record ↗', exact: true})).toHaveAttribute('href', aggregateURL);
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'The captured typed settings ↗', exact: true})).toHaveCount(0);
  await expect(page.getByTestId('journey-panel').locator('.unavailable-reference').filter({hasText: 'The captured typed settings'})).toHaveAttribute('title', /No matching public capture/);
  await page.getByRole('button', {name: 'Next →', exact: true}).click();
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'The captured typed settings ↗', exact: true})).toHaveAttribute('href', baseline.artifacts[0].url);
});

test('named setup references resolve one projected file without accepting similar opaque prefixes', async ({page}) => {
  const fixture = recording('boardgames');
  fixture.artifacts = fixture.artifacts.filter((artifact: Data) => artifact.path !== 'usersim-setup.json');
  const projected = `${'a'.repeat(24)}-usersim-setup.projection.json`;
  const projectedURL = `${repo}/blob/offline-projection-fixture/recordings/boardgames/${demos.boardgames}/${projected}`;
  fixture.artifacts.push({path: `captures/${projected}`, url: projectedURL},
    {path: `captures/${'a'.repeat(23)}-usersim-setup.projection.json`, url: 'https://example.invalid/wrong-prefix.json'},
    {path: `captures/${'a'.repeat(24)}-other-usersim-setup.projection.json`, url: 'https://example.invalid/wrong-name.json'});
  await page.route('**/api/journey/lesson?scenario_id=boardgames', route => route.fulfill({json: fixture}));
  await page.goto('/'); await page.getByLabel('Scenario', {exact: true}).selectOption('boardgames');
  await stage(page, 2); await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await page.getByRole('button', {name: 'Explain NeMo UserSim: Apply the custom learning-advisor hooks', exact: true}).click();
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'The saved simulator setup ↗', exact: true})).toHaveAttribute('href', projectedURL);
  await expect(page.getByTestId('journey-panel').locator('a[href*="example.invalid"]')).toHaveCount(0);
});

test('autoplay clears comparison scope before teaching the next lesson', async ({page}) => {
  const fixture = recording('dreamjob'), inventory = metadata('dreamjob');
  const condition = 'offline-comparison-before-playback';
  fixture.context['routing-comparison.json'] = {conditions: [{condition_id: condition,
    label: 'Offline comparison', purpose: 'Synthetic browser scope test', status: 'failed',
    cleanup_confirmed: true, calls: 0, usage: [], native_decisions: []}]};
  inventory.conditions.push({id: condition, purpose: 'switchyard', execution_status: 'failed'});
  const baseline = inventory.rows.find((row: Data) => row.id === 'CAP-FAB-01');
  await page.route('**/api/journey/lesson?scenario_id=dreamjob', route => route.fulfill({json: fixture}));
  await page.route('**/api/journey/metadata?scenario_id=dreamjob', route => route.fulfill({json: inventory}));
  await page.goto('/'); await page.getByLabel('Scenario', {exact: true}).selectOption('dreamjob');
  await stage(page, 7); await page.getByRole('button', {name: 'Detailed', exact: true}).click();
  await expect(page.getByLabel('Routing comparison condition', {exact: true})).toHaveValue(condition);
  await page.clock.install(); await page.getByRole('button', {name: 'Play', exact: true}).click();
  await page.clock.fastForward(4300);
  await expect(page.getByTestId('step-counter')).toHaveText('Step 8 of 9');
  await page.getByRole('button', {name: 'Explain NeMo Fabric: Build the typed FabricConfig', exact: true}).click();
  await expect(page.getByTestId('journey-panel').getByRole('link', {name: 'The captured typed settings ↗', exact: true})).toHaveAttribute('href', baseline.artifacts[0].url);
});

function savedComparisonFixture() {
  const fixture=recording('dreamjob'),inventory=metadata('dreamjob');
  const conditions=['offline-first-comparison','offline-second-comparison'];
  fixture.context['routing-comparison.json']={conditions:conditions.map((id,index)=>({condition_id:id,
    label:`Offline comparison ${index+1}`,purpose:'Saved comparison selection test',status:'failed',
    cleanup_confirmed:true,calls:0,usage:[],native_decisions:[]}))};
  const baseline=inventory.rows.find((row:Data)=>row.id==='CAP-FAB-01');
  for(const condition of conditions){
    inventory.conditions.push({id:condition,purpose:'fixed-candidate',execution_status:'failed'});
    inventory.rows.push({...baseline,condition_id:condition,condition_purpose:'fixed-candidate',artifacts:[{
      ...baseline.artifacts[0],path:`${condition}-fabric-config.json`,
      url:`${repo}/blob/offline-saved-selection/recordings/dreamjob/${demos.dreamjob}/${condition}-fabric-config.json`,
    }]});
  }
  return {fixture,inventory,conditions,baseline};
}

test('saved retail comparison restores its run-bound proof and semantic destination after reload',async({page})=>{
  const {fixture,inventory,conditions}=savedComparisonFixture(),methods:string[]=[];
  page.on('request',request=>{if(request.url().includes('/api/journey/'))methods.push(request.method());});
  await page.route('**/api/journey/lesson?scenario_id=dreamjob',route=>route.fulfill({json:fixture}));
  await page.route('**/api/journey/metadata?scenario_id=dreamjob',route=>route.fulfill({json:inventory}));
  await page.goto('/');await page.getByLabel('Scenario',{exact:true}).selectOption('dreamjob');
  await stage(page,4);await page.getByRole('button',{name:'Turn 3',exact:true}).click();
  await stage(page,7);await page.getByRole('button',{name:'Detailed',exact:true}).click();
  await page.getByLabel('Routing comparison condition',{exact:true}).selectOption(conditions[1]);
  await page.getByRole('button',{name:'Explain NeMo Fabric: Build the typed FabricConfig',exact:true}).click();
  await expect.poll(()=>page.evaluate(()=>JSON.parse(localStorage.getItem('persona-lab-guide-wireframe:selection:v4')!)))
    .toMatchObject({version:6,scenarioId:'dreamjob',stageId:'routing',turnIndex:2,selected:'fabric',operationId:'fabric.config',conditionId:conditions[1],conditionRunId:demos.dreamjob});
  await page.reload();
  await expect(page.locator('.step-title')).toHaveText('Build the typed FabricConfig');
  await expect(page.getByTestId('step-counter')).toHaveText('Step 7 of 9');
  await expect(page.getByTestId('journey-panel').getByRole('link',{name:'The captured typed settings ↗',exact:true}))
    .toHaveAttribute('href',new RegExp(`${conditions[1]}-fabric-config\\.json$`));
  await page.getByRole('button',{name:/Back to step 7/}).click();
  await expect(page.getByLabel('Routing comparison condition',{exact:true})).toHaveValue(conditions[1]);
  await page.getByLabel('Scenario',{exact:true}).selectOption('boardgames');
  await expect.poll(()=>page.evaluate(()=>JSON.parse(localStorage.getItem('persona-lab-guide-wireframe:selection:v4')!)))
    .toMatchObject({scenarioId:'boardgames',conditionId:'',conditionRunId:''});
  await page.getByLabel('Scenario',{exact:true}).selectOption('dreamjob');await stage(page,7);
  await expect(page.getByLabel('Routing comparison condition',{exact:true})).toHaveValue(conditions[0]);
  await expect.poll(()=>page.evaluate(()=>JSON.parse(localStorage.getItem('persona-lab-guide-wireframe:selection:v4')!)))
    .toMatchObject({scenarioId:'dreamjob',conditionId:conditions[0],conditionRunId:demos.dreamjob});
  expect(methods.length).toBeGreaterThan(0);expect(methods.every(method=>method==='GET')).toBe(true);
});

for(const invalid of ['foreign-condition','previous-run'])test(`saved comparison rejects ${invalid} after the selected recording loads`,async({page})=>{
  const {fixture,inventory,conditions,baseline}=savedComparisonFixture();
  await page.route('**/api/journey/lesson?scenario_id=dreamjob',route=>route.fulfill({json:fixture}));
  await page.route('**/api/journey/metadata?scenario_id=dreamjob',route=>route.fulfill({json:inventory}));
  await page.addInitScript(({condition,run})=>localStorage.setItem('persona-lab-guide-wireframe:selection:v4',JSON.stringify({
    version:6,page:'map',scenarioId:'dreamjob',stageId:'routing',detailed:true,focused:true,
    selected:'fabric',operationId:'fabric.config',turnIndex:2,conditionId:condition,conditionRunId:run,
  })),{condition:invalid==='foreign-condition'?'foreign-recording-condition':conditions[1],
    run:invalid==='previous-run'?demos.photography:demos.dreamjob});
  await page.goto('/');
  await expect(page.locator('.step-title')).toHaveText('Build the typed FabricConfig');
  await expect(page.getByTestId('journey-panel').getByRole('link',{name:'The captured typed settings ↗',exact:true}))
    .toHaveAttribute('href',baseline.artifacts[0].url);
  await expect.poll(()=>page.evaluate(()=>JSON.parse(localStorage.getItem('persona-lab-guide-wireframe:selection:v4')!).conditionId)).toBe('');
});

test('version five semantic selections migrate without changing turn or destination',async({page})=>{
  await page.addInitScript(()=>localStorage.setItem('persona-lab-guide-wireframe:selection:v4',JSON.stringify({
    version:5,page:'map',scenarioId:'boardgames',stageId:'build',detailed:false,focused:true,
    selected:'advisor',operationId:'advisor.0',turnIndex:1,
  })));
  await page.goto('/');
  await expect(page.locator('.step-title')).toHaveText('Connect the selected agent');
  await expect(page.getByTestId('step-counter')).toHaveText('Step 3 of 9');
  await expect.poll(()=>page.evaluate(()=>JSON.parse(localStorage.getItem('persona-lab-guide-wireframe:selection:v4')!)))
    .toMatchObject({version:6,scenarioId:'boardgames',turnIndex:1,selected:'advisor',operationId:'advisor.0',conditionId:''});
});

test('guarded maps show both message directions while photography keeps its direct reply',async({page})=>{
  await page.goto('/');
  for(const scenario of ['photography','boardgames','dreamjob']){
    await page.getByLabel('Scenario',{exact:true}).selectOption(scenario);
    for(const audience of ['Simplified','Detailed']){
      await page.getByRole('button',{name:audience,exact:true}).click();
      const learner=audience==='Detailed'?'usersim':'learner',advisor=audience==='Detailed'?'fabric':'advisor';
      for(const [source,target] of scenario==='photography'?[[learner,advisor],[advisor,learner]]:
        [[learner,'guardrails'],['guardrails',advisor],[advisor,'guardrails'],['guardrails',learner]]){
        await expect(page.locator(`.svelte-flow__edge[data-id="${source}-${target}-request"]`)).toHaveCount(1);
      }
      if(scenario!=='photography')await expect(page.locator(`.svelte-flow__edge[data-id="${advisor}-${learner}-request"]`)).toHaveCount(0);
    }
  }
});

test('only the recorded managed lesson or platform inspection changes the workload boundary',async({page})=>{
  const methods:string[]=[];
  page.on('request',request=>{if(request.url().includes('/api/journey/'))methods.push(request.method());});
  await page.goto('/');await page.getByLabel('Scenario',{exact:true}).selectOption('dreamjob');
  for(const audience of ['Simplified','Detailed']){
    await page.getByRole('button',{name:audience,exact:true}).click();
    const graph=page.getByTestId('integration-graph');
    await expect(graph).toHaveAttribute('data-boundary','standalone');
    const layoutKey=`persona-lab-guide-wireframe:integration-map:v2:${audience==='Detailed'?'detailed':'simple'}`;
    await page.getByRole('button',{name:'Save layout',exact:true}).click();
    await expect.poll(()=>page.evaluate(key=>localStorage.getItem(key),layoutKey)).not.toBeNull();
    await stage(page,9);
    if(await page.getByRole('button',{name:'Follow this step on the map →',exact:true}).count())
      await page.getByRole('button',{name:'Follow this step on the map →',exact:true}).click();
    await expect(graph).toHaveAttribute('data-boundary','managed');
    const caller=await page.locator('.svelte-flow__node[data-id="zone-caller"]').boundingBox();
    const sandbox=await page.locator('.svelte-flow__node[data-id="zone-sandbox"]').boundingBox();
    const guard=await page.locator('.svelte-flow__node[data-id="guardrails"]').boundingBox();
    expect(caller).not.toBeNull();expect(sandbox).not.toBeNull();expect(guard).not.toBeNull();
    expect(caller!.y+caller!.height).toBeLessThanOrEqual(sandbox!.y);
    expect(guard!.y).toBeGreaterThanOrEqual(caller!.y);
    expect(guard!.y+guard!.height).toBeLessThanOrEqual(caller!.y+caller!.height);
    await page.getByRole('button',{name:'Reset layout',exact:true}).click();
    await expect(graph).toHaveAttribute('data-boundary','standalone');
    await expect.poll(()=>page.evaluate(key=>localStorage.getItem(key),layoutKey)).toBeNull();
    await page.getByRole('button',{name:`Inspect ${audience==='Detailed'?'Helix managed operations':'Managed operations'}`,exact:true}).click();
    await expect(graph).toHaveAttribute('data-boundary','managed');
    await page.getByRole('button',{name:`Inspect ${audience==='Detailed'?'NeMo Guardrails · input / output':'Behavioural safeguards'}`,exact:true}).click();
    await expect(graph).toHaveAttribute('data-boundary','managed');
    await page.getByRole('button',{name:`Inspect ${audience==='Detailed'?'OpenShell · trusted supervisor':'Controlled execution'}`,exact:true}).click();
    await expect(graph).toHaveAttribute('data-boundary','managed');
    await stage(page,8);
    await expect(graph).toHaveAttribute('data-boundary','standalone');
    await page.getByRole('button',{name:`Inspect ${audience==='Detailed'?'Helix managed operations':'Managed operations'}`,exact:true}).click();
    await expect(graph).toHaveAttribute('data-boundary','managed');
    await page.getByRole('button',{name:`Inspect ${audience==='Detailed'?'NeMo Guardrails · input / output':'Behavioural safeguards'}`,exact:true}).click();
    await expect(graph).toHaveAttribute('data-boundary','standalone');
  }
  await page.getByLabel('Scenario',{exact:true}).selectOption('boardgames');
  await stage(page,9);await expect(page.getByTestId('integration-graph')).toHaveAttribute('data-boundary','standalone');
  expect(methods.length).toBeGreaterThan(0);expect(methods.every(method=>method==='GET')).toBe(true);
});

test('retail without a managed recording keeps its standalone boundary',async({page})=>{
  const fixture=recording('dreamjob');delete fixture.context['platform-condition.json'];
  await page.route('**/api/journey/lesson?scenario_id=dreamjob',route=>route.fulfill({json:fixture}));
  await page.goto('/');await page.getByLabel('Scenario',{exact:true}).selectOption('dreamjob');
  await stage(page,9);
  await expect(page.getByTestId('integration-graph')).toHaveAttribute('data-boundary','standalone');
  await page.getByRole('button',{name:'Inspect Managed operations',exact:true}).click();
  await expect(page.getByTestId('integration-graph')).toHaveAttribute('data-boundary','standalone');
});
