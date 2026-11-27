<script lang="ts">
  import {onMount} from 'svelte';
  import type {ReviewScope} from './reviewScope';
  import {conditionInfo} from './reviewScope';
  import {returnedFacts} from './courseEvidence';
  let {scope,turnIndex=$bindable(0),conditionId=$bindable(''),detailed=false}:{scope:ReviewScope;turnIndex?:number;conditionId?:string;detailed?:boolean}=$props();
  let data=$state<Record<string,any>|null>(null),error=$state(''),mounted=$state(false),loading=$state(false);
  const pretty=(v:unknown)=>typeof v==='string'?v:JSON.stringify(v,null,2);
  const number=(v:unknown)=>typeof v==='number'?v.toLocaleString(undefined,{maximumFractionDigits:3}):'Not captured';
  const spans=$derived<Record<string,any>[]>(data?.spans||[]);
  const start=$derived(Math.min(...spans.map(s=>Date.parse(s.started_at)).filter(Number.isFinite)));
  const finish=$derived(Math.max(...spans.map(s=>Date.parse(s.ended_at)).filter(Number.isFinite)));
  function depth(row:Record<string,any>){let n=0,current=row;const seen=new Set<string>();while(current.parent_available&&n<12&&!seen.has(current.id)){seen.add(current.id);const parent=spans.find(p=>p.id===current.parent_id);if(!parent)break;current=parent;n++;}return n;}
  onMount(()=>{mounted=true;});
  $effect(()=>{
    const {scenarioId,conditionId:cid,publicTurn,purpose}=scope;if(!mounted)return;
    loading=false;error='';data=null;if(!cid)return;
    const controller=new AbortController();loading=true;
    const query=new URLSearchParams({scenario_id:scenarioId,condition_id:cid});
    if(purpose==='baseline')query.set('public_turn',String(publicTurn));
    void fetch(`/api/journey/execution?${query}`,{signal:controller.signal}).then(async response=>{
      const value=await response.json();if(!response.ok)throw new Error(value.error||'Execution evidence could not be read.');
      if(value.scenario_id!==scenarioId||value.condition?.id!==cid)throw new Error('Execution evidence belongs to another condition.');
      if(!controller.signal.aborted)data=value;
    }).catch(e=>{if(!controller.signal.aborted)error=e.message;}).finally(()=>{if(!controller.signal.aborted)loading=false;});
    return()=>controller.abort();
  });
</script>

<div class="execution-viewer" data-testid="execution-viewer" data-condition={scope.conditionId}>
  <p>Start with a question about the answer: which course facts did the advisor retrieve? Open a tool record below to compare its request with the returned facts, then follow its place in the execution.</p>
  {#if scope.scenarioId==='dreamjob'&&data?.conditions?.length}
    <label>Execution condition<select aria-label="Execution condition" value={scope.conditionId||''} onchange={event=>{conditionId=event.currentTarget.value;turnIndex=0;}}>{#each data.conditions.filter((c:Record<string,any>)=>c.purpose!=='managed') as c}<option value={c.id}>{conditionInfo(c.purpose).label}</option>{/each}</select></label>
  {/if}
  {#if scope.purpose==='baseline'&&scope.scenarioId!=='photography'}<label>Public turn<select aria-label="Trace public turn" bind:value={turnIndex}>{#each Array(scope.scenarioId==='dreamjob'?3:2) as _,i}<option value={i}>Turn {i+1}</option>{/each}</select></label>{/if}
  {#if loading}<p role="status">Reading this condition’s saved execution…</p>
  {:else if error}<p role="alert">{error}</p>
  {:else if data}
    <p class="observation"><strong>{conditionInfo(data.condition.purpose).label}:</strong> {spans.length} displayed native scopes; {data.condition_span_count} in this condition. {data.correlation.explanation}</p>
    {#each data.tools as tool}<article class="tool-fact"><h4>{tool.name} · {tool.status}</h4><p>{returnedFacts(tool,detailed)}</p><details class="record"><summary>{tool.name} · {tool.status||'recorded result'}</summary><h4>Tool input</h4><pre>{pretty(tool.arguments??tool.input??'Not captured')}</pre><h4>Returned result</h4><pre>{pretty(tool.result??tool.output??'Not captured')}</pre></details></article>{/each}
    <h4>Recorded execution and timing</h4>
    <p class="small">Indentation follows captured parent IDs. A nested agent scope can describe a wrapper around a request; it does not establish that a subagent was spawned.</p>
    {#each spans as span}<details class="record span" style:margin-left={`${depth(span)*12}px`}>
      <summary><span>{span.category} · {span.name}</span><small>{span.status} · {number(span.duration_ms)} ms</small></summary>
      {#if Number.isFinite(start)&&Number.isFinite(finish)&&finish>start}<div class="timeline" aria-label="Recorded position in this condition"><i style:margin-left={`${Math.max(0,(Date.parse(span.started_at)-start)/(finish-start)*95)}%`} style:width={`${Math.max(.5,Math.min(100,(Number(span.duration_ms)||0)/(finish-start)*100))}%`}></i></div>{/if}
      <dl><div><dt>Native source</dt><dd>{span.source}</dd></div><div><dt>Start → end</dt><dd>{span.started_at} → {span.ended_at}</dd></div><div><dt>Native ID</dt><dd><code>{span.id}</code></dd></div><div><dt>Parent</dt><dd>{span.parent_id||'No parent recorded'}{#if !span.parent_available} · parent missing from this export{/if}</dd></div></dl>
      {#if span.model}<p>Model: {span.model}</p>{/if}
      {#if span.input!==undefined}<h4>Captured input</h4><pre>{pretty(span.input)}</pre>{/if}
      {#if span.output!==undefined}<h4>Captured output</h4><pre>{pretty(span.output)}</pre>{/if}
      {#if span.payload_availability}<p class="small">{span.payload_availability}</p>{/if}
    </details>
    {:else}<p>{data.correlation.status==='application-only'?'There is no native agent subtree for this clarification.':'No native scopes are published for this condition.'}</p>{/each}
    <h4>Model usage for this condition</h4>
    <p>The gateway counts model requests for the advisor and, where applicable, UserSim’s learner and judges. This accounting has separate IDs from native Relay scopes. The table is condition-wide even when one public turn is selected.</p>
    <div class="table-wrap"><table><thead><tr><th>Role</th><th>Requests</th><th>Known tokens</th><th>Request duration</th></tr></thead><tbody>{#each data.usage.summary.by_role as role}<tr><td>{role.role==='assistant'?'Advisor':role.role==='user'?'UserSim learner':role.role==='judge'?'UserSim judges':role.role}</td><td>{role.calls}</td><td>{number(role.known_tokens)}{#if role.unknown_usage_calls} + {role.unknown_usage_calls} unknown{/if}</td><td>{number(role.model_request_ms)} ms{#if role.unknown_latency_calls} + {role.unknown_latency_calls} unknown{/if}</td></tr>{/each}</tbody></table></div>
    {#if data.run_id==='94e49df8-7dfa-445b-9614-d79e31f2c024'&&data.condition.purpose==='baseline'}<p>UserSim request 2 checks the generated learner question before it reaches the advisor. After the advisor replies, UserSim request 5 judges the delivered answer’s quality. We identify these purposes from the saved activation order and matching usage. The later nine application assertions run separately and make no model requests.</p>{/if}
    <p class="small">{data.usage.notice} Summed request durations are not end-to-end response time. No monetary cost or performance threshold was recorded.</p>
    <details><summary>Individual model-request accounting · {data.usage.summary.calls} requests</summary>{#each data.usage.records as call}<p class="small">Global request {call.call} · {call.role} · {call.status} · {call.selected_model||call.requested_model||'model unknown'} · {number(call.usage?.total_tokens)} tokens · {number(call.latency_ms)} ms</p>{/each}</details>
    <h4>What this recording establishes</h4><ul>{#each data.coverage as row}<li>{row.capability}: {row.status.replaceAll('-',' ')}{row.explanation?`. ${row.explanation}`:''}</li>{/each}</ul>
    <h4>Open the historical trace in Phoenix</h4>
    <p>Phoenix shows the retained advisor model and tool details on this machine. It imports the original execution times; viewing it does not run the advisor again.</p>
    <p class="small">Phoenix may show estimated costs using its bundled token prices. Those are pricing estimates, not measured billing for this recording.</p>
    {#if data.phoenix.available&&data.phoenix.url}<a href={data.phoenix.url} target="_blank" rel="noreferrer">Open this condition in local Phoenix ↗</a>{:else}<p class="small">{data.phoenix.notice||'Local Phoenix is not running or this condition has not been imported. The in-app records above remain available.'}</p>{/if}
  {/if}
</div>

<style>
  .execution-viewer{min-width:0}.execution-viewer p{line-height:1.75}.record{border:1px solid var(--line);border-radius:4px;padding:11px;margin:10px 0}.record summary{display:flex;justify-content:space-between;gap:10px;font-size:12px}.record small{font-size:10px;color:var(--muted)}h4{font-size:13px;margin:18px 0 9px}pre{max-height:340px;overflow:auto;background:#f6f8fa;padding:12px;font-size:11px}dl{font-size:11px}dl div{display:grid;grid-template-columns:95px minmax(0,1fr);gap:10px;padding:7px 0}dt{color:var(--muted)}dd{margin:0;overflow-wrap:anywhere}.small{font-size:11px}.observation{font-size:12px}.timeline{height:8px;margin-top:12px;background:#eef2f5;overflow:hidden}.timeline i{display:block;height:100%;background:var(--teal)}.table-wrap{overflow:auto}table{width:100%;border-collapse:collapse;font-size:11px;text-align:left}th,td{padding:8px;border-bottom:1px solid var(--line)}ul{font-size:12px;line-height:1.75;padding-left:20px}
</style>
