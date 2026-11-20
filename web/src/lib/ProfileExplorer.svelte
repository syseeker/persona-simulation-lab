<script lang="ts">
  import { onMount } from 'svelte';
  import { fieldGroups } from './fieldGroups.ts';
  import type { DatasetMeta, PersonaSource, ProfilePage, ProfileOptions, SourceRecord } from './profileTypes.ts';

  let { onshowschema }: { onshowschema: () => void } = $props();
  let source = $state<PersonaSource>('hf-profile-only');
  let search = $state(''), ageMin = $state(''), ageMax = $state(''), area = $state(''), education = $state('');
  let limit = $state('10');
  let catalogue = $state<DatasetMeta[]>([]);
  let options = $state<ProfileOptions | null>(null);
  let result = $state<ProfilePage | null>(null);
  let selectedIndex = $state(0);
  let loading = $state(true), error = $state(''), restored = $state(false);
  let applied = $state('');
  const preferenceKey = 'persona-lab-guide:profile-filters:v1';
  let serial = 0, controller: AbortController | undefined;
  const currentMeta = $derived(catalogue.find(item => item.source === source));
  const selected = $derived(result?.records[selectedIndex]);
  const geography = $derived(source === 'ngc' ? 'district' : 'planning_area');
  const filterSignature = $derived(JSON.stringify({ source, search, ageMin, ageMax, area, education, limit }));
  const unapplied = $derived(Boolean(result && applied !== filterSignature));
  const detailGroups = $derived(fieldGroups.map(group => ({ ...group,
    fields: group.fields.filter(([name]) => selected && Object.hasOwn(selected.profile, name))
  })).filter(group => group.fields.length));

  async function read<T>(url: string, signal: AbortSignal): Promise<T> {
    const response = await fetch(url, { signal, cache: 'no-store' });
    const body = await response.json();
    if (!response.ok) throw new Error(body.error || 'The local dataset could not be read.');
    return body as T;
  }
  async function loadPage(offset = 0, refresh = false) {
    const ticket = ++serial;
    controller?.abort(); controller = new AbortController();
    const signal = controller.signal;
    loading = true; error = ''; result = null; selectedIndex = 0;
    const requestedSource = source, signature = filterSignature;
    try {
      if (!catalogue.length || refresh) {
        const value = await read<{ datasets: DatasetMeta[] }>('/api/local-datasets', signal);
        if (ticket !== serial) return;
        catalogue = value.datasets;
      }
      const meta = catalogue.find(item => item.source === requestedSource);
      if (!meta?.ready) throw new Error(meta?.reason || 'This distribution is not installed or ready. Check its setup, then retry.');
      const query = new URLSearchParams({ source: requestedSource, limit, offset: String(offset) });
      for (const [key, value] of [['search', search], ['age_min', ageMin], ['age_max', ageMax], ['planning_area', area], ['education_level', education]]) {
        if (value.trim()) query.set(key, value.trim());
      }
      const [page, facets] = await Promise.all([
        read<ProfilePage>(`/api/personas?${query}`, signal),
        options?.source === requestedSource && !refresh ? Promise.resolve(options) : read<ProfileOptions>(`/api/persona-options?source=${requestedSource}`, signal)
      ]);
      if (ticket !== serial) return;
      result = page; options = facets; applied = signature;
    } catch (failure) {
      if (ticket === serial && !(failure instanceof DOMException && failure.name === 'AbortError')) {
        error = failure instanceof Error ? failure.message : 'The local dataset could not be read.';
      }
    } finally { if (ticket === serial) loading = false; }
  }
  function clearFilters() { search = ''; ageMin = ''; ageMax = ''; area = ''; education = ''; }
  function changeSource(next: PersonaSource) {
    if (source === next) return;
    source = next; clearFilters(); options = null; void loadPage();
  }
  function display(value: unknown): string {
    if (value === null) return 'Not supplied (null)';
    if (value === undefined) return 'Not in this source';
    if (value === '') return 'Empty source value';
    return typeof value === 'object' ? JSON.stringify(value) : String(value);
  }
  function name(record: SourceRecord, index: number) {
    const profile = record.profile;
    const parts = [profile.first_name, profile.middle_name, profile.last_name].filter(value => typeof value === 'string' && value.trim());
    return parts.length ? parts.join(' ') : `Profile ${((result?.offset ?? 0) + index + 1).toLocaleString('en-SG')}`;
  }
  function excerpt(value: unknown, maximum = 110) {
    const text = display(value); return text.length > maximum ? `${text.slice(0, maximum)}…` : text;
  }
  function trait(value: unknown): { t_score: number; label: string; description: string } | null {
    try {
      const parsed = typeof value === 'string' ? JSON.parse(value) : value;
      return parsed && typeof parsed === 'object' && typeof parsed.t_score === 'number' && typeof parsed.label === 'string' && typeof parsed.description === 'string' ? parsed : null;
    } catch { return null; }
  }
  onMount(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(preferenceKey) || 'null');
      if (saved && ['hf-profile-only', 'ngc'].includes(saved.source)) {
        source = saved.source;
        search = typeof saved.search === 'string' ? saved.search.slice(0, 200) : '';
        ageMin = /^\d{2,3}$/.test(saved.ageMin) ? saved.ageMin : '';
        ageMax = /^\d{2,3}$/.test(saved.ageMax) ? saved.ageMax : '';
        area = typeof saved.area === 'string' ? saved.area.slice(0, 100) : '';
        education = typeof saved.education === 'string' ? saved.education.slice(0, 150) : '';
        limit = ['10', '20'].includes(saved.limit) ? saved.limit : '10';
      }
    } catch { /* Preferences never contain profile rows. */ }
    restored = true; void loadPage();
    return () => { serial += 1; controller?.abort(); };
  });
  $effect(() => {
    const preference = filterSignature;
    if (restored) try { localStorage.setItem(preferenceKey, preference); } catch { /* Optional preference. */ }
  });
</script>

<main class="profile-explorer" aria-label="Explore installed persona profiles">
  <header class="explorer-heading">
    <div><span class="eyebrow">READ THE INSTALLED SOURCE</span><h1>Explore profiles.</h1><p>Browse a page of original synthetic profiles, then narrow the full local corpus with filters.</p></div>
    <span class="reader-badge">LOCAL DATA · READ ONLY</span>
  </header>
  <div class="source-choice" role="group" aria-label="Choose a persona distribution">
    {#each [{ id: 'hf-profile-only', title: 'Public Hugging Face', note: 'Profile only · no OCEAN' }, { id: 'ngc', title: 'NGC Extended', note: 'Singapore · includes OCEAN' }] as dataset}
      {@const meta = catalogue.find(item => item.source === dataset.id)}
      <button aria-pressed={source === dataset.id} onclick={() => changeSource(dataset.id as PersonaSource)}><span><strong>{dataset.title}</strong><small>{dataset.note}</small></span><span class="source-count">{meta ? meta.ready ? `${meta.row_count.toLocaleString('en-SG')} profiles` : 'Not ready' : 'Checking local source…'}</span></button>
    {/each}
  </div>
  <p class="source-context">Files are installed under the checkout’s ignored <code>data/</code> directory, or the configured local NGC source. They are separate from tracked application code. Filtering reads existing records; it creates no data or simulation.</p>

  <form class="profile-filters" onsubmit={event => { event.preventDefault(); void loadPage(); }}>
    <div class="filter-heading"><h2>Find profiles</h2><span>Options come from this distribution’s full corpus.</span></div>
    <div class="filter-fields">
      <label class="keyword">Search profile text<input aria-label="Search profile text" bind:value={search} maxlength="200" placeholder="Try photography, retail or data analysis…" /></label>
      <label>Minimum age<input aria-label="Minimum age" type="number" min="18" max="120" value={ageMin} oninput={event => ageMin = event.currentTarget.value} placeholder="18" /></label>
      <label>Maximum age<input aria-label="Maximum age" type="number" min="18" max="120" value={ageMax} oninput={event => ageMax = event.currentTarget.value} placeholder="Any" /></label>
      <label>{source === 'ngc' ? 'District' : 'Planning area'}<select aria-label={source === 'ngc' ? 'District' : 'Planning area'} bind:value={area}><option value="">All areas</option>{#each options?.source === source ? options.fields[geography] || [] : [] as item}<option value={item.value}>{item.value} ({item.count.toLocaleString('en-SG')})</option>{/each}</select></label>
      <label>Education level<select aria-label="Education level" bind:value={education}><option value="">All education levels</option>{#each options?.source === source ? options.fields.education_level || [] : [] as item}<option value={item.value}>{item.value} ({item.count.toLocaleString('en-SG')})</option>{/each}</select></label>
    </div>
    <div class="filter-actions"><button class="primary" disabled={loading} type="submit">Apply filters</button><button type="button" disabled={loading} onclick={() => { clearFilters(); void loadPage(); }}>Clear filters</button><label class="page-size">Rows per page<select aria-label="Rows per page" bind:value={limit}><option value="10">10</option><option value="20">20</option></select></label>{#if unapplied}<span class="pending-note">Apply filters to update the results.</span>{/if}</div>
  </form>

  {#if loading}<div class="reader-state" role="status">Reading the installed {source === 'ngc' ? 'NGC Extended' : 'HF'} source…</div>{/if}
  {#if error}<div class="reader-error" role="alert"><h2>Profiles could not be loaded.</h2><p>{error}</p><button onclick={() => loadPage(0, true)}>Retry local reader</button><button class="text-button" onclick={onshowschema}>View the schema reference →</button></div>{/if}
  {#if result}
    <section class="loaded-results" aria-label="Filtered source profiles" aria-busy={loading}>
      <div class="result-heading"><div><h2>{result.total.toLocaleString('en-SG')} matching profiles</h2><p>{result.total ? `${(result.offset + 1).toLocaleString('en-SG')}–${(result.offset + result.records.length).toLocaleString('en-SG')}` : '0'} shown · {result.dataset.row_count.toLocaleString('en-SG')} in this distribution</p></div><span class="read-confirmation">Original source rows · 0 inference calls</span></div>
      {#if !result.records.length}<div class="empty-results"><h3>No profiles match these filters.</h3><p>Try a broader search or clear the filters. No substitute or generated rows are shown.</p></div>{:else}
      <div class="profile-workspace">
        <div class="table-column">
          <!-- svelte-ignore a11y_no_noninteractive_tabindex (A labelled scroll region supports keyboard navigation of the wide table.) -->
          <div class="profile-table-scroll" role="region" aria-label="Scrollable profile snapshot" tabindex="0">
            <table data-testid="profile-snapshot"><caption>One bounded page from the selected local Parquet source. Select a profile to inspect its original fields.</caption><thead><tr><th>Name / identity</th><th>Age</th><th>{source === 'ngc' ? 'District' : 'Planning area'}</th><th>Education and work</th><th>Interests</th></tr></thead><tbody>
              {#each result.records as record, index (record.source_id)}
              <tr class:selected={selectedIndex === index} data-profile-row>
                <td><button class="profile-pick" aria-pressed={selectedIndex === index} aria-label={`Inspect profile ${result.offset + index + 1}`} onclick={() => selectedIndex = index}>{name(record, index)}</button><small>{source === 'hf-profile-only' ? 'Name not supplied by HF' : 'Synthetic source name'}</small></td>
                <td>{display(record.profile.age)}</td><td>{display(record.profile[geography])}</td>
                <td><strong>{display(record.profile.occupation)}</strong><small>{display(record.profile.education_level)}</small></td>
                <td>{excerpt(record.profile.hobbies_and_interests || record.profile.hobbies_and_interests_list)}</td>
              </tr>
              {/each}
            </tbody></table>
          </div>
          <div class="pagination"><button disabled={loading || unapplied || result.offset === 0} onclick={() => loadPage(Math.max(0, result!.offset - result!.limit))}>← Previous page</button><span>Page {Math.floor(result.offset / result.limit) + 1}</span><button disabled={loading || unapplied || !result.has_more} onclick={() => loadPage(result!.offset + result!.limit)}>Next page →</button></div>
        </div>
        {#if selected}
        <aside class="profile-detail" aria-label="Original profile details">
          <div class="detail-heading"><span class="eyebrow">ORIGINAL SOURCE PROFILE</span><h2>{name(selected, selectedIndex)}</h2><p>{source === 'ngc' ? 'NGC Extended · source-supplied OCEAN fields' : 'HF public · profile-only conditioning'}</p></div>
          {#each detailGroups as group}
            <details class="profile-group" open={['identity','personal','interests','ocean'].includes(group.id)}><summary>{group.title}<span>{group.fields.length} fields</span></summary><dl>
              {#each group.fields as [key, title]}
              {@const value = selected.profile[key]}
              {@const decoded = group.id === 'ocean' ? trait(value) : null}
              <div data-profile-field={key}><dt>{title}<code>{key}</code></dt><dd>{#if decoded}<div class="trait-value"><strong>{decoded.label}</strong><span>T-score {decoded.t_score}</span></div><p>{decoded.description}</p><details class="stored-value"><summary>Stored JSON</summary><pre>{display(value)}</pre></details>{:else}<p class:missing={value === null || value === ''}>{display(value)}</p>{/if}</dd></div>
              {/each}
            </dl></details>
          {/each}
          <details class="row-provenance"><summary>Source revision and original-row hash</summary><dl><dt>Distribution</dt><dd>{selected.source}</dd><dt>Revision</dt><dd><code>{selected.source_revision}</code></dd><dt>Original profile SHA-256</dt><dd><code>{selected.original_profile_sha256}</code></dd></dl><p>This hash identifies the original row. Browsing does not lock it into a simulation.</p></details>
        </aside>
        {/if}
      </div>
      {/if}
      <p class="loaded-revision">Loaded from {result.dataset.name} · revision <code>{result.dataset.revision}</code>. {result.dataset.ocean_fields.length ? 'Five OCEAN fields belong to this synthetic source.' : 'No OCEAN fields exist in this distribution.'}</p>
    </section>
  {/if}
  <footer class="explorer-footer"><p>Synthetic profiles provide test context. They do not establish citizenship, funding eligibility or measured behaviour. Original rows stay separate from Designer-generated hypotheses.</p><button class="text-button" onclick={onshowschema}>Compare the data schemas →</button>{#if currentMeta}<a href={currentMeta.source_url} target="_blank" rel="noreferrer">Open this distribution’s source ↗</a>{/if}</footer>
</main>

<style>
  .profile-explorer{max-width:1480px;margin:auto;padding:35px 28px 30px;color:#2c4555}.explorer-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:20px}.eyebrow{display:block;font-size:10px;letter-spacing:1px;color:#607c89;margin-bottom:9px}.explorer-heading h1{font-size:32px;letter-spacing:-.8px;margin:0 0 10px}.explorer-heading p{font-size:14px;color:#607888;line-height:1.7}.reader-badge{font:10px ui-monospace,monospace;white-space:nowrap;border:1px solid #9cc2b2;background:#edf6f0;color:#376f58;padding:6px 8px;border-radius:3px;margin-top:4px}.source-choice{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin:22px 0 12px}.source-choice button{display:flex;align-items:center;justify-content:space-between;text-align:left;gap:14px;padding:16px 18px;border:1px solid #d4dfe6;border-radius:5px;background:white;color:#3d596c}.source-choice button[aria-pressed='true']{border-color:#478c82;box-shadow:inset 0 0 0 1px #478c82;background:#f0f7f4}.source-choice strong{font-size:14px;font-weight:600}.source-choice small{display:block;font-size:11px;margin-top:5px;color:#597482}.source-count{font-size:12px;white-space:nowrap}.source-context{font-size:11px;line-height:1.75;color:#617988;margin-bottom:21px}.source-context code{font-size:11px}.profile-filters{padding:18px;border:1px solid #d8e2e8;border-radius:5px;background:white}.filter-heading{display:flex;align-items:baseline;justify-content:space-between;gap:12px;margin-bottom:13px}h2{font-size:18px;letter-spacing:-.2px;margin:0}.filter-heading span{font-size:10px;color:#617988}.filter-fields{display:grid;grid-template-columns:minmax(230px,2fr) 95px 95px minmax(150px,1fr) minmax(165px,1.1fr);gap:12px}label{display:block;font-size:11px;color:#506e7e;font-weight:500}input,select{display:block;width:100%;min-width:0;border:1px solid #d3dfe7;border-radius:4px;padding:8px 9px;margin-top:6px;font-family:inherit;font-size:12px;background:white;color:#314f62;height:36px}.filter-actions{display:flex;align-items:center;gap:9px;margin-top:15px}.filter-actions button,.pagination button{font-size:12px}.page-size{margin-left:auto;display:flex;align-items:center;gap:8px;font-size:10px;white-space:nowrap}.page-size select{width:65px;height:32px;margin:0}.pending-note{font-size:11px;color:#775e37}.reader-state,.reader-error{padding:30px 20px;border:1px solid #d6e1e8;background:white;margin-top:20px;border-radius:5px;font-size:14px}.reader-error{border-left:3px solid #b77a59}.reader-error p{font-size:13px;color:#6b574c;margin:14px 0}.reader-error button{font-size:12px;margin-right:10px}.loaded-results{margin-top:28px}.result-heading{display:flex;justify-content:space-between;align-items:baseline;gap:15px;margin-bottom:15px}.result-heading p{font-size:12px;margin:7px 0 0;color:#657c8a}.read-confirmation{font-size:10px;color:#477664}.profile-workspace{display:grid;grid-template-columns:minmax(0,1.65fr) minmax(310px,1fr);gap:19px;align-items:start}.table-column{min-width:0}.profile-table-scroll{overflow:auto;border:1px solid #d7e2e9;border-radius:5px;background:white;scrollbar-width:thin}table{border-collapse:collapse;width:100%;min-width:640px;text-align:left;font-size:12px;line-height:1.6}caption{font-size:10px;line-height:1.7;padding:11px 13px;color:#607a8a;text-align:left}th,td{border-top:1px solid #e0e8ed;padding:12px 13px;vertical-align:top}th{font-size:10px;color:#617b8b;background:#f0f5f8;white-space:nowrap;font-weight:550}th:first-child{width:22%}td:first-child{min-width:135px}td:last-child{max-width:230px}td strong{font-size:11px;font-weight:550}td small{display:block;font-size:10px;line-height:1.65;margin-top:5px;color:#687f8d}tr.selected{background:#edf5f1}.profile-pick{border:0;background:transparent;color:#2d736c;font-size:12px;line-height:1.5;padding:0;text-align:left;font-weight:600}.profile-pick:hover{text-decoration:underline}.pagination{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:13px 0;font-size:11px;color:#627a89}.profile-detail{min-width:0;background:white;border:1px solid #d7e2e9;border-radius:5px;max-height:980px;overflow:auto;scrollbar-width:thin;position:sticky;top:12px}.detail-heading{padding:19px;border-bottom:1px solid #e0e8ed;background:#f8fafb}.detail-heading h2{font-size:20px;line-height:1.5}.detail-heading p{font-size:11px;margin:8px 0 0;color:#607988}.profile-group{border-bottom:1px solid #e2e9ef;padding:0 17px}.profile-group>summary{display:flex;justify-content:space-between;gap:9px;align-items:center;padding:14px 0;font-size:12px;font-weight:600;color:#3c5d6f;cursor:pointer}.profile-group>summary:before{content:'▸';color:#699182}.profile-group[open]>summary:before{content:'▾'}.profile-group>summary span{margin-left:auto;font-size:10px;font-weight:400;color:#687f8d}dl{margin:0}dl>div{margin-bottom:15px}dt{font-size:11px;color:#567384;font-weight:550}dt code{display:block;font-size:9px;color:#768b98;margin-top:3px}dd{margin:6px 0 0;overflow-wrap:anywhere;font-size:12px;color:#304e60;line-height:1.8}dd p{margin:0;white-space:pre-wrap}.missing{font-style:italic;color:#728493}.trait-value{display:flex;align-items:baseline;justify-content:space-between;gap:10px}.trait-value strong{font-size:12px;font-weight:600;color:#47725e}.trait-value span{font-size:10px;white-space:nowrap;color:#627b6d}.trait-value+p{margin-top:6px}.stored-value{margin-top:8px}.stored-value summary{font-size:10px;color:#6e8190;cursor:pointer}.stored-value pre{max-width:100%;overflow:auto;white-space:pre-wrap;font-size:10px;line-height:1.6;background:#f5f8fa;padding:8px;border-radius:3px;overflow-wrap:anywhere}.row-provenance{padding:15px 17px;background:#f8fafb}.row-provenance summary{font-size:11px;color:#537180;cursor:pointer}.row-provenance dl{margin-top:12px}.row-provenance dd{margin-bottom:12px}.row-provenance code{font-size:10px;overflow-wrap:anywhere}.row-provenance p{font-size:10px;line-height:1.7;color:#687f8d}.loaded-revision{font-size:10px;color:#667e8d;line-height:1.8;margin-top:14px;overflow-wrap:anywhere}.loaded-revision code{font-size:10px}.empty-results{padding:30px 20px;border:1px solid #d7e2e9;background:white;border-radius:5px}.empty-results h3{font-size:15px;margin:0 0 10px}.empty-results p{font-size:12px;color:#637b8b}.explorer-footer{margin-top:25px;border-top:1px solid #d8e2e9;padding-top:18px;display:flex;align-items:center;gap:18px;flex-wrap:wrap}.explorer-footer p{font-size:11px;color:#657e8d;line-height:1.8;flex:1;min-width:220px}.explorer-footer button,.explorer-footer a{font-size:11px}.explorer-footer a{color:#397d7a}input:focus-visible,select:focus-visible,.profile-table-scroll:focus-visible{outline:2px solid #4a8c85;outline-offset:2px}button:disabled{opacity:.5;cursor:default}
  @media(max-width:1150px){.filter-fields{grid-template-columns:minmax(160px,1fr) 1fr 1fr}.keyword{grid-column:1/-1}.profile-workspace{grid-template-columns:minmax(0,1.5fr) minmax(290px,1fr)}.pending-note{flex-basis:100%}.filter-actions{flex-wrap:wrap}}
  @media(max-width:900px){.profile-workspace{grid-template-columns:1fr}.profile-detail{position:static;max-height:none}.source-choice button{align-items:flex-start;flex-direction:column;gap:9px}.result-heading{align-items:flex-start}.read-confirmation{max-width:140px;line-height:1.6}}
  @media(max-width:600px){.profile-explorer{padding:26px 18px}.explorer-heading{display:block}.explorer-heading h1{font-size:28px}.reader-badge{display:inline-block;margin:0 0 5px}.source-choice{gap:9px;margin-top:18px}.source-choice button{padding:13px 12px}.source-choice strong{font-size:12px}.source-choice small{font-size:10px}.source-count{font-size:10px}.profile-filters{padding:14px}.filter-heading{display:block}.filter-heading span{display:block;margin-top:7px;line-height:1.6}.filter-fields{grid-template-columns:1fr 1fr;gap:11px}.filter-fields label:last-child{grid-column:1/-1}.filter-actions{gap:8px}.filter-actions button{font-size:11px;padding:7px 8px}.page-size{font-size:9px;gap:5px}.page-size select{width:49px}.result-heading{display:block}.read-confirmation{display:block;margin-top:11px;max-width:none}.result-heading h2{font-size:18px}.pagination{gap:5px}.pagination button{font-size:11px;padding:7px 8px}.source-context{font-size:10px}.explorer-footer{gap:10px}.explorer-footer p{flex-basis:100%}}
</style>
