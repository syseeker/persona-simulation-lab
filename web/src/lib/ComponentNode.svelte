<script lang="ts">
  import { Handle, Position } from '@xyflow/svelte';

  type Module = { id: string; title: string; component?: string; hint?: string };
  type NodeData = {
    title: string;
    eyebrow?: string;
    subtitle?: string;
    modules: Module[];
    active?: boolean;
    dim?: boolean;
    inspected?: boolean;
    badge?: string;
    kind?: string;
    inspectId?: string;
    extension?: string;
    wide?: boolean;
    oninspect?: (node: string, module?: string, tab?: 'overview' | 'evidence' | 'sources') => void;
  };
  let { id, data }: { id: string; data: NodeData } = $props();

  function inspect(event: MouseEvent, module?: Module, tab: 'overview' | 'evidence' | 'sources' = 'overview') {
    event.stopPropagation();
    data.oninspect?.(module?.component ?? data.inspectId ?? id, module?.title, tab);
  }
</script>

<article
  class="component-node"
  class:active={data.active}
  class:dim={data.dim}
  class:inspected={data.inspected}
  class:wide={data.wide}
  data-component={id}
  data-active={data.active ? 'true' : 'false'}
  data-kind={data.kind ?? 'runtime'}
  aria-label={data.title}
>
  <Handle id="in-left" type="target" position={Position.Left} isConnectable={false} />
  <Handle id="out-right" type="source" position={Position.Right} isConnectable={false} />
  <Handle id="in-top" type="target" position={Position.Top} isConnectable={false} />
  <Handle id="out-top" type="source" position={Position.Top} isConnectable={false} />
  <Handle id="in-bottom" type="target" position={Position.Bottom} isConnectable={false} />
  <Handle id="out-bottom" type="source" position={Position.Bottom} isConnectable={false} />
  <Handle id="out-left" type="source" position={Position.Left} isConnectable={false} />
  <Handle id="in-right" type="target" position={Position.Right} isConnectable={false} />

  <header class="node-drag-handle" title="Drag this header to move the component">
    <div class="heading">
      {#if data.eyebrow}<span class="eyebrow">{data.eyebrow}</span>{/if}
      <strong>{data.title}</strong>
    </div>
    <button class="inspect nodrag nopan" aria-label={`Inspect ${data.title}`} onclick={(event) => inspect(event)} title={`Inspect ${data.title}`}>
      <svg viewBox="0 0 16 16" width="13" height="13" aria-hidden="true"><path d="M4 3h9v9M12.5 3.5 3 13" fill="none" stroke="currentColor" stroke-width="1.5" /></svg>
    </button>
  </header>
  {#if data.subtitle}<p class="subtitle">{data.subtitle}</p>{/if}
  <div class="modules">
    {#each data.modules as module (module.id)}
      <div class="module" data-module={module.id}>
        <span class="module-title" title={module.hint ?? module.title}>{module.title}</span>
        <div class="module-actions nodrag nopan">
          <button class="nodrag nopan" aria-label={`Code: ${data.title} / ${module.title}`} title={`Open source for ${module.title}`} onclick={(event) => inspect(event, module, 'sources')}>Code</button>
          <button class="nodrag nopan" aria-label={`Log: ${data.title} / ${module.title}`} title={`Inspect evidence for ${module.title}`} onclick={(event) => inspect(event, module, 'evidence')}>Log</button>
        </div>
      </div>
    {/each}
  </div>
  {#if data.extension}<div class="extension">{data.extension}</div>{/if}
  {#if data.badge}<span class="badge">{data.badge}</span>{/if}
</article>

<style>
  .component-node { --node-accent: #567b8e; box-sizing: border-box; width: 100%; height: 100%; display: flex; flex-direction: column; position: relative; border: 1px solid #c7d3d9; border-radius: 9px; background: #fff; color: #263e4b; box-shadow: none; transition: opacity 150ms, border-color 150ms, box-shadow 150ms; }
  .component-node[data-kind='data'] { --node-accent: #587b69; }
  .component-node[data-kind='evidence'] { --node-accent: #7b6c8c; }
  .component-node[data-kind='deployment'] { --node-accent: #8b7658; }
  .component-node.active { border-color: var(--node-accent); box-shadow: none; outline: 1px solid color-mix(in srgb, var(--node-accent) 35%, transparent); outline-offset: 0; }
  .component-node.dim { opacity: .37; }
  .component-node.dim:hover, .component-node.dim:focus-within { opacity: .95; }
  .component-node.inspected { outline: 2px solid #377d91; outline-offset: 3px; }
  .node-drag-handle { display: flex; align-items: center; gap: 7px; padding: 10px 10px 8px; min-height: 23px; border-bottom: 1px solid #e8eef1; cursor: grab; user-select: none; border-radius: 8px 8px 0 0; background: #f8fafb; }
  .node-drag-handle:active { cursor: grabbing; }
  .heading { display: flex; flex: 1; min-width: 0; flex-direction: column; gap: 3px; }
  strong { font-size: 15.5px; font-weight: 680; line-height: 1.15; letter-spacing: -.1px; }
  .eyebrow { font-size: 8.5px; line-height: 1; font-weight: 650; letter-spacing: .75px; text-transform: uppercase; color: #708590; }
  button { font: inherit; cursor: pointer; border: 0; }
  .inspect { width: 23px; height: 23px; padding: 4px; display: grid; place-items: center; border-radius: 4px; color: #69818c; background: #f0f5f7; }
  .inspect:hover { color: #1c6075; background: #e3eef2; }
  .subtitle { font-size: 10px; line-height: 1.35; margin: 7px 10px 0; color: #75858e; }
  .modules { display: flex; flex-direction: column; justify-content: center; gap: 0; padding: 5px 8px 7px; flex: 1; }
  .module { display: flex; align-items: center; justify-content: space-between; gap: 6px; min-height: 28px; padding: 3px 1px; border-bottom: 1px solid #edf1f3; }
  .module:last-child { border-bottom: 0; }
  .module-title { font-size: 13.5px; line-height: 1.15; font-weight: 500; min-width: 0; }
  .module-actions { display: flex; align-items: center; gap: 4px; flex: none; }
  .module-actions button { background: #f2f6f8; border-radius: 3px; padding: 3px 4px; font-size: 11.5px; line-height: 1.3; color: #426777; }
  .module-actions button:hover { background: #dfeef3; color: #1d566a; }
  button:focus-visible { outline: 2px solid #2d7c96; outline-offset: 2px; }
  .wide .modules { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 9px; }
  .wide .module { flex-direction: column; align-items: flex-start; justify-content: center; gap: 6px; border-bottom: 0; border-right: 1px solid #edf1f3; padding-right: 8px; }
  .wide .module:last-child { border-right: 0; }
  .wide .module-title { font-size: 13.5px; }
  .badge { position: absolute; top: -8px; right: 9px; background: #e7f0eb; border: 1px solid #cadbcf; border-radius: 4px; padding: 2px 5px; font-size: 8px; font-weight: 650; line-height: 1.2; color: #43624f; letter-spacing: .2px; }
  .extension { font-size: 9px; padding: 3px 9px 5px; color: #806c52; border-top: 1px dashed #d8cdbb; background: #fcfaf6; border-radius: 0 0 8px 8px; }
  .component-node :global(.svelte-flow__handle) { width: 5px; height: 5px; min-width: 5px; min-height: 5px; background: #bccbd2; border: 1px solid #fff; opacity: .7; }
  .component-node.active :global(.svelte-flow__handle) { background: var(--node-accent); opacity: 1; }
  @media (prefers-reduced-motion: reduce) { .component-node { transition: none; } }
</style>
