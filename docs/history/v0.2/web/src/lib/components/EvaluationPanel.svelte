<script lang="ts">
  import { pretty } from '#lib/api.ts';
  import CodeReference from './CodeReference.svelte';

  let { evaluation, onrequest, busy = false }: { evaluation?: any; onrequest: () => void | Promise<void>; busy?: boolean } = $props();
  let filter = $state('all');
  const details = $derived(evaluation?.details ?? evaluation);
  const rows: any[] = $derived(details?.rows ?? []);
  const summaries = $derived(Object.entries(details?.summary ?? evaluation?.summary ?? {}) as [string, any][]);
  const visibleRows = $derived(rows.filter(row => filter === 'all' || (filter === 'attention' ? ['fail', 'error'].includes(row.status) : row.status === filter)));
  const metricRows = $derived(evaluation?.row_scores ?? []);

  function label(value: string) { return value.replaceAll('_', ' ').replaceAll('-', ' '); }
  function statusLabel(value: string) { return value === 'not_applicable' ? 'not applicable' : value; }
</script>

<section class="lab-card" aria-label="Inspectable Helix evaluation">
  <div class="lab-eyebrow">Local Helix checks</div>
  <h2>See each assertion and its evidence.</h2>
  <p>The application authors narrow checks over saved replies; the real Helix Evals SDK scores those assertions with ExactMatch. Open a criterion to see its expected value, observed result and reason. Evaluation makes no new inference calls.</p>
  <div class="lab-actions"><button class="lab-button primary" disabled={busy} onclick={onrequest}>{busy ? 'Evaluating saved evidence…' : evaluation ? 'Re-evaluate saved replies' : 'Evaluate saved replies'}</button></div>
  {#if evaluation}
    {#if !rows.length}<p class="lab-note">This older evaluation has aggregate scores without inspectable criterion rows. Re-evaluate the saved replies to distinguish failed answers, unavailable evidence and checks that do not apply.</p>{/if}
    <div class="lab-grid">
      {#each summaries as [condition, summary]}
        <div class="evaluation-summary"><h3>{label(condition)}</h3><div class="lab-stat">{summary.passed} / {summary.criteria}</div><p class="lab-muted">Applicable checks passed</p><div class="lab-badges">{#if summary.failed !== undefined}<span class="lab-badge fail">{summary.failed} failed</span>{/if}{#if summary.errors !== undefined}<span class="lab-badge error">{summary.errors} errors</span>{/if}{#if summary.not_applicable !== undefined}<span class="lab-badge not_applicable">{summary.not_applicable} not applicable</span>{/if}</div></div>
      {/each}
    </div>
    <p class="lab-note">A usable answer is checked before its claims. Empty replies, model-generated error text and unparsed tool calls cannot earn a successful answer score. Checks that do not apply are excluded; unavailable evidence remains an error.</p>
    {#if rows.length}
      <label class="lab-label">Criterion rows<select bind:value={filter}><option value="all">All checks</option><option value="attention">Failures and errors</option><option value="pass">Passed</option><option value="not_applicable">Not applicable</option></select></label>
      <p class="lab-muted">{visibleRows.length} of {rows.length} saved criterion rows</p>
      {#if !visibleRows.length}<p class="lab-empty">No rows match this filter.</p>{/if}
      {#each visibleRows as row, index (`${row.case_id}:${row.criterion}:${index}`)}
        <details class="lab-check-row"><summary><span class="lab-badge" class:fail={row.status === 'fail'} class:error={row.status === 'error'} class:not_applicable={row.status === 'not_applicable'}>{statusLabel(row.status)}</span> <strong>{label(row.criterion)}</strong> <span class="lab-muted">· {label(row.condition)} · turn {row.turn}</span></summary>
          <p>{row.reason}</p><div class="lab-inline"><span class="lab-badge">Expected: {row.expected ?? 'not scored'}</span><span class="lab-badge">Observed: {row.output ?? 'not applicable'}</span></div>
          <p class="lab-path">Episode {row.episode_id} · case {row.case_id}</p>
          {#if row.evidence && Object.keys(row.evidence).length}<h3>Saved supporting evidence</h3><pre class="lab-code">{pretty(row.evidence)}</pre>{/if}
        </details>
      {/each}
    {/if}
    <details class="lab-check-row"><summary>Actual Helix metric output · {metricRows.length} rows</summary>
      <p>Metric: ExactMatch. Each applicable authored assertion is compared with the expected boolean value. A metric score validates that assertion only; it does not assess every sentence or establish citizen outcomes.</p>
      {#if evaluation.result_file}<div class="lab-path">{evaluation.result_file}</div>{/if}
      {#if metricRows.length}<pre class="lab-code">{pretty(metricRows)}</pre>{:else}<p class="lab-muted">No SDK metric rows were retained in this evaluation response. Inspect the saved Helix artifact or re-evaluate.</p>{/if}
    </details>
    {#each details?.limitations ?? [] as limitation}<p class="lab-muted">{limitation}</p>{/each}
  {:else}
    <p class="lab-muted">After a conversation finishes, evaluate that saved result here. Incomplete turns and missing original constraints stay visible; they are not replaced with a plausible answer or invented settings.</p>
  {/if}
  <CodeReference source="helix" label="Open the authored checks and Helix SDK integration" />
</section>

<style>
  .evaluation-summary{border:1px solid #e0e8da;border-radius:8px;padding:15px;min-width:0}.evaluation-summary h3{margin-top:0}.evaluation-summary .lab-muted{margin:5px 0}.lab-label{max-width:330px}.lab-check-row strong{font-size:12px}.lab-check-row summary>.lab-muted{font-size:10px}
</style>
