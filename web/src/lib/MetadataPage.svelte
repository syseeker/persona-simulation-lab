<script lang="ts">
  import {onMount} from 'svelte';
  import type {CaptureAvailability, CapturePrivacy, GuideMetadata, MetadataRow} from './metadataTypes';
  import {conditionInfo} from './reviewScope';
  import {artifactGroups,moduleRows} from './metadataPresentation';

  let {scenarioId='photography',focusRequirement='',focusCondition='',onScenarioChange=(_id:string)=>{}}:
    {scenarioId?:string;focusRequirement?:string;focusCondition?:string;onScenarioChange?:(id:string)=>void}=$props();
  const scenarios=[{id:'photography',name:'Photography'},{id:'boardgames',name:'Board games'},
    {id:'dreamjob',name:'Retail learning'}];
  let data=$state<GuideMetadata|null>(null),error=$state(''),loading=$state(false),mounted=$state(false);
  let condition=$state(''),query=$state('');
  const visibleRows=$derived((data?.rows??[]).filter(row=>
    (!focusRequirement||row.id===focusRequirement)&&
    (condition==='*'||!row.condition_id||row.condition_id===condition)&&
    `${row.module} ${row.id} ${row.operation} ${row.filenames.join(' ')} ${availability(row.status)} ${row.status==='exists'?access(row.privacy):''}`.toLowerCase().includes(query.toLowerCase())));
  const groupedRows=$derived(moduleRows(visibleRows));
  const selectedCondition=$derived(data?.conditions.find(c=>c.id===condition));

  function availability(value:CaptureAvailability){
    return ({exists:'EXISTS',missing:'NOT EXIST','not-used':'NOT USED',unavailable:'UNAVAILABLE'})[value];
  }
  function access(value:CapturePrivacy){
    return ({public:'PUBLIC',private:'PRIVATE',projection:'PARTIAL',unknown:'ACCESS UNKNOWN'})[value];
  }
  function scenarioName(id:string){return scenarios.find(item=>item.id===id)?.name??id;}
  function privateCount(row:MetadataRow){return row.artifacts.filter(item=>item.privacy==='private').length;}
  const filename=(path?:string)=>path?.split('/').at(-1)?.replace(/^[a-f0-9]{24}-/,'')||'Saved capture';
  function stateSummary(rows:MetadataRow[]){return[...new Set(rows.map(r=>availability(r.status)))].join(' · ');}
  function scopeName(purpose:string|null){return purpose?conditionInfo(purpose).label:'This scenario';}
  function chooseScenario(event:Event){
    const next=(event.currentTarget as HTMLSelectElement).value;
    scenarioId=next;query='';focusRequirement='';onScenarioChange(next);
  }
  onMount(()=>{mounted=true;});
  $effect(()=>{
    const scenario=scenarioId;if(!mounted)return;
    const controller=new AbortController();data=null;error='';loading=true;condition='';
    void fetch(`/api/journey/metadata?scenario_id=${encodeURIComponent(scenario)}`,{signal:controller.signal})
      .then(async response=>{
        const value=await response.json();
        if(!response.ok)throw new Error(value.error||'The capture inventory could not be read.');
        if(value.schema!=='citizen-guide-metadata/v1'||value.scenario_id!==scenario||!Array.isArray(value.rows)){
          throw new Error('The inventory does not match the selected scenario.');
        }
        if(!controller.signal.aborted){
          data=value as GuideMetadata;
          condition=value.conditions?.some((c:{id:string})=>c.id===focusCondition)?focusCondition:
            value.conditions?.find((c:{purpose:string})=>c.purpose==='baseline')?.id||value.conditions?.[0]?.id||'*';
        }
      }).catch(reason=>{if(!controller.signal.aborted)error=reason.message;})
      .finally(()=>{if(!controller.signal.aborted)loading=false;});
    return()=>controller.abort();
  });
</script>

<main class="metadata-page" aria-labelledby="metadata-title">
  <span class="eyebrow">CONFIGURATION AND EVIDENCE</span>
  <h1 id="metadata-title">Metadata</h1>
  <p class="introduction">Choose an execution to inspect the settings it used and the results it saved. Each file explains who created it, who uses it and whether it is an input or an output. A published projection is a lab-created view of retained evidence; it may omit fields required to run the original library configuration.</p>
  {#if focusRequirement}<p class="requirement-focus">Showing {focusRequirement}. <button class="text-button" onclick={()=>{focusRequirement='';}}>Show all modules</button></p>{/if}
  <div class="metadata-filters">
    <label>Scenario<select value={scenarioId} onchange={chooseScenario}>
      {#each scenarios as scenario}<option value={scenario.id}>{scenario.name}</option>{/each}
    </select></label>
    <label>Condition<select bind:value={condition} disabled={!data?.conditions.length}>
      <option value="*">Compare all recorded conditions</option>
      {#each data?.conditions??[] as item}
        <option value={item.id}>{conditionInfo(item.purpose).label}</option>
      {/each}
    </select></label>
    <label>Find a module, file or status<input type="search" bind:value={query} placeholder="Fabric, PRIVATE, CAP-FAB-01…" /></label>
  </div>
  {#if loading}<p role="status">Loading the selected demo’s capture inventory…</p>
  {:else if error}<p class="metadata-notice error" role="alert">{error}</p>
  {:else if data}
    <div class="metadata-context">
      {#if selectedCondition}<p><strong>{conditionInfo(selectedCondition.purpose).label}.</strong> {conditionInfo(selectedCondition.purpose).description}</p>
      {:else}<p>Shared settings appear once when their published bytes, format and role match. Results remain attached to their own execution, even when the same checks passed.</p>{/if}
      {#if data.run_id}<details><summary>Recording reference</summary><p class="run-identity">{scenarioName(scenarioId)} · <code>{data.run_id}</code></p><p>{data.notice}</p></details>{/if}
    </div>
    <div class="metadata-table-wrap">
      <table>
        <caption>{scenarioName(scenarioId)} · {groupedRows.length} module and operation entries</caption>
        <thead><tr><th scope="col">Module</th><th scope="col">Steps</th><th scope="col">YAML / JSON file</th><th scope="col">Status</th><th scope="col">Location</th><th scope="col">Apply to scenario</th></tr></thead>
        <tbody>
          {#each groupedRows as group (group.id)}
            {@const row=group.rows[0]}
            {@const artifacts=artifactGroups(group.rows)}
            <tr data-requirement={row.id}>
              <th scope="row"><strong>{row.module}</strong><span class="requirement-id">{row.id}</span></th>
              <td><span class="step-numbers">{row.steps.join(', ')}</span><p>{row.operation}</p></td>
              <td>
                {#if artifacts.length}<ul class="file-list">{#each [...new Set(artifacts.map(a=>filename(a.uses[0].artifact.path)))] as name}<li><code>{name}</code></li>{/each}</ul>
                {:else if row.filenames.length}<ul class="file-list">{#each row.filenames as name}<li><code>{name}</code></li>{/each}</ul>
                {:else}<span class="muted">No additional file required.</span>{/if}
              </td>
              <td>
                <span class:missing={group.rows.some(r=>r.status==='missing')} class="metadata-status">{stateSummary(group.rows)}</span>
                {#if row.status==='exists'}<span class="privacy-label">{[...new Set(group.rows.map(r=>access(r.privacy)))].join(' · ')}</span>{/if}
                <span class="execution-status">Execution: {[...new Set(group.rows.map(r=>r.execution_status.replaceAll('_',' ')))].join(' · ')}</span>
              </td>
              <td>
                {#each artifacts as artifactGroup}
                  {@const artifact=artifactGroup.uses[0].artifact}
                  <details class="artifact-link">
                    <summary>{filename(artifact.path)}<small>{artifact.direction||'Saved capture'}{artifactGroup.uses.length>1?` · shared by ${artifactGroup.uses.length} executions`:condition==='*'?` · ${scopeName(artifactGroup.uses[0].purpose)}`:''}</small></summary>
                    {#if artifact.purpose}<p>{artifact.purpose}</p>{/if}
                    <dl class="artifact-purpose">
                      {#if artifact.producer}<div><dt>Created by</dt><dd>{artifact.producer}</dd></div>{/if}
                      {#if artifact.consumer}<div><dt>Used by</dt><dd>{artifact.consumer}</dd></div>{/if}
                      <div><dt>Published form</dt><dd>{artifact.representation||artifact.kind.replaceAll('-',' ')}</dd></div>
                      {#if artifact.source_schema}<div><dt>Original format</dt><dd>{artifact.source_schema}</dd></div>{/if}
                    </dl>
                    {#each artifactGroup.uses as use}
                      <div class="condition-file">{#if artifactGroup.uses.length>1||condition==='*'}<strong>{scopeName(use.purpose)}</strong>{/if}
                      {#if use.artifact.url}<a href={use.artifact.url} target="_blank" rel="noreferrer">Open this saved file ↗</a>
                      {:else}<small>Awaiting check-in; GitHub link unavailable.</small>{/if}</div>
                    {/each}
                  </details>
                {/each}
                {#if group.rows.some(r=>privateCount(r))}<span class="private-location">Private source captures are retained outside Git. The published views above omit private data.</span>{/if}
                {#if !row.artifacts.length}<span class="muted">{row.status==='not-used'?'Not used by this preset.':'No published file available.'}</span>{/if}
              </td>
              <td>
                <span>{row.scenario_ids.map(scenarioName).join(', ')||'None currently'}</span>
                {#if group.rows.some(r=>r.condition_id)}<details class="condition-identity"><summary>{group.rows.length===1?scopeName(row.condition_purpose):`${group.rows.length} recorded executions`}</summary>{#each group.rows.filter(r=>r.condition_id) as entry}<p>{scopeName(entry.condition_purpose)}<br /><code>{entry.condition_id}</code></p>{/each}</details>{/if}
              </td>
            </tr>
          {:else}<tr><td colspan="6">No entries match this filter.</td></tr>{/each}
        </tbody>
      </table>
    </div>
  {/if}
</main>

<style>
  .artifact-purpose{margin:10px 0}.artifact-purpose div{display:grid;grid-template-columns:80px minmax(0,1fr);gap:8px;margin:6px 0}.artifact-purpose dt{color:var(--muted)}.artifact-purpose dd{margin:0}.artifact-link summary{cursor:pointer;color:var(--teal)}.artifact-link p{margin:9px 0}.condition-file{display:grid;gap:4px;margin-top:8px}.condition-file strong{font-weight:500}.condition-identity summary{cursor:pointer}
  .metadata-page{max-width:1560px;margin:0 auto;padding:42px 30px 50px}.metadata-page h1{margin-bottom:13px}.introduction{max-width:900px;font-size:14px;line-height:1.75;color:var(--muted)}
  .metadata-filters{display:grid;grid-template-columns:minmax(180px,1fr) minmax(220px,1fr) minmax(240px,1.4fr);gap:18px;margin:26px 0 12px}.metadata-filters label{margin:0}.metadata-filters input{display:block;margin-top:4px;width:100%;border:1px solid var(--line);border-radius:4px;background:#fff;padding:8px 9px;font-size:13px;color:var(--ink)}
  .metadata-context{font-size:12px;line-height:1.7;margin:17px 0 21px;color:var(--muted)}.metadata-context p{margin:0 0 5px}.run-identity code{font-size:11px}.metadata-notice{padding:15px 18px;border:1px solid var(--line);background:#fff;border-radius:5px;font-size:13px}.error{color:#8b3434}
  .metadata-table-wrap{overflow:auto;border:1px solid var(--line);border-radius:6px;background:#fff}table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:12px;line-height:1.6}caption{text-align:left;padding:13px 15px;color:var(--muted);font-size:11px;border-bottom:1px solid var(--line)}thead{background:#f6f9fb}th,td{text-align:left;vertical-align:top;padding:14px 13px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}thead th{font-weight:600;font-size:11px;color:var(--muted)}thead th:nth-child(1){width:15%}thead th:nth-child(2){width:18%}thead th:nth-child(3){width:19%}thead th:nth-child(4){width:12%}thead th:nth-child(5){width:22%}thead th:nth-child(6){width:14%}tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}tbody th{font-weight:400}td p{margin:5px 0 0}.requirement-id{display:block;font-family:ui-monospace,monospace;font-size:10px;color:var(--muted);margin-top:7px}.step-numbers{color:var(--teal);font-weight:600}.file-list{list-style:none;padding:0;margin:0}.file-list li+li{margin-top:7px}.file-list code{font-size:11px}.metadata-status{display:inline-block;color:var(--teal);font-size:10px;font-weight:650;letter-spacing:.3px}.metadata-status.missing{color:#8b3434}.privacy-label,.execution-status{display:block;font-size:10px;margin-top:5px;color:var(--muted)}.execution-status{margin-top:10px}.artifact-link{margin-bottom:12px}.artifact-link:last-child{margin-bottom:0}.artifact-link small,.private-location{display:block;font-size:10px;color:var(--muted);margin-top:3px}.private-location{margin-top:10px}.condition-identity{display:block;font-size:10px;color:var(--muted);margin-top:8px}.condition-identity code{font-size:9px}
  @media(max-width:900px){.metadata-page{padding:32px 22px}.metadata-filters{grid-template-columns:1fr 1fr}.metadata-filters label:last-child{grid-column:1/-1}table{min-width:930px}}
  @media(max-width:560px){.metadata-page{padding:28px 19px}.metadata-filters{grid-template-columns:1fr;gap:12px}.metadata-filters label:last-child{grid-column:auto}.metadata-page h1{font-size:27px}.run-identity code{overflow-wrap:anywhere}}
</style>
