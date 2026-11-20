<script lang="ts">
  import { onMount } from 'svelte';
  import DatasetSchema from './DatasetSchema.svelte';
  import ProfileExplorer from './ProfileExplorer.svelte';
  let { onchoose }: { onchoose?: () => void } = $props();
  let section = $state<'schema' | 'explore'>('schema');
  let restored = $state(false);
  const key = 'persona-lab-guide:dataset-section:v1';
  onMount(() => {
    try { if (localStorage.getItem(key) === 'explore') section = 'explore'; } catch { /* Optional preference. */ }
    restored = true;
  });
  $effect(() => { if (restored) try { localStorage.setItem(key, section); } catch { /* Optional preference. */ } });
  function tabKey(event: KeyboardEvent) {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    event.preventDefault();
    section = event.key === 'Home' ? 'schema' : event.key === 'End' ? 'explore' : section === 'schema' ? 'explore' : 'schema';
    document.getElementById(`dataset-tab-${section}`)?.focus();
  }
</script>

<div class="dataset-toolbar">
  <div role="tablist" aria-label="Dataset views">
    <button role="tab" id="dataset-tab-schema" aria-controls="dataset-schema-panel" aria-selected={section === 'schema'} tabindex={section === 'schema' ? 0 : -1} onkeydown={tabKey} onclick={() => section = 'schema'}>Data schema</button>
    <button role="tab" id="dataset-tab-explore" aria-controls="dataset-explore-panel" aria-selected={section === 'explore'} tabindex={section === 'explore' ? 0 : -1} onkeydown={tabKey} onclick={() => section = 'explore'}>Explore profiles</button>
  </div>
  <span>Singapore Personas · two separate distributions</span>
</div>
{#if section === 'schema'}
  <div role="tabpanel" id="dataset-schema-panel" aria-labelledby="dataset-tab-schema"><DatasetSchema {onchoose} /></div>
{:else}
  <div role="tabpanel" id="dataset-explore-panel" aria-labelledby="dataset-tab-explore"><ProfileExplorer onshowschema={() => section = 'schema'} /></div>
{/if}

<style>
  .dataset-toolbar { display:flex; align-items:center; justify-content:space-between; gap:16px; padding:10px 17px; background:#fff; border-bottom:1px solid #d6e0e7; }
  [role='tablist'] { display:flex; gap:5px; }
  button { font-size:12px; padding:7px 11px; border:1px solid #d6e0e7; border-radius:4px; background:white; color:#385265; }
  button[aria-selected='true'] { color:white; background:#293746; border-color:#293746; }
  span { color:#677f8f; font-size:11px; }
  @media(max-width:600px) { .dataset-toolbar { padding:10px 11px; } span { display:none; } }
</style>
