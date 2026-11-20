<script lang="ts">
  import { onMount, tick, untrack } from 'svelte';
  import {
    SvelteFlow, Background, BackgroundVariant, Controls, MarkerType,
    getNodesBounds, getViewportForBounds, type Node, type Edge, type Viewport
  } from '@xyflow/svelte';
  import '@xyflow/svelte/dist/style.css';
  import ComponentNode from './ComponentNode.svelte';
  import ZoneNode from './ZoneNode.svelte';

  type Inspect = (node: string, module?: string, tab?: 'overview' | 'evidence' | 'sources') => void;
  type Module = { id: string; title: string; component?: string; hint?: string };
  type Definition = { id: string; title: string; kind: string; modules: Module[]; subtitle?: string; eyebrow?: string; inspectId?: string; members?: string[] };
  let {
    detailed = false, active = [], activeEdges = [], designer = false, harness = 'deepagents', routing = 'fixed',
    execution = 'standalone', guardrails = false, helix = false, search = '', filter = 'all', labels = true, extensions = false,
    selected = null, oninspect = () => {}
  }: {
    detailed?: boolean; active?: string[]; activeEdges?: string[]; designer?: boolean;
    harness?: 'deepagents' | 'hermes'; routing?: 'fixed' | 'switchyard'; execution?: 'standalone' | 'managed'; guardrails?: boolean; helix?: boolean;
    search?: string; filter?: string; labels?: boolean; extensions?: boolean; selected?: string | null; oninspect?: Inspect;
  } = $props();

  const definitions: Definition[] = [
    { id: 'personas', title: 'Nemotron Personas', kind: 'data', eyebrow: 'Singapore profiles', modules: [
      { id: 'source', title: 'Load source' }, { id: 'sample', title: 'Sample & preview' }, { id: 'lock', title: 'Lock identity' }
    ] },
    { id: 'designer', title: 'Data Designer', kind: 'data', subtitle: 'Hypotheses stay separate', modules: [
      { id: 'schema', title: 'Define columns' }, { id: 'generate', title: 'Generate scenario' }, { id: 'lineage', title: 'Validate & link' }
    ] },
    { id: 'usersim', title: 'NeMo UserSim', kind: 'runtime', modules: [
      { id: 'activate', title: 'Activate profile' }, { id: 'message', title: 'Learner message' }, { id: 'conversation', title: 'Conversation state' }
    ] },
    { id: 'fabric', title: 'NeMo Fabric', kind: 'runtime', eyebrow: 'Harness lifecycle', modules: [
      { id: 'configuration', title: 'Configure agent' }, { id: 'plan', title: 'Plan & doctor' }, { id: 'runtime', title: 'Start runtime' }
    ] },
    { id: 'deepagents', title: 'Deep Agents', kind: 'runtime', modules: [
      { id: 'policy', title: 'Application policy' }, { id: 'tools', title: 'Tool allowlist' }, { id: 'reply', title: 'Bounded agent loop' }
    ] },
    { id: 'hermes', title: 'Hermes', kind: 'runtime', modules: [
      { id: 'profile', title: 'Isolated runtime' }, { id: 'discovery', title: 'Discover MCP tools' }, { id: 'reply', title: 'Bounded agent loop' }
    ] },
    { id: 'mcp', title: 'Course MCP', kind: 'tools', eyebrow: 'Read-only tools', modules: [
      { id: 'search', title: 'Search courses' }, { id: 'details', title: 'Get course details' }, { id: 'preferences', title: 'Read constraints' }
    ] },
    { id: 'catalogue', title: 'Course catalogue', kind: 'tools', modules: [
      { id: 'snapshot', title: 'Dated snapshot' }, { id: 'matching', title: 'Match constraints' }, { id: 'citations', title: 'Source links' }
    ] },
    { id: 'gateway', title: 'Inference gateway', kind: 'models', modules: [
      { id: 'admission', title: 'Admit & bound calls' }, { id: 'schemas', title: 'Limit tool schemas' }, { id: 'ledger', title: 'Record call ledger' }
    ] },
    { id: 'routing', title: 'NeMo Switchyard', kind: 'models', modules: [
      { id: 'policy', title: 'Routing policy' }, { id: 'decision', title: 'Select model' }, { id: 'receipt', title: 'Decision evidence' }
    ] },
    { id: 'litellm', title: 'LiteLLM proxy', kind: 'models', modules: [
      { id: 'aliases', title: 'Model aliases' }, { id: 'plugin', title: 'Switchyard hook' }, { id: 'provider', title: 'Provider request' }
    ] },
    { id: 'providers', title: 'LLM providers', kind: 'models', modules: [
      { id: 'nim', title: 'Hosted NIM' }, { id: 'brev', title: 'Brev endpoint' }, { id: 'frontier', title: 'Frontier API' }
    ] },
    { id: 'relay', title: 'NeMo Relay', kind: 'evidence', modules: [
      { id: 'scopes', title: 'Native scopes' }, { id: 'tools', title: 'Tool inputs / outputs' }, { id: 'parents', title: 'Parent relationships' }
    ] },
    { id: 'records', title: 'Saved records', kind: 'evidence', modules: [
      { id: 'manifest', title: 'Run manifest' }, { id: 'artifacts', title: 'Artifact files' }, { id: 'replay', title: 'Reopen evidence' }
    ] },
    { id: 'checks', title: 'Application assertions', kind: 'evidence', modules: [
      { id: 'facts', title: 'Check saved facts' }, { id: 'criteria', title: 'Expected / actual' }, { id: 'coverage', title: 'Reasons & coverage' }
    ] },
    { id: 'guardrails', title: 'NeMo Guardrails', kind: 'runtime', subtitle: 'Behavioural checks · planned', modules: [
      { id: 'input', title: 'Input checks' }, { id: 'output', title: 'Output checks' }, { id: 'decision', title: 'Decision & errors' }
    ] },
    { id: 'helix', title: 'Helix Evals', kind: 'evidence', modules: [
      { id: 'criteria', title: 'Evaluate saved reply' }, { id: 'rows', title: 'Criterion reasons' }, { id: 'limits', title: 'Failures & limits' }
    ] },
    { id: 'platform', title: 'Helix control plane', kind: 'deployment', modules: [
      { id: 'register', title: 'Agent registry' }, { id: 'deploy', title: 'Deploy & session' }, { id: 'jobs', title: 'Evaluation jobs' }, { id: 'experiments', title: 'Experiment control' }
    ] },
    { id: 'openshell', title: 'OpenShell', kind: 'deployment', modules: [
      { id: 'policy', title: 'Agent / tool boundary' }, { id: 'network', title: 'Network policy' }, { id: 'review', title: 'Access review' }
    ] }
  ];
  const byId = new Map(definitions.map((definition) => [definition.id, definition]));
  const responsibilities: Definition[] = [
    { id: 'testpeople', title: 'Choose test people', kind: 'data', eyebrow: '1 · Profiles & scenarios', inspectId: 'personas', members: ['personas', 'designer'], modules: [
      { id: 'profiles', title: 'Singapore Personas', component: 'personas' }, { id: 'scenarios', title: 'Designer scenarios', component: 'designer' }, { id: 'lineage', title: 'Lock source & lineage', component: 'designer' }
    ] },
    { id: 'simulator', title: 'Simulate the learner', kind: 'runtime', eyebrow: '2 · UserSim', inspectId: 'usersim', members: ['usersim'], modules: [
      { id: 'activation', title: 'Activate one profile', component: 'usersim' }, { id: 'messages', title: 'Public messages', component: 'usersim' }, { id: 'state', title: 'Isolated conversation', component: 'usersim' }
    ] },
    { id: 'application', title: 'Run your application', kind: 'runtime', eyebrow: '3 · Fabric + harness', inspectId: 'fabric', members: ['fabric', 'deepagents', 'hermes'], modules: [
      { id: 'runtime', title: 'Fabric lifecycle', component: 'fabric' }, { id: 'harness', title: 'Deep Agents harness', component: 'deepagents' }, { id: 'policy', title: 'Application policy', component: 'deepagents' }
    ] },
    { id: 'courses', title: 'Ground in real facts', kind: 'tools', eyebrow: '4 · Bounded course tools', inspectId: 'mcp', members: ['mcp', 'catalogue'], modules: [
      { id: 'tools', title: 'Read-only course MCP', component: 'mcp' }, { id: 'facts', title: 'Dated catalogue', component: 'catalogue' }, { id: 'constraints', title: 'Budget & availability', component: 'mcp' }
    ] },
    { id: 'models', title: 'Connect a model', kind: 'models', eyebrow: '5 · Gateway & proxy', inspectId: 'gateway', members: ['gateway', 'routing', 'litellm', 'providers'], modules: [
      { id: 'gateway', title: 'Call limits & ledger', component: 'gateway' }, { id: 'route', title: 'Fixed model route', component: 'litellm' }, { id: 'proxy', title: 'LiteLLM → provider', component: 'litellm' }
    ] },
    { id: 'evidence', title: 'Inspect & evaluate', kind: 'evidence', eyebrow: '6 · Native evidence & checks', inspectId: 'relay', members: ['relay', 'records', 'checks', 'helix'], modules: [
      { id: 'trace', title: 'Native Relay trace', component: 'relay' }, { id: 'saved', title: 'Saved run artifacts', component: 'records' }, { id: 'evaluate', title: 'Application assertions', component: 'checks' }
    ] }
  ];

  const nodeTypes = { component: ComponentNode, zone: ZoneNode };
  let nodes = $state.raw<Node[]>([]);
  let edges = $state.raw<Edge[]>([]);
  let viewport = $state<Viewport>({ x: 20, y: 20, zoom: .8 });
  let width = $state(0);
  let height = $state(0);
  let mounted = $state(false);
  let restoredViewport = false;
  let currentView = '';
  const storagePrefix = 'persona-lab-guide-wireframe:integration-map:v1:';
  const inspect: Inspect = (node, module, tab) => oninspect(node, module, tab);

  function card(definition: Definition, x: number, y: number, w: number, h: number, parentId?: string): Node {
    return { id: definition.id, type: 'component', position: { x, y }, width: w, height: h,
      style: `width:${w}px;height:${h}px`, parentId, ...(parentId ? { extent: 'parent' as const } : {}),
      dragHandle: '.node-drag-handle', deletable: false, connectable: false, zIndex: 2,
      data: { ...definition, wide: w > 350, oninspect: inspect } };
  }
  function zone(id: string, title: string, x: number, y: number, w: number, h: number, kind: string, number: string, caption = '', overlay = false): Node {
    return { id, type: 'zone', position: { x, y }, width: w, height: h, style: `width:${w}px;height:${h}px`,
      dragHandle: '.zone-drag-handle', selectable: false, deletable: false, connectable: false, zIndex: 0,
      data: { title, caption, kind, number, overlay, ...(id === 'zone-application' ? { oninspect: inspect, component: 'application' } : {}) } };
  }
  function baseNodes(detail: boolean): Node[] {
    if (!detail) return [
      zone('zone-sandbox', 'OpenShell · application + course tools', 604, -40, 302, 540, 'deployment', '', 'Illustrative boundary', true),
      ...responsibilities.map((definition, index) => {
        const positions = [[0, 0], [310, 0], [16, 40], [16, 312], [310, 272], [0, 272]];
        return card(definition, positions[index][0], positions[index][1], 270, 212, ['application','courses'].includes(definition.id) ? 'zone-sandbox' : undefined);
      }),
      zone('zone-deploy', 'Managed operations & native policy', 0, 548, 890, 240, 'deployment', '', 'Helix optional · OpenShell in all live presets', true),
      card(byId.get('platform')!, 16, 49, 420, 174, 'zone-deploy'),
      card(byId.get('openshell')!, 454, 49, 420, 174, 'zone-deploy'),
      card(byId.get('guardrails')!, 0, 812, 890, 145)
    ];
    return [
      zone('zone-inputs', 'Test people & messages', 0, 0, 222, 612, 'data', '01'),
      zone('zone-application', 'OpenShell · Citizen application', 246, 0, 440, 612, 'deployment', '02', 'Persistent harness + tools', true),
      zone('zone-models', 'Model access', 710, 0, 440, 444, 'models', '03', 'Fixed or routed'),
      zone('zone-evidence', 'Trace & evaluate', 0, 636, 686, 400, 'evidence', '04', 'Application assertions · optional Helix scoring'),
      zone('zone-deploy', 'Managed operations & policy', 710, 466, 440, 382, 'deployment', '05', 'Control plane outside the sandbox', true),
      zone('zone-guards', 'Behavioural safeguards', 710, 872, 440, 205, 'runtime', '06', 'Native checks in scenarios 2 and 3'),
      card(byId.get('personas')!, 12, 48, 198, 164, 'zone-inputs'),
      card(byId.get('designer')!, 12, 230, 198, 180, 'zone-inputs'),
      card(byId.get('usersim')!, 12, 430, 198, 174, 'zone-inputs'),
      card(byId.get('fabric')!, 14, 48, 412, 138, 'zone-application'),
      card(byId.get('deepagents')!, 14, 208, 198, 174, 'zone-application'),
      card(byId.get('hermes')!, 228, 208, 198, 174, 'zone-application'),
      card(byId.get('mcp')!, 14, 412, 198, 178, 'zone-application'),
      card(byId.get('catalogue')!, 228, 412, 198, 178, 'zone-application'),
      card(byId.get('gateway')!, 14, 48, 198, 174, 'zone-models'),
      card(byId.get('routing')!, 228, 48, 198, 174, 'zone-models'),
      card(byId.get('litellm')!, 14, 246, 198, 174, 'zone-models'),
      card(byId.get('providers')!, 228, 246, 198, 174, 'zone-models'),
      card(byId.get('relay')!, 12, 45, 212, 160, 'zone-evidence'),
      card(byId.get('records')!, 236, 45, 212, 160, 'zone-evidence'),
      card(byId.get('helix')!, 460, 45, 212, 160, 'zone-evidence'),
      card(byId.get('checks')!, 12, 228, 660, 150, 'zone-evidence'),
      card(byId.get('guardrails')!, 14, 43, 412, 150, 'zone-guards'),
      card(byId.get('platform')!, 14, 51, 198, 310, 'zone-deploy'),
      card(byId.get('openshell')!, 228, 51, 198, 310, 'zone-deploy')
    ];
  }

  type Link = [string, string, string, string?, string?];
  function baseLinks(detail: boolean): Link[] {
    if (!detail) return [
      ['testpeople', 'simulator', 'Profile + scenario'], ['simulator', 'application', 'Public learner message'],
      ['testpeople', 'evidence', 'Scenario + lineage', 'out-bottom', 'in-top'],
      ['simulator', 'models', 'Simulation calls', 'out-bottom', 'in-top'],
      ['simulator', 'evidence', 'Public turns', 'out-left', 'in-top'],
      ['application', 'courses', 'Read facts', 'out-bottom', 'in-top'],
      ['application', 'models', 'Model request', 'out-bottom', 'in-top'],
      ['courses', 'application', 'Course facts', 'out-right', 'in-right'],
      ['models', 'application', 'Model reply', 'out-right', 'in-left'],
      ['application', 'simulator', 'Public reply', 'out-top', 'in-top'],
      ['courses', 'evidence', 'Frozen facts', 'out-bottom', 'in-right'],
      ['models', 'evidence', 'Response + usage', 'out-left', 'in-right'],
      ['application', 'evidence', 'Native trace', 'out-left', 'in-top'],
      ['platform', 'openshell', 'Deploy agent + tools'],
      ['application', 'platform', 'Register application', 'out-bottom', 'in-top'],
      ['openshell', 'application', 'Runtime policy', 'out-right', 'in-right'],
      ['simulator','guardrails','Public input check','out-bottom','in-top'],
      ['guardrails','application','Allowed public message','out-right','in-bottom'],
      ['application','guardrails','Public output check','out-right','in-right'],
      ['guardrails','simulator','Checked public reply','out-top','in-bottom'],
      ['guardrails','evidence','Check decision','out-left','in-bottom'],
      ['platform','evidence','Managed jobs','out-top','in-bottom']
    ];
    return [
      ['personas', 'designer', 'Source seed', 'out-bottom', 'in-top'],
      ['personas', 'usersim', 'Locked profile', 'out-left', 'in-left'],
      ['designer', 'usersim', 'Selected scenario', 'out-bottom', 'in-top'],
      ['designer', 'records', 'Scenario + lineage', 'out-left', 'in-left'],
      ['usersim', 'fabric', 'Public message'],
      ['usersim', 'gateway', 'Simulation calls', 'out-right', 'in-top'],
      ['usersim', 'records', 'Public turns', 'out-bottom', 'in-top'],
      ['fabric', 'deepagents', 'Start harness', 'out-bottom', 'in-top'],
      ['fabric', 'hermes', 'Start harness', 'out-bottom', 'in-top'],
      ['deepagents', 'mcp', 'Tool request', 'out-bottom', 'in-top'],
      ['hermes', 'mcp', 'Tool request', 'out-bottom', 'in-top'],
      ['mcp', 'catalogue', 'Read facts'],
      ['catalogue', 'records', 'Frozen snapshot', 'out-bottom', 'in-top'],
      ['deepagents', 'gateway', 'Model request', 'out-top', 'in-left'],
      ['hermes', 'gateway', 'Model request'],
      ['litellm', 'routing', 'Routing plugin'],
      ['gateway', 'records', 'Role + usage ledger', 'out-bottom', 'in-top'],
      ['gateway', 'litellm', 'Requested alias', 'out-bottom', 'in-top'],
      ['routing', 'litellm', 'Selected candidate', 'out-bottom', 'in-top'],
      ['litellm', 'providers', 'Provider request'],
      ['fabric', 'relay', 'Native scopes', 'out-left', 'in-top'],
      ['fabric', 'records', 'Plan + lifecycle', 'out-bottom', 'in-top'],
      ['mcp', 'relay', 'Tool evidence', 'out-bottom', 'in-top'],
      ['relay', 'records', 'Persist events'],
      ['records', 'checks', 'Saved replies'],
      ['checks', 'helix', 'Score criteria'],
      ['platform', 'helix', 'Evaluation job'],
      ['platform', 'records', 'Lifecycle + job identities'],
      ['usersim', 'guardrails', 'Public input check'],
      ['guardrails', 'fabric', 'Allowed public input'],
      ['fabric', 'guardrails', 'Public output check'],
      ['guardrails', 'usersim', 'Checked public reply'],
      ['guardrails', 'records', 'Native check decision'],
      ['fabric', 'platform', 'Register recipe', 'out-right', 'in-top'],
      ['platform', 'openshell', 'Agent + tools'],
      ['openshell', 'fabric', 'Contains runtime', 'out-top', 'in-right']
    ];
  }
  const simpleMembership = new Map(responsibilities.flatMap((definition) => (definition.members ?? []).map((member) => [member, definition.id])));
  function simpleEdge(id: string): string {
    for (const source of [...byId.keys()].sort((a, b) => b.length - a.length)) {
      if (!id.startsWith(`${source}-`)) continue;
      const target = id.slice(source.length + 1);
      return `${simpleMembership.get(source) ?? source}-${simpleMembership.get(target) ?? target}`;
    }
    return id;
  }

  function updateEmphasis(options: { active: string[]; activeEdges: string[]; designer: boolean; harness: string; routing: string; execution: string; guardrails: boolean; helix: boolean; search: string; filter: string; labels: boolean; extensions: boolean; selected: string | null; detailed: boolean }) {
    const lit = new Set(options.active);
    const litEdges = new Set(options.detailed ? options.activeEdges : options.activeEdges.map(simpleEdge));
    const query = options.search.trim().toLocaleLowerCase();
    const category = options.filter.toLocaleLowerCase();
    nodes = nodes.map((node) => {
      if (node.type === 'zone') return node;
      const definition = (options.detailed ? byId.get(node.id) : responsibilities.find((item) => item.id === node.id)) ?? byId.get(node.id)!;
      if (!definition) return node;
      const members = definition.members ?? [node.id];
      const isActive = members.some((member) => lit.has(member)) || lit.has(node.id);
      const notHarness = (node.id === 'deepagents' || node.id === 'hermes') && node.id !== options.harness;
      const notRoute = node.id === 'routing' && options.routing !== 'switchyard' && !isActive;
      const notDeployment = ['platform', 'helix'].includes(node.id) && !options.helix;
      const notGuardrails = node.id === 'guardrails' && !options.guardrails;
      const text = `${definition.title} ${definition.id} ${definition.modules.map((module) => module.title).join(' ')}`.toLocaleLowerCase();
      const unmatched = !!query && !text.includes(query);
      const categoryMatch = category === 'simulation' ? members.includes('usersim')
        : category === 'inference' ? definition.kind === 'models'
        : category === 'runtime' ? members.some((member) => ['fabric', 'deepagents', 'hermes', 'mcp', 'catalogue'].includes(member))
        : ['data', 'tools', 'models', 'evidence', 'deployment'].includes(category) ? definition.kind === category
        : category === 'active' ? isActive : true;
      const wrongCategory = !categoryMatch;
      let modules = definition.modules;
      if (node.id === 'testpeople' && !options.designer) modules = modules.map((module) => module.id === 'scenarios' ? { ...module, title: 'Authored situation', component: 'situation', hint: 'Designer is skipped for this preset' } : module.id === 'lineage' ? { ...module, title: 'Lock source identity', component: 'personas' } : module);
      if (node.id === 'application') modules = modules.map((module) => module.id === 'harness' ? { ...module, title: options.harness === 'hermes' ? 'Hermes harness' : 'Deep Agents harness', component: options.harness } : module.id === 'policy' ? { ...module, component: options.harness } : module);
      if (node.id === 'evidence') modules = modules.map((module) => module.id === 'evaluate' && options.helix ? { ...module, title: 'Helix Evals + assertions', component: 'helix' } : module);
      if (node.id === 'models') modules = modules.map((module) => module.id === 'route' ? { ...module, title: options.routing === 'switchyard' ? 'Switchyard decision' : 'Fixed model route', component: options.routing === 'switchyard' ? 'routing' : 'litellm' } : module);
      let badge = '';
      if (['deepagents', 'hermes'].includes(node.id) && node.id === options.harness) badge = 'Selected harness';
      if (node.id === 'designer') badge = options.designer ? 'Scenario generation preview' : 'Skipped in this preset';
      if (node.id === 'routing') badge = options.routing === 'switchyard' ? 'Dynamic routing preview' : 'Skipped: fixed model';
      if (node.id === 'openshell') badge = options.execution === 'managed' ? 'Helix-managed · planned' : 'Standalone · planned';
      if (['platform','helix'].includes(node.id)) badge = options.helix ? 'Scenario 3 · planned' : 'Not used in this preset';
      if (node.id === 'guardrails') badge = options.guardrails ? 'Native checks · planned' : 'Not used in this preset';
      return { ...node, data: { ...definition, modules, active: isActive, inspected: options.selected === node.id || members.includes(options.selected ?? ''),
        dim: notHarness || notRoute || notDeployment || notGuardrails || unmatched || wrongCategory || (lit.size > 0 && !isActive), badge,
        extension: options.extensions && ['mcp', 'courses'].includes(node.id) ? 'Extension: another read-only service' : undefined,
        wide: (node.width ?? 0) > 350, oninspect: inspect } };
    });
    edges = baseLinks(options.detailed).map(([source, target, label, sourceHandle = 'out-right', targetHandle = 'in-left']) => {
      const id = `${source}-${target}`;
      const animated = litEdges.has(id);
      const inactiveHarness = ['deepagents', 'hermes'].some((name) => (source === name || target === name) && name !== options.harness);
      const inactiveRoute = (((source === 'routing' || target === 'routing') && options.routing !== 'switchyard') || false) && !animated;
      const deployment = ['platform', 'openshell'].includes(source) || ['platform', 'openshell'].includes(target);
      const evidence = ['relay', 'records', 'evidence'].includes(target) || ['relay', 'records'].includes(source);
      const preparation = ['personas', 'designer', 'testpeople'].includes(source) || (source === 'fabric' && ['deepagents', 'hermes'].includes(target));
      const kind = deployment ? 'control' : evidence ? 'telemetry' : preparation ? 'prep' : 'request';
      const palette = { prep: ['#8ba59c', '#477b66'], request: ['#8b9aae', '#3c6c95'], telemetry: ['#9282b3', '#7b5da6'], control: ['#b79057', '#9d7436'] };
      const color = palette[kind][animated ? 1 : 0];
      const dash = kind === 'control' ? '2 5' : kind === 'telemetry' ? '7 4' : animated ? '6 5' : 'none';
      const unavailable = (([source, target].some(id => ['platform','helix'].includes(id))) && !options.helix) || ((source === 'guardrails' || target === 'guardrails') && !options.guardrails);
      const dim = inactiveHarness || inactiveRoute || unavailable || (litEdges.size > 0 && !animated);
      return { id, source, target, sourceHandle, targetHandle, type: 'smoothstep', animated, selectable: false, deletable: false,
        label: options.labels ? label : undefined, zIndex: 1, data: { kind },
        class: `integration-edge kind-${kind}${animated ? ' is-active' : ''}${dim ? ' is-dim' : ''}`,
        style: `stroke:${color};stroke-width:${animated ? 2.2 : 1.15};opacity:${dim ? .2 : .8};stroke-dasharray:${dash};${kind === 'control' ? 'stroke-linecap:round;' : ''}`,
        labelStyle: `font-size:10px;font-weight:${animated ? 650 : 500};color:${color};background:#fafdfe;padding:2px 4px;border-radius:3px;opacity:${dim ? .3 : 1}`,
        markerEnd: { type: MarkerType.ArrowClosed, width: 12, height: 12, color } };
    });
  }

  function readLayout(detail: boolean) {
    const key = storagePrefix + (detail ? 'detailed' : 'simple');
    let initial = baseNodes(detail);
    let savedView: Viewport | null = null;
    if (typeof localStorage !== 'undefined') {
      try {
        const saved = JSON.parse(localStorage.getItem(key) ?? 'null');
        if (saved?.version === 1 && Array.isArray(saved.positions)) {
          const positions = new Map<string, { x: number; y: number }>();
          for (const item of saved.positions) {
            if (typeof item.id === 'string' && Number.isFinite(item.x) && Number.isFinite(item.y) && Math.abs(item.x) < 20000 && Math.abs(item.y) < 20000) positions.set(item.id, { x: item.x, y: item.y });
          }
          if (!detail && !positions.has('zone-sandbox')) {
            for (const id of ['application', 'courses']) {
              const point = positions.get(id);
              if (point) positions.set(id, { x: point.x - 604, y: point.y + 40 });
            }
          }
          initial = initial.map((node) => ({ ...node, position: positions.get(node.id) ?? node.position }));
          const value = saved.viewport;
          if (value && Number.isFinite(value.x) && Number.isFinite(value.y) && Number.isFinite(value.zoom) && value.zoom >= .2 && value.zoom <= 1.8) savedView = value;
        }
      } catch { /* An unavailable or stale local preference must not break the map. */ }
    }
    nodes = initial;
    currentView = key;
    restoredViewport = !!savedView;
    if (savedView) viewport = savedView;
    else void tick().then(() => fit());
  }

  $effect(() => {
    const detail = detailed;
    if (mounted) untrack(() => {
      readLayout(detail);
      updateEmphasis({ active, activeEdges, designer, harness, routing, execution, guardrails, helix, search, filter, labels, extensions, selected, detailed: detail });
    });
  });
  $effect(() => {
    const options = { active: [...active], activeEdges: [...activeEdges], designer, harness, routing, execution, guardrails, helix, search, filter, labels, extensions, selected, detailed };
    // The position-bearing nodes are intentionally not a dependency: emphasis never resets a dragged layout.
    untrack(() => updateEmphasis(options));
  });
  onMount(() => { mounted = true; });

  export function saveLayout(): boolean {
    if (!currentView || typeof localStorage === 'undefined') return false;
    try {
      localStorage.setItem(currentView, JSON.stringify({ version: 1, positions: nodes.map((node) => ({ id: node.id, x: node.position.x, y: node.position.y })), viewport }));
      return true;
    } catch { return false; }
  }
  export function resetLayout() {
    if (typeof localStorage !== 'undefined') {
      try { localStorage.removeItem(storagePrefix + (detailed ? 'detailed' : 'simple')); } catch { /* Storage may be disabled. */ }
    }
    readLayout(detailed);
    updateEmphasis({ active, activeEdges, designer, harness, routing, execution, guardrails, helix, search, filter, labels, extensions, selected, detailed });
    void tick().then(() => fit());
  }
  export function fit() {
    if (!width || !height || !nodes.length) return;
    const bounds = getNodesBounds(nodes.filter((node) => !node.parentId));
    viewport = getViewportForBounds(bounds, width, height, .2, 1, '6%');
  }
  function inspectNode({ node, event }: { node: Node; event: MouseEvent | TouchEvent }) {
    if (node.type !== 'component' || (event.target instanceof Element && event.target.closest('button'))) return;
    inspect((node.data.inspectId as string | undefined) ?? node.id, undefined, 'overview');
  }
</script>

<div class="integration-map" class:detailed bind:clientWidth={width} bind:clientHeight={height} data-testid="integration-graph" data-view={detailed ? 'detailed' : 'simple'}>
  <SvelteFlow
    id="citizen-integration-map"
    bind:nodes bind:edges bind:viewport {nodeTypes}
    minZoom={.2} maxZoom={1.8} nodesConnectable={false} edgesFocusable={false}
    deleteKey={null} zoomOnDoubleClick={false} panOnScroll={false}
    nodeDragThreshold={4} elevateNodesOnSelect={false} defaultMarkerColor="#9dafb9"
    onnodeclick={inspectNode}
    oninit={() => { if (!restoredViewport) void tick().then(() => fit()); }}
    aria-label="Interactive NeMo integration map"
  >
    <Background variant={BackgroundVariant.Dots} gap={20} size={.7} patternColor="#d4dfe5" bgColor="#fbfdfe" />
    <Controls position="bottom-left" showLock={false} fitViewOptions={{ padding: '6%', minZoom: .2, maxZoom: 1 }} />
  </SvelteFlow>
  <div class="map-hint nodrag nopan" aria-hidden="true"><span class="hint-dot"></span>Drag a header · Pan the canvas · Code / Log opens the inspector</div>
</div>

<style>
  .integration-map { position: relative; width: 100%; height: 100%; min-height: 0; border: 0; border-radius: 0; overflow: hidden; background: #fbfdfe; isolation: isolate; }
  .integration-map :global(.svelte-flow) { --xy-background-color: #fbfdfe; --xy-controls-button-background-color: #fff; --xy-controls-button-background-color-hover: #eef5f8; --xy-controls-button-color: #496674; --xy-controls-button-border-color: #e0e8ec; font-family: inherit; }
  .integration-map :global(.svelte-flow__node-component), .integration-map :global(.svelte-flow__node-zone) { border: 0; background: transparent; padding: 0; }
  .integration-map :global(.svelte-flow__node-component) { border-radius: 9px; }
  .integration-map :global(.svelte-flow__node-component:focus-visible) { outline: 2px solid #31839a; outline-offset: 4px; }
  .integration-map :global(.svelte-flow__controls) { overflow: hidden; border-radius: 7px; box-shadow: none; border: 1px solid #dce5ea; }
  .integration-map :global(.svelte-flow__controls-button) { width: 31px; height: 31px; }
  .integration-map :global(.integration-edge.is-active .svelte-flow__edge-path) { animation: edge-travel 750ms linear infinite; }
  .integration-map :global(.svelte-flow__edge-textwrapper) { pointer-events: none; }
  /* Edges have no actions. Their padded hit areas must never cover module links. */
  .integration-map :global(.svelte-flow__edge),
  .integration-map :global(.svelte-flow__edge-interaction),
  .integration-map :global(.svelte-flow__edge-path),
  .integration-map :global(.svelte-flow__edge-labels),
  .integration-map :global(.svelte-flow__edge-label),
  .integration-map :global(.svelte-flow__edge-label *) { pointer-events: none !important; }
  .map-hint { position: absolute; right: 12px; bottom: 31px; display: flex; align-items: center; gap: 6px; color: #82959e; background: #ffffffeb; border: 1px solid #e3ebef; border-radius: 5px; padding: 6px 9px; font-size: 9px; line-height: 1.2; pointer-events: none; }
  .hint-dot { width: 5px; height: 5px; border-radius: 50%; background: #749aa9; }
  @keyframes edge-travel { to { stroke-dashoffset: -22; } }
  @media (max-width: 600px) { .map-hint { max-width: 205px; font-size: 8px; bottom: 30px; right: 7px; padding: 5px; } }
  @media (prefers-reduced-motion: reduce) { .integration-map :global(.integration-edge.is-active .svelte-flow__edge-path), .integration-map :global(.svelte-flow__edge.animated path) { animation: none !important; } }
</style>
