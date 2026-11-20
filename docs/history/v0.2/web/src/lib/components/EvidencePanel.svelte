<script lang="ts">
  import { labApi, pretty } from '#lib/api.ts';
  import CodeReference from './CodeReference.svelte';

  let { runId, episodeId }: { runId: string; episodeId?: string } = $props();
  let evidence = $state<any>(null);
  let loading = $state(false);
  let error = $state('');
  let copied = $state('');
  let view = $state('tree');
  let raw = $state<any>(null);
  let artifactBusy = $state('');
  let artifactRequest = 0;
  const scopes = $derived(evidence?.relay?.scopes ?? []);
  const renderedScopes = $derived(scopeRows(scopes, view));
  const artifacts = $derived(evidence?.artifacts ?? []);
  const fabricSections = [
    { key: 'config', title: 'Effective typed configuration', text: 'The model endpoint, harness adapter, runtime limits and allowed MCP surface supplied to Fabric.' },
    { key: 'plan', title: 'Resolved execution plan', text: 'How Fabric resolved the adapter, environment, capabilities and telemetry before starting the runtime.' },
    { key: 'doctor', title: 'Preflight report', text: 'The actual SDK checks before runtime start. A planned configuration alone does not establish readiness.' },
    { key: 'lifecycle', title: 'Runtime and invocation lifecycle', text: 'One runtime can serve successive invocations. Compare runtime IDs with invocation IDs, then check its close event.' }
  ];

  function query() {
    return 'run_id=' + encodeURIComponent(runId) + (episodeId ? '&episode_id=' + encodeURIComponent(episodeId) : '');
  }

  $effect(() => {
    const selection = query();
    let active = true;
    loading = true; error = ''; evidence = null; raw = null; copied = ''; artifactBusy = '';
    artifactRequest++;
    labApi('evidence?' + selection)
      .then(value => { if (active) evidence = value; })
      .catch(reason => { if (active) error = reason instanceof Error ? reason.message : 'Evidence could not be read'; })
      .finally(() => { if (active) loading = false; });
    return () => { active = false; };
  });

  function scopeRows(items: any[], selectedView: string) {
    if (selectedView === 'timeline') return [...items].sort((a, b) => (a.started_at ?? a.ended_at ?? '').localeCompare(b.started_at ?? b.ended_at ?? '')).map(scope => ({ ...scope, depth: 0 }));
    const known = new Set(items.map(item => item.id));
    const children = new Map<string, any[]>();
    const roots: any[] = [];
    for (const item of items) {
      if (!item.parent_id || !known.has(item.parent_id)) roots.push(item);
      else children.set(item.parent_id, [...(children.get(item.parent_id) ?? []), item]);
    }
    const output: any[] = [];
    const seen = new Set<string>();
    function visit(item: any, depth: number) {
      if (seen.has(item.id)) return;
      seen.add(item.id); output.push({ ...item, depth });
      for (const child of children.get(item.id) ?? []) visit(child, Math.min(depth + 1, 10));
    }
    for (const root of roots) visit(root, 0);
    for (const item of items) if (!seen.has(item.id)) visit(item, 0);
    return output;
  }

  function time(value: string | undefined) {
    if (!value) return 'Time unavailable';
    const parsed = new Date(value);
    return Number.isNaN(parsed.getTime()) ? value : parsed.toLocaleTimeString('en-SG', { timeZone: 'Asia/Singapore', hour12: false }) + ' SGT';
  }

  async function copy(value: string) {
    try { await navigator.clipboard.writeText(value); copied = 'Location copied'; }
    catch { copied = 'Select the displayed path to copy it; clipboard access is unavailable.'; }
  }

  async function inspectArtifact(artifact: any, download = false) {
    const request = ++artifactRequest;
    artifactBusy = artifact.id; error = ''; copied = '';
    try {
      const result = await labApi('artifact?' + query() + '&artifact_id=' + encodeURIComponent(artifact.id));
      if (request !== artifactRequest) return;
      raw = result;
      if (download) {
        const url = URL.createObjectURL(new Blob([pretty(result.content) + '\n'], { type: 'application/json' }));
        const anchor = document.createElement('a');
        anchor.href = url;
        anchor.download = 'sanitized-' + artifact.name.split('/').pop().replace(/[^a-zA-Z0-9._-]/g, '_') + '.json';
        anchor.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
    } catch (reason) {
      if (request === artifactRequest) error = reason instanceof Error ? reason.message : 'Artifact could not be read';
    } finally { if (request === artifactRequest) artifactBusy = ''; }
  }
</script>

<section class="lab-card" aria-label="Backend evidence">
  <div class="lab-eyebrow">From the interface to the backend</div>
  <h2>Inspect what actually ran.</h2>
  <p>Relay records the agent, model and tool scopes. Fabric resolves and starts the harness. The gateway counts model calls across advisor, simulated learner and judges. Saved evidence opens without new model calls.</p>
  {#if loading}<p class="lab-loading" role="status">Reading saved backend evidence…</p>{/if}
  {#if error}<p class="lab-error" role="alert">{error}</p>{/if}
  {#if evidence}
    <div class="lab-path">{evidence.folder}</div>
    <div class="lab-actions"><button class="lab-button" onclick={() => copy(evidence.folder)}>Copy local run folder</button></div>
    {#if copied}<p class="lab-muted" role="status">{copied}</p>{/if}
    <div class="lab-badges">
      <span class="lab-badge">{evidence.relay?.events ?? 0} saved native Relay events</span>
      <span class="lab-badge">{scopes.length} scopes</span>
      <span class="lab-badge">{scopes.filter((scope: any) => scope.category === 'llm').length} traced model scopes</span>
      <span class="lab-badge">{scopes.filter((scope: any) => scope.category === 'tool').length} tool scopes</span>
    </div>
    <p class="lab-muted">These are native trace counts, not the experiment's total model-call ledger. An incomplete span stays incomplete; a successful invocation can still contain an unusable model answer.</p>
    {#each evidence.relay?.notices ?? [] as notice}<p class="lab-note">{notice}</p>{/each}
    {#if scopes.length}
      <div class="lab-actions" aria-label="Relay views">
        <button class="lab-button" class:active={view === 'tree'} aria-pressed={view === 'tree'} onclick={() => view = 'tree'}>Parent tree</button>
        <button class="lab-button" class:active={view === 'timeline'} aria-pressed={view === 'timeline'} onclick={() => view = 'timeline'}>Timeline</button>
      </div>
      <div class="lab-timeline" aria-label="Native Relay scopes">
        {#each renderedScopes as scope (scope.id)}
          <details style:margin-left={`${Math.min(scope.depth, 6) * 12}px`}>
            <summary><span class="lab-badge">{scope.category}</span> <strong>{scope.name}</strong> <span class="lab-badge" class:fail={scope.status === 'failed'}>{scope.status}</span> <span class="lab-muted">{time(scope.started_at)} · {scope.duration_ms === null ? 'duration unavailable' : `${scope.duration_ms} ms`}</span></summary>
            <p class="lab-path">Scope {scope.uuid}<br />Parent {scope.parent_uuid ?? 'root scope'}</p>
            {#if scope.parent_available === false}<p class="lab-note">The referenced parent is absent from the saved evidence; its relationship is not reconstructed.</p>{/if}
            <div class="lab-grid"><div><h3>Observed input</h3><pre class="lab-code">{pretty(scope.input)}</pre></div><div><h3>Observed output</h3><pre class="lab-code">{pretty(scope.output)}</pre></div></div>
            {#if scope.metadata && Object.keys(scope.metadata).length}<details class="lab-check-row"><summary>Native status metadata</summary><pre class="lab-code">{pretty(scope.metadata)}</pre></details>{/if}
            {#if artifacts.find((artifact: any) => artifact.id === scope.artifact_id)}<button class="lab-button" onclick={() => inspectArtifact(artifacts.find((artifact: any) => artifact.id === scope.artifact_id))}>Inspect saved native events</button>{/if}
          </details>
        {/each}
      </div>
    {/if}

    {#if fabricSections.some(section => evidence.fabric?.[section.key]?.length)}
      <h3>What Fabric managed</h3>
      <p class="lab-muted">Follow configuration → plan → preflight → runtime → invocation. The application still owns the experiment, budget admission and saved results.</p>
      {#each fabricSections as section}
        {#if evidence.fabric?.[section.key]?.length}
          <details class="lab-check-row"><summary>{section.title}</summary><p>{section.text}</p>
            {#each evidence.fabric[section.key] as record}
              <pre class="lab-code">{pretty(record.content)}</pre>
              {#each record.notices ?? [] as notice}<p class="lab-note">{notice}</p>{/each}
            {/each}
          </details>
        {/if}
      {/each}
    {/if}

    {#if evidence.gateway}
      <h3>Model calls and routing</h3>
      <p class="lab-muted">{evidence.gateway.calls} admitted calls across the whole experiment, including simulator and judge roles. These counts can differ from the selected episode's Relay scopes. Missing provider usage stays unknown.</p>
      {#each evidence.gateway.usage ?? [] as call, index (`${call.call ?? index}`)}
        <details class="lab-check-row"><summary><span class="lab-badge">Call {call.call ?? index + 1}</span> <strong>{call.role}</strong> · {call.status} · {call.selected_model ?? call.model ?? 'model unavailable'}</summary>
          <p>Requested alias: {call.requested_model ?? 'scripted/offline'} · route: {call.routing ?? call.mode} · latency: {call.latency_ms === undefined ? 'unknown' : `${call.latency_ms} ms`}</p>
          {#if call.routing_decision}<h4>Native Switchyard decision</h4><pre class="lab-code">{pretty(call.routing_decision)}</pre>{:else if call.routing === 'switchyard'}<p class="lab-note">Switchyard was requested, but no native decision metadata was saved for this call.</p>{/if}
          <pre class="lab-code">{pretty(call)}</pre>
        </details>
      {/each}
      <CodeReference source="routing" label="Switchyard and LiteLLM integration" />
    {/if}

    <details class="lab-check-row"><summary>Saved artifacts · {artifacts.length} files</summary>
      <p>Only known run artifacts are readable here. Headers and credential fields are redacted in this view and in downloads. Truncated or missing records remain labelled.</p>
      {#each artifacts as artifact (artifact.id)}
        <div class="artifact-row"><strong>{artifact.name}</strong><span class="lab-badge">{artifact.kind} · {Math.ceil(artifact.size / 1024)} KB</span><div class="lab-path">{artifact.path}</div><div class="lab-actions"><button class="lab-button" disabled={!!artifactBusy} onclick={() => inspectArtifact(artifact)}>{artifactBusy === artifact.id ? 'Reading…' : 'Read artifact'}</button><button class="lab-button" disabled={!!artifactBusy} onclick={() => inspectArtifact(artifact, true)}>Download sanitized JSON</button><button class="lab-button" onclick={() => copy(artifact.path)}>Copy local path</button></div></div>
      {/each}
    </details>
    {#if raw}
      <div class="raw-artifact" aria-live="polite"><h3>{raw.name}</h3><div class="lab-path">{raw.path}</div>{#each raw.notices ?? [] as notice}<p class="lab-note">{notice}</p>{/each}<pre class="lab-code">{pretty(raw.content)}</pre></div>
    {/if}
    <details class="lab-check-row"><summary>Where to integrate this into your application</summary>
      <CodeReference source="usersim" label="UserSim activations and target isolation" />
      <CodeReference source="deepagents" label="Deep Agents harness and public reply validation" />
      <CodeReference source="relay" label="Relay instrumentation and local capture" />
      <CodeReference source="fabric" label="Fabric typed configuration and runtime lifecycle" />
      <CodeReference source="mcp" label="Course MCP tools and trusted constraints" />
      <CodeReference source="budget" label="Model-call routing, limits and measured usage" />
    </details>
  {/if}
</section>

<style>
  .artifact-row{padding:14px 0;border-top:1px solid #e1e8dc;font-size:11px;overflow-wrap:anywhere}.artifact-row>strong{display:block;margin-bottom:8px}.raw-artifact{margin-top:18px}.lab-timeline strong{font-size:11px}.lab-timeline .lab-muted{font-size:10px}.lab-timeline .lab-grid{margin:8px 0}
</style>
