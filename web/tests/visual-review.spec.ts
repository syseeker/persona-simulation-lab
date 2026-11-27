import {createHash} from 'node:crypto';
import {mkdirSync, readFileSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {expect, test} from '@playwright/test';

test('capture the real read-only guide for visual developer review', async ({page}) => {
  test.setTimeout(120000);
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
    expect(['/api/journey/lesson', '/api/journey/demo-persona', '/api/journey/metadata', '/api/journey/execution']).toContain(url.pathname);
    await route.continue();
  });
  async function capture(file: string) {
    const path = resolve(output, file);
    await page.screenshot({path});
    screenshots.push({file, sha256: createHash('sha256').update(readFileSync(path)).digest('hex')});
  }
  await page.goto('/');
  await page.getByRole('button',{name:/1\s+Why NeMo Stack/}).click();
  await expect(page.getByTestId('app-version')).toHaveText('v0.3.0 · Developer review');
  await capture('00-version-first-page.png');
  await page.getByRole('button',{name:/2\s+Integration Map/}).click();
  await expect(page.getByTestId('selected-persona').or(page.getByTestId('scenario-facts').locator('.unavailable'))).toBeVisible();
  await capture('00-simplified-overview.png');
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
  await page.getByRole('button',{name:/2\s+Integration Map/}).click();
  await page.getByRole('button',{name:'Reset layout',exact:true}).click();
  await capture('06-detailed-overview.png');
  for(const scenario of ['photography','boardgames','dreamjob'])for(const audience of ['Simplified','Detailed']){
    await page.getByLabel('Scenario',{exact:true}).selectOption(scenario);
    await page.getByRole('button',{name:audience,exact:true}).click();
    await expect(page.locator('[data-edge-label]').first()).toBeVisible();
    await expect(page.getByTestId('selected-persona').or(page.getByTestId('scenario-facts').locator('.unavailable'))).toBeVisible();
    const overlaps=await page.evaluate(()=>{
      const hit=(a:DOMRect,b:DOMRect)=>Math.min(a.right,b.right)-Math.max(a.left,b.left)>1&&Math.min(a.bottom,b.bottom)-Math.max(a.top,b.top)>1;
      const cards=[...document.querySelectorAll('.component-node')].map(el=>({id:el.getAttribute('data-component'),box:el.getBoundingClientRect()}));
      const labels=[...document.querySelectorAll('[data-edge-label]')].map(el=>({id:el.getAttribute('data-edge-label'),box:el.getBoundingClientRect()}));
      return labels.flatMap((label,index)=>[...cards.filter(card=>hit(label.box,card.box)).map(card=>`${label.id} crosses ${card.id}`),...labels.slice(index+1).filter(other=>hit(label.box,other.box)).map(other=>`${label.id} overlaps ${other.id}`)]);
    });
    expect(overlaps).toEqual([]);
    await capture(`06-${scenario}-${audience.toLowerCase()}-overview.png`);
  }

  await page.getByLabel('Scenario',{exact:true}).selectOption('dreamjob');
  for(let n=1;n<9;n++)await page.getByRole('button',{name:'Next →',exact:true}).click();
  if(await page.getByRole('button',{name:'Follow this step on the map →',exact:true}).count())
    await page.getByRole('button',{name:'Follow this step on the map →',exact:true}).click();
  await page.getByLabel('Deployment condition',{exact:true}).selectOption('managed');
  await expect(page.getByTestId('integration-graph')).toHaveAttribute('data-boundary','managed');
  await capture('07-managed-detailed.png');
  await page.getByRole('button',{name:'Simplified',exact:true}).click();
  if(await page.getByRole('button',{name:'Follow this step on the map →',exact:true}).count())
    await page.getByRole('button',{name:'Follow this step on the map →',exact:true}).click();
  await page.getByLabel('Deployment condition',{exact:true}).selectOption('managed');
  await capture('08-managed-simplified.png');
  for(const width of [1000,390]){
    await page.setViewportSize({width,height:1000});
    // Resizing preserves the user's viewport; use the existing Fit control.
    await page.locator('.svelte-flow__controls-fitview').click();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
    await capture(`09-managed-width-${width}.png`);
  }

  writeFileSync(resolve(output, 'manifest.json'), JSON.stringify({schema: 'citizen-ui-review/v1',
    captured_at: new Date().toISOString(), source: 'current local guide and its tagged fixed recordings',
    viewport: {width: 1800, height: 1100}, scenario_id: 'photography', requests, screenshots}, null, 2) + '\n');
  expect(requests.length).toBeGreaterThan(0);
  expect(requests.every(request => request.method === 'GET')).toBe(true);
  console.log(`Visual review screenshots: ${output}`);
});
