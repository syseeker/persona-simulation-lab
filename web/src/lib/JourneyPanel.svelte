<script lang="ts">
  import {onMount} from 'svelte';
  import {stages} from './content';
  import {componentById,operationById,componentTitle,componentUsed,lessonFor,lessonsUsing,architectureUrl} from './lessonArchitecture';
  import LessonFacts from './LessonFacts.svelte';
  import ReviewLinks from './ReviewLinks.svelte';
  type Data=Record<string,any>;
  let {scenarioId,stageId,detailed=false,component='',operation='',focused=false,turnIndex=$bindable(0),
    oninspect=(_component:string,_operation?:string)=>{},onback=()=>{},onfollow=()=>{},onlesson=(_index:number)=>{}}:
    {scenarioId:string;stageId:string;detailed?:boolean;component?:string;operation?:string;focused?:boolean;turnIndex?:number;
      oninspect?:(c:string,o?:string)=>void;onback?:()=>void;onfollow?:()=>void;onlesson?:(i:number)=>void}=$props();
  let context=$state<Data|null>(null),persona=$state<Data|null>(null),error=$state(''),loading=$state(false),personaLoading=$state(false),mounted=$state(false);
  const lesson=$derived(lessonFor(scenarioId,stageId));
  const selectedComponent=$derived(componentById[component]);
  const selectedOperation=$derived(operationById[operation]);
  const selectedOps=$derived(selectedOperation?[operation]:selectedComponent?selectedComponent.operations.map(o=>o.id):lesson.operations);
  const groups=$derived([...new Set(selectedOps.map(id=>operationById[id].component))]);
  const relatedLessons=$derived(component?lessonsUsing(component,scenarioId):[]);
  const reviewChecks=$derived(selectedComponent?selectedComponent.operations.map(op=>op.check):lesson.checks);
  const step=$derived(stages.findIndex(s=>s.id===stageId));
  const factsStage=$derived(selectedComponent?({personas:'persona',situation:'situation',designer:'situation',usersim:operation==='usersim.prepare'||operation==='usersim.probe'?'situation':'run',fabric:operation==='fabric.invoke'||operation==='fabric.result'?'run':'build',harness:'run',mcp:'investigate',catalogue:'investigate',gateway:'routing',litellm:'routing',routing:'routing',relay:'investigate',records:'investigate',checks:'evaluate',helix:'evaluate',guardrails:'safeguards',openshell:'deploy',platform:'deploy'} as Record<string,string>)[component]:stageId);
  async function read(action:string,scenario:string,signal:AbortSignal){
    const response=await fetch(`/api/journey/${action}?scenario_id=${encodeURIComponent(scenario)}`,{signal});
    const value=await response.json();if(!response.ok)throw new Error(value.error||'The recording could not be read.');return value;
  }
  onMount(()=>{mounted=true;});
  $effect(()=>{
    const scenario=scenarioId;if(!mounted)return;
    const controller=new AbortController();context=null;persona=null;error='';loading=true;personaLoading=true;
    void read('lesson',scenario,controller.signal).then(value=>{if(!controller.signal.aborted)context=value;}).catch(e=>{if(!controller.signal.aborted)error=e.message;}).finally(()=>{if(!controller.signal.aborted)loading=false;});
    void read('demo-persona',scenario,controller.signal).then(value=>{if(!controller.signal.aborted)persona=value;}).catch(e=>{if(!controller.signal.aborted)persona={available:false,notice:e.message};}).finally(()=>{if(!controller.signal.aborted)personaLoading=false;});
    return()=>controller.abort();
  });
  function operationStatus(id:string){
    const c=operationById[id].component;
    if(!componentUsed(c,scenarioId))return 'Not used in this preset';
    if(context?.state!=='recorded')return 'Planned · no scenario evidence';
    if(['mcp.details','mcp.compare'].includes(id))return 'Available tool · not called in this recording';
    if(id==='persona.select')return 'Locked result recorded · sampling details not captured';
    return operationById[id].proof.some(name=>context?.artifacts?.some((a:Data)=>a.path===name))?'Recorded · inspect the matching proof':'Evidence unavailable';
  }
</script>

<div class="journey-evidence" data-testid="journey-panel" data-scenario={scenarioId}>
  <div class="step-meta"><span data-testid="step-counter">Step {step+1} of 9</span><span>{detailed?'DEVELOPER VIEW':'CONCEPT VIEW'}</span></div>
  {#if component}<button class="back-link" onclick={onback}>← Back to step {step+1} · {stages[step].title}</button>{/if}
  <h2 class="step-title">{selectedOperation?.title|| (selectedComponent?componentTitle(component,scenarioId):stages[step].title)}</h2>
  {#if component}<p class="component-context">{componentTitle(component,scenarioId)} · lesson position preserved</p>{/if}
  <div class="record-state" data-testid="record-state">
    {#if loading}<span role="status">Loading this scenario’s review context…</span>
    {:else if context?.state==='recorded'}<strong>Recorded photography demo</strong><span>Run {context.run_id.slice(0,8)} · {context.trace.run.status} · cleanup {context.trace.run.cleanup_confirmed?'confirmed':'not confirmed'}</span>
    {:else}<strong>{context?.state==='unavailable'?'Demo unavailable':'Planned scenario'}</strong><span>{context?.notice||'No verified recording is loaded.'}</span>{/if}
  </div>
  {#if error}<p class="operation-error" role="alert">{error} No recording was substituted.</p>{/if}
  {#if context?.trace?.run?.error}<p class="operation-error" role="alert">Recorded failure: {context.trace.run.error}</p>{/if}
  {#if context?.trace?.developer_review}<p class="operation-error">Developer review: {context.trace.developer_review.summary} Original results remain unchanged.</p>{/if}
  {#if !focused}<button class="text-button follow-step" onclick={onfollow}>Follow this step on the map →</button>{/if}
  <section class="teaching-section"><h3>Why this matters</h3><p>{selectedOperation?.concept||selectedComponent?.purpose||lesson.why}</p></section>
  <section class="teaching-section"><h3>In this scenario</h3>
    {#if component&&!componentUsed(component,scenarioId)}<p class="not-used">This component is not used in this preset. Its architecture is shown for context; there is no matching execution or native decision.</p>
    {:else}<p>{selectedOperation?.input||(!component?lesson.input:selectedComponent.purpose)}</p><LessonFacts stageId={factsStage} {scenarioId} {context} {persona} {personaLoading} {detailed} bind:turnIndex />{/if}
    {#if !component}<p class="output"><strong>Result to look for:</strong> {lesson.output}</p>{/if}
  </section>
  <section class="teaching-section"><h3>How it works</h3>
    <p>{selectedOperation?selectedOperation.owner:selectedComponent?selectedComponent.operations.map(op=>op.title).join(' → '):lesson.action}</p>
    <p class="design-choice"><strong>Design choice.</strong> {selectedOperation?.concept||selectedComponent?.operations[0].concept||lesson.design}</p>
    {#if !component&&lesson.notUsed}<p class="small muted">{lesson.notUsed}</p>{/if}
    {#if detailed}
      <ol class="operation-path" aria-label="Application and library operations">
        {#each selectedOps as id}
          {@const op=operationById[id]}
          <li data-operation={id}>
            <details open={id===operation||selectedOps.length===1}>
              <summary><span><strong>{componentTitle(op.component,scenarioId)}</strong> · {op.title}<small>{operationStatus(id)}</small></span></summary>
              <p class="small muted">{op.owner}</p><p>{op.concept}</p>
              <dl><div><dt>Input</dt><dd>{op.input}</dd></div><div><dt>Configuration</dt><dd>{op.config}</dd></div><div><dt>Output</dt><dd>{op.output}</dd></div></dl>
              <p><strong>Cross-check:</strong> {op.check}</p>
              {#if componentUsed(op.component,scenarioId)}<ReviewLinks operation={id} {scenarioId} {context} detailed />{:else}<p class="small muted">No application call or scenario log is claimed for this unused component.</p><a href={architectureUrl(op.component,scenarioId)} target="_blank" rel="noreferrer">Library architecture ↗</a>{/if}
              {#if component!==op.component||operation!==id}<button class="text-button" onclick={()=>oninspect(op.component,id)}>Locate this operation on the map →</button>{/if}
            </details>
          </li>
        {/each}
      </ol>
    {:else}
      <ol class="concept-path">{#each groups as id}<li><button class="text-button" onclick={()=>oninspect(id)}>{componentById[id].simple} →</button><p>{componentById[id].purpose}</p></li>{/each}</ol>
      {#if selectedOperation}<dl><div><dt>Receives</dt><dd>{selectedOperation.input}</dd></div><div><dt>Returns</dt><dd>{selectedOperation.output}</dd></div></dl>{/if}
    {/if}
  </section>
  <section class="teaching-section"><h3>Check your implementation</h3>
    {#if selectedOperation}<p>{selectedOperation.check}</p>{:else}<ul>{#each reviewChecks as check}<li>{check}</li>{/each}</ul>{/if}
    {#if !detailed}{#each groups as id}{@const first=selectedOps.find(key=>operationById[key].component===id)!}<div class="component-reference"><h4>{componentTitle(id,scenarioId)}</h4>{#if componentUsed(id,scenarioId)}<ReviewLinks operation={first} {scenarioId} {context} />{:else}<span class="small muted">Not used · no scenario log</span><a href={architectureUrl(id,scenarioId)} target="_blank" rel="noreferrer">Library architecture ↗</a>{/if}</div>{/each}{/if}
    {#if detailed}<p class="small muted">Open an operation above for its exact application call, configuration and scenario log. Compare IDs and expected fields with your own output; no partial code or raw payload is embedded here.</p>{/if}
    {#if component&&relatedLessons.length}<p class="small muted">This component participates in:</p><div class="related-lessons">{#each relatedLessons as id}{@const index=stages.findIndex(s=>s.id===id)}<button class="text-button" onclick={()=>onlesson(index)}>Step {index+1} · {stages[index].title}</button>{/each}</div>{/if}
    {#if context?.state==='recorded'}<p class="provenance small muted">This is one fixed run. Native records and clearly labelled projections remain separate. Code links identify committed application files; each operation reports whether its source hash matches the recording.</p>{/if}
  </section>
</div>

<style>
  .journey-evidence{min-width:0}.teaching-section{padding:18px 0;border-bottom:1px solid var(--line)}.teaching-section h3{font-size:13px;letter-spacing:.02em;margin:0 0 12px}.teaching-section p{margin:10px 0}.record-state{display:flex;flex-direction:column;gap:5px;padding:10px 12px;border:1px solid var(--line);border-radius:5px;font-size:11px;margin:14px 0}.record-state span{color:var(--muted)}.component-context{font-size:11px;color:var(--muted)}.design-choice{border-left:2px solid #9ac4b5;padding-left:12px;font-size:12px}.output{font-size:12px}.not-used{background:#faf8f3;padding:12px;border-left:2px solid #b8a98b}.operation-path{padding-left:20px;margin:16px 0}.operation-path>li{padding:10px 0;border-top:1px solid var(--line)}.operation-path summary{font-size:12px}.operation-path summary small{display:block;font-size:10px;color:var(--muted);margin-top:5px}.operation-path summary strong{color:var(--teal)}.concept-path{padding-left:20px}.concept-path li{margin:12px 0}.concept-path p{font-size:12px}.concept-path button{text-align:left}.component-reference{padding:10px 0;border-top:1px solid var(--line)}h4{font-size:12px;margin:4px 0}.related-lessons{display:flex;gap:8px;flex-wrap:wrap}.related-lessons button{font-size:11px;text-align:left}.provenance{margin-top:20px!important}.operation-error{color:#8d3e2a;padding:12px;background:#fff6f0;border:1px solid #e7c9b8;border-radius:5px}dl{font-size:12px}dl div{display:grid;grid-template-columns:100px minmax(0,1fr);gap:12px;padding:8px 0;border-bottom:1px solid var(--line)}dt{color:var(--muted)}dd{margin:0;overflow-wrap:anywhere}.small{font-size:11px}.follow-step{margin-top:8px}
</style>
