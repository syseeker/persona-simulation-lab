<script lang="ts">
  import {onMount,untrack} from 'svelte';
  import {renderMarkdown} from './markdown';
  type Data=Record<string,any>;
  let {runId=$bindable<string|null>(null),source=$bindable('ngc'),persona=$bindable<Data|null>(null)}:
    {runId?:string|null;source?:string;persona?:Data|null}=$props();
  let readiness=$state<Data|null>(null),trace=$state<Data|null>(null),busy=$state(''),error=$state(''),mounted=$state(false);
  const active=$derived(trace&&!['completed','failed','cancelled','interrupted'].includes(trace.run.status));
  async function api(action:string,data?:Data,signal?:AbortSignal){
    const write=['sample','start','cancel','recover'].includes(action);
    const response=await fetch('/api/journey/'+action+(!write&&data?'?'+new URLSearchParams(data):''),write?
      {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data||{}),signal}:{signal});
    const result=await response.json();if(!response.ok)throw new Error(result.error||'The operation failed.');return result;
  }
  async function action(label:string,work:()=>Promise<void>){if(busy)return;busy=label;error='';try{await work();}catch(e){error=e instanceof Error?e.message:'The operation failed.';}finally{busy='';}}
  onMount(()=>{mounted=true;void action('Checking prerequisites',async()=>{readiness=await api('readiness');});});
  $effect(()=>{
    const id=runId;if(!mounted||!id)return;
    const controller=new AbortController();let timer:ReturnType<typeof setTimeout>;
    async function refresh(){try{const value=await api('trace',{run_id:id},controller.signal);if(controller.signal.aborted)return;trace=value;
      if(!['completed','failed','cancelled','interrupted'].includes(value.run.status))timer=setTimeout(refresh,1500);
    }catch(e){if(!controller.signal.aborted)error=e instanceof Error?e.message:'Run unavailable.';}}
    void refresh();return()=>{controller.abort();clearTimeout(timer);};
  });
  $effect(()=>{if(persona&&persona.source!==source)untrack(()=>persona=null);});
  const text=(value:unknown):string=>Array.isArray(value)?value.join(', '):value&&typeof value==='object'?Object.entries(value).map(([k,v])=>`${k}: ${String(v)}`).join(' · '):String(value??'Unknown');
</script>

<section data-testid="live-session">
  <span class="panel-eyebrow">NEW PHOTOGRAPHY CONDITION</span><h2>Run one real conversation.</h2>
  <p>UserSim generates one public learner turn. Persistent Fabric with Deep Agents and the course tools runs inside a fresh OpenShell sandbox. The host gateway uses fixed LiteLLM access.</p>
  <p class="small muted">This creates new results. Trace a Request always returns to the curated demo; it does not relabel this live run as the recording.</p>
  {#if error}<p class="operation-error" role="alert">{error}</p>{/if}{#if busy}<p role="status">{busy}…</p>{/if}
  <button onclick={()=>action('Checking prerequisites',async()=>{readiness=await api('readiness');})} disabled={!!busy}>Check prerequisites</button>
  {#if readiness}<dl>
    <div><dt>OpenShell gateway</dt><dd>{readiness.native.gateway?'Reachable':'Unavailable'}</dd></div>
    <div><dt>Reusable agent image</dt><dd>{readiness.native.image?'Installed':'Build required'}</dd></div>
    <div><dt>LiteLLM fixed / simulator aliases</dt><dd>{readiness.proxy.fixed_alias_available&&readiness.proxy.support_alias_available?'Available':'Unavailable'}</dd></div>
    <div><dt>Workload ownership</dt><dd>{readiness.active?'Active/unresolved run retained':'Available'}</dd></div>
  </dl>{#if readiness.native.reason}<p class="small muted">{readiness.native.reason}</p>{/if}{/if}
  <label>Test persona source<select aria-label="Live test persona source" bind:value={source}><option value="ngc">Singapore NGC Extended · OCEAN source traits</option><option value="hf-profile-only">HF Singapore · profile-only</option></select></label>
  <button onclick={()=>action('Sampling and locking one original',async()=>{persona=await api('sample',{source});})} disabled={!!busy||!!active}>Choose a random test persona</button>
  {#if persona}<div class="io-grid"><h3>Locked original</h3><dl>{#each Object.entries(persona.summary||{}) as [key,value]}<div><dt>{key.replaceAll('_',' ')}</dt><dd>{text(value)}</dd></div>{/each}</dl><p class="small muted">Revision {persona.source_revision}. This profile is simulator context; the advisor receives only public messages.</p></div>{/if}
  <p class="small muted">Beginner photography · Saturday · S$50 before funding. One public turn, 120 total model calls, 1,024 output tokens per call and four advisor tool rounds. Designer generation, Switchyard, native Guardrails and Helix are omitted.</p>
  <button class="primary" disabled={!!busy||!readiness?.ready||!persona||!!active} onclick={()=>action('Starting photography',async()=>{
    const run=await api('start',{spec:{scenario_id:'photography',source:persona!.source,source_id:persona!.source_id,original_sha256:persona!.original_sha256}});runId=run.run_id;
  })}>Start live photography simulation</button>
  {#if trace}
    <p class="run-status"><strong>{trace.run.status}</strong> · {trace.run.calls} of 120 model calls · cleanup {trace.run.cleanup_confirmed?'confirmed':'pending'}</p>
    {#if trace.run.error}<p class="operation-error">{trace.run.error}</p>{/if}
    {#if active}<button disabled={!!busy} onclick={()=>action('Requesting cancellation',async()=>{await api('cancel',{run_id:runId});})}>Cancel this run</button>{/if}
    {#if trace.run.recovery_required||trace.run.ownership_notice}<p class="operation-error">{trace.run.ownership_notice||'Cleanup needs recovery. New execution remains blocked.'}</p><button disabled={!!busy} onclick={()=>action('Recovering this native condition',async()=>{await api('recover',{run_id:runId});trace=await api('trace',{run_id:runId});readiness=await api('readiness');})}>Recover and verify cleanup</button>{/if}
    {#each trace.conversation||[] as message}<article class="conversation-message"><span>{message.role==='user'?'LEARNER':'ADVISOR'} · LIVE RUN</span><div>{@html renderMarkdown(String(message.content||'No public content saved.'))}</div></article>{/each}
    <p class="small muted">Run {trace.run.run_id}. Leaving this panel does not cancel the workload. This run remains separate from the curated review pack.</p>
  {/if}
</section>
<style>
  dl{font-size:12px;margin:16px 0}dl div{display:flex;justify-content:space-between;gap:14px;padding:8px 0;border-bottom:1px solid var(--line)}dd{margin:0;text-align:right;overflow-wrap:anywhere}button{margin-bottom:8px}.operation-error{color:#8d3e2a;padding:12px;background:#fff6f0;border:1px solid #e7c9b8;border-radius:5px;overflow-wrap:anywhere}.run-status{padding:12px;border:1px solid var(--line);border-radius:5px;font-size:12px}
</style>
