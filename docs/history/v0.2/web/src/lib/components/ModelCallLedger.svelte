<script lang="ts">
  let { records, admittedCalls, budget, jobStatus }: {
    records?: unknown;
    admittedCalls?: unknown;
    budget?: unknown;
    jobStatus?: string;
  } = $props();

  const maximumRecords = 120;
  const savedRecords = $derived(Array.isArray(records) ? records : []);
  const visibleRecords = $derived(savedRecords.slice(0, maximumRecords));
  const active = $derived(['queued', 'running'].includes(jobStatus ?? ''));

  function record(value: unknown): Record<string, unknown> {
    return value !== null && typeof value === 'object' && !Array.isArray(value)
      ? value as Record<string, unknown> : {};
  }

  function display(value: unknown, maximumLength = 800): string {
    if (value === undefined || value === null || value === '') return 'Unknown (not recorded)';
    const text = typeof value === 'string' ? value : JSON.stringify(value, null, 2);
    return text.length > maximumLength ? text.slice(0, maximumLength) + '\n[truncated for display]' : text;
  }

  function count(value: unknown): string {
    return typeof value === 'number' && Number.isFinite(value) && value >= 0
      ? value.toLocaleString('en-SG') : 'Unknown (not recorded)';
  }

  function tokens(value: unknown, kind: 'input' | 'output' | 'total'): string {
    const usage = record(value);
    const valueToShow = kind === 'input' ? usage.prompt_tokens ?? usage.input_tokens
      : kind === 'output' ? usage.completion_tokens ?? usage.output_tokens : usage.total_tokens;
    return count(valueToShow);
  }

  function hasError(call: Record<string, unknown>): boolean {
    return ['error_type', 'error', 'provider_error', 'http_status'].some(key => call[key] !== undefined && call[key] !== null);
  }
</script>

<section class="model-call-ledger" aria-label="Saved Designer model-call ledger">
  <h3>Saved model-call ledger</h3>
  <p class="lab-muted">Admitted calls: {count(admittedCalls)} · job cap: {count(budget)} · {savedRecords.length} saved records from job.usage. Inspection makes no model calls. Call status records transport execution; it does not establish generated-data quality.</p>
  {#if !savedRecords.length}
    <p class="lab-note">{active ? 'No model-call records have been saved yet. This job is still active; inspect its saved ledger after it stops.' : 'No model-call records were saved for this job. Token usage is unknown; calls are not reconstructed from results or logs.'}</p>
  {:else}
    <p class="lab-muted">Provider-reported token counts are shown as saved. Missing counts stay unknown, and totals are never estimated.</p>
    {#if savedRecords.length > maximumRecords}<p class="lab-note">Showing the first {maximumRecords} of {savedRecords.length} saved records. Remaining records stay in the local job artifact.</p>{/if}
    <details>
      <summary>Inspect saved model calls · {savedRecords.length} records</summary>
      {#each visibleRecords as value, index}
        {@const call = record(value)}
        <details class="lab-check-row">
          <summary>
            <strong>{call.call === undefined || call.call === null ? `Record ${index + 1} · call ID unknown` : `Call ${display(call.call, 80)}`}</strong>
            <span class="lab-badge" class:fail={['failed', 'error', 'cancelled', 'budget_exhausted'].includes(String(call.status))}>{display(call.status, 80)}</span>
            <span class="lab-badge">Role: {display(call.role, 120)}</span>
          </summary>
          <dl class="call-fields">
            <div><dt>Requested model / alias</dt><dd>{display(call.requested_model)}</dd></div>
            <div><dt>Selected provider model</dt><dd>{display(call.selected_model)}</dd></div>
            <div><dt>Configured model</dt><dd>{display(call.model)}</dd></div>
            <div><dt>Execution mode</dt><dd>{display(call.mode, 120)}</dd></div>
            <div><dt>Input tokens</dt><dd>{tokens(call.usage, 'input')}</dd></div>
            <div><dt>Output tokens</dt><dd>{tokens(call.usage, 'output')}</dd></div>
            <div><dt>Total tokens</dt><dd>{tokens(call.usage, 'total')}</dd></div>
            <div><dt>Latency (ms)</dt><dd>{count(call.latency_ms)}</dd></div>
          </dl>
          {#if hasError(call)}
            <div class="lab-error">
              <strong>Saved error evidence</strong>
              {#if call.error_type !== undefined}<p>Error type: {display(call.error_type)}</p>{/if}
              {#if call.http_status !== undefined}<p>HTTP status: {display(call.http_status, 80)}</p>{/if}
              {#if call.error !== undefined}<pre class="lab-code">{display(call.error, 4000)}</pre>{/if}
              {#if call.provider_error !== undefined}<pre class="lab-code">{display(call.provider_error, 4000)}</pre>{/if}
            </div>
          {:else}<p class="lab-muted">No error details were recorded for this call.</p>{/if}
          <details><summary>Saved provider usage fields</summary><pre class="lab-code">{display(call.usage, 4000)}</pre></details>
        </details>
      {/each}
    </details>
  {/if}
</section>

<style>
  .model-call-ledger{margin:18px 0;min-width:0}.model-call-ledger summary{cursor:pointer;font-size:12px;line-height:1.8;overflow-wrap:anywhere}.call-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin:14px 0;font-size:11px;line-height:1.7}.call-fields dt{color:#6f8072}.call-fields dd{margin:3px 0 0;overflow-wrap:anywhere;white-space:pre-wrap}.lab-error p{color:inherit}@media(max-width:600px){.call-fields{grid-template-columns:1fr}}
</style>
