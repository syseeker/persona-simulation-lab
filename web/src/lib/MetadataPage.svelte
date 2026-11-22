<script lang="ts">
  import {onMount} from 'svelte';
  import type {CaptureAvailability, CapturePrivacy, GuideMetadata, MetadataRow} from './metadataTypes';

  let {scenarioId='photography',focusRequirement='',focusCondition='',onScenarioChange=(_id:string)=>{}}:
    {scenarioId?:string;focusRequirement?:string;focusCondition?:string;onScenarioChange?:(id:string)=>void}=$props();
  const scenarios=[{id:'photography',name:'Photography'},{id:'boardgames',name:'Board games'},
    {id:'dreamjob',name:'Retail learning'}];
  let data=$state<GuideMetadata|null>(null),error=$state(''),loading=$state(false),mounted=$state(false);
  let condition=$state(''),query=$state('');
  const visibleRows=$derived((data?.rows??[]).filter(row=>
    (!focusRequirement||row.id===focusRequirement)&&
    (!condition||!row.condition_id||row.condition_id===condition)&&
    `${row.module} ${row.id} ${row.operation} ${row.filenames.join(' ')} ${availability(row.status)} ${row.status==='exists'?access(row.privacy):''}`.toLowerCase().includes(query.toLowerCase())));

  function availability(value:CaptureAvailability){
    return ({exists:'EXISTS',missing:'NOT EXIST','not-used':'NOT USED',unavailable:'UNAVAILABLE'})[value];
  }
  function access(value:CapturePrivacy){
    return ({public:'PUBLIC',private:'PRIVATE',projection:'PARTIAL',unknown:'ACCESS UNKNOWN'})[value];
  }
  function scenarioName(id:string){return scenarios.find(item=>item.id===id)?.name??id;}
  function privateCount(row:MetadataRow){return row.artifacts.filter(item=>item.privacy==='private').length;}
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
          condition=value.conditions?.some((c:{id:string})=>c.id===focusCondition)?focusCondition:'';
        }
      }).catch(reason=>{if(!controller.signal.aborted)error=reason.message;})
      .finally(()=>{if(!controller.signal.aborted)loading=false;});
    return()=>controller.abort();
  });
</script>

<main class="metadata-page" aria-labelledby="metadata-title">
  <span class="eyebrow">CONFIGURATION AND EVIDENCE</span>
  <h1 id="metadata-title">Metadata</h1>
  <p class="introduction">Inspect the settings and saved outputs behind each demo. The files below connect a library operation to its configuration or result. Private originals stay private; published projections show a selected part of the original.</p>
  {#if focusRequirement}<p class="requirement-focus">Showing {focusRequirement}. <button class="text-button" onclick={()=>{focusRequirement='';}}>Show all modules</button></p>{/if}
  <div class="metadata-filters">
    <label>Scenario<select value={scenarioId} onchange={chooseScenario}>
      {#each scenarios as scenario}<option value={scenario.id}>{scenario.name}</option>{/each}
    </select></label>
    <label>Condition<select bind:value={condition} disabled={!data?.conditions.length}>
      <option value="">All conditions</option>
      {#each data?.conditions??[] as item}
        <option value={item.id}>{item.purpose} · {item.id.slice(0,8)}</option>
      {/each}
    </select></label>
    <label>Find a module, file or status<input type="search" bind:value={query} placeholder="Fabric, PRIVATE, CAP-FAB-01…" /></label>
  </div>
  {#if loading}<p role="status">Loading the selected demo’s capture inventory…</p>
  {:else if error}<p class="metadata-notice error" role="alert">{error}</p>
  {:else if data}
    <div class="metadata-context">
      <p>{data.notice}</p>
      {#if data.run_id}<p class="run-identity">Selected demo: <code>{data.run_id}</code></p>{/if}
    </div>
    <div class="metadata-table-wrap">
      <table>
        <caption>{scenarioName(scenarioId)} · {visibleRows.length} module and operation entries</caption>
        <thead><tr><th scope="col">Module</th><th scope="col">Steps</th><th scope="col">YAML / JSON file</th><th scope="col">Status</th><th scope="col">Location</th><th scope="col">Apply to scenario</th></tr></thead>
        <tbody>
          {#each visibleRows as row (`${row.id}:${row.condition_id??'unused'}`)}
            <tr data-requirement={row.id}>
              <th scope="row"><strong>{row.module}</strong><span class="requirement-id">{row.id}</span></th>
              <td><span class="step-numbers">{row.steps.join(', ')}</span><p>{row.operation}</p></td>
              <td>
                {#if row.filenames.length}<ul class="file-list">{#each row.filenames as name}<li><code>{name}</code></li>{/each}</ul>
                {:else}<span class="muted">No additional file required.</span>{/if}
              </td>
              <td>
                <span class:missing={row.status==='missing'} class="metadata-status">{availability(row.status)}</span>
                {#if row.status==='exists'}<span class="privacy-label">{access(row.privacy)}</span>{/if}
                {#if row.condition_id}<span class="execution-status">Condition: {row.execution_status.replaceAll('_',' ')}</span>{/if}
              </td>
              <td>
                {#each row.artifacts.filter(item=>item.privacy!=='private') as artifact}
                  <div class="artifact-link">
                    {#if artifact.url}<a href={artifact.url} target="_blank" rel="noreferrer">{artifact.path?.split('/').at(-1)?.replace(/^[a-f0-9]{24}-/,'')} ↗</a>
                    {:else}<span>{artifact.path?.split('/').at(-1)?.replace(/^[a-f0-9]{24}-/,'')}</span><small>Awaiting check-in; GitHub link unavailable.</small>{/if}
                    <small>{artifact.kind.replaceAll('-',' ')}</small>
                  </div>
                {/each}
                {#if privateCount(row)}<span class="private-location">{privateCount(row)} private original{privateCount(row)===1?'':'s'} retained. No public link.</span>{/if}
                {#if !row.artifacts.length}<span class="muted">{row.status==='not-used'?'Not used by this preset.':'No published file available.'}</span>{/if}
              </td>
              <td>
                <span>{row.scenario_ids.map(scenarioName).join(', ')||'None currently'}</span>
                {#if row.condition_id}<small class="condition-identity">{row.condition_purpose}<br /><code>{row.condition_id}</code></small>{/if}
              </td>
            </tr>
          {:else}<tr><td colspan="6">No entries match this filter.</td></tr>{/each}
        </tbody>
      </table>
    </div>
  {/if}
</main>

<style>
  .metadata-page{max-width:1560px;margin:0 auto;padding:42px 30px 50px}.metadata-page h1{margin-bottom:13px}.introduction{max-width:900px;font-size:14px;line-height:1.75;color:var(--muted)}
  .metadata-filters{display:grid;grid-template-columns:minmax(180px,1fr) minmax(220px,1fr) minmax(240px,1.4fr);gap:18px;margin:26px 0 12px}.metadata-filters label{margin:0}.metadata-filters input{display:block;margin-top:4px;width:100%;border:1px solid var(--line);border-radius:4px;background:#fff;padding:8px 9px;font-size:13px;color:var(--ink)}
  .metadata-context{font-size:12px;line-height:1.7;margin:17px 0 21px;color:var(--muted)}.metadata-context p{margin:0 0 5px}.run-identity code{font-size:11px}.metadata-notice{padding:15px 18px;border:1px solid var(--line);background:#fff;border-radius:5px;font-size:13px}.error{color:#8b3434}
  .metadata-table-wrap{overflow:auto;border:1px solid var(--line);border-radius:6px;background:#fff}table{border-collapse:collapse;width:100%;table-layout:fixed;font-size:12px;line-height:1.6}caption{text-align:left;padding:13px 15px;color:var(--muted);font-size:11px;border-bottom:1px solid var(--line)}thead{background:#f6f9fb}th,td{text-align:left;vertical-align:top;padding:14px 13px;border-bottom:1px solid var(--line);overflow-wrap:anywhere}thead th{font-weight:600;font-size:11px;color:var(--muted)}thead th:nth-child(1){width:15%}thead th:nth-child(2){width:18%}thead th:nth-child(3){width:19%}thead th:nth-child(4){width:12%}thead th:nth-child(5){width:22%}thead th:nth-child(6){width:14%}tbody tr:last-child td,tbody tr:last-child th{border-bottom:0}tbody th{font-weight:400}td p{margin:5px 0 0}.requirement-id{display:block;font-family:ui-monospace,monospace;font-size:10px;color:var(--muted);margin-top:7px}.step-numbers{color:var(--teal);font-weight:600}.file-list{list-style:none;padding:0;margin:0}.file-list li+li{margin-top:7px}.file-list code{font-size:11px}.metadata-status{display:inline-block;color:var(--teal);font-size:10px;font-weight:650;letter-spacing:.3px}.metadata-status.missing{color:#8b3434}.privacy-label,.execution-status{display:block;font-size:10px;margin-top:5px;color:var(--muted)}.execution-status{margin-top:10px}.artifact-link{margin-bottom:12px}.artifact-link:last-child{margin-bottom:0}.artifact-link small,.private-location{display:block;font-size:10px;color:var(--muted);margin-top:3px}.private-location{margin-top:10px}.condition-identity{display:block;font-size:10px;color:var(--muted);margin-top:8px}.condition-identity code{font-size:9px}
  @media(max-width:900px){.metadata-page{padding:32px 22px}.metadata-filters{grid-template-columns:1fr 1fr}.metadata-filters label:last-child{grid-column:1/-1}table{min-width:930px}}
  @media(max-width:560px){.metadata-page{padding:28px 19px}.metadata-filters{grid-template-columns:1fr;gap:12px}.metadata-filters label:last-child{grid-column:auto}.metadata-page h1{font-size:27px}.run-identity code{overflow-wrap:anywhere}}
</style>
