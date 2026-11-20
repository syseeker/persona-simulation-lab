<script lang="ts">
  import { labApi } from '#lib/api.ts';
  let { source = 'application', label = 'Integration code' }: { source?: string; label?: string } = $props();
  let record = $state<any>(null);
  let loading = $state(false);
  let error = $state('');
  async function load() {
    if (record || loading) return;
    loading = true;
    try { record = await labApi('source?id=' + encodeURIComponent(source)); }
    catch (e) { error = e instanceof Error ? e.message : 'Source unavailable'; }
    finally { loading = false; }
  }
</script>

<details class="lab-check-row" ontoggle={event => { if (event.currentTarget.open) void load(); }}>
  <summary>{label}</summary>
  {#if loading}<p class="lab-muted">Reading the integration entry point…</p>{/if}
  {#if error}<p class="lab-error">{error}</p>{/if}
  {#if record}<p class="lab-muted">{record.purpose}</p><div class="lab-path">{record.absolute_path}:{record.line}</div><pre class="lab-code">{record.content}</pre><p class="lab-muted">{record.notice}</p>{#if record.github_url}<a class="lab-link" href={record.github_url} target="_blank" rel="noreferrer">View recorded commit on GitHub</a>{/if}{/if}
</details>
