<script lang="ts">
  import { auditDate, datasetSnapshots, schemaComparison, schemaCounts, type FieldScope } from './datasetMetadata.ts';
  import { fieldGroups, fieldLabel } from './fieldGroups.ts';

  let { onchoose }: { onchoose?: () => void } = $props();
  let search = $state('');
  let scope = $state<'all' | FieldScope>('all');
  const query = $derived(search.trim().toLocaleLowerCase());
  const visibleFields = $derived(schemaComparison.filter(field =>
    (scope === 'all' || field.scope === scope) &&
    (!query || field.name.includes(query) || fieldLabel(field.name).toLocaleLowerCase().includes(query) || field.hf?.type.includes(query) || field.ngc?.type.includes(query) || (field.ocean && 'ocean'.includes(query)))
  ));
  const visibleGroups = $derived(fieldGroups.map(group => ({ ...group,
    entries: visibleFields.filter(field => group.fields.some(([name]) => name === field.name))
  })).filter(group => group.entries.length));
  const scopeNames = { shared: 'Shared', 'hf-only': 'HF only', 'ngc-only': 'NGC only' };
</script>

<main class="datasets-page" aria-label="Singapore persona dataset comparison">
  <header class="datasets-intro">
    <span class="section-label">THE PEOPLE BEHIND THE TEST</span>
    <div class="title-row"><h1>Two distributions.<br />Know what each contains.</h1><span class="snapshot-label">AUDITED LOCAL SNAPSHOT</span></div>
    <p class="intro">Compare the public Hugging Face and NGC Extended Singapore persona schemas before choosing a source for the application.</p>
    <p class="audit-date">Metadata snapshot · {auditDate} <span aria-hidden="true">/</span> Data schema · audited reference</p>
  </header>

  <section class="dataset-cards" aria-label="The two audited distributions">
    {#each datasetSnapshots as dataset (dataset.id)}
      <article class="dataset-card" data-testid="dataset-snapshot" data-source={dataset.id} aria-labelledby={`dataset-title-${dataset.id}`}>
        <div class="source-heading"><span class="source-index">{dataset.id === 'hf' ? '01' : '02'}</span><span class="source-kind">{dataset.id === 'hf' ? 'PUBLIC HF · PROFILE ONLY' : 'NGC · EXTENDED en_SG'}</span></div>
        <h2 id={`dataset-title-${dataset.id}`}>{dataset.title}</h2>
        <p class="source-subtitle">{dataset.subtitle}</p>
        <dl class="dataset-stats">
          <div><dt>Synthetic profiles</dt><dd>{dataset.rows.toLocaleString('en-SG')}</dd></div>
          <div><dt>Schema fields</dt><dd>{dataset.columns}</dd></div>
          <div><dt>OCEAN fields</dt><dd>{dataset.oceanColumns}</dd></div>
        </dl>
        <p class="source-meaning">{dataset.id === 'hf' ? 'Profile fields without OCEAN conditioning. Keep this source labelled profile-only.' : 'Source-supplied synthetic OCEAN attributes are present. They are stored as JSON strings.'}</p>
        <dl class="source-identity"><div><dt>{dataset.versionLabel}</dt><dd><code>{dataset.version}</code></dd></div></dl>
        {#if dataset.bytes || dataset.originalSha256}
          <details class="provenance"><summary>File identity from the audit</summary><dl>
            {#if dataset.bytes}<div><dt>Original Parquet size</dt><dd>{dataset.bytes.toLocaleString('en-SG')} bytes</dd></div>{/if}
            {#if dataset.originalSha256}<div><dt>Original file SHA-256</dt><dd><code>{dataset.originalSha256}</code></dd></div>{/if}
          </dl><p class="identity-note">A local content fingerprint for reproducibility; this is not a publisher signature.</p></details>
        {/if}
        <a class="source-link" href={dataset.sourceUrl} target="_blank" rel="noopener noreferrer">{dataset.id === 'hf' ? 'Open Hugging Face viewer' : 'Open NGC catalogue'} <span aria-hidden="true">↗</span></a>
      </article>
    {/each}
  </section>

  <section class="comparison-section" aria-labelledby="schema-heading">
    <div class="section-heading"><div><span class="section-label">READ THE ACTUAL SCHEMAS</span><h2 id="schema-heading">Which fields are shared?</h2></div><p class="schema-summary"><strong>{schemaCounts.shared}</strong> shared <span>·</span> <strong>{schemaCounts.hfOnly}</strong> HF only <span>·</span> <strong>{schemaCounts.ngcOnly}</strong> NGC only</p></div>
    <p class="section-copy">There are 20 common field names. HF has <code>planning_area</code>; NGC has <code>district</code> among its additional fields. These names are not treated as equivalent. Equal row counts do not establish row-by-row identity.</p>
    <div class="schema-tools">
      <label>Search schema fields<input type="search" bind:value={search} placeholder="Try occupation, openness or OCEAN…" aria-label="Search schema fields" /></label>
      <label>Show fields<select bind:value={scope} aria-label="Schema field scope"><option value="all">All fields ({schemaCounts.all})</option><option value="shared">Shared ({schemaCounts.shared})</option><option value="hf-only">HF only ({schemaCounts.hfOnly})</option><option value="ngc-only">NGC only ({schemaCounts.ngcOnly})</option></select></label>
    </div>
    <div class="schema-result-summary" aria-live="polite">Showing {visibleFields.length} of {schemaCounts.all} schema fields <span><i aria-hidden="true"></i> OCEAN fields are highlighted</span></div>
    <!-- svelte-ignore a11y_no_noninteractive_tabindex (The labelled overflow region is focusable so keyboard users can scroll the schema.) -->
    <div class="schema-scroll" tabindex="0" role="region" aria-label="Scrollable schema field comparison">
      <table data-testid="dataset-schema">
        <caption>Exact Arrow field types from the audited local Parquet schemas. This table contains schema metadata, not profile rows.</caption>
        <thead><tr><th scope="col">Field</th><th scope="col">Public HF</th><th scope="col">NGC Extended</th></tr></thead>
        {#each visibleGroups as group (group.id)}
        <tbody aria-label={group.title}>
          <tr class="group-heading"><th colspan="3" scope="rowgroup">{group.title}<span>{group.entries.length} fields</span></th></tr>
          {#each group.entries as field (field.name)}
            <tr class:ocean={field.ocean} data-field={field.name} data-scope={field.scope} data-ocean={field.ocean ? 'true' : 'false'}>
              <th scope="row"><strong class="field-label">{fieldLabel(field.name)}</strong><code>{field.name}</code><span class="field-scope">{field.ocean ? 'OCEAN · NGC only' : scopeNames[field.scope]}</span></th>
              <td>{#if field.hf}<code>{field.hf.type}</code>{:else}<span class="absent" aria-label="Not in the public HF schema">—</span>{/if}</td>
              <td>{#if field.ngc}<code class:null-type={field.ngc.type === 'null'}>{field.ngc.type}</code>{:else}<span class="absent" aria-label="Not in the NGC Extended schema">—</span>{/if}</td>
            </tr>
          {/each}
        </tbody>
        {/each}
        {#if !visibleFields.length}<tbody><tr><td colspan="3" class="empty">No field names or types match this search.</td></tr></tbody>{/if}
      </table>
    </div>
    <p class="schema-note">All fields are marked nullable in these schemas; that describes allowed nulls, not completeness. Six NGC fields have Arrow type <code>null</code>: <code>street_number</code>, <code>street_name</code>, <code>unit</code>, <code>city</code>, <code>region</code> and <code>bachelors_field</code>.</p>
  </section>

  <section class="dataset-difference" aria-labelledby="difference-heading">
    <h2 id="difference-heading">The main difference</h2>
    <p><strong>Public Hugging Face:</strong> Profile details, interests and goals, without OCEAN personality fields.</p>
    <p><strong>NGC Extended:</strong> More profile fields, plus five synthetic personality traits (OCEAN) to shape simulated behaviour.</p>
  </section>

  <footer class="datasets-footer"><div><strong>Metadata inspection only</strong><p>Data schema preserves this dated schema and audit reference without bundling persona rows. Use Explore profiles to read and filter the separately installed local Parquet files. Reading data starts no inference.</p></div>{#if onchoose}<button class="locate-button" onclick={() => onchoose?.()}>Locate personas in map <span aria-hidden="true">→</span></button>{/if}</footer>
</main>

<style>
  .datasets-page { max-width: 1160px; margin: 0 auto; padding: 47px 34px 38px; color: #293d4d; }
  .section-label { display: block; font-size: 10px; letter-spacing: 1.25px; font-weight: 650; color: #5b6f7b; margin-bottom: 11px; }
  .title-row { display: flex; align-items: flex-start; gap: 22px; justify-content: space-between; }
  h1 { font-size: 36px; line-height: 1.22; letter-spacing: -1.1px; font-weight: 650; margin: 0 0 19px; }
  .snapshot-label { border: 1px solid #d1ddd7; background: #f0f6f2; color: #527263; border-radius: 4px; padding: 5px 7px; font-family: ui-monospace, monospace; font-size: 9px; line-height: 1.5; letter-spacing: .4px; margin-top: 6px; white-space: nowrap; }
  .intro { font-size: 16px; line-height: 1.75; color: #5c7181; max-width: 760px; margin-bottom: 13px; }
  .audit-date { font-size: 11px; color: #5b6f7b; margin: 0; }
  .audit-date>span { margin: 0 9px; color: #c0cbd1; }
  .dataset-cards { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 19px; margin-top: 31px; }
  .dataset-card { min-width: 0; padding: 24px 25px 21px; border: 1px solid #d6e1e6; border-top: 3px solid #90b2a8; border-radius: 6px; background: #fff; display: flex; flex-direction: column; }
  .dataset-card[data-source='ngc'] { border-top-color: #91a9bf; }
  .source-heading { display: flex; align-items: center; gap: 10px; margin-bottom: 19px; }
  .source-index { font-family: ui-monospace,monospace; font-size: 11px; color: #537367; }
  .source-kind { color: #5b6f7b; font-size: 9px; letter-spacing: .8px; font-weight: 600; }
  h2 { font-size: 22px; line-height: 1.3; letter-spacing: -.4px; margin: 0 0 8px; font-weight: 630; }
  .source-subtitle { font-size: 12px; color: #5b6f7b; margin-bottom: 23px; }
  .dataset-stats { display: grid; grid-template-columns: 1.3fr 1fr 1fr; margin: 0 0 20px; padding-bottom: 21px; border-bottom: 1px solid #e7edf0; gap: 8px; }
  .dataset-stats div { display: flex; flex-direction: column-reverse; gap: 3px; }
  .dataset-stats dt { font-size: 10px; color: #5b6f7b; line-height: 1.4; }
  .dataset-stats dd { margin: 0; font-size: 26px; line-height: 1.3; font-weight: 600; color: #365e58; letter-spacing: -.5px; }
  .dataset-card[data-source='ngc'] .dataset-stats dd { color: #45627b; }
  .source-meaning { font-size: 12px; line-height: 1.7; color: #5e7481; min-height: 41px; margin: 0 0 17px; }
  .source-identity { margin: 0 0 16px; }
  .source-identity dt, .provenance dt { font-size: 10px; color: #5b6f7b; margin-bottom: 4px; }
  .source-identity dd, .provenance dd { margin: 0; min-width: 0; color: #536e7e; font-size: 11px; line-height: 1.6; }
  .source-identity code, .provenance code { font-size: 10px; overflow-wrap: anywhere; word-break: break-all; }
  .provenance { margin-bottom: 18px; }
  .provenance summary { color: #5b6f7b; font-size: 11px; font-weight: 500; }
  .identity-note { font-size: 10px; line-height: 1.7; color: #5b6f7b; margin: 10px 0 0; }
  .provenance dl { padding: 9px 0 0; margin: 0; }
  .provenance dl>div+div { margin-top: 11px; }
  .source-link { align-self: flex-start; margin-top: auto; font-size: 11px; line-height: 1.5; color: #397b83; text-decoration: none; border-bottom: 1px solid #c7dcd9; padding-bottom: 2px; }
  .source-link>span { margin-left: 4px; }
  .source-link:hover { border-color: #528b8b; }
  .comparison-section { margin-top: 44px; }
  .section-heading { display: flex; justify-content: space-between; align-items: flex-end; gap: 22px; }
  .section-heading .section-label { margin-bottom: 8px; }
  .section-heading h2 { margin-bottom: 13px; }
  .schema-summary { margin-bottom: 16px; font-size: 11px; color: #5b6f7b; white-space: nowrap; }
  .schema-summary strong { color: #5a7684; font-weight: 600; }
  .schema-summary>span { padding: 0 6px; color: #bbc7ce; }
  .section-copy { max-width: 880px; color: #5b6f7b; font-size: 12px; line-height: 1.8; margin-bottom: 19px; }
  .section-copy code { font-size: 11px; color: #54727e; }
  .schema-tools { display: grid; grid-template-columns: minmax(0,1fr) 200px; gap: 15px; margin-bottom: 10px; }
  .schema-tools label { font-size: 10px; font-weight: 500; letter-spacing: .1px; color: #5b6f7b; margin-bottom: 0; }
  .schema-tools input, .schema-tools select { width: 100%; display: block; margin-top: 5px; border: 1px solid #d4e0e5; border-radius: 5px; background: #fff; color: #4c6676; padding: 9px 11px; font: inherit; font-size: 12px; min-width: 0; height: 37px; }
  .schema-result-summary { display: flex; justify-content: space-between; gap: 12px; padding: 7px 1px 10px; font-size: 10px; color: #5b6f7b; }
  .schema-result-summary>span { display: inline-flex; align-items: center; gap: 5px; }
  .schema-result-summary i { width: 6px; height: 6px; border-radius: 50%; background: #8bb7a6; }
  .schema-scroll { max-height: 542px; overflow: auto; border: 1px solid #d8e2e7; border-radius: 5px; background: #fff; scrollbar-width: thin; scrollbar-color: #c9d5dc #f7f9fa; }
  table { width: 100%; border-collapse: collapse; table-layout: fixed; font-size: 11px; text-align: left; }
  caption { text-align: left; padding: 12px 15px; border-bottom: 1px solid #e1e8ec; color: #5b6f7b; font-size: 10px; line-height: 1.6; }
  thead { position: sticky; top: 0; z-index: 1; background: #f3f7f9; }
  th, td { padding: 9px 15px; border-bottom: 1px solid #eaf0f3; vertical-align: middle; }
  th:first-child { width: 52%; }
  thead th { color: #5b6f7b; font-size: 10px; font-weight: 550; }
  tbody th { font-weight: 450; }
  .group-heading th { background: #eaf0f4; padding: 12px 15px; color: #365565; font-size: 12px; font-weight: 650; }
  .group-heading span { float: right; font-size: 10px; font-weight: 400; color: #647b89; }
  .field-label { display: block; font-size: 12px; font-weight: 550; margin-bottom: 3px; color: #344f5d; }
  td { color: #5c7483; }
  th code, td code { font-size: 11px; overflow-wrap: anywhere; }
  .field-scope { display: block; font-size: 10px; line-height: 1.4; margin-top: 3px; color: #5b6f7b; font-weight: 400; }
  tr.ocean { background: #f1f7f3; }
  tr.ocean th code { color: #3f7961; }
  tr.ocean .field-scope { color: #537367; }
  .absent { color: #6c7a83; }
  .null-type { color: #5b6f7b; }
  .empty { text-align: center; padding: 30px 12px; color: #5b6f7b; }
  .schema-note { color: #5b6f7b; font-size: 10px; line-height: 1.8; margin-top: 11px; }
  .schema-note code { font-size: 10px; }
  .dataset-difference { margin-top: 31px; padding: 20px 24px; border: 1px solid #dce5e9; border-radius: 5px; background: #fff; }
  .dataset-difference p { margin: 9px 0 0; color: #5b6f7b; font-size: 12px; line-height: 1.8; }
  .dataset-difference strong { color: #293d4d; font-weight: 600; }
  .datasets-footer { display: flex; align-items: center; justify-content: space-between; gap: 30px; border-top: 1px solid #dce5e9; margin-top: 28px; padding-top: 21px; }
  .datasets-footer>div { max-width: 730px; }
  .datasets-footer strong { color: #5b6f7b; font-size: 11px; font-weight: 550; }
  .datasets-footer p { color: #5b6f7b; font-size: 10px; line-height: 1.8; margin: 5px 0 0; }
  .locate-button { flex-shrink: 0; border: 1px solid #ccdeda; background: #edf5f1; color: #4e7e70; border-radius: 5px; padding: 9px 12px; font-size: 11px; cursor: pointer; white-space: nowrap; }
  input:focus-visible, select:focus-visible, button:focus-visible, a:focus-visible, summary:focus-visible, .schema-scroll:focus-visible { outline: 2px solid #528f8c; outline-offset: 3px; }
  @media (max-width: 780px) { .datasets-page { padding: 36px 24px 28px; } .title-row { display: block; } .snapshot-label { display: inline-block; margin-top: 0; margin-bottom: 17px; } h1 { font-size: 31px; } .dataset-cards { gap: 13px; } .dataset-card { padding: 20px 18px; } .dataset-stats dd { font-size: 22px; } .dataset-stats { grid-template-columns: 1.3fr 1fr 1fr; gap: 7px; } .section-heading { display: block; } .schema-summary { margin-bottom: 13px; } .datasets-footer { display: block; } .locate-button { margin-top: 17px; } }
  @media (max-width: 600px) { .datasets-page { padding: 30px 19px 25px; } h1 { font-size: 28px; } .intro { font-size: 14px; } .audit-date { line-height: 1.8; } .audit-date>span { display: none; } .dataset-cards { grid-template-columns: 1fr; gap: 16px; margin-top: 23px; } .dataset-card { padding: 20px; } .dataset-stats dd { font-size: 26px; } .source-meaning { min-height: 0; } .comparison-section { margin-top: 32px; } .schema-tools { grid-template-columns: 1fr; gap: 10px; } .schema-result-summary { flex-direction: column; gap: 3px; } th, td { padding: 9px 9px; } th:first-child { width: 49%; } thead th { font-size: 9px; } th code, td code { font-size: 10px; } .schema-scroll { max-height: 470px; } }
</style>
