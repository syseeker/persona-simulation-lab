<script lang="ts">
  let { id, data }: { id: string; data: { title: string; caption?: string; number?: string; kind?: string; overlay?: boolean; component?:string; oninspect?:(node:string,module?:string,tab?:'overview'|'evidence'|'sources')=>void } } = $props();
</script>

<section class="zone" class:overlay={data.overlay} data-zone={id} data-kind={data.kind ?? 'runtime'} aria-label={data.title}>
  <header class="zone-drag-handle" title="Drag this header to move the group and its components">
    {#if data.number}<span class="number">{data.number}</span>{/if}
    <strong>{data.title}</strong>
    {#if data.caption}<span class="caption">{data.caption}</span>{/if}
    {#if data.component}
      <span class="zone-actions nodrag nopan">
        <button class="nodrag nopan" aria-label="Code: Shared application services" onclick={(event) => { event.stopPropagation(); data.oninspect?.(data.component!, undefined, 'sources'); }}>Code</button>
        <button class="nodrag nopan" aria-label="Log: Shared application services" onclick={(event) => { event.stopPropagation(); data.oninspect?.(data.component!, undefined, 'evidence'); }}>Log</button>
      </span>
    {/if}
    <span class="grip" aria-hidden="true">⠿</span>
  </header>
</section>

<style>
  .zone { box-sizing: border-box; width: 100%; height: 100%; border: 1px solid #d8e2e7; border-radius: 13px; background: #f4f8faad; color: #576f7c; }
  .zone[data-kind='data'] { background: #f0f5f1c4; border-color: #d5e0d7; }
  .zone[data-kind='evidence'] { background: #f5f2f7c9; border-color: #ded8e3; }
  .zone[data-kind='deployment'] { background: #f8f5efb8; border-color: #e1d9cd; }
  .zone.overlay { border-style: dashed; }
  .zone-drag-handle { box-sizing: border-box; height: 40px; display: flex; align-items: center; gap: 8px; padding: 0 12px; cursor: grab; user-select: none; }
  .zone-drag-handle:active { cursor: grabbing; }
  .number { font-size: 9px; border: 1px solid #d4dfe4; background: #fff9; border-radius: 4px; padding: 2px 4px; color: #718793; }
  strong { font-size: 11px; font-weight: 650; letter-spacing: .15px; white-space: nowrap; }
  .caption { color: #81939d; font-size: 9px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .grip { margin-left: auto; color: #a7b5bd; font-size: 18px; line-height: 1; }
  .zone-actions{display:flex;gap:4px;flex:none;margin-left:auto}.zone-actions button{font:inherit;font-size:11px;color:#456777;background:#fff;border:1px solid #d8e2e7;border-radius:3px;padding:3px 5px;cursor:pointer}.zone-actions button:focus-visible{outline:2px solid #267d79;outline-offset:2px}
</style>
