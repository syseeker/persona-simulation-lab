<script lang="ts">
  import {BaseEdge,EdgeLabel,type EdgeProps} from '@xyflow/svelte';
  import type {RoutedLink} from './orthogonalRouter';
  let {id,data,style,markerEnd}:EdgeProps=$props();
  const route=$derived(data?.route as RoutedLink|undefined);
</script>

{#if route}
  <BaseEdge {id} path={route.path} {style} {markerEnd} interactionWidth={0}/>
  {#if route.labelBox}
    <EdgeLabel x={route.labelBox.x+route.labelBox.width/2} y={route.labelBox.y+route.labelBox.height/2} width={route.labelBox.width} height={route.labelBox.height} style="padding:0;background:transparent">
      <span class="connection-label" class:active={data?.active} style:width={`${route.labelBox.width}px`} style:height={`${route.labelBox.height}px`} style:color={data?.active?String(data.color):'#627684'} data-edge-label={id}>{#each route.labelLines as line}<span>{line}</span>{/each}</span>
    </EdgeLabel>
  {/if}
{/if}

<style>
  .connection-label{box-sizing:border-box;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#fbfdfe;border:1px solid #e4eaee;border-radius:4px;padding:3px 6px;font-size:10px;font-weight:500;line-height:12px;white-space:nowrap;pointer-events:none}
  .connection-label.active{font-weight:650;border-color:currentColor;background:#fff}
</style>
