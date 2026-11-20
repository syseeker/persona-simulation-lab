<script lang="ts">
  import { onMount, untrack } from 'svelte';
  import { renderMarkdown } from './markdown';
  import { stages } from './content';
  import { references } from './references';
  import { requestFocus, type RequestFocus } from './requestFocus';

  type Data = Record<string, any>;
  let { runId = $bindable<string | null>(null), live = $bindable(false), choiceMade = $bindable(false),
        source = $bindable('ngc'), persona = $bindable<Data | null>(null), stageId, component = '', moduleName = '', view = 'guide',
        requestId = $bindable(''), oninspect = (_component: string, _module = '', _view: 'overview' | 'sources' | 'evidence' = 'overview') => {},
        onback = () => {}, onrecord = () => {}, onfocus = (_focus: RequestFocus | null) => {} }:
      { runId?: string | null; live?: boolean; choiceMade?: boolean; source?: string; persona?: Data | null; stageId: string; component?: string; moduleName?: string; view?: string;
        requestId?: string; oninspect?: (c: string, m?: string, v?: 'overview' | 'sources' | 'evidence') => void;
        onback?: () => void; onrecord?: () => void; onfocus?: (focus:RequestFocus | null) => void } = $props();
  let runs = $state<Data[]>([]), trace = $state<Data | null>(null), readiness = $state<Data | null>(null);
  let busy = $state(''), error = $state('');
  let code = $state<Data | null>(null), artifact = $state<Data | null>(null), mounted = $state(false);
  let loadEpoch = 0;
  const currentStage = $derived(stages.find(s => s.id === stageId)!);
  const sourceComponent = $derived(component || ({persona:'personas',situation:'situation',build:'fabric',run:'usersim',
    investigate:'relay',evaluate:'checks',routing:'litellm',safeguards:'deepagents',deploy:'openshell'} as Record<string,string>)[stageId]);
  const active = $derived(trace && !['completed','failed','cancelled','interrupted'].includes(trace.run.status));
  const files = $derived<Data[]>(trace?.artifacts || []);
  const requests = $derived<Data[]>([
    ...(trace?.conversation || []).filter((m: Data) => m.role === 'user').map((m: Data) => ({id:`turn:${m.turn}`,label:`Public turn ${m.turn}`})),
    ...(trace?.usage.records || []).map((r: Data) => ({id:`call:${r.call}`,label:`Model call ${r.call} · ${r.role} · ${r.status}`})),
    ...(trace?.tools || []).map((r: Data) => ({id:`tool:${r.scope_uuid}`,label:`Tool · ${r.name}`}))
  ]);
  const logFiles = $derived.by(() => {
    const names: Record<string,string[]> = {
      personas:['source-lock.json'], situation:['situation.json'], usersim:['usersim-activations.jsonl','usersim-result.json','public-conversation.json'],
      fabric:['fabric-config.json','fabric-plan.json','fabric-doctor.json','fabric-lifecycle.jsonl','sandbox-stderr.log'],
      deepagents:['reply-outcomes.jsonl','fabric-lifecycle.jsonl','native-tools.json'], mcp:['relay.jsonl','native-tools.json','public-conversation.json'], catalogue:['catalogue-snapshot.json'],
      gateway:['usage.json'], litellm:['usage.json'], providers:['usage.json'], relay:['relay.jsonl','relay-scopes.json','native-tools.json'], records:['run.json','events.jsonl'],
      checks:['evaluation.json'], standalone:['sandbox-lifecycle.jsonl','cleanup.json'],
      openshell:['effective-policy.yaml','effective-policy.json','boundary-probes.json','sandbox-lifecycle.jsonl','cleanup.json']
    };
    const wanted = names[sourceComponent] || [];
    return files.filter(f => wanted.some(name => f.path === name || f.path.endsWith('/' + name)));
  });
  const reference = $derived(references[sourceComponent]);
  $effect(() => { onfocus(requestFocus(trace, requestId)); });

  async function api(action: string, data?: Data, signal?: AbortSignal) {
    const writes = ['sample','start','cancel','recover'].includes(action);
    const query = !writes && data ? '?' + new URLSearchParams(data as Record<string,string>) : '';
    const response = await fetch('/api/journey/' + action + query, writes ? {
      method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(data || {}), signal
    } : {signal});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'The operation failed.');
    return result;
  }
  async function action(label: string, work: () => Promise<void>) {
    if (busy) return;
    busy = label; error = '';
    try { await work(); } catch (e) { error = e instanceof Error ? e.message : 'The operation failed.'; }
    finally { busy = ''; }
  }
  async function loadRuns() {
    const result = await api('list', {scenario_id:'photography'});
    runs = result.runs;
    if (!runId && !choiceMade && !live) {
      const saved = runs.find(r => r.status === 'completed');
      if (saved) { runId = saved.run_id; onrecord(); }
    }
  }
  function chooseRun(value: string) { choiceMade = true; runId = value || null; requestId = ''; artifact = null; code = null; onback(); }
  async function inspectArtifact(file: Data) { await action('Loading local log', async () => {
    const requestedRun = runId;
    const result = await api('artifact',{run_id:requestedRun!,artifact_id:file.id});
    if (requestedRun === runId) artifact = result;
  }); }
  function file(name: string) { return files.find(f => f.path === name || f.path.endsWith('/' + name)); }
  async function showFile(name: string) { const match = file(name); if (match) await inspectArtifact(match); }
  const pretty = (value: unknown) => JSON.stringify(value, null, 2);
  onMount(() => { mounted = true; void action('Loading saved runs', async () => {
    await loadRuns();
    if (live) readiness = await api('readiness');
  }); });
  $effect(() => {
    const id = runId;
    if (!mounted) return;
    trace = null; artifact = null;
    if (!id) return;
    const epoch = ++loadEpoch, controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    async function refresh() {
      try {
        const value = await api('trace', {run_id:id!}, controller.signal);
        if (epoch !== loadEpoch || value.run.scenario_id !== 'photography') return;
        trace = value;
        if (!['completed','failed','cancelled','interrupted'].includes(value.run.status)) timer = setTimeout(refresh, 1500);
        else void loadRuns();
      } catch (e) { if (!controller.signal.aborted) error = e instanceof Error ? e.message : 'Saved run unavailable.'; }
    }
    void refresh();
    return () => { controller.abort(); clearTimeout(timer); };
  });
  $effect(() => {
    const isLive = live;
    if (mounted && isLive) untrack(() => { void action('Checking prerequisites', async () => { readiness = await api('readiness'); }); });
  });
  $effect(() => {
    const chosen = sourceComponent, module = moduleName, currentView = view;
    code = null;
    if (!mounted || currentView !== 'sources') return;
    const controller = new AbortController();
    void api('source',{component:chosen,module},controller.signal).then(result=>code=result).catch(e=>{
      if (!controller.signal.aborted) error=e.message;
    });
    return () => controller.abort();
  });
  $effect(() => {
    if (persona && persona.source !== source) persona = null;
  });
</script>

<div class="journey-evidence" data-testid="journey-panel">
  <details class="saved-selection" open={live}>
    <summary>{runId ? 'Selected photography run' : 'Saved photography runs'}</summary>
    <label>Evidence<select aria-label="Photography evidence" value={runId || ''} onchange={e=>chooseRun(e.currentTarget.value)}>
      <option value="">Illustrative walkthrough · no execution evidence</option>
      {#if runId && !runs.some(run=>run.run_id===runId)}<option value={runId}>Requested run {runId.slice(0,8)} · loading or unavailable</option>{/if}
      {#each runs as run}<option value={run.run_id}>{run.status} · {run.created_at.slice(0,16).replace('T',' ')} UTC · {run.run_id.slice(0,8)}</option>{/each}
    </select></label>
    {#if runId}<code class="run-path">{trace?.run.run_directory || `runs/journeys/${runId}`}</code><p class="small muted">One condition and episode. This selection never relabels another scenario's evidence.</p>{/if}
    <button class="text-button" onclick={()=>action('Refreshing saved runs',loadRuns)}>Refresh saved runs</button>
  </details>
  {#if error}<p class="operation-error" role="alert">{error}</p>{/if}
  {#if busy}<p class="small muted" role="status">{busy}…</p>{/if}
  {#if !trace && !live && view === 'sources'}
    <button class="back-link" onclick={onback}>← Back to the walkthrough</button>
    <h2>Application implementation</h2>
    {#if code?.available}
      <code>{code.path}:{code.line}</code>
      <div class="inspector-actions">{#if code.github_url}<a href={code.github_url} target="_blank" rel="noreferrer">GitHub code ↗</a>{:else}<span class="small muted">GitHub code · publication pending</span>{/if}{#if code.repository_url}<a href={code.repository_url} target="_blank" rel="noreferrer">Your repository ↗</a>{/if}</div>
      <p class="small muted">{code.github_notice}</p><pre class="compact-code">{code.content}</pre>
      <p class="small muted">Current working-tree code. No saved-run revision is selected.</p>
    {:else if code}<p>{code.notice}</p>{:else}<p>Loading the allowlisted implementation…</p>{/if}
  {/if}
  {#if live}
    <span class="panel-eyebrow">NEW LIVE PHOTOGRAPHY CONDITION</span><h2>Run one real conversation.</h2>
    <p>UserSim generates one public learner turn. Fabric with Deep Agents and the course tools runs inside a fresh OpenShell sandbox. The host budget gateway uses the fixed LiteLLM alias.</p>
    <button onclick={()=>action('Checking prerequisites',async()=>{readiness=await api('readiness');})} disabled={!!busy}>Check prerequisites</button>
    {#if readiness}<dl class="readiness">
      <div><dt>OpenShell gateway</dt><dd>{readiness.native.gateway ? 'Reachable' : 'Unavailable'}</dd></div>
      <div><dt>Reusable agent image</dt><dd>{readiness.native.image ? 'Installed' : 'Build required'}</dd></div>
      <div><dt>LiteLLM fixed / simulator aliases</dt><dd>{readiness.proxy.fixed_alias_available && readiness.proxy.support_alias_available ? 'Available' : 'Unavailable'}</dd></div>
      <div><dt>Workload ownership</dt><dd>{readiness.active ? 'An active/unresolved run is retained' : 'Available'}</dd></div>
    </dl>{#if readiness.native.reason}<p class="small muted">{readiness.native.reason}</p>{/if}{/if}
    <label>Test persona source<select aria-label="Live test persona source" bind:value={source}><option value="ngc">Singapore NGC Extended · OCEAN source traits</option><option value="hf-profile-only">HF Singapore · profile-only</option></select></label>
    <button onclick={()=>action('Sampling and locking one original',async()=>{persona=await api('sample',{source});})} disabled={!!busy || !!active}>Choose a random test persona</button>
    {#if persona}<div class="io-grid"><h3>Locked original</h3><pre>{pretty(persona.summary)}</pre><code>{persona.source_id}</code><p class="small muted">Revision {persona.source_revision} · original SHA-256 {persona.original_sha256}</p><p class="small muted">The profile belongs to the simulator. The advisor sees only public messages.</p></div>{/if}
    <p class="small muted">Beginner photography · Saturday · S$50 before funding. Designer, Switchyard, native Guardrails and Helix are intentionally omitted. Limits: one public turn, 120 total model calls, 1,024 output tokens per call, four tool rounds per advisor reply.</p>
    <button class="primary" disabled={!!busy || !readiness?.ready || !persona || !!active} onclick={()=>action('Starting photography',async()=>{
      const run=await api('start',{spec:{scenario_id:'photography',source:persona!.source,source_id:persona!.source_id,original_sha256:persona!.original_sha256}});
      choiceMade=true;runId=run.run_id;requestId='';
    })}>Start live photography simulation</button>
  {/if}
  {#if trace}
    {#if trace.recording_notice}<p class="small muted">{trace.recording_notice}</p>{/if}
    <div class="run-status" role="status"><strong>{trace.run.status}</strong><span>{trace.run.calls} of 120 model calls · cleanup {trace.run.cleanup_confirmed ? 'confirmed' : 'pending'}</span></div>
    {#if trace.run.error}<p class="operation-error">{trace.run.error}</p>{/if}
    {#if trace.developer_review}<p class="operation-error"><strong>Developer review:</strong> {trace.developer_review.summary} Original run/check results remain unchanged.</p>{/if}
    {#if active}<button disabled={!!busy} onclick={()=>action('Requesting cancellation',async()=>{await api('cancel',{run_id:runId});})}>Cancel this run</button>{/if}
    {#if trace.run.recovery_required || trace.run.ownership_notice}<p class="operation-error">{trace.run.ownership_notice || 'Cleanup needs recovery. New execution remains blocked.'}</p><button disabled={!!busy} onclick={()=>action('Recovering this native condition',async()=>{await api('recover',{run_id:runId});trace=await api('trace',{run_id:runId});readiness=await api('readiness');})}>Recover and verify cleanup</button>{/if}
    {#if live && !active}<button class="primary" onclick={()=>{live=false;onrecord();onback();}}>Inspect this run across the nine steps →</button>{/if}
    {#if !live}
      <div class="step-meta"><span data-testid="recorded-step-counter">Step {stages.findIndex(s=>s.id===stageId)+1} of 9</span><span>RECORDED · {trace.run.run_id.slice(0,8)}</span></div>
      <h2 class="step-title">{currentStage.title}</h2><p class="developer-pain">“{currentStage.pain}”</p>
      {#if view === 'sources'}
        <button class="back-link" onclick={onback}>← Back to the selected run</button>
        {#if code?.available}<h3>{code.symbol || code.path}</h3><code>{code.path}:{code.line}</code>
          <div class="inspector-actions">{#if code.github_url}<a href={code.github_url} target="_blank" rel="noreferrer">GitHub code ↗</a>{:else}<span class="small muted">GitHub code · publication pending</span>{/if}{#if code.repository_url}<a href={code.repository_url} target="_blank" rel="noreferrer">Your repository ↗</a>{/if}</div>
          <p class="small muted">{code.github_notice}</p><pre class="compact-code">{code.content}</pre>
          <p class="small muted">Current checkout SHA-256: {code.sha256}. This run recorded revision {trace.run.source_revision || 'unavailable'} and separate source hashes.</p>
        {:else if code}<p>{code.notice}</p>{:else}<p>Loading the allowlisted implementation…</p>{/if}
      {:else if view === 'evidence'}
        <button class="back-link" onclick={onback}>← Back to the selected run</button><h3>Scenario-specific {trace.run.recording ? 'recorded' : 'local'} logs</h3>
        <p class="small muted">{trace.run.run_directory} · episode {trace.run.episode_id}</p>
        {#each logFiles as log}<div class="artifact-row"><button onclick={()=>inspectArtifact(log)}>{log.path}</button><a href={log.url} target="_blank" rel="noreferrer">{log.kind === 'recorded' ? 'Open recorded log ↗' : 'Open local record ↗'}</a></div>{/each}
        {#if !logFiles.length}<p>No matching native log has been saved for this component in this run.</p>{/if}
      {:else if view === 'component'}
        <button class="back-link" onclick={onback}>← Back to the selected step</button>
        <h3>{reference?.title || sourceComponent}</h3>
        {#if moduleName}<p class="module-selection">Selected module: <strong>{moduleName}</strong></p>{/if}
        <p>{reference?.ownership || 'This component is outside the implemented photography path.'}</p>
        <p class="small muted">{logFiles.length ? `${logFiles.length} matching records are available in this photography run.` : 'No matching execution record is available in this run.'}</p>
        <div class="inspector-actions"><button onclick={()=>oninspect(sourceComponent,moduleName,'sources')}>Application code</button><button onclick={()=>oninspect(sourceComponent,moduleName,'evidence')}>Scenario log</button></div>
      {:else}
        {#if stageId === 'persona'}<p>The original was locked before execution. Its country context and source traits are simulator input, not citizenship or entitlement evidence.</p><pre class="compact-code">{pretty(trace.source_lock)}</pre>{#if trace.source_lock?.source_url}<a href={trace.source_lock.source_url} target="_blank" rel="noreferrer">Original dataset distribution ↗</a>{/if}
        {:else if stageId === 'situation'}<p>The photography situation is authored. No Designer job was run; original profile fields were not overwritten.</p><pre class="compact-code">{pretty(trace.situation)}</pre>
        {:else if stageId === 'build'}<p>One persistent Fabric/Deep Agents runtime serves this condition inside OpenShell. Inspect its actual configuration, plan and Doctor record.</p><pre class="compact-code">{pretty(trace.run.configuration)}</pre><p class="small muted">Native thread {trace.run.native_thread_id || 'not established'}</p><button onclick={()=>showFile('fabric-plan.json')}>Open this runtime's plan</button><button onclick={()=>showFile('fabric-doctor.json')}>Open Doctor result</button>
        {:else if stageId === 'run'}
          {#each trace.conversation as message}<article class:learner={message.role === 'user'} class:advisor={message.role === 'assistant'} class="conversation-message"><span>{message.role === 'user' ? 'LEARNER · USERSIM' : 'ADVISOR · ACTUAL SAVED RESPONSE'}</span><div>{@html renderMarkdown(String(message.content || 'No public content saved.'))}</div></article>{/each}
          {#if !trace.conversation.length}<p>No public turn has been saved. Inspect the failure or wait for execution; there is no substitute reply.</p>{/if}
          <button onclick={()=>showFile('usersim-activations.jsonl')}>Open UserSim activation lifecycle</button>
          {#if trace.run.usersim_outcome}<details><summary>Native UserSim outcome</summary><pre>{pretty(trace.run.usersim_outcome)}</pre></details>{/if}
          {#if trace.run.usersim_notice}<p class="small muted">{trace.run.usersim_notice}</p>{/if}
        {:else if stageId === 'investigate'}
          <label>Saved request<select aria-label="Saved request" bind:value={requestId}><option value="">All attributable requests</option>{#each requests as request}<option value={request.id}>{request.label}</option>{/each}</select></label>
          {#if requestId.startsWith('turn:')}<section>{#each trace.conversation.filter((m:Data)=>`turn:${m.turn}`===requestId) as message}<article class="conversation-message"><span>{message.role}</span><div>{@html renderMarkdown(String(message.content || 'No public content.'))}</div></article>{/each}</section>
          {:else if requestId.startsWith('call:')}<pre class="compact-code">{pretty(trace.usage.records.find((r:Data)=>`call:${r.call}`===requestId))}</pre>
          {:else if requestId.startsWith('tool:')}<pre class="compact-code">{pretty(trace.tools.find((r:Data)=>`tool:${r.scope_uuid}`===requestId))}</pre>
          {:else}<h3>{trace.tools.length} native tool records · {trace.relay.scopes.length} native scopes</h3>{#each trace.tools as tool}<details><summary>{tool.name} · {tool.status}</summary><pre>{pretty(tool)}</pre></details>{/each}{/if}
          {#each trace.relay.notices as warning}<p class="small muted">{warning}</p>{/each}<p class="small muted">Relay UUIDs/parents remain native. Model calls also have a control-request identity in the gateway ledger; no missing native model-to-call correlation is invented.</p>
        {:else if stageId === 'evaluate'}
          {#if trace.evaluation}<p>{trace.evaluation.passed} of {trace.evaluation.total} application assertions passed. No Helix SDK or model judge ran.</p>{#each trace.evaluation.rows as criterion}<details class="criterion"><summary>{criterion.criterion}<span>{criterion.status}</span></summary><p>{criterion.reason}</p><pre>{pretty({expected:criterion.expected,actual:criterion.actual,evidence:criterion.evidence})}</pre></details>{/each}<p class="small muted">{trace.evaluation.coverage}</p>{:else}<p>Evaluation is unavailable. A missing or incomplete response is not a passed check.</p>{/if}
        {:else if stageId === 'routing'}<p>This condition uses a fixed LiteLLM alias. No Switchyard decision is expected.</p>{#each trace.usage.records as call}<details><summary>Call {call.call} · {call.role} · {call.status}</summary><pre>{pretty({requested_alias:call.requested_model,selected_model:call.selected_model,provider_route:call.provider_route,usage:call.usage ?? 'unknown',latency_ms:call.latency_ms,routing_decision:call.routing_decision ?? null})}</pre></details>{/each}
        {:else if stageId === 'safeguards'}<p>Photography uses application restrictions and the native sandbox. Native Guardrails is intentionally omitted.</p><pre class="compact-code">{pretty(trace.usage.records.filter((r:Data)=>r.role==='assistant').map((r:Data)=>({call:r.call,status:r.status,tool_surface:r.tool_surface})))}</pre><p class="small muted">The Fabric execution gate and provider-bound tool-schema filter are distinct. Inspect the saved surfaces; a configured allowlist alone is not proof of execution.</p>
        {:else if stageId === 'deploy'}<p>Standalone OpenShell contains the persistent advisor and its read-only course tools. Native exec carries the bounded model bridge to the host gateway, which alone accesses LiteLLM credentials. Helix Platform was not used.</p>
          {#each ['sandbox-identity.json','effective-policy.yaml','effective-policy.json','boundary-probes.json','cleanup.json'] as name}<button onclick={()=>showFile(name)} disabled={!file(name)}>{name}</button>{/each}
          <p class="small muted">Native policy version/admission, allow/deny probes and confirmed cleanup are separate records. An unsuccessful connection without a policy-denial error does not pass the network probe.</p>
        {/if}
        <div class="inspector-actions"><button onclick={()=>oninspect(sourceComponent,moduleName,'sources')}>Application code</button><button onclick={()=>oninspect(sourceComponent,moduleName,'evidence')}>Scenario log</button></div>
      {/if}
      {#if reference?.upstream.length}<div class="source-links">{#each reference.upstream as upstream}<a href={upstream.url} target="_blank" rel="noreferrer">{upstream.label} ↗</a>{/each}</div>{/if}
    {/if}
    {#if artifact}<section class="artifact-preview"><h3>{artifact.path}</h3><a href={artifact.url} target="_blank" rel="noreferrer">{artifact.kind === 'recorded' ? 'Open this recording on GitHub ↗' : 'Open this run\'s local record ↗'}</a><pre class="compact-code">{typeof artifact.content === 'string' ? artifact.content : pretty(artifact.content)}</pre><p class="small muted">Run {artifact.run_id} · SHA-256 {artifact.sha256}{artifact.truncated ? ' · preview truncated; original retained locally' : ''}</p><button onclick={()=>artifact=null}>Close log preview</button></section>{/if}
    <details class="all-files"><summary>All files in this run</summary>{#each files as log}<div class="artifact-row"><button onclick={()=>inspectArtifact(log)}>{log.path}</button><a href={log.url} target="_blank" rel="noreferrer">{log.kind === 'recorded' ? 'Recorded log ↗' : 'Local log ↗'}</a></div>{/each}</details>
  {/if}
</div>

<style>
  .journey-evidence { min-width:0; }
  .saved-selection { margin-bottom:18px; padding-bottom:12px; border-bottom:1px solid var(--line); }
  .saved-selection label { margin-top:12px; }
  .run-path { display:block; overflow-wrap:anywhere; font-size:11px; margin:10px 0; }
  .run-status { display:flex; gap:12px; flex-wrap:wrap; margin:18px 0; padding:12px; border:1px solid var(--line); border-radius:5px; font-size:12px; }
  .operation-error { color:#8d3e2a; padding:12px; background:#fff6f0; border:1px solid #e7c9b8; border-radius:5px; overflow-wrap:anywhere; }
  .readiness { font-size:12px; margin:16px 0; }
  .readiness div { display:flex; justify-content:space-between; gap:14px; padding:8px 0; border-bottom:1px solid var(--line); }
  dd { margin:0; text-align:right; }
  button { margin-bottom:6px; }
  .artifact-row { display:flex; flex-direction:column; align-items:flex-start; gap:3px; margin:10px 0; font-size:11px; overflow-wrap:anywhere; }
  .artifact-row button { max-width:100%; overflow-wrap:anywhere; text-align:left; }
  .artifact-preview { margin:20px 0; padding-top:15px; border-top:1px solid var(--line); }
  .artifact-preview h3 { overflow-wrap:anywhere; }
  .all-files { margin:20px 0; }
  .criterion { margin-bottom:8px; }
  .criterion summary { display:flex; gap:14px; justify-content:space-between; }
  pre { max-width:100%; overflow-wrap:anywhere; }
</style>
