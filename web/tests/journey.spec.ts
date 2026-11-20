import { expect, test } from '@playwright/test';

const first='11111111-1111-4111-8111-111111111111', second='22222222-2222-4222-8222-222222222222';
function trace(id:string) {
  return {run:{run_id:id,scenario_id:'photography',episode_id:`episode-${id}`,status:'completed',calls:5,cleanup_confirmed:true,
    run_directory:`runs/journeys/${id}`,source_revision:'fixture-revision',configuration:{harness:'deepagents'}},
    artifacts:[{id:`artifact-${id}`,path:'usage.json',url:`/api/journey/artifact?run_id=${id}&artifact_id=artifact-${id}`}],
    source_lock:{source:'ngc',original_sha256:'fixture'},situation:{kind:'authored fixture'},
    usage:{records:[{call:3,role:'assistant',status:'completed',selected_model:'fixture-model'}]},
    conversation:[{turn:1,role:'user',content:'Photography on Saturday, S$50.'},{turn:1,role:'assistant',content:'Offline test fixture, not execution evidence.'}],
    relay:{scopes:[],notices:['Fixture has no native scopes.']},tools:[],
    evaluation:{passed:1,total:1,rows:[],coverage:'Fixture only'}};
}

test.beforeEach(async({page})=>{
  await page.route('**/api/journey/**',async route=>{
    expect(route.request().method()).toBe('GET');
    const url=new URL(route.request().url()),action=url.pathname.split('/').at(-1);
    const id=url.searchParams.get('run_id') || first;
    if(action==='list') await route.fulfill({json:{runs:[first,second].map(run_id=>({run_id,status:'completed',created_at:'2026-11-20T00:00:00Z'}))}});
    else if(action==='trace') await route.fulfill({json:trace(id)});
    else if(action==='source') await route.fulfill({json:{available:true,path:'src/learning_lab/fabric_target.py',symbol:'build_config',line:25,
      github_url:'https://github.com/example/citizen-app/blob/fixture/src/learning_lab/fabric_target.py#L25',
      repository_url:'https://github.com/example/citizen-app',content:'def build_config(): ...',github_notice:'Current checkout differs from saved source.',sha256:'fixture'}});
    else if(action==='artifact') await route.fulfill({json:{run_id:id,path:'usage.json',url:url.pathname+url.search,sha256:'fixture',content:{selected_run:id}}});
    else await route.abort();
  });
});

test('nine recorded stages, code and local logs retain the same run',async({page})=>{
  const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto('/');
  const counter=page.getByTestId('recorded-step-counter');
  await expect(counter).toHaveText('Step 1 of 9');
  for(let stage=2;stage<=9;stage++) {
    await page.getByRole('button',{name:'Next →',exact:true}).click();
    await expect(counter).toHaveText(`Step ${stage} of 9`);
  }
  await page.getByRole('button',{name:'Reset playback',exact:true}).click();
  await page.getByRole('button',{name:'Next →',exact:true}).click();
  await page.getByRole('button',{name:'Next →',exact:true}).click();
  await page.getByRole('button',{name:'Application code',exact:true}).click();
  await expect(page.getByRole('link',{name:'GitHub code ↗',exact:true})).toHaveAttribute('href',/github\.com\/example\/citizen-app\/blob\/fixture\/src\/learning_lab\/fabric_target.py#L25/);
  await page.getByRole('button',{name:'← Back to the selected run',exact:true}).click();
  for(let n=0;n<4;n++)await page.getByRole('button',{name:'Next →',exact:true}).click();
  await page.getByRole('button',{name:'Scenario log',exact:true}).click();
  await expect(page.getByRole('link',{name:'Open local record ↗',exact:true})).toHaveAttribute('href',`/api/journey/artifact?run_id=${first}&artifact_id=artifact-${first}`);
  await page.getByRole('button',{name:'usage.json',exact:true}).first().click();
  await expect(page.locator('.artifact-preview')).toContainText(first);
  await page.locator('.saved-selection > summary').click();
  await page.getByLabel('Photography evidence').selectOption(second);
  await expect(counter).toHaveText('Step 7 of 9');
  await page.getByRole('button',{name:'Scenario log',exact:true}).click();
  await expect(page.getByRole('link',{name:'Open local record ↗',exact:true})).toHaveAttribute('href',`/api/journey/artifact?run_id=${second}&artifact_id=artifact-${second}`);
  await expect(page.locator('.artifact-preview')).toHaveCount(0);
  await page.reload();
  await expect(counter).toHaveText('Step 7 of 9');
  await expect(page.getByRole('link',{name:'Open local record ↗',exact:true})).toHaveAttribute('href',new RegExp(second));
  expect(errors).toEqual([]);
});

test('saved request attribution survives view changes and reload',async({page})=>{
  await page.goto('/');await expect(page.getByTestId('recorded-step-counter')).toBeVisible();
  for(let n=0;n<4;n++)await page.getByRole('button',{name:'Next →',exact:true}).click();
  await page.getByLabel('Saved request',{exact:true}).selectOption('call:3');
  await expect(page.locator('.canvas-caption')).toContainText('Native Relay span correlation is not assumed');
  await page.getByRole('button',{name:'Detailed',exact:true}).click();
  await expect(page.getByLabel('Saved request',{exact:true})).toHaveValue('call:3');
  await page.reload();
  await expect(page.getByLabel('Saved request',{exact:true})).toHaveValue('call:3');
  await expect(page.locator('.canvas-caption')).toContainText('Gateway call 3');
});

test('fixed recording log links target the matching GitHub pack',async({page})=>{
  await page.route('**/api/journey/trace?**',async route=>{
    const value=trace(first);
    const recorded={...value,recording_notice:'Fixed sanitized recording',
      run:{...value.run,recording:true,kind:'recorded',run_directory:`recordings/photography/${first}`},
      artifacts:value.artifacts.map(file=>({...file,kind:'recorded',url:`https://github.com/example/citizen-app/blob/recording-commit/recordings/photography/${first}/${file.path}`}))};
    await route.fulfill({json:recorded});
  });
  await page.goto('/');await expect(page.getByTestId('recorded-step-counter')).toBeVisible();
  for(let n=0;n<6;n++)await page.getByRole('button',{name:'Next →',exact:true}).click();
  await page.getByRole('button',{name:'Scenario log',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Scenario-specific recorded logs'})).toBeVisible();
  await expect(page.getByRole('link',{name:'Open recorded log ↗',exact:true})).toHaveAttribute('href',`https://github.com/example/citizen-app/blob/recording-commit/recordings/photography/${first}/usage.json`);
});

test('future scenarios stay illustrative without inheriting photography logs',async({page})=>{
  await page.goto('/');await expect(page.getByTestId('recorded-step-counter')).toBeVisible();
  for(const scenario of ['boardgames','dreamjob']) {
    await page.getByLabel('Scenario',{exact:true}).selectOption(scenario);
    await expect(page.getByRole('button',{name:'Simulate a Session',exact:true})).toBeDisabled();
    await expect(page.getByTestId('journey-panel')).toHaveCount(0);
    await expect(page.locator('.trace-heading')).toContainText('ILLUSTRATIVE');
    for(let n=0;n<8;n++)await page.getByRole('button',{name:'Next →',exact:true}).click();
    await expect(page.locator('.footer-step')).toHaveText('Step 9 of 9');
  }
  await page.getByLabel('Scenario',{exact:true}).selectOption('photography');
  await expect(page.getByTestId('recorded-step-counter')).toHaveText('Step 1 of 9');
  await expect(page.locator('.trace-heading')).toContainText('RECORDED');
});

test('journey chart fits desktop and phone widths without a horizontal scrollbar',async({page})=>{
  await page.goto('/');await page.getByRole('button',{name:/1\s+Why NeMo Stack/}).click();
  for(const width of [1800,1000,390]) {
    await page.setViewportSize({width,height:1000});
    const chart=page.locator('.journey-chart');
    await expect(chart.getByRole('button')).toHaveCount(9);
    expect(await chart.evaluate(el=>el.scrollWidth<=el.clientWidth+1)).toBe(true);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true);
  }
});
