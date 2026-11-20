import {expect,test} from '@playwright/test';
import {readFileSync,readdirSync} from 'node:fs';
import {resolve} from 'node:path';

const run='7863c607-cb99-4a31-b60c-381bf2099f0e';
const demoRuns:Record<string,string>={photography:run,boardgames:'938bdb3f-568e-442e-889f-fed046edf5a0',dreamjob:'8542330d-d6df-494e-8509-d81a5841d69e'};
const repo='https://github.com/syseeker/persona-simulation-lab';
const read=(path:string)=>JSON.parse(readFileSync(resolve('..',path),'utf8'));
function context(scenario:string){
  const identity=demoRuns[scenario];
  const folder=`recordings/${scenario}/${identity}`,companion=`recordings/guide-context/${scenario}/${identity}`;
  const trace=read(`${folder}/trace.json`),extra:Record<string,unknown>={};
  for(const name of readdirSync(resolve('..',companion)).filter(n=>n.endsWith('.json')&&n!=='manifest.json'))extra[name]=read(`${companion}/${name}`);
  for(const name of Object.keys(read(`${folder}/manifest.json`).files)){
    if(name.endsWith('.json'))extra[name]=read(`${folder}/${name}`);
    else if(name.endsWith('.jsonl'))extra[name]=readFileSync(resolve('..',`${folder}/${name}`),'utf8').trim().split('\n').filter(Boolean).map(line=>JSON.parse(line));
  }
  const artifacts=[...Object.keys(read(`${folder}/manifest.json`).files).map(path=>({path,url:`${repo}/blob/recorded-commit/${folder}/${path}`})),...Object.keys(read(`${companion}/manifest.json`).files).map(path=>({path,url:`${repo}/blob/context-commit/${companion}/${path}`}))];
  const link={available:true,path:'src/learning_lab/fabric_target.py',symbol:'def build_config',url:`${repo}/blob/source-commit/src/learning_lab/fabric_target.py#L25`,recording_match:'matched',notice:'Committed code matches the recorded source hash.'};
  return {state:'recorded',scenario_id:scenario,run_id:identity,trace,context:extra,artifacts,sources:{'fabric.config':link,'fabric.invoke':{...link,symbol:'self.runtime.invoke'},'fabric.result':link,'fabric.plan':link,'fabric.start':link}};
}
test.beforeEach(async({page})=>{
  await page.route('**/api/journey/**',async route=>{
    expect(route.request().method()).toBe('GET');
    const url=new URL(route.request().url()),scenario=url.searchParams.get('scenario_id')||'photography';
    if(url.pathname.endsWith('/lesson'))await route.fulfill({json:context(scenario)});
    else if(url.pathname.endsWith('/demo-persona'))await route.fulfill({json:scenario==='photography'?{available:true,name:'Review Fixture',source:'ngc',revision:'fixture-only',fields:[{label:'Age',value:24},{label:'Interests',value:'Photography'}],traits:[],original_sha256:'f'.repeat(64)}:{available:false,notice:'No recorded persona for this scenario.'}});
    else throw new Error('Inspection attempted an unexpected operation: '+url.pathname);
  });
});

test('all 27 scenario lessons teach concepts, inputs/results and verification without execution',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  for(const scenario of ['photography','boardgames','dreamjob']){
    await page.getByLabel('Scenario',{exact:true}).selectOption(scenario);
    for(let step=1;step<=9;step++){
      await expect(page.getByTestId('step-counter')).toHaveText(`Step ${step} of 9`);
      const panel=page.getByTestId('journey-panel');
      for(const name of ['Why this matters','In this scenario','How it works','Check your implementation'])await expect(panel.getByRole('heading',{name,exact:true})).toBeVisible();
      await expect(panel.locator('pre')).toHaveCount(0);
      await expect(page.getByLabel('Photography evidence',{exact:true})).toHaveCount(0);
      await expect(panel.getByText('All files in this run',{exact:true})).toHaveCount(0);
      await expect(panel.getByTestId('record-state')).toContainText(demoRuns[scenario].slice(0,8));
      for(const other of Object.keys(demoRuns).filter(id=>id!==scenario))await expect(panel.locator(`a[href*="recordings/${other}/"], a[href*="recordings/guide-context/${other}/"]`)).toHaveCount(0);
      if(scenario==='dreamjob'&&step===2)await expect(panel.getByTestId('scenario-facts')).toContainText('generated test assumptions, not original profile facts');
      if(scenario==='dreamjob'&&step===7){await expect(panel.getByTestId('scenario-facts')).toContainText('fixed-candidate · failed');await expect(panel.getByTestId('scenario-facts')).toContainText('available-switchyard · completed');}
      if(scenario==='dreamjob'&&step===9)await expect(panel.getByTestId('scenario-facts')).toContainText('14 native Intake spans');
      if(step<9)await page.getByRole('button',{name:'Next →',exact:true}).click();
    }
  }
  expect(errors).toEqual([]);
});

test('switching scenarios keeps live ownership separate and never starts or cancels a workload',async({page})=>{
  const live='11111111-1111-4111-8111-111111111111',methods:string[]=[];
  page.on('request',request=>{if(request.url().includes('/api/journey/'))methods.push(request.method());});
  await page.addInitScript(({live})=>localStorage.setItem('persona-lab-guide-wireframe:selection:v4',JSON.stringify({version:4,page:'map',scenarioId:'photography',liveRuns:{photography:live}})),{live});
  await page.route('**/api/journey/readiness*',route=>route.fulfill({json:{ready:false,native:{gateway:true,image:true},proxy:{fixed_alias_available:true,support_alias_available:true},active:{run_id:live}}}));
  await page.route('**/api/journey/trace*',route=>route.fulfill({json:{run:{run_id:live,scenario_id:'photography',status:'running',stage:'run',calls:3,cleanup_confirmed:false},conversation:[{role:'user',content:'Public photography live fixture'}]}}));
  await page.goto('/');
  await page.getByRole('button',{name:'Simulate a Session',exact:true}).click();
  await expect(page.getByTestId('live-session')).toContainText('Public photography live fixture');
  await page.getByLabel('Scenario',{exact:true}).selectOption('boardgames');
  await page.getByRole('button',{name:'Simulate a Session',exact:true}).click();
  await expect(page.getByTestId('live-session')).not.toContainText('Public photography live fixture');
  await expect(page.getByTestId('live-session')).toContainText('NEW BOARD-GAMES CONDITION');
  await page.getByLabel('Scenario',{exact:true}).selectOption('photography');
  await page.getByRole('button',{name:'Simulate a Session',exact:true}).click();
  await expect(page.getByTestId('live-session')).toContainText('Public photography live fixture');
  expect(methods.every(method=>method==='GET')).toBe(true);
});

test('overview shows everything; explicit persona focus does not activate UserSim',async({page})=>{
  await page.goto('/');await expect(page.locator('[data-component="person"]')).toBeVisible();
  await expect(page.locator('.component-node.dim')).toHaveCount(0);
  await page.getByRole('button',{name:'Follow this step on the map →',exact:true}).click();
  await expect(page.locator('.component-node.active')).toHaveCount(1);
  await expect(page.locator('[data-component="person"]')).toHaveAttribute('data-active','true');
  await expect(page.locator('[data-component="learner"]')).toHaveAttribute('data-active','false');
  await page.getByRole('button',{name:'Detailed',exact:true}).click();
  await expect(page.locator('.component-node.dim')).toHaveCount(0);
  await page.getByRole('button',{name:'Reset playback',exact:true}).click();
  await expect(page.locator('.component-node.active')).toHaveCount(1);
  await expect(page.locator('[data-component="personas"]')).toHaveAttribute('data-active','true');
  await expect(page.locator('[data-component="usersim"]')).toHaveAttribute('data-active','false');
  await page.getByRole('button',{name:'Reset layout',exact:true}).click();
  await expect(page.locator('.component-node.dim')).toHaveCount(0);
  await expect(page.locator('.component-node.active')).toHaveCount(0);
});

test('collapse keeps one scenario choice visible and Step 2 separates supplied inputs from generated wording',async({page})=>{
  await page.goto('/');await expect(page.getByTestId('selected-persona')).toContainText('Review Fixture');
  await page.getByRole('button',{name:'Next →',exact:true}).click();
  await expect(page.getByTestId('scenario-facts')).toContainText('Supplied by this scenario');
  await expect(page.getByTestId('scenario-facts')).toContainText('USERSIM WORDING · SAVED OPENING');
  await expect(page.getByTestId('scenario-facts')).toContainText('Generated during Step 4');
  await page.getByLabel('Toggle scenario summary',{exact:true}).click();
  await expect(page.getByLabel('Scenario',{exact:true})).toBeVisible();
  await expect(page.getByLabel('Scenario',{exact:true})).toHaveCount(1);
  await page.getByLabel('Scenario',{exact:true}).selectOption('boardgames');
  await expect(page.getByTestId('step-counter')).toHaveText('Step 1 of 9');
  await expect(page.getByTestId('selected-persona')).toHaveCount(0);
});

test('Fabric operation has exact repository and run links; inspection preserves lesson and reload selection',async({page})=>{
  await page.goto('/');
  await page.getByRole('button',{name:'Next →',exact:true}).click();await page.getByRole('button',{name:'Next →',exact:true}).click();
  await page.getByRole('button',{name:'Detailed',exact:true}).click();
  await page.getByRole('button',{name:'Explain NeMo Fabric: Build FabricConfig and resolve the adapter',exact:true}).click();
  await expect(page.getByTestId('step-counter')).toHaveText('Step 3 of 9');
  const op=page.locator('[data-operation="fabric.config"]');
  await expect(op.getByRole('link',{name:'Application call ↗',exact:true})).toHaveAttribute('href',`${repo}/blob/source-commit/src/learning_lab/fabric_target.py#L25`);
  await expect(op.getByRole('link',{name:'Scenario log ↗',exact:true})).toHaveAttribute('href',new RegExp(`/recordings/(guide-context/)?photography/${run}/`));
  await expect(op).toContainText('Committed code matches the recorded source hash.');
  await page.reload();
  await expect(page.getByTestId('step-counter')).toHaveText('Step 3 of 9');
  await expect(page.locator('.step-title')).toHaveText('Build FabricConfig and resolve the adapter');
  await page.getByRole('button',{name:'Simplified',exact:true}).click();
  await expect(page.locator('.step-title')).toHaveText('Build FabricConfig and resolve the adapter');
  await expect(page.locator('.component-node.dim')).toHaveCount(0);
  await page.getByRole('button',{name:'Detailed',exact:true}).click();
  await expect(page.locator('.step-title')).toHaveText('Build FabricConfig and resolve the adapter');
  await page.getByRole('button',{name:/Back to step 3/}).click();
  await expect(page.locator('.step-title')).toHaveText('Build and connect the agent');
  await page.getByRole('button',{name:/2\s+Integration Map/}).click();
  await expect(page.locator('.component-node.dim')).toHaveCount(0);
});

test('saved geometry, inspector width and reduced-motion preferences survive the redesigned map',async({page})=>{
  await page.emulateMedia({reducedMotion:'reduce'});await page.setViewportSize({width:1800,height:1100});
  await page.goto('/');await expect(page.locator('[data-component="person"]')).toBeVisible();
  const node=page.locator('.svelte-flow__node[data-id="person"]');
  const header=node.locator('header'),box=await header.boundingBox();expect(box).not.toBeNull();
  await page.mouse.move(box!.x+30,box!.y+15);await page.mouse.down();await page.mouse.move(box!.x+70,box!.y+45,{steps:8});await page.mouse.up();
  const transform=await node.getAttribute('style');await page.getByRole('button',{name:'Save layout',exact:true}).click();
  const divider=page.getByRole('separator');await divider.focus();await page.keyboard.press('ArrowLeft');
  const width=await divider.getAttribute('aria-valuenow');
  await page.reload();await expect(node).toHaveAttribute('style',transform!);await expect(divider).toHaveAttribute('aria-valuenow',width!);
  await page.getByRole('button',{name:'Follow this step on the map →',exact:true}).click();
  await page.getByRole('button',{name:'Next →',exact:true}).click();
  const animations=await page.locator('.integration-edge.is-active .svelte-flow__edge-path').evaluateAll(paths=>paths.map(p=>getComputedStyle(p).animationName));
  expect(animations.length).toBeGreaterThan(0);expect(animations.every(a=>a==='none')).toBe(true);
});

test('playback progresses through nine chapters without changing geometry or starting execution',async({page})=>{
  await page.goto('/');await expect(page.getByTestId('step-counter')).toHaveText('Step 1 of 9');
  await page.clock.install();await page.getByRole('button',{name:'Play',exact:true}).click();
  for(let step=2;step<=9;step++){await page.clock.fastForward(4300);await expect(page.getByTestId('step-counter')).toHaveText(`Step ${step} of 9`);}
  await page.clock.fastForward(4300);await expect(page.getByRole('button',{name:'Play',exact:true})).toHaveAttribute('aria-pressed','false');
});

test('unavailable recordings and originals remain visible without substitute evidence',async({page})=>{
  await page.route('**/api/journey/lesson?**',route=>route.fulfill({json:{state:'unavailable',scenario_id:'photography',trace:null,context:{},artifacts:[],sources:{},notice:'The tagged demo recording is unavailable. No substitute.'}}));
  await page.route('**/api/journey/demo-persona?**',route=>route.fulfill({json:{available:false,notice:'No original matches this revision and hash. No substitute profile.'}}));
  await page.goto('/');
  await expect(page.getByTestId('record-state')).toContainText('Demo unavailable');
  await expect(page.getByTestId('scenario-facts')).toContainText('No original matches');
  await expect(page.locator('a[href*="recordings/photography"]')).toHaveCount(0);
  await expect(page.getByTestId('selected-persona')).toHaveCount(0);
});

test('journey chart retains its responsive design',async({page})=>{
  await page.goto('/');await page.getByRole('button',{name:/1\s+Why NeMo Stack/}).click();
  for(const width of [1800,1000,390]){
    await page.setViewportSize({width,height:1000});const chart=page.locator('.journey-chart');
    await expect(chart.getByRole('button')).toHaveCount(9);
    expect(await chart.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  }
});
