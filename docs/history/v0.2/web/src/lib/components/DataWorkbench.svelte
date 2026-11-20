<script lang="ts">
  import { onMount } from 'svelte';
  import { labApi, pretty } from '#lib/api.ts';
  import CodeReference from './CodeReference.svelte';
  import ModelCallLedger from './ModelCallLedger.svelte';
  let { onchoose = (_ids: string[], _source: string) => {}, ongenerated = (_job: any) => {} } = $props();
  let datasets = $state<any[]>([]), data = $state<any>(null), selected = $state<string[]>([]);
  let source = $state('hf-profile-only'), search = $state(''), area = $state('');
  let offset = $state(0), busy = $state(false), error = $state(''), detail = $state<any>(null);
  let operation = $state('scenarios'), count = $state(5), fields = $state<any[]>([]);
  let job = $state<any>(null), jobs = $state<any[]>([]), instructions = $state(false);
  let chosenRecord = $state('');
  let datasetRequest = 0;
  const meta = $derived(datasets.find(item => item.source === source));
  const generatedRecords: any[] = $derived(job?.result?.records ?? []);
  const selectedResult = $derived(generatedRecords.find(record => record.profile.uuid === chosenRecord) ?? generatedRecords[0]);
  function configuredFields() {
    return fields.map(field => ({ name: field.name, type: field.type, description: field.description,
      ...(['integer','decimal'].includes(field.type) ? { minimum: field.minimum, maximum: field.maximum } : {}),
      choices: field.type === 'enum' ? field.choices : [] }));
  }
  async function load() {
    const request = ++datasetRequest;
    busy = true; error = '';
    try { const value = await labApi('dataset-browse', { source, offset, limit: 20, search, ...(area ? { planning_area: area } : {}) }); if (request === datasetRequest) data = value; }
    catch (e) { if (request === datasetRequest) { data = null; error = e instanceof Error ? e.message : 'Dataset unavailable'; } }
    finally { if (request === datasetRequest) busy = false; }
  }
  async function chooseSource() { datasetRequest++; selected = []; detail = null; offset = 0; busy = false; if (meta?.ready) await load(); else data = null; }
  async function shuffle() {
    const request = ++datasetRequest;
    busy = true; error = '';
    try { const result = await labApi('persona-sample', { source, count: 1, filters: { search, ...(area ? { planning_area: area } : {}) } });
      if (request === datasetRequest) { selected = result.source_ids; detail = result.records[0]; } }
    catch (e) { if (request === datasetRequest) error = e instanceof Error ? e.message : 'Could not select a profile'; }
    finally { if (request === datasetRequest) busy = false; }
  }
  function toggle(id: string) { selected = selected.includes(id) ? selected.filter(value => value !== id) : [...selected, id].slice(0, 10); }
  function preset(which: string) {
    const field = which === 'salary' ? { name: 'last_drawn_salary_sgd', type: 'decimal', minimum: 0,
      description: 'A hypothetical last drawn gross monthly salary in Singapore dollars. A generated scenario assumption, not an observed fact.', choices: [] }
      : { name: 'favourite_brands', type: 'text-list', description: 'Hypothetical favourite brands consistent with this synthetic scenario. These are generated preferences, not source observations.', choices: [] };
    if (!fields.some(item => item.name === field.name)) fields = [...fields, field];
  }
  async function generate() {
    busy = true; error = '';
    try { job = await labApi('workbench', { operation, source, source_ids: selected, count, fields: configuredFields() }); chosenRecord = ''; }
    catch (e) { error = e instanceof Error ? e.message : 'Generation could not start'; }
    finally { busy = false; }
  }
  async function openJob(id: string) { try { job = await labApi('workbench-job?job_id=' + id); } catch(e) { error = String(e); } }
  async function cancel() { if (job) job = await labApi('workbench-cancel', { job_id: job.job_id }); }
  onMount(() => {
    void labApi('datasets').then(result => { datasets = result.datasets; if (datasets[0]?.ready) void load(); }).catch(e => error = e.message);
    void labApi('workbench-history').then(result => jobs = result).catch(e => error = e.message);
    let polling = false;
    const timer = setInterval(async () => {
      if (polling || !job || !['queued','running'].includes(job.status)) return;
      polling = true;
      try { job = await labApi('workbench-job?job_id=' + job.job_id); }
      catch (e) { error = e instanceof Error ? e.message : 'Job status unavailable'; }
      finally { polling = false; }
    }, 1500);
    return () => clearInterval(timer);
  });
</script>

<div class="lab-stack">
  <div class="lab-note">Explore the original country dataset, then build a separately labelled derived dataset. Browsing, sampling and inspecting saved jobs make no inference calls.</div>
  <section class="lab-card" aria-label="Persona dataset explorer">
    <div class="lab-eyebrow">01 / Original data</div><h2>Meet the available Singapore personas</h2>
    <div class="lab-grid">
      {#each datasets as item}<button class:active={source === item.source} class="lab-button" onclick={() => { source = item.source; void chooseSource(); }}><strong>{item.name}</strong><div class="lab-badges"><span class="lab-badge">{item.row_count?.toLocaleString() ?? 0} local records</span><span class="lab-badge">{item.ready ? 'Ready to explore' : 'Setup required'}</span></div></button>{/each}
    </div>
    {#if meta}<p>{meta.notice}</p><div class="lab-path">Revision · {meta.revision}</div><p>{meta.license}</p>
      <div class="lab-badges"><span class="lab-badge">{meta.columns?.length ?? 0} columns</span><span class="lab-badge">{meta.ocean_fields?.length ? 'Source OCEAN fields available' : 'No OCEAN fields available'}</span></div>
      {#if !meta.ready}<div class="lab-note">{meta.reason}<p>{meta.setup}</p><a class="lab-link" href={meta.source_url} target="_blank" rel="noreferrer">Official dataset reference</a></div>{/if}
      <details><summary>Compare source schema</summary><div class="lab-table-wrap"><table class="lab-table"><thead><tr><th>Field</th><th>Type</th></tr></thead><tbody>{#each meta.columns ?? [] as column}<tr><td>{column.name}</td><td>{column.type}</td></tr>{/each}</tbody></table></div></details>
    {/if}
    <div class="lab-grid"><label class="lab-label">Search source fields<input bind:value={search} placeholder="Occupation, hobby or career ambition" /></label><label class="lab-label">Planning area<input bind:value={area} placeholder="Optional exact area" /></label></div>
    <div class="lab-actions"><button class="lab-button" onclick={() => { offset = 0; void load(); }} disabled={busy || !meta?.ready}>Search profiles</button><button class="lab-button" onclick={shuffle} disabled={busy || !meta?.ready}>Random profile</button><button class="lab-button primary" onclick={() => onchoose(selected, source)} disabled={!selected.length}>Use {selected.length} locked profile{selected.length === 1 ? '' : 's'} in simulation</button></div>
    {#if error}<div class="lab-error" role="alert">{error}</div>{/if}
    {#if busy}<p class="lab-loading" role="status">Reading the selected local dataset…</p>{/if}
    {#if data}<p class="lab-muted">{data.total.toLocaleString()} matching source records · {selected.length} selected. The selection retains source IDs and exact source records.</p><div class="lab-table-wrap"><table class="lab-table"><thead><tr><th>Select</th><th>Age</th><th>Occupation</th><th>Area</th><th>Source profile</th></tr></thead><tbody>{#each data.records as record}<tr class:selected={selected.includes(record.source_id)}><td><input aria-label={'Select profile ' + record.source_id} type="checkbox" checked={selected.includes(record.source_id)} onchange={() => toggle(record.source_id)} /></td><td>{record.profile.age ?? 'Unknown'}</td><td>{record.profile.occupation ?? 'Unknown'}</td><td>{record.profile.planning_area ?? record.profile.district ?? 'Unknown'}</td><td><button onclick={() => detail = record}>Inspect original fields</button></td></tr>{/each}</tbody></table></div><div class="lab-actions"><button class="lab-button" disabled={busy || offset === 0} onclick={() => { offset = Math.max(0, offset - 20); void load(); }}>Previous records</button><span class="lab-muted">{offset + 1}–{Math.min(offset + 20, data.total)}</span><button class="lab-button" disabled={busy || !data.has_more} onclick={() => { offset += 20; void load(); }}>Next records</button></div>{/if}
    {#if detail}<div class="lab-note"><strong>Original profile · {detail.source_id}</strong><div class="lab-path">SHA-256 · {detail.original_profile_sha256}</div></div><pre class="lab-code">{pretty(detail.profile)}</pre>{/if}
    <CodeReference source="personas" label="Where the dataset explorer enters the application" />
  </section>
  <section class="lab-card" aria-label="Data Designer studio">
    <div class="lab-eyebrow">02 / Derived data</div><h2>Extend the data with Data Designer</h2>
    <p>Use selected source records as seeds. Every generated cell is hypothetical; new rows receive new identities and preserve their seed lineage.</p>
    <div class="lab-grid"><label class="lab-label">Data Designer operation<select bind:value={operation}><option value="scenarios">Generate learning scenarios</option><option value="columns">Add columns to selected profiles</option><option value="profiles">Generate additional synthetic profile rows</option></select></label><label class="lab-label">Preview rows<input type="number" min="1" max="20" bind:value={count} /></label></div>
    <div class="lab-actions"><button class="lab-button" onclick={() => preset('salary')}>Add salary example</button><button class="lab-button" onclick={() => preset('brands')}>Add favourite brands example</button><button class="lab-button" onclick={() => fields = [...fields, { name: 'custom_field_' + (fields.length + 1), type: 'text', description: '', choices: [] }]} disabled={fields.length >= 8}>Add custom column</button></div>
    {#each fields as field, index}<div class="lab-card"><div class="lab-grid"><label class="lab-label">Column name<input bind:value={field.name} /></label><label class="lab-label">Column type<select bind:value={field.type}><option value="text">Text</option><option value="integer">Integer</option><option value="decimal">Decimal</option><option value="boolean">Boolean</option><option value="enum">Enumeration</option><option value="text-list">Text list</option></select></label></div><label class="lab-label">Generation instruction<textarea bind:value={field.description} placeholder="Describe this hypothetical field and how it should use the seed profile"></textarea></label>{#if ['integer','decimal'].includes(field.type)}<div class="lab-grid"><label class="lab-label">Minimum<input type="number" bind:value={field.minimum} /></label><label class="lab-label">Maximum<input type="number" bind:value={field.maximum} /></label></div>{/if}{#if field.type === 'enum'}<label class="lab-label">Choices, separated by commas<input value={field.choices.join(', ')} oninput={event => field.choices = event.currentTarget.value.split(',').map(value => value.trim()).filter(Boolean)} /></label>{/if}<button class="lab-button" onclick={() => fields = fields.filter((_, i) => i !== index)}>Remove column</button></div>{/each}
    <div class="lab-note">Pipeline: source snapshot → typed column definitions → real Data Designer generation → schema validation → derived records with lineage. Live model calls share a 120-call job cap; automatic restarts and corrections are disabled.</div>
    <div class="lab-actions"><button class="lab-button" onclick={() => instructions = !instructions}>Preview generation configuration</button><button class="lab-button primary" onclick={generate} disabled={busy || !meta?.ready || job && ['queued','running'].includes(job.status)}>Generate live preview</button></div>
    {#if instructions}<pre class="lab-code">{pretty({ operation, source, source_ids: selected, count, fields: configuredFields() })}</pre>{/if}
    {#if job}<h3>Generation job</h3><div class="lab-badges"><span class="lab-badge">{job.status}</span><span class="lab-badge">{job.calls} / {job.budget} calls</span></div>{#if job.error}<div class="lab-error">{job.error}</div>{/if}
      <ModelCallLedger records={job.usage} admittedCalls={job.calls} budget={job.budget} jobStatus={job.status} />
      {#if ['running','queued'].includes(job.status)}<button class="lab-button danger" onclick={cancel}>Cancel generation</button>{/if}{#if job.result}
      {#each job.result.warnings ?? [] as warning}<div class="lab-note">{warning.notice ?? warning.error}</div>{/each}
      {#if generatedRecords.length}<label class="lab-label">Preview row to use<select value={selectedResult?.profile.uuid} onchange={event => chosenRecord = event.currentTarget.value}>{#each generatedRecords as record, index}<option value={record.profile.uuid}>Row {index + 1} · {record.scenario?.story_title ?? record.profile.occupation ?? record.kind}</option>{/each}</select></label>
        <div class="lab-table-wrap"><table class="lab-table"><thead><tr><th>Record</th><th>Identity</th><th>Parent source</th><th>Generated fields</th></tr></thead><tbody>{#each generatedRecords as record, index}<tr class:selected={record.profile.uuid === selectedResult?.profile.uuid}><td>Row {index + 1}<br />{record.kind}</td><td>{record.profile.uuid}</td><td>{record.source_id}</td><td>{Object.keys(record.generated_fields ?? {}).join(', ') || (record.scenario ? 'Learning scenario' : 'New profile')}</td></tr>{/each}</tbody></table></div>
        <h3>Selected row and its provenance</h3><pre class="lab-code">{pretty(selectedResult)}</pre>
        <p class="lab-muted">Use one selected row for one citizen story. Choosing a generated scenario explicitly applies its typed learning goal and budget to the simulator and advisor. Availability remains narrative context; salary and brand hypotheses never become course constraints. Original records and eligibility remain unchanged.</p><button class="lab-button primary" onclick={() => ongenerated({ ...job, selected_record_ids: [selectedResult.profile.uuid] })}>Use generated data in the guided story</button>
      {/if}
      <details><summary>Native generation result and artifacts</summary><pre class="lab-code">{pretty(job.result)}</pre></details>
    {/if}{/if}
    {#if jobs.length}<details><summary>Reopen a saved generation job</summary><div class="lab-actions">{#each jobs as saved}<button class="lab-button" onclick={() => openJob(saved.job_id)}>{saved.spec.operation} · {saved.status} · {new Date(saved.started_at).toLocaleDateString('en-SG')}</button>{/each}</div></details>{/if}
    <CodeReference source="designer" label="Inspect the Data Designer pipeline implementation" />
  </section>
</div>
