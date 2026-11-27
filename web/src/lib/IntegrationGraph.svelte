<script lang="ts">
  import { onMount, tick, untrack } from 'svelte';
  import { SvelteFlow, Background, BackgroundVariant, Controls, MarkerType,
    getViewportForBounds, type Node, type Edge, type Viewport } from '@xyflow/svelte';
  import '@xyflow/svelte/dist/style.css';
  import ComponentNode from './ComponentNode.svelte';
  import ZoneNode from './ZoneNode.svelte';
  import OrthogonalEdge from './OrthogonalEdge.svelte';
  import {integrationNodes} from './integrationLayout';
  import {routeConnections,absoluteRectangles,rectanglesOverlap,type RoutedLink} from './orthogonalRouter';
  import { components, componentById, operationById, componentTitle, componentUsed, simpleBlocks, edgesFor, preset, hostCallerPosition } from './lessonArchitecture';
  import {conceptOperations} from './teaching/selection';

  let { applicationOnly=false,managedCondition=false,detailed=false, scenarioId='photography', active=[], focused=false, search='', labels=true, selected=null, oninspect=()=>{} }:
    { detailed?:boolean; applicationOnly?:boolean; managedCondition?:boolean; scenarioId?:string; active?:string[]; focused?:boolean; search?:string; labels?:boolean; selected?:string|null;
      oninspect?:(component:string,operation?:string)=>void } = $props();
  const nodeTypes={component:ComponentNode,zone:ZoneNode};
  const edgeTypes={orthogonal:OrthogonalEdge};
  let dragging=$state(false),dragSnapshot:Node[]=[];
  let routingKey='',routes=new Map<string,RoutedLink>();
  let nodes=$state.raw<Node[]>([]), edges=$state.raw<Edge[]>([]);
  let viewport=$state<Viewport>({x:20,y:20,zoom:.8});
  let width=$state(0),height=$state(0),mounted=$state(false);
  let restoredViewport=false,currentView='';
  const storagePrefix='persona-lab-guide-wireframe:integration-map:v2:';
  const inspect=(component:string,operation?:string)=>oninspect(component,operation);

  function updateEmphasis(options:{detail:boolean;scenario:string;operations:string[];focus:boolean;query:string;labels:boolean;selection:string|null}) {
    const lit=new Set(options.operations), query=options.query.trim().toLocaleLowerCase();
    const blocks=simpleBlocks(options.scenario);
    const membership=new Map(blocks.flatMap(b=>b.members.map(c=>[c,b.id])));
    const translate=(id:string)=>options.detail?id:membership.get(id)||id;
    nodes=nodes.map(node=>{
      if(node.type==='zone') return node;
      const simple=blocks.find(b=>b.id===node.id), component=componentById[node.id];
      if(!simple&&!component)return node;
      const members=simple?.members||[node.id];
      const operations=simple?members.flatMap(m=>componentById[m].operations):component.operations;
      const isActive=operations.some(o=>lit.has(o.id))||(applicationOnly&&['advisor','evidence','records'].includes(node.id));
      const modules=simple?simple.rows.map((r,index)=>({id:`${simple.id}.${index}`,title:r.title,component:simple.id,
        active:conceptOperations(options.scenario,simple.id,`${simple.id}.${index}`).some(id=>lit.has(id))})):
        component.operations.map((o,index)=>({id:options.detail?o.id:`${component.id}.${index}`,title:o.title,component:component.id,active:lit.has(o.id)}));
      const title=simple?.title||(!options.detail?component.simple:componentTitle(node.id,options.scenario));
      const used=members.some(m=>componentUsed(m,options.scenario));
      const text=`${title} ${members.map(m=>componentTitle(m,options.scenario)).join(' ')} ${operations.map(o=>o.title).join(' ')}`.toLocaleLowerCase();
      let badge='';
      const recorded=['photography','boardgames','dreamjob'].includes(options.scenario);
      if(!used)badge='Not used in this preset';
      else if(!recorded&&['designer','routing','guardrails','helix','platform'].includes(node.id))badge='Planned · no scenario evidence';
      else if(node.id==='harness')badge='Selected harness';
      return {...node,data:{title,kind:simple?.kind||component.kind,subtitle:simple?.purpose,
        modules,active:options.focus&&isActive,dim:(!!query&&!text.includes(query))||(options.focus&&!isActive),
        inspected:options.selection===node.id||members.includes(options.selection||''),badge,wide:false,
        inspectId:node.id,oninspect:inspect}};
    });
    const links=edgesFor(options.scenario), grouped=new Map<string,{source:string;target:string;label:string;kind:string;ops:string[]}>();
    for(const e of links){
      const source=translate(e.source),target=translate(e.target);
      if(source===target)continue;
      const id=`${source}-${target}-${e.kind}`;
      const previous=grouped.get(id);
      if(previous)previous.ops.push(...e.operations);
      else grouped.set(id,{source,target,label:options.detail?e.label:({
        'person-situation':'Same person + learning goal','situation-learner':'Private test context',
        'learner-advisor':'Public learner message','advisor-learner':'Public advisor reply',
        'harness-tools':'Course tool connection / facts','harness-model':'Model connection / calls',
        'harness-relay':'Observed execution','supervisor-workload':'Enforced access',
      } as Record<string,string>)[e.id]||e.label,kind:e.kind,ops:[...e.operations]});
    }
    const input=[...grouped.entries()].map(([id,e])=>({id,...e,label:options.labels?e.label:undefined}));
    const geometryKey=JSON.stringify([nodes.map(n=>[n.id,n.type,n.position.x,n.position.y,n.width,n.height,n.parentId]),input.map(e=>[e.id,e.source,e.target,e.label])]);
    if(geometryKey!==routingKey){
      routes=new Map(routeConnections(nodes,input).map(route=>[route.id,route]));routingKey=geometryKey;
    }
    edges=input.map(e=>{
      const nativePath=applicationOnly&&(options.detail?[e.source,e.target].some(id=>['fabric','harness','mcp','catalogue','relay'].includes(id)):
        (e.source==='advisor'&&!['learner','guardrails'].includes(e.target))||(e.target==='advisor'&&!['learner','guardrails'].includes(e.source))||[e.source,e.target].includes('courses'));
      const emphasized=options.focus&&!nativePath&&e.ops.some(o=>lit.has(o));
      const dim=options.focus&&!emphasized;
      const palette:Record<string,string>={prep:'#477b66',request:'#3c6c95',telemetry:'#7b5da6',control:'#9d7436'};
      const color=emphasized?palette[e.kind]:'#a0adb5',route=routes.get(e.id);
      return {id:e.id,source:e.source,target:e.target,
        sourceHandle:`out-${route?.sourceSide||'right'}`,targetHandle:`in-${route?.targetSide||'left'}`,
        type:'orthogonal',animated:false,selectable:false,deletable:false,zIndex:1,
        data:{kind:e.kind,route,active:emphasized,color},
        class:`integration-edge kind-${e.kind}${emphasized?' is-active':''}${dim?' is-dim':''}`,
        style:`stroke:${color};stroke-width:${emphasized?2:1.1};opacity:${dim?.16:emphasized?.95:.62};stroke-dasharray:${e.kind==='control'?'2 5':e.kind==='telemetry'?'5 4':'none'}`,
        markerEnd:{type:MarkerType.ArrowClosed,width:12,height:12,color}} as Edge;
    });
  }
  const layoutKey=(detail:boolean,managed:boolean)=>storagePrefix+(detail?'detailed':'simple')+(managed?':managed':'');
  function keepHostCallerOutside(initial:Node[]):Node[] {
    const caller=initial.find(n=>n.id==='zone-caller'),sandbox=initial.find(n=>n.id==='zone-sandbox');
    if(!caller||!sandbox)return initial;
    const position=hostCallerPosition({...caller.position,width:caller.width!,height:caller.height!},
      {...sandbox.position,width:sandbox.width!,height:sandbox.height!});
    return initial.map(n=>n.id===caller.id?{...n,position}:n.id==='guardrails'?{...n,position:{
      x:Math.max(0,Math.min(n.position.x,caller.width!-n.width!)),
      y:Math.max(40,Math.min(n.position.y,caller.height!-n.height!))}}:n);
  }
  function readLayout(detail:boolean,managed:boolean){
    const key=layoutKey(detail,managed);
    let initial=integrationNodes(detail,managed),savedView:Viewport|null=null;
    try{
      const saved=JSON.parse(localStorage.getItem(key)||'null');
      if(saved?.version===2&&Array.isArray(saved.positions)){
        const positions=new Map<string,{x:number;y:number}>();
        for(const p of saved.positions)if(typeof p.id==='string'&&Number.isFinite(p.x)&&Number.isFinite(p.y)&&Math.abs(p.x)<20000&&Math.abs(p.y)<20000)positions.set(p.id,{x:p.x,y:p.y});
        initial=initial.map(n=>({...n,position:positions.get(n.id)||n.position}));
        const v=saved.viewport;
        if(v&&Number.isFinite(v.x)&&Number.isFinite(v.y)&&v.zoom>=.2&&v.zoom<=1.8)savedView=v;
      }
    }catch{/* Optional browser layout. */}
    nodes=keepHostCallerOutside(initial);currentView=key;restoredViewport=!!savedView;
    if(savedView)viewport=savedView;else void tick().then(()=>fit());
  }
  $effect(()=>{const detail=detailed,managed=managedCondition;if(mounted)untrack(()=>{readLayout(detail,managed);updateEmphasis({detail,scenario:scenarioId,operations:active,focus:focused,query:search,labels,selection:selected});});});
  $effect(()=>{const options={detail:detailed,scenario:scenarioId,operations:[...active],focus:focused,query:search,labels,selection:selected};untrack(()=>updateEmphasis(options));});
  const positionsKey=$derived(nodes.map(n=>`${n.id}:${n.position.x}:${n.position.y}`).join('|'));
  $effect(()=>{const key=positionsKey,isDragging=dragging;if(mounted&&!isDragging&&key)untrack(()=>updateEmphasis({detail:detailed,scenario:scenarioId,operations:active,focus:focused,query:search,labels,selection:selected}));});
  function startDrag(){dragSnapshot=nodes.map(n=>({...n,position:{...n.position}}));dragging=true;}
  function endDrag(){
    const proposed=managedCondition?keepHostCallerOutside(nodes):nodes,rectangles=absoluteRectangles(proposed);
    const cards=rectangles.filter(r=>proposed.find(n=>n.id===r.id)?.type==='component');
    const invalid=cards.some((r,i)=>cards.some((other,j)=>j>i&&rectanglesOverlap(r,other,8)));
    nodes=invalid?dragSnapshot:proposed;dragging=false;
  }
  onMount(()=>{mounted=true;});
  export function saveLayout(){if(!currentView)return false;try{localStorage.setItem(currentView,JSON.stringify({version:2,positions:nodes.map(n=>({id:n.id,x:n.position.x,y:n.position.y})),viewport}));return true;}catch{return false;}}
  export function resetLayout(){try{localStorage.removeItem(layoutKey(detailed,managedCondition));}catch{/* Optional browser layout. */}readLayout(detailed,managedCondition);updateEmphasis({detail:detailed,scenario:scenarioId,operations:active,focus:focused,query:search,labels,selection:selected});void tick().then(()=>fit());}
  export function fit(){
    if(!width||!height||!nodes.length)return;
    // Children are constrained to their groups. Root rectangles therefore bound
    // the entire architecture, including groups moved by the developer.
    const roots=nodes.filter(n=>!n.parentId),x=Math.min(...roots.map(n=>n.position.x)),y=Math.min(...roots.map(n=>n.position.y));
    const points=[...routes.values()].flatMap(r=>[...r.points,...(r.labelBox?[{x:r.labelBox.x,y:r.labelBox.y},{x:r.labelBox.x+r.labelBox.width,y:r.labelBox.y+r.labelBox.height}]:[])]);
    const left=Math.min(x,...points.map(p=>p.x)),top=Math.min(y,...points.map(p=>p.y));
    const bounds={x:left,y:top,width:Math.max(...roots.map(n=>n.position.x+(n.width||0)),...points.map(p=>p.x))-left,height:Math.max(...roots.map(n=>n.position.y+(n.height||0)),...points.map(p=>p.y))-top};
    viewport=getViewportForBounds(bounds,width,height,.2,1,'6%');
  }
  function inspectNode({node,event}:{node:Node;event:MouseEvent|TouchEvent}){if(node.type!=='component'||(event.target instanceof Element&&event.target.closest('button')))return;inspect((node.data.inspectId as string)||node.id);}
</script>

<div class="integration-map" class:detailed bind:clientWidth={width} bind:clientHeight={height} data-testid="integration-graph" data-view={detailed ? 'detailed' : 'simple'} data-boundary={managedCondition ? 'managed' : 'standalone'}>
  <SvelteFlow
    id="citizen-integration-map"
    bind:nodes bind:edges bind:viewport {nodeTypes} {edgeTypes}
    minZoom={.2} maxZoom={1.8} nodesConnectable={false} edgesFocusable={false}
    deleteKey={null} zoomOnDoubleClick={false} panOnScroll={false}
    nodeDragThreshold={4} elevateNodesOnSelect={false} zIndexMode="manual" defaultMarkerColor="#9dafb9"
    onnodeclick={inspectNode}
    onnodedragstart={startDrag} onnodedragstop={endDrag}
    oninit={() => { if (!restoredViewport) void tick().then(() => fit()); }}
    aria-label="Interactive NeMo integration map"
  >
    <Background variant={BackgroundVariant.Dots} gap={20} size={.7} patternColor="#d4dfe5" bgColor="#fbfdfe" />
    <Controls position="bottom-left" showLock={false} fitViewOptions={{ padding: '6%', minZoom: .2, maxZoom: 1 }} />
  </SvelteFlow>
  {#if applicationOnly}<div class="application-branch nodrag nopan" role="note"><strong>Application clarification · inside OpenShell</strong><span>Input check → ask for missing constraints → output check → public reply</span><small>No advisor model, Fabric invocation or course-tool call. UserSim's learner/judge work remains separate.</small></div>{/if}
  <div class="map-hint nodrag nopan" aria-hidden="true"><span class="hint-dot"></span>Drag a header · Pan the canvas · Select a block or operation to understand it</div>
</div>

<style>
  .integration-map { position: relative; width: 100%; height: 100%; min-height: 0; border: 0; border-radius: 0; overflow: hidden; background: #fbfdfe; isolation: isolate; }
  .integration-map :global(.svelte-flow) { --xy-background-color: #fbfdfe; --xy-controls-button-background-color: #fff; --xy-controls-button-background-color-hover: #eef5f8; --xy-controls-button-color: #496674; --xy-controls-button-border-color: #e0e8ec; font-family: inherit; }
  .integration-map :global(.svelte-flow__node-component), .integration-map :global(.svelte-flow__node-zone) { border: 0; background: transparent; padding: 0; }
  .integration-map :global(.svelte-flow__node-component) { border-radius: 9px; }
  .integration-map :global(.svelte-flow__node-component:focus-visible) { outline: 2px solid #31839a; outline-offset: 4px; }
  .integration-map :global(.svelte-flow__controls) { overflow: hidden; border-radius: 7px; box-shadow: none; border: 1px solid #dce5ea; }
  .integration-map :global(.svelte-flow__controls-button) { width: 31px; height: 31px; }
  .integration-map :global(.integration-edge .svelte-flow__edge-path) { animation: none; }
  .integration-map :global(.svelte-flow__edge-textwrapper) { pointer-events: none; }
  /* Edges have no actions. Their padded hit areas must never cover module links. */
  .integration-map :global(.svelte-flow__edge),
  .integration-map :global(.svelte-flow__edge-interaction),
  .integration-map :global(.svelte-flow__edge-path),
  .integration-map :global(.svelte-flow__edge-labels),
  .integration-map :global(.svelte-flow__edge-label),
  .integration-map :global(.svelte-flow__edge-label *) { pointer-events: none !important; }
  .application-branch{position:absolute;left:22px;bottom:78px;max-width:440px;padding:12px 15px;border:1px solid #b6cec6;border-left:3px solid var(--teal);background:#f2f8f6f7;border-radius:5px;font-size:12px;display:grid;gap:6px;line-height:1.5;z-index:4}.application-branch small{color:var(--muted);font-size:10px}
  .map-hint { position: absolute; right: 12px; bottom: 31px; display: flex; align-items: center; gap: 6px; color: #82959e; background: #ffffffeb; border: 1px solid #e3ebef; border-radius: 5px; padding: 6px 9px; font-size: 9px; line-height: 1.2; pointer-events: none; }
  .hint-dot { width: 5px; height: 5px; border-radius: 50%; background: #749aa9; }
  @media (max-width: 600px) { .map-hint { max-width: 205px; font-size: 8px; bottom: 30px; right: 7px; padding: 5px; } }
  @media (prefers-reduced-motion: reduce) { .integration-map :global(.integration-edge.is-active .svelte-flow__edge-path), .integration-map :global(.svelte-flow__edge.animated path) { animation: none !important; } }
</style>
