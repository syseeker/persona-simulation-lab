<script lang="ts">
  import {onMount} from 'svelte';
  import {stages} from './content';
  import {componentUsed} from './lessonArchitecture';
  import type {LessonId} from './lessonArchitecture';
  import {lessonPage} from './teaching/lessons';
  import {simplePage} from './teaching/concepts';
  import {detailedPage} from './teaching/libraries';
  import InlineTeaching from './teaching/InlineTeaching.svelte';
  import OperationObservation from './teaching/OperationObservation.svelte';
  import LessonFacts from './LessonFacts.svelte';
  import type {ReviewScope} from './reviewScope';
  type Data=Record<string,any>;
  let {scenarioId,stageId,scope,deploymentMode=$bindable<'standalone'|'managed'>('standalone'),detailed=false,component='',operation='',focused=false,turnIndex=$bindable(0),conditionId=$bindable(''),
    onback=()=>{},onfollow=()=>{},oncontext=(_value:Data|null)=>{},onmetadata=(_id:string,_condition?:string)=>{}}:
    {scenarioId:string;stageId:string;scope:ReviewScope;deploymentMode?:'standalone'|'managed';detailed?:boolean;component?:string;operation?:string;focused?:boolean;turnIndex?:number;conditionId?:string;
      onback?:()=>void;onfollow?:()=>void;oncontext?:(value:Data|null)=>void;onmetadata?:(id:string,condition?:string)=>void}=$props();
  let context=$state<Data|null>(null),persona=$state<Data|null>(null),metadata=$state<Data|null>(null),error=$state(''),loading=$state(false),personaLoading=$state(false),mounted=$state(false);
  const step=$derived(stages.findIndex(s=>s.id===stageId));
  const evidenceCondition=$derived(scope.conditionId||'');
  const page=$derived(component?(detailed?detailedPage(scenarioId,component,operation||undefined):simplePage(scenarioId,component,operation||undefined)):lessonPage(scenarioId,stageId as LessonId,detailed));
  async function read(action:string,scenario:string,signal:AbortSignal){
    const response=await fetch(`/api/journey/${action}?scenario_id=${encodeURIComponent(scenario)}`,{signal});
    const value=await response.json();if(!response.ok)throw new Error(value.error||'The recording could not be read.');return value;
  }
  onMount(()=>{mounted=true;});
  $effect(()=>{
    const scenario=scenarioId;if(!mounted)return;
    const controller=new AbortController();context=null;persona=null;metadata=null;error='';loading=true;personaLoading=true;oncontext(null);
    void read('lesson',scenario,controller.signal).then(value=>{if(!controller.signal.aborted){context=value;oncontext(value);}}).catch(e=>{if(!controller.signal.aborted)error=e.message;}).finally(()=>{if(!controller.signal.aborted)loading=false;});
    void read('demo-persona',scenario,controller.signal).then(value=>{if(!controller.signal.aborted)persona=value;}).catch(e=>{if(!controller.signal.aborted)persona={available:false,notice:e.message};}).finally(()=>{if(!controller.signal.aborted)personaLoading=false;});
    void read('metadata',scenario,controller.signal).then(value=>{if(!controller.signal.aborted)metadata=value;}).catch(()=>{});
    return()=>controller.abort();
  });
</script>

<div class="journey-evidence" data-testid="journey-panel" data-scenario={scenarioId} data-destination={component?(operation?'action-or-operation':'block'):'lesson'}>
  <div class="step-meta"><span data-testid="step-counter">Step {step+1} of 9</span><span>{detailed?'DEVELOPER VIEW':'CONCEPT VIEW'}</span></div>
  {#if component}<button class="back-link" onclick={onback}>← Back to step {step+1} · {stages[step].title}</button>{/if}
  <h2 class="step-title">{page.title}</h2>
  <p class="teaching-introduction"><InlineTeaching text={page.intro} {context} {metadata} {scenarioId} conditionId={evidenceCondition} {onmetadata} /></p>
  {#if scenarioId==='dreamjob'&&stageId==='deploy'&&!component}
    <label>Deployment<select aria-label="Deployment condition" bind:value={deploymentMode}><option value="standalone">Standalone OpenShell · original run</option><option value="managed">Helix-managed · fresh session</option></select></label>
    <p class="small muted">The diagram, policy and results below all belong to the selected deployment.</p>
  {/if}
  {#if error}<p class="operation-error" role="alert">{error}</p>{/if}
  {#if loading}<p role="status" class="small muted">Loading this scenario's saved observations…</p>{/if}
  {#if component&&detailed&&!componentUsed(component,scenarioId)}<p class="not-used">This scenario does not use this component. The explanation describes the integration boundary; there is no matching execution to inspect.</p>{/if}
  {#if !focused}<button class="text-button follow-step" onclick={onfollow}>Follow this step on the map →</button>{/if}
  {#each page.sections as section}
    <section class="teaching-section">
      {#if section.heading}<h3>{section.heading}</h3>{/if}
      {#each section.paragraphs||[] as paragraph}<p><InlineTeaching text={paragraph} {context} {metadata} {scenarioId} conditionId={evidenceCondition} {onmetadata} /></p>{/each}
      {#if section.flow}<ol class="teaching-flow">{#each section.flow as item}<li><InlineTeaching text={item} {context} {metadata} {scenarioId} conditionId={evidenceCondition} {onmetadata} /></li>{/each}</ol>{/if}
      {#if section.rows}<dl>{#each section.rows as [label,value]}<div><dt>{label}</dt><dd><InlineTeaching text={value} {context} {metadata} {scenarioId} conditionId={evidenceCondition} {onmetadata} /></dd></div>{/each}</dl>{/if}
      {#if section.observation}<LessonFacts stageId={section.observation} {scope} {scenarioId} {context} {persona} {personaLoading} {detailed} bind:turnIndex bind:conditionId />{/if}
    </section>
  {/each}
  {#if component&&operation&&detailed}<OperationObservation {operation} {scenarioId} {context} {turnIndex} conditionId={evidenceCondition} />{/if}
</div>

<style>
.journey-evidence{min-width:0}.teaching-section{padding:18px 0;border-bottom:1px solid var(--line)}.teaching-section h3{font-size:13px;letter-spacing:.02em;margin:0 0 12px}.teaching-section p{margin:10px 0}.not-used{background:#faf8f3;padding:12px;border-left:2px solid #b8a98b}.operation-error{color:#8d3e2a;padding:12px;background:#fff6f0;border:1px solid #e7c9b8;border-radius:5px}dl{font-size:12px}dl div{display:grid;grid-template-columns:100px minmax(0,1fr);gap:12px;padding:8px 0;border-bottom:1px solid var(--line)}dt{color:var(--muted)}dd{margin:0;overflow-wrap:anywhere}.small{font-size:11px}.follow-step{margin-top:8px}.teaching-introduction{line-height:1.75}.teaching-flow{padding-left:22px;line-height:1.7}.teaching-flow li{padding:7px 0}
</style>
