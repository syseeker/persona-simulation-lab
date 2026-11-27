<script lang="ts">
  import {renderMarkdown} from './markdown';
  import {scenarios} from './content';
  import RecordedObservations from './RecordedObservations.svelte';
  import type {ReviewScope} from './reviewScope';
  let {stageId,scenarioId,context,scope,persona,personaLoading=false,detailed=false,turnIndex=$bindable(0),conditionId=$bindable('')}:
    {stageId:string;scenarioId:string;scope:ReviewScope;context:Record<string,any>|null;persona:Record<string,any>|null;personaLoading?:boolean;detailed?:boolean;turnIndex?:number;conditionId?:string}=$props();
  const trace=$derived(context?.trace),extra=$derived(context?.context||{});
  const scenario=$derived(scenarios.find(s=>s.id===scenarioId)!);
  const planned=$derived(context?.state!=='recorded');
  const opening=$derived(trace?.conversation?.find((m:Record<string,any>)=>m.role==='user'));
  const config=$derived(extra['framework-config.json']);
  const sim=$derived(extra['usersim-setup.json']);
  const overlay=$derived(extra['designer-output.json']);
  const routing=$derived(extra['routing-comparison.json']);
  $effect(()=>{if(stageId==='routing'&&routing?.conditions?.length&&!routing.conditions.some((c:Record<string,any>)=>c.condition_id===conditionId))conditionId=routing.conditions[0].condition_id;});
  const selectedRoutingCondition=$derived(routing?.conditions?.find((c:Record<string,any>)=>c.condition_id===conditionId)||routing?.conditions?.[0]);
  const managed=$derived(extra['platform-condition.json']);
  const calls=$derived<Record<string,any>[]>(trace?.usage?.records||[]);
  const scopes=$derived<Record<string,any>[]>(trace?.relay?.scopes||[]);
  const tools=$derived<Record<string,any>[]>(trace?.tools||[]);
  const invocation=$derived(extra['fabric-invocations.json']?.find((r:Record<string,any>)=>r.public_turn===turnIndex+1));
  const turnTools=$derived<Record<string,any>[]>(invocation?.tool_scope_uuids?tools.filter(t=>invocation.tool_scope_uuids.includes(t.scope_uuid)):[]);
  const applicationTurn=$derived(extra['application-turns.json']?.find((r:Record<string,any>)=>r.public_turn===turnIndex+1));
  const turns=$derived<number[]>([...new Set<number>((trace?.conversation||[]).filter((m:Record<string,any>)=>m.role==='user').map((m:Record<string,any>)=>Number(m.turn)))]);
  const text=(value:unknown):string=>value===null||value===undefined?'Unknown':Array.isArray(value)?value.map(text).join(', '):typeof value==='object'?Object.entries(value).map(([k,v])=>`${k.replaceAll('_',' ')}: ${text(v)}`).join(' · '):String(value);
  function depth(scope:Record<string,any>){let n=0,current=scope;const seen=new Set<string>();while(current.parent_available&&n<8&&!seen.has(current.uuid)){seen.add(current.uuid);const parent=scopes.find(s=>s.uuid===current.parent_uuid);if(!parent)break;current=parent;n++;}return n;}

</script>

<div class="scenario-facts" data-testid="scenario-facts">
  {#if stageId==='persona'}
    {#if personaLoading}<p role="status">Finding the exact original in the installed dataset…</p>
    {:else if persona?.available}
      <article class="profile" data-testid="selected-persona"><h4>{persona.name}</h4><p class="small muted">Selected original synthetic test person · {persona.source==='ngc'?'Singapore NGC Extended':'HF profile-only'} · revision {persona.revision}</p>
        <p class="small">{#if persona.preferred_english_name}{persona.preferred_english_name} is this profile’s preferred English name; {persona.structured_name} is its structured name. Both identify the same selected original.{/if}</p>
        <dl>{#each persona.fields as field}<div><dt>{field.label}</dt><dd>{text(field.value)}</dd></div>{/each}</dl>
        {#if persona.traits?.length}<details><summary>Original behavioural traits used by the simulator</summary>{#each persona.traits as trait}<p><strong>{trait.name}</strong> · {trait.label}<br /><span class="small muted">{trait.description}</span></p>{/each}<p class="small muted">Synthetic traits shape the test; they are not assessments of real residents.</p></details>{/if}
      </article>
    {:else}<p class="unavailable">{persona?.notice||'The selected original is unavailable. No substitute profile is shown.'}</p>{/if}
    <p class="small muted">UserSim has not run in this step. These profile fields belong to the simulator, not the advisor.</p>
  {:else if stageId==='situation'}
    <dl>
      <div><dt>From the original</dt><dd>{persona?.available?`${persona.name} · background, interests and original behaviour traits`:'The locked original; unavailable until its source can be verified.'}</dd></div>
      <div><dt>Supplied by this scenario</dt><dd>{trace?.situation?[trace.situation.goal,trace.situation.day,trace.situation.budget_sgd!==undefined?`under S$${trace.situation.budget_sgd}`:null,trace.situation.followup].filter(Boolean).join(' · '):scenario.preset.constraints}</dd></div>
      {#if scenarioId==='dreamjob'}<div><dt>{overlay?'Selected Designer hypotheses':'Planned Designer hypotheses'}</dt><dd>{overlay?text(overlay.fields):'Hypothetical preferred brands and salary band.'} These are generated test assumptions, not original profile facts. Salary stays private until public turn 2.</dd></div>{/if}
    </dl>
    {#if detailed&&sim}<dl><div><dt>Resolved probe / locale</dt><dd>{sim.probe} · {sim.configuration.locale}</dd></div><div><dt>Public turns / internal steps</dt><dd>{sim.configuration.max_turns} / {sim.configuration.max_steps}</dd></div><div><dt>Profile-only mode</dt><dd>{text(sim.configuration.probe_options?.learning_advisor?.profile_only)}</dd></div><div><dt>Language check</dt><dd>{sim.configuration.enforce_user_language?'Enabled':'Disabled'}</dd></div></dl><p class="small muted">{sim.behaviour_basis} Private resolved rows and prompts are deliberately not published.</p>{/if}
    {#if overlay}<p>Designer produced one row with three physical columns: two copied seed columns and one generated <code>retail_situation</code> structure. That structure contains the three hypothetical fields shown above. It did not add a new persona or change the source dataset.</p><details><summary>Inspect the generated fields</summary><pre>{JSON.stringify(overlay.fields,null,2)}</pre></details>{/if}
    {#if overlay&&detailed}<dl><div><dt>Generation</dt><dd>{extra['designer-generation.json']?.engine} {extra['designer-generation.json']?.version} · {extra['designer-generation.json']?.model_calls??'Unknown'} model calls</dd></div><div><dt>Original → selected overlay</dt><dd>Original preserved · explicit selection {text(extra['designer-lineage.json']?.explicit_selection)}<span class="hash">{extra['designer-lineage.json']?.original_sha256}</span></dd></div></dl>{/if}
  {:else if stageId==='build'}
    <dl><div><dt>Selected harness</dt><dd>{scenario.preset.harness==='hermes'?'Hermes':'LangChain Deep Agents'}</dd></div><div><dt>Course tools</dt><dd>{config?.tools?.enabled?.join(', ')||'Search, details and comparison · planned connection'}</dd></div><div><dt>Model access</dt><dd>{scenario.preset.baseline}</dd></div></dl>
    {#if config&&detailed}<dl><div><dt>Fabric schema / adapter</dt><dd>{config.schema_version}<br />{config.harness.adapter_id}</dd></div><div><dt>Resolution</dt><dd>{config.harness.resolution}</dd></div><div><dt>Input → output schema</dt><dd>{config.runtime.input_schema} → {config.runtime.output_schema}</dd></div><div><dt>Timeout / internal turns</dt><dd>{config.runtime.timeout_seconds}s / {config.runtime.max_turns} · not public conversation turns</dd></div><div><dt>Model</dt><dd>{config.models.default.model} · temperature {config.models.default.temperature} · max {config.models.default.max_tokens} output tokens</dd></div><div><dt>Doctor</dt><dd>{extra['fabric-doctor.json']?.status||'Unavailable'}</dd></div><div><dt>Relay</dt><dd>{config.relay.enabled?'Enabled':'Disabled'} · full payloads {text(config.relay.observability.enable_full_payloads)}</dd></div></dl>{/if}
    {#if extra['fabric-lifecycle.jsonl']?.length&&detailed}<p class="proof-fact">Startup observation: {extra['fabric-lifecycle.jsonl'].filter((event:Record<string,any>)=>['plan_created','doctor_completed','runtime_started'].includes(event.event)).map((event:Record<string,any>)=>event.event==='runtime_started'?'the persistent runtime started':event.event==='doctor_completed'?`preflight ${event.status||'completed'}`:'the adapter plan was created').join('; ')}.</p>{/if}
    {#if planned}<p class="unavailable">No matching configuration, preflight or startup receipt exists for this scenario yet.</p>{/if}
  {:else if stageId==='run'}
    {#if !planned}
      {#if turns.length>1}<div class="turn-buttons" aria-label="Recorded public turns">{#each turns as turn,i}<button class:pressed={turnIndex===i} onclick={()=>turnIndex=i}>Turn {turn}</button>{/each}</div>{/if}
      {#each trace.conversation.filter((m:Record<string,any>)=>Number(m.turn)===(turns[turnIndex]||turns[0])) as message}<article class="conversation-message" class:learner={message.role==='user'} class:advisor={message.role==='assistant'}><span>{message.role==='user'?'LEARNER · USERSIM':'ADVISOR · SAVED PUBLIC REPLY'}</span><div>{@html renderMarkdown(String(message.content||'No public content saved.'))}</div></article>{/each}
      {#if detailed&&invocation}<dl><div><dt>This turn's Fabric result</dt><dd>Runtime {invocation.runtime_status}; public-answer validation {invocation.outcome?.status||'not retained'}.</dd></div><div><dt>Response handling</dt><dd>{invocation.output?.native_response_published===false?'The native proposal was preserved separately; the application delivered the validated source-based response above.':'The normalized response supplied the public reply above.'}</dd></div></dl>{/if}
      {#if applicationTurn}<p><strong>How this reply was produced:</strong> the application asked for {applicationTurn.missing_constraints?.map((key:string)=>key==='days'?'study days':'training budget').join(' and ')} before agent dispatch. Advisor model calls: {applicationTurn.inference_calls}. There is no Fabric invocation or new course lookup for this reply.</p>{/if}
      {#if sim}<p class="small">UserSim saved {sim.outcome.n_turns} public {sim.outcome.n_turns===1?'turn':'turns'}. Step 6 explains its separate answer-quality judgments and any warnings alongside the application checks.</p>{/if}
      {#if scenarioId==='dreamjob'&&extra['public-constraints.jsonl']?.length}<h4>Information available at this turn</h4><dl>{#each extra['public-constraints.jsonl'].filter((c:Record<string,any>)=>c.turn===turnIndex+1) as constraint}<div><dt>Public constraints</dt><dd>Salary {constraint.salary_publicly_disclosed?'disclosed':'not disclosed'}; training budget {constraint.preferences.budget_sgd===null?'not stated':`S$${constraint.preferences.budget_sgd}`}; study days {constraint.preferences.days===null?'not stated':text(constraint.preferences.days.map((day:number)=>['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][day]))}.</dd></div>{/each}</dl>{/if}
    {:else}
      <p class="unavailable">No executed conversation is recorded. Planned interaction:</p><ol>{#each scenario.turns as turn,i}<li><strong>Turn {i+1}</strong><p>{turn.learner}</p></li>{/each}</ol><p class="small muted">Authored story prompts; no generated follow-ups or advisor replies are claimed.</p>
    {/if}
  {:else}
    <RecordedObservations {stageId} {scenarioId} {context} {scope} {detailed} bind:turnIndex bind:conditionId />
  {/if}
</div>

<style>
  dl{margin:12px 0;font-size:12px}dl div{padding:9px 0;border-bottom:1px solid var(--line);display:grid;grid-template-columns:minmax(95px,.65fr) minmax(0,1.5fr);gap:14px}dt{color:var(--muted)}dd{margin:0;overflow-wrap:anywhere;white-space:pre-wrap}h4{font-size:14px;margin:12px 0 6px}.hash{display:block;overflow-wrap:anywhere;font-family:var(--mono);font-size:10px;margin-top:6px}.profile{padding:12px 14px;border:1px solid var(--line);border-radius:5px;margin:12px 0}.proof-fact{padding:10px 12px;border-left:2px solid var(--teal);background:#f2f8f6;font-size:12px}.unavailable{padding:10px 12px;border-left:2px solid #b8a98b;background:#faf8f3;font-size:12px}.small{font-size:11px}.scenario-facts{min-width:0}
</style>
