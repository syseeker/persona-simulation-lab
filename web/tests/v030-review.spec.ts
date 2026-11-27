import {expect,test,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

const promoted:Record<string,string>=JSON.parse(process.env.LAB_REVIEW_EXPECTED_DEMOS||'{}');
const readers=['/api/journey/lesson','/api/journey/demo-persona','/api/journey/metadata','/api/journey/execution'];
async function stage(page:Page,target:number){
  const current=Number((await page.getByTestId('step-counter').innerText()).match(/Step (\d+)/)?.[1]);
  for(let n=0;n<Math.abs(target-current);n++)await page.getByRole('button',{name:current<target?'Next →':'← Back',exact:true}).click();
  await expect(page.getByTestId('step-counter')).toHaveText(`Step ${target} of 9`);
}
test.beforeEach(async({page})=>{
  test.skip(!promoted.dreamjob,'Supply the explicit reviewed demo IDs to inspect native recordings.');
  await page.setViewportSize({width:1800,height:1100});
  await page.route('**/api/**',async route=>{
    expect(route.request().method()).toBe('GET');expect(readers).toContain(new URL(route.request().url()).pathname);await route.continue();
  });
});

test('review identity, generated data and turn-one entry remain explicit',async({page})=>{
  await page.goto('/');await page.getByRole('button',{name:/1\s+Why NeMo Stack/}).click();
  await expect(page.getByTestId('app-version')).toHaveText('v0.3.0 · Developer review');
  await page.getByRole('button',{name:/2\s+Integration Map/}).click();
  await page.getByLabel('Scenario',{exact:true}).selectOption('boardgames');
  await expect(page.getByTestId('selected-persona')).toContainText('Caroline');
  await expect(page.getByTestId('selected-persona')).toContainText('structured name');
  for(const scenario of ['boardgames','dreamjob']){
    await page.getByLabel('Scenario',{exact:true}).selectOption(scenario);await stage(page,4);
    await expect(page.getByRole('button',{name:'Turn 1',exact:true})).toHaveClass(/pressed/);
    await page.getByRole('button',{name:'Turn 2',exact:true}).click();
    await page.getByRole('button',{name:'Detailed',exact:true}).click();
    await expect(page.getByRole('button',{name:'Turn 1',exact:true})).toHaveClass(/pressed/);
    await page.getByRole('button',{name:'Turn 2',exact:true}).click();await page.reload();
    await expect(page.getByRole('button',{name:'Turn 1',exact:true})).toHaveClass(/pressed/);
    await stage(page,5);await stage(page,4);
    await expect(page.getByRole('button',{name:'Turn 1',exact:true})).toHaveClass(/pressed/);
  }
  await stage(page,2);await page.getByText('Inspect the generated fields',{exact:true}).click();
  const fields=page.getByTestId('scenario-facts').locator('pre');
  await expect(fields).toBeVisible();const generated=JSON.parse(await fields.innerText());
  expect(Object.keys(generated)).toHaveLength(3);
  await expect(page.getByTestId('scenario-facts')).toContainText('one row with three physical columns');
});

test('deployment selections scope graph, policy and configuration links to the same recorded execution',async({page})=>{
  await page.goto('/');await page.getByLabel('Scenario',{exact:true}).selectOption('dreamjob');
  const context=await (await page.request.get('/api/journey/lesson?scenario_id=dreamjob')).json();
  const managed=context.context['platform-condition.json'].condition_id;
  const inventory=await (await page.request.get('/api/journey/metadata?scenario_id=dreamjob')).json();
  for(const audience of ['Simplified','Detailed']){
    await page.getByRole('button',{name:audience,exact:true}).click();await stage(page,9);
    await expect(page.getByLabel('Deployment condition')).toHaveValue('standalone');
    await expect(page.getByTestId('integration-graph')).toHaveAttribute('data-boundary','standalone');
    await expect(page.getByTestId('scenario-facts')).toContainText('Standalone OpenShell execution');
    await page.getByLabel('Deployment condition').selectOption('managed');
    await expect(page.getByTestId('integration-graph')).toHaveAttribute('data-boundary','managed');
    await expect(page.getByTestId('scenario-facts')).toContainText('Helix owns sandbox creation and deletion');
    await page.getByRole('button',{name:`Inspect ${audience==='Detailed'?'OpenShell · trusted supervisor':'Controlled execution'}`,exact:true}).click();
    await page.getByRole('button',{name:`Explain ${audience==='Detailed'?'OpenShell · trusted supervisor':'Controlled execution'}: Verify allowed/denied operations and cleanup`,exact:true}).click();
    const links=await page.getByTestId('journey-panel').locator('a[href*="recordings/captures/"]').evaluateAll(nodes=>nodes.map(a=>(a as HTMLAnchorElement).href));
    expect(links.every(url=>url.includes(`/managed/${managed}/`))).toBe(true);
    if(audience==='Detailed'){
      await expect(page.getByRole('region',{name:'Observed operation result'})).toContainText('belongs to the Helix-managed deployment');
      await page.getByTestId('journey-panel').getByRole('button',{name:'its own policy/probes/cleanup ↗',exact:true}).click();
      await expect(page.getByRole('combobox',{name:'Condition',exact:true})).toHaveValue(managed);
      await expect(page.locator('tr[data-requirement]')).toHaveCount(1);
      const row=page.locator('tr[data-requirement="CAP-OS-03"]');
      const recordedLinks=await row.locator('a').evaluateAll(nodes=>nodes.map(a=>(a as HTMLAnchorElement).href));
      expect(recordedLinks).toHaveLength(3);expect(recordedLinks.every(url=>url.includes(`/managed/${managed}/`))).toBe(true);
      await page.getByRole('button',{name:'Show all modules',exact:true}).click();
      await page.getByRole('button',{name:/2\s+Integration Map/}).click();
    }
    await stage(page,8);
  }
  await page.getByLabel('Scenario',{exact:true}).selectOption('photography');
  await page.getByLabel('Scenario',{exact:true}).selectOption('dreamjob');
  await page.getByRole('button',{name:/5\s+Metadata/}).click();
  await expect(page.getByRole('combobox',{name:'Condition',exact:true})).toHaveValue(inventory.conditions.find((c:Record<string,any>)=>c.purpose==='baseline').id);
  const baselineId=inventory.conditions.find((c:Record<string,any>)=>c.purpose==='baseline').id;
  const baselineRows=new Set(inventory.rows.filter((r:Record<string,any>)=>!r.condition_id||r.condition_id===baselineId).map((r:Record<string,any>)=>r.id)).size;
  await expect(page.locator('tr[data-requirement]')).toHaveCount(baselineRows);
  await page.getByRole('combobox',{name:'Condition',exact:true}).selectOption('*');await expect(page.locator('tr[data-requirement]')).toHaveCount(51);
  await page.getByRole('combobox',{name:'Condition',exact:true}).selectOption(managed);
  for(const id of ['CAP-PLAT-01','CAP-PLAT-02']){
    const row=page.locator(`tr[data-requirement="${id}"]`);
    expect(inventory.rows.find((r:Record<string,any>)=>r.id===id&&r.condition_id===managed).artifacts.some((a:Record<string,any>)=>a.path===('managed-'+(id==='CAP-PLAT-01'?'client':'agent')+'-config.json'))).toBe(true);
    await expect(row).toContainText('config.json');
  }
});

test('routing and historical trace readers expose measured work without starting workloads',async({page})=>{
  await page.goto('/');await page.getByLabel('Scenario',{exact:true}).selectOption('dreamjob');await stage(page,7);
  await page.getByRole('button',{name:'Detailed',exact:true}).click();
  const selector=page.getByLabel('Routing comparison condition',{exact:true});
  await expect(selector.locator('option')).toHaveCount(5);
  await expect(selector).toContainText('MiniMax fixed');await expect(selector).toContainText('Automatic choice: MiniMax or Mistral');
  await expect(page.getByTestId('scenario-facts')).toContainText('24 of 24 criterion rows');
  await expect(page.getByTestId('scenario-facts')).toContainText('4 admitted');
  await expect(page.locator('[data-component="routing"]')).toHaveAttribute('data-active','false');
  await expect(page.locator('.integration-edge[data-id="litellm-routing-request"]')).toHaveCount(1);
  await expect(page.locator('.integration-edge[data-id="litellm-routing-request"].is-active')).toHaveCount(0);
  await stage(page,5);await expect(page.getByTestId('execution-viewer')).toContainText('Recorded execution and timing');
  const cid=await page.getByTestId('execution-viewer').getAttribute('data-condition');
  const response=await page.request.get(`/api/journey/execution?scenario_id=dreamjob&condition_id=${cid}`);
  expect(response.status()).toBe(200);
  const execution=await response.json();expect(execution.inference_calls_for_inspection).toBe(0);expect(execution.condition.id).toBe(cid);
  // The UI requests are the authoritative selected scope; the API independently rejects foreign IDs.
  expect((await page.request.get('/api/journey/execution?scenario_id=dreamjob&condition_id=foreign')).status()).toBe(400);
  const receipt=JSON.parse(readFileSync(resolve('..','runs/observability/import-receipt.json'),'utf8'));
  expect(receipt.status).toBe('verified');expect(receipt.span_count).toBe(94);expect(receipt.conditions).toHaveLength(9);
  await expect(page.getByTestId('execution-viewer').getByRole('link',{name:'Open this condition in local Phoenix ↗',exact:true})).toHaveAttribute('href',/^http:\/\/127\.0\.0\.1:6006\//);
  await page.getByLabel('Trace public turn',{exact:true}).selectOption('1');
  await expect(page.getByTestId('execution-viewer')).toContainText('There is no native agent subtree for this clarification');
  await expect(page.getByTestId('execution-viewer').locator('.tool-fact')).toHaveCount(0);

});
