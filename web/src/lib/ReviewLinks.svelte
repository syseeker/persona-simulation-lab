<script lang="ts">
  import { operationById, componentById, sourceId, architectureUrl, preset } from './lessonArchitecture';
  let { operation, scenarioId, context, detailed=false }:
    {operation:string;scenarioId:string;context:Record<string,any>|null;detailed?:boolean}=$props();
  const op=$derived(operationById[operation]);
  const call=$derived(context?.sources?.[sourceId(operation,scenarioId)||'']);
  const config=$derived(context?.sources?.[op.configCall||'']);
  const files=$derived<Record<string,any>[]>((context?.artifacts||[]).filter((f:Record<string,any>)=>op.proof.includes(f.path)));
  const workflow=$derived(op.component==='harness'&&preset(scenarioId).harness==='hermes'?'https://docs.nvidia.com/nemo/fabric/adapter-contract/overview':componentById[op.component].workflow);
  const architecture=$derived(op.component==='personas'&&context?.trace?.source_lock?.source==='ngc'?componentById.personas.workflow:architectureUrl(op.component,scenarioId));
</script>

<div class="review-links" data-operation-links={operation}>
  <div class="links">
    {#if call?.url}<a href={call.url} target="_blank" rel="noreferrer" title={`${call.path} · ${call.symbol}`}>Application call ↗</a>{:else}<span>Application call · unavailable</span>{/if}
    {#if config?.url}<a href={config.url} target="_blank" rel="noreferrer" title={`${config.path} · ${config.symbol}`}>Configuration ↗</a>{:else}<span>Configuration · unavailable</span>{/if}
    {#if files.some(f=>f.url)}
      {@const first=files.find(f=>f.url)!}
      <a href={first.url} target="_blank" rel="noreferrer" title={first.path}>Scenario log ↗</a>
    {:else}<span>Scenario log · unavailable</span>{/if}
    <a href={architecture} target="_blank" rel="noreferrer">{op.component==='personas'?'Dataset distribution':op.component==='catalogue'?'Course catalogue':'Library architecture'} ↗</a>
  </div>
  {#if detailed}
    {#if op.component==='personas'}<p class="source-note"><a href={componentById.personas.architecture} target="_blank" rel="noreferrer">HF dataset viewer ↗</a> · <a href={componentById.personas.workflow} target="_blank" rel="noreferrer">NGC Extended catalogue ↗</a></p>{:else if workflow}<p class="source-note"><a href={workflow} target="_blank" rel="noreferrer">Library workflow / sequence ↗</a></p>{/if}
    {#if call?.url}<p class="source-note">{call.path} · {call.symbol || 'file'}<br />{scenarioId==='photography'?call.notice:'Existing integration reference; not verified for this planned scenario.'}{call.working_tree_differs?' Uncommitted working-tree changes are not in this link.':''}</p>{/if}
    {#if files.length}<p class="record-links">Recorded configuration / proof: {#each files as file,i}{#if i} · {/if}{#if file.url}<a href={file.url} target="_blank" rel="noreferrer">{file.path} ↗</a>{:else}<span>{file.path} · publication pending</span>{/if}{/each}</p>{:else}<p class="source-note">Expected proof: {op.proof.join(', ')}. No matching record is published for this scenario.</p>{/if}
    {#if op.component==='harness'}<p class="source-note">The application calls Fabric. The selected adapter owns the internal harness operations.</p>{/if}
  {/if}
</div>

<style>
  .links{display:flex;gap:8px 16px;flex-wrap:wrap;font-size:12px;margin:12px 0 6px}.links span{color:var(--muted)}
  .source-note,.record-links{font-size:11px;line-height:1.65;color:var(--muted);overflow-wrap:anywhere;margin:8px 0}
</style>
