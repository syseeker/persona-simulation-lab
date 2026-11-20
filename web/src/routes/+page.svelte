<script lang="ts">
  import JourneyChart from '../lib/JourneyChart.svelte';
  import JourneyPanel from '../lib/JourneyPanel.svelte';
  import LiveSessionPanel from '../lib/LiveSessionPanel.svelte';
  import {onMount,tick} from 'svelte';
  import IntegrationGraph from '#lib/IntegrationGraph.svelte';
  import PanelDivider from '#lib/PanelDivider.svelte';
  import DatasetsPage from '#lib/DatasetsPage.svelte';
  import {stages,scenarios,faqs,legacyStageIds} from '#lib/content.ts';
  import {learningResources} from '#lib/learningResources.ts';
  import {lessonFor,componentById,operationById,resolveComponent} from '#lib/lessonArchitecture.ts';
  import '../style.css';
  type Page='why'|'map'|'qa'|'datasets';
  let page=$state<Page>('map'),scenarioId=$state('photography'),liveMode=$state(false),liveRunId=$state<string|null>(null);
  let personaSource=$state('ngc'),lockedPersona=$state<Record<string,any>|null>(null);
  let setupOpen=$state(true),detailed=$state(false),stageIndex=$state(0),turnIndex=$state(0),focused=$state(false);
  let search=$state(''),qaSearch=$state(''),qaGroup=$state('all'),labels=$state(true);
  let selected=$state<string|null>(null),operationId=$state(''),playing=$state(false),notice=$state(''),restored=$state(false),reducedMotion=$state(false);
  let workspaceWidth=$state(1600),preferredPanelWidth=$state<number|null>(null);
  const panelWidthKey='persona-lab-guide-wireframe:inspector-width:v1',panelMin=360;
  const panelMax=$derived(Math.max(panelMin,Math.min(900,Math.floor(workspaceWidth*.65),workspaceWidth-428)));
  const defaultPanelWidth=$derived(workspaceWidth>=1700?645:workspaceWidth<=1200?548:608);
  const panelWidth=$derived(Math.max(panelMin,Math.min(panelMax,preferredPanelWidth??defaultPanelWidth)));
  let graph:{saveLayout:()=>boolean;resetLayout:()=>void;fit:()=>void}|undefined=$state();
  const storageKey='persona-lab-guide-wireframe:selection:v4';
  const currentScenario=$derived(scenarios.find(s=>s.id===scenarioId)||scenarios[0]);
  const harness=$derived(currentScenario.preset.harness),designer=$derived(currentScenario.preset.designer),routing=$derived(currentScenario.preset.routing);
  const nativeGuards=$derived(currentScenario.preset.guardrails),managed=$derived(currentScenario.preset.helix);
  const lastStage=stages.length-1,faqGroups=[...new Set(faqs.map(f=>f.group))];
  const stage=$derived(stages[stageIndex]);
  const activeOperations=$derived(!focused?[]:operationId?[operationId]:selected?componentById[selected].operations.map(o=>o.id):lessonFor(scenarioId,stage.id).operations);
  const filteredFaqs=$derived(faqs.filter(f=>(qaGroup==='all'||f.group===qaGroup)&&`${f.question} ${f.answer}`.toLowerCase().includes(qaSearch.toLowerCase())));
  function stopPlayback(){playing=false;}
  function scrollInspectorTop(){void tick().then(()=>document.querySelector('.trace-inspector .inspector-content')?.scrollTo({top:0,behavior:'instant'}));}
  function overview(){focused=false;selected=null;operationId='';search='';}
  function changePage(next:Page){stopPlayback();page=next;if(next==='map')overview();}
  async function locate(index:number,node?:string){stopPlayback();page='map';liveMode=false;stageIndex=Math.max(0,index);selected=null;operationId='';focused=true;
    if(node&&componentById[resolveComponent(node)]&&!lessonFor(scenarioId,stage.id).operations.some(id=>operationById[id].component===resolveComponent(node)))selected=resolveComponent(node);
    await tick();graph?.fit();scrollInspectorTop();}
  function chooseStage(index:number){stopPlayback();liveMode=false;stageIndex=Math.max(0,Math.min(lastStage,index));selected=null;operationId='';focused=true;scrollInspectorTop();}
  function inspect(component:string,operation=''){stopPlayback();const id=resolveComponent(component);if(!componentById[id])return;selected=id;operationId=operationById[operation]?.component===id?operation:'';focused=true;scrollInspectorTop();}
  function returnToPlayer(){selected=null;operationId='';scrollInspectorTop();}
  function scenarioChanged(){stopPlayback();liveMode=false;stageIndex=0;turnIndex=0;overview();notice='';scrollInspectorTop();}
  function changeDetail(value:boolean){stopPlayback();detailed=value;focused=false;search='';scrollInspectorTop();}
  function saveLayout(){notice=graph?.saveLayout()?`${detailed?'Detailed':'Simplified'} layout saved in this browser.`:'Browser storage is unavailable. This layout has not been saved.';}
  function resetLayout(){stopPlayback();overview();graph?.resetLayout();notice='Default layout restored for this view. The whole architecture is visible.';}
  onMount(()=>{
    reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    try{
      const savedWidth=JSON.parse(localStorage.getItem(panelWidthKey)||'null');
      if(Number.isFinite(savedWidth)&&savedWidth>=panelMin&&savedWidth<=900)preferredPanelWidth=savedWidth;
      const saved=JSON.parse(localStorage.getItem(storageKey)||localStorage.getItem('persona-lab-guide-wireframe:selection:v3')||localStorage.getItem('persona-lab-guide-wireframe:selection:v2')||'null');
      if([2,3,4].includes(saved?.version)){
        if(['why','map','qa','datasets'].includes(saved.page))page=saved.page;
        if(scenarios.some(s=>s.id===saved.scenarioId))scenarioId=saved.scenarioId;
        if(typeof saved.setupOpen==='boolean')setupOpen=saved.setupOpen;
        const index=stages.findIndex(s=>s.id===(saved.version===2?legacyStageIds[saved.stageIndex]:saved.stageId));if(index>=0)stageIndex=index;
        if(typeof saved.detailed==='boolean')detailed=saved.detailed;
        if(Number.isInteger(saved.turnIndex)&&saved.turnIndex>=0&&saved.turnIndex<currentScenario.turns.length)turnIndex=saved.turnIndex;
        if(saved.version===4){
          focused=saved.focused===true;
          if(componentById[saved.selected])selected=saved.selected;
          if(operationById[saved.operationId]?.component===selected)operationId=saved.operationId;
          if(typeof saved.liveRunId==='string'&&/^[a-f0-9-]{36}$/.test(saved.liveRunId))liveRunId=saved.liveRunId;
        }
      }
      // Obsolete selections may contain raw source identifiers; retain only the new safe preferences.
      localStorage.removeItem('persona-lab-guide-wireframe:selection:v3');localStorage.removeItem('persona-lab-guide-wireframe:selection:v2');
    }catch{/* Browser preferences are optional. */}
    restored=true;
  });
  $effect(()=>{const snapshot={version:4,page,scenarioId,setupOpen,stageId:stage.id,turnIndex,detailed,selected,operationId,focused,liveRunId};if(restored)try{localStorage.setItem(storageKey,JSON.stringify(snapshot));}catch{/* Optional preference. */}});
  $effect(()=>{const width=preferredPanelWidth;if(restored)try{if(width===null)localStorage.removeItem(panelWidthKey);else localStorage.setItem(panelWidthKey,JSON.stringify(width));}catch{/* Optional preference. */}});
  $effect(()=>{if(!playing||page!=='map')return;const position=stageIndex;const timer=window.setTimeout(()=>{if(position<lastStage){stageIndex=position+1;selected=null;operationId='';scrollInspectorTop();}else playing=false;},4200);return()=>window.clearTimeout(timer);});
</script>

<svelte:head><title>Building Citizen Apps with NeMo · Integration Guide</title></svelte:head>

<div class="app-shell" data-page={page}>
  <header class="app-header">
    <button class="brand" onclick={() => changePage('why')} aria-label="Building Citizen Apps with NeMo home">
      <span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i></span>
      <span><strong>Building Citizen Apps with NeMo</strong><small>NeMo Stack Integration Guide · Singapore</small></span>
    </button>
    <div class="header-note"><span class="status-pill">INTEGRATION GUIDE</span><span class="header-caption">{page === 'datasets' ? 'Schema reference · local profile reader · no inference' : 'Photography connected · other scenarios illustrative'}</span></div>
  </header>

  <nav class="main-nav" aria-label="Main sections">
    <button class:active={page === 'why'} aria-current={page === 'why' ? 'page' : undefined} onclick={() => changePage('why')}><span>1</span> Why NeMo Stack</button>
    <button class:active={page === 'map'} aria-current={page === 'map' ? 'page' : undefined} onclick={() => changePage('map')}><span>2</span> Integration Map</button>
    <button class:active={page === 'qa'} aria-current={page === 'qa' ? 'page' : undefined} onclick={() => changePage('qa')}><span>3</span> Q&amp;A</button>
    <button class:active={page === 'datasets'} aria-current={page === 'datasets' ? 'page' : undefined} onclick={() => changePage('datasets')}><span>4</span> Datasets</button>
    <span class="nav-meta">One application. Nine developer lessons.</span>
  </nav>

  {#if page === 'why'}
    <main class="editorial">
      <section class="hero">
        <div class="eyebrow">BUILD · INSPECT · IMPROVE · CONTAIN</div>
        <h1>Build citizen-focused AI.<br />Follow the agent development journey.</h1>
        <p class="hero-lead">How do synthetic test personas, an agent harness, application tools and the NeMo stack become one understandable application?</p>
        <div class="north-star"><span class="eyebrow">NORTH STAR</span><p>Teach developers to build a citizen-focused AI application with country-specific Nemotron Personas and the NVIDIA NeMo stack—by seeing how it works, following its information flow, and opening the code and evidence behind it.</p></div>
        <div class="application-story"><span class="eyebrow">THE APPLICATION WE ARE BUILDING</span><h2>A Singapore learning and community advisor</h2><p>Can it understand different needs, recommend only supported options, explain its behaviour, and run within controlled boundaries?</p><p class="muted">Learning is the goal: a hobby, a community activity or skills towards a dream job. Career aspirations guide course advice; they do not establish vacancies, endorsement or guaranteed outcomes.</p></div>
      </section>

      <section class="editorial-section">
        <div class="section-heading"><div><span class="eyebrow">THE DEVELOPER'S JOURNEY</span><h2>Nine steps. One connected application.</h2></div><button class="text-button" onclick={() => locate(0)}>Follow the journey <span aria-hidden="true">→</span></button></div>
        <JourneyChart onselect={(index) => locate(index)} />
        <p class="section-intro">Prepare data, build and connect the agent, inspect its behaviour, measure changes and deploy with controlled access. A baseline model is configured before the first run; routing is a later, explicit experiment.</p>
        <div class="lesson-grid">{#each stages as lesson, i}
          <article class="lesson-card">
            <div class="card-number">{String(i + 1).padStart(2, '0')} <span>{lesson.journey}</span></div>
            <h3>{lesson.title}</h3><p class="pain">“{lesson.pain}”</p><p class="component-label">{lesson.component}</p>
            <div class="card-links"><button onclick={() => locate(i)}>Locate in the Map <span aria-hidden="true">↗</span></button>{#each learningResources[lesson.id] as source}<a href={source.url} target="_blank" rel="noreferrer">{source.label} ↗</a>{/each}</div>
          </article>
        {/each}</div>
      </section>

      <section class="editorial-section">
        <span class="eyebrow">THREE SITUATIONS · THE SAME NINE STAGES</span><h2>Different needs should teach different lessons.</h2>
        <div class="scenario-grid">{#each scenarios as scenario, i}<article class="scenario-card"><span class="scenario-number">SCENARIO {i + 1}</span><h3>{scenario.title}</h3><p>{scenario.lesson}</p><button class="text-button" onclick={() => { scenarioId = scenario.id; scenarioChanged(); locate(0); }}>Explore this scenario →</button></article>{/each}</div>
      </section>

      <section class="editorial-section fit-section">
        <div><span class="eyebrow">WHERE IT FITS</span><h2>Keep your application at the centre.</h2><p>Bring your UI, approved service APIs and business rules. Fabric manages the selected harness. The lab connects test inputs, model access, execution evidence, evaluation and deployment around that application.</p><p>Designer prepares inputs. Relay observes execution. Helix supports evaluation, experiments and managed operations. Guardrails checks behaviour. OpenShell contains execution.</p></div>
        <dl class="fit-list"><div><dt>Your application</dt><dd>Business rules and read-only course services</dd></div><div><dt>Shared services</dt><dd>The UI, CLI and developer MCP use the same application services</dd></div><div><dt>Explicit extensions</dt><dd>Generation, routing comparisons and sandbox deployment</dd></div></dl>
      </section>

      <section class="editorial-section">
        <h2>Know what you are looking at.</h2>
        <div class="availability-grid"><div><span class="tag">TRACE WALKTHROUGH</span><h3>Follow one request</h3><p>Choose a simple scenario and advance through nine stages. Authored examples explain the flow; no observed execution is implied.</p></div><div><span class="tag muted-tag">CODE AND LOGS</span><h3>Open the relevant detail</h3><p>Application code and scenario log links stay beside the map. Source links identify the repository. Local logs identify the selected photography run; absent evidence remains explicit.</p></div><div><span class="tag muted-tag">LIVE PHOTOGRAPHY</span><h3>Run a real interaction</h3><p>Simulate a Session opens explicit photography execution. Check prerequisites, lock one test persona, then start a new saved condition.</p></div></div>
        <details class="disclosure"><summary>Prerequisites and integration limits</summary><p>The actual lab needs local persona data and configured model endpoints. Designer, Helix evaluation and Platform adapters retain their separately compatible environments. NGC scope is Singapore Nemotron Personas Extended only.</p><p>The repository retains historical photography/S$50/Saturday sandbox evidence. Historical records do not establish current live readiness. A selected new photography run supplies its own native evidence. Other scenarios need their own reviewed presets and verification. The separate dynamic Docker profile retains its recorded host-ingress limitation.</p><p>The guide reads installed originals and saved photography runs. Other scenarios remain illustrative; no source or log inspection starts inference.</p></details>
        <button class="primary large" onclick={() => locate(0)}>Explore the Integration Map <span aria-hidden="true">→</span></button>
      </section>
      <footer class="editorial-footer">Current code and selected-run evidence are distinct. Scenarios 2 and 3 remain illustrative.</footer>
    </main>
  {:else if page === 'map'}
    <section class="map-page" aria-label="Integration workspace">
      <div class="map-toolbar">
        <div class="toolbar-group"><button class:pressed={!detailed} aria-pressed={!detailed} onclick={()=>changeDetail(false)}>Simplified</button><button class:pressed={detailed} aria-pressed={detailed} onclick={()=>changeDetail(true)}>Detailed</button></div>
        <input class="map-search" aria-label="Search components" placeholder="Search components…" bind:value={search} />
        <label class="checkbox-label"><input type="checkbox" bind:checked={labels} /> Arrow labels</label>
        <div class="toolbar-group workspace-actions"><button disabled={currentScenario.id !== 'photography'} class:pressed={liveMode} aria-pressed={liveMode} title={currentScenario.id === 'photography' ? 'Open explicit live execution controls' : 'This scenario is still illustrative'} onclick={()=>{liveMode=true;stopPlayback();}}>Simulate a Session</button><button class:pressed={!liveMode} aria-pressed={!liveMode} onclick={()=>{liveMode=false;returnToPlayer();}}>Trace a Request</button></div>
        <div class="toolbar-group toolbar-layout"><button onclick={saveLayout}>Save layout</button><button onclick={resetLayout}>Reset layout</button></div>
      </div>
      <div class="workspace" bind:clientWidth={workspaceWidth} style:--inspector-width={`${panelWidth}px`}>
        <div class="graph-column">
          <div class="canvas-caption"><span>{focused?'Highlighted paths explain the selected lesson or operation; logs establish what actually ran.':'Whole architecture · select a lesson or operation to follow its information flow.'}</span><span class="illustration-label">{currentScenario.id==='photography'?'Curated photography recording':'Planned scenario · no execution evidence'}</span></div>
          <div class="graph-host"><IntegrationGraph bind:this={graph} {detailed} {scenarioId} active={activeOperations} {focused} {search} {labels} {selected} oninspect={inspect} /></div>
          <div class="graph-footer"><div class="flow-legend"><span><i class="prep"></i>Preparation</span><span><i class="request"></i>Request / response</span><span><i class="telemetry"></i>Evidence</span><span><i class="control"></i>Deployment control</span></div><span>{reducedMotion ? 'Reduced motion' : 'Arrows indicate direction'}</span></div>
          <div class="graph-context"><strong>{currentScenario.title}</strong><span>{managed?'Helix-managed OpenShell preview':currentScenario.id==='photography'?'Standalone OpenShell · no Helix':'Standalone OpenShell preview · no Helix'} · {routing==='switchyard'?'Switchyard with LiteLLM':'Fixed model via LiteLLM'} · {harness==='deepagents'?'Fabric + Deep Agents':'Fabric + Hermes'}</span></div>
        </div>
        <PanelDivider value={panelWidth} min={panelMin} max={panelMax} onresize={width=>preferredPanelWidth=width} onreset={()=>preferredPanelWidth=null} />
        <aside id="request-inspector" class="inspector trace-inspector" aria-label="Request trace and component inspector">
          <div class="trace-heading"><strong>{liveMode?'Simulate a Session':'Trace a Request'}</strong><span class="tag">{liveMode?'EXPLICIT LIVE RUN':currentScenario.id==='photography'?'CURATED DEMO':'PLANNED'}</span></div>
          <div class="scenario-setup-body"><label>Scenario<select aria-label="Scenario" bind:value={scenarioId} onchange={scenarioChanged}>{#each scenarios as scenario}<option value={scenario.id}>{scenario.title}</option>{/each}</select></label></div>
          <details class="scenario-setup" bind:open={setupOpen}>
            <summary aria-label="Toggle scenario summary"><span class="setup-summary">Scenario summary</span><span class="setup-action">{setupOpen?'Hide summary':'Show summary'}</span></summary>
            <div class="scenario-setup-body">
              <p class="preset-summary">{harness==='deepagents'?'Fabric + LangChain Deep Agents':'Fabric + Hermes'} · {currentScenario.preset.baseline}</p>
              <p class="preset-constraints">{currentScenario.preset.constraints}</p>
              <p class="preset-allocation">{currentScenario.turns.length} public {currentScenario.turns.length===1?'turn':'turns'} · {designer?'Designer scenario':'Designer enrichment skipped'} · {routing==='switchyard'?'Routing comparison planned':'Fixed routing'} · {nativeGuards?'Native Guardrails planned':'Native Guardrails omitted'} · {managed?'Helix-managed OpenShell planned':currentScenario.id==='photography'?'Standalone OpenShell verified · Helix omitted':'Standalone OpenShell planned · Helix omitted'}</p>
            </div>
          </details>
          <div class="inspector-content" data-testid="trace-content">
            {#if liveMode}
              <LiveSessionPanel bind:runId={liveRunId} bind:source={personaSource} bind:persona={lockedPersona} />
            {:else}
              <JourneyPanel {scenarioId} stageId={stage.id} {detailed} component={selected||''} operation={operationId} {focused} bind:turnIndex oninspect={inspect} onback={returnToPlayer} onfollow={()=>chooseStage(stageIndex)} onlesson={chooseStage} />
            {/if}
          </div>
          <div class="player-footer"><span class="footer-step">Step {stageIndex+1} of {stages.length}</span><div class="playback-controls"><button onclick={()=>chooseStage(stageIndex-1)} disabled={stageIndex===0}>← Back</button><button class="primary" onclick={()=>chooseStage(stageIndex+1)} disabled={stageIndex===lastStage}>Next →</button><button aria-pressed={playing} onclick={()=>{if(stageIndex===lastStage)stageIndex=0;returnToPlayer();liveMode=false;focused=true;playing=!playing;}}>{playing?'Pause':'Play'}</button><button onclick={()=>{chooseStage(0);turnIndex=0;}} aria-label="Reset playback">Reset</button></div></div>
          <div class="inspector-footer">Playback, source browsing and saved-log inspection make zero inference calls. Live execution requires Start.</div>
        </aside>
      </div>
    </section>
  {:else if page === 'datasets'}
    <DatasetsPage onchoose={() => locate(0, 'personas')} />
  {:else}
    <main class="editorial qa-page"><span class="eyebrow">QUESTIONS ABOUT THE STACK</span><h1>Understand the boundaries.</h1><p class="hero-lead">What each component does, what evidence establishes, and where your application code connects.</p><input class="qa-search" aria-label="Search questions" placeholder="Search questions, components or evidence…" bind:value={qaSearch} /><div class="qa-filters"><button class:active={qaGroup === 'all'} onclick={() => qaGroup = 'all'}>All questions</button>{#each faqGroups as group}<button class:active={qaGroup === group} onclick={() => qaGroup = group}>{group}</button>{/each}</div><div class="faq-list">{#each filteredFaqs as faq}<details class="faq"><summary>{faq.question}</summary><p>{faq.answer}</p><button class="text-button" onclick={() => locate(stages.findIndex(item => item.id === faq.stage), faq.component)}>Locate in the Map →</button></details>{/each}{#if !filteredFaqs.length}<p class="empty-search">No matching questions. Try a component name such as Fabric, Relay or Helix.</p>{/if}</div><button class="primary" onclick={() => locate(stageIndex)}>Back to the Integration Map →</button></main>
  {/if}

  {#if notice}<div class="status-toast" role="status"><span>{notice}</span><button onclick={() => notice = ''} aria-label="Dismiss notification">×</button></div>{/if}

</div>
