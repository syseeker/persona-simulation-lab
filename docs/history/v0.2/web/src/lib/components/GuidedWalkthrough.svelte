<script lang="ts">
  import { onMount } from 'svelte';
  import { goto } from '$app/navigation';
  import { labApi, pretty } from '#lib/api.ts';
  import CodeReference from './CodeReference.svelte';
  import RunTrace from './RunTrace.svelte';
  import EvidencePanel from './EvidencePanel.svelte';
  import EvaluationPanel from './EvaluationPanel.svelte';
  import DeploymentPanel from './DeploymentPanel.svelte';
  import { prepareManagedStory } from '#lib/managedStory.ts';
  import type { ManagedStoryCondition } from '#lib/types.ts';
  let { status, selectedIds = [], selectedSource = 'hf-profile-only', generatedJob = null,
    ondata = () => {}, onreview = (_id: string) => {} }:
    { status: any; selectedIds?: string[]; selectedSource?: string; generatedJob?: any; ondata?: () => void; onreview?: (id: string) => void } = $props();
  const steps = [
    ['The citizen story', 'Meet the synthetic learner and inspect the scenario.'],
    ['One conversation', 'Run once and follow the saved dialogue.'],
    ['Follow the evidence', 'UserSim → model → MCP → reply, with native Relay scopes.'],
    ['Inside Fabric', 'See the actual plan, adapter and runtime lifecycle.'],
    ['Evaluate with Helix', 'Read each criterion and its supporting evidence.'],
    ['Change one thing', 'Compare a harness, routing policy or generated scenario.'],
    ['Deploy in OpenShell', 'Register, deploy, invoke and inspect a managed agent.'],
  ];
  let step = $state(0), stories = $state<any[]>([]), storyId = $state('photography');
  let mode = $state('demo'), harness = $state('deepagents'), route = $state('fixed');
  let persona = $state<any>(null), run = $state<any>(null), busy = $state(false), error = $state('');
  let comparisonBudget = $state(130);
  let parent = $state<any>(null), evaluationBusy = $state(false), initialized = $state(false);
  let ready = $state(false), modeChosen = $state(false);
  let selectionRequest = 0, selectionBusy = $state(false);
  let managedStory = $state<ManagedStoryCondition | null>(null), deploymentEpisode = $state('');
  let selectedRunId = '';
  $effect(() => { const id = run?.run_id ?? ''; if (id !== selectedRunId) { selectedRunId = id; deploymentEpisode = ''; managedStory = null; } });
  const story = $derived(stories.find(item => item.id === storyId));
  const generatedRecord = $derived(generatedJob?.result?.records?.find((record: any) => selectedIds.includes(record.profile.uuid)));
  const effectiveScenario = $derived(run?.scenarios?.[0]);
  const running = $derived(!!run && ['queued','running'].includes(run.status));
  $effect(() => { if (status && !initialized) { if (!modeChosen) mode = status.inference_configured || status.nim_key_present || status.proxy_configured ? 'live' : 'demo'; initialized = true; } });
  $effect(() => {
    const ids = [...selectedIds], source = selectedSource;
    const request = ++selectionRequest;
    if (ids.length && source !== 'generated') {
      selectionBusy = true;
      void labApi('persona-lock', { source, source_ids: ids }).then(result => { if (request === selectionRequest) persona = result; })
        .catch(e => { if (request === selectionRequest) error = e.message; })
        .finally(() => { if (request === selectionRequest) selectionBusy = false; });
    } else {
      persona = null; selectionBusy = false;
    }
  });
  async function sample() {
    const request = ++selectionRequest;
    busy = true; error = '';
    try { const value = await labApi('persona-sample', { source: selectedSource === 'generated' ? 'hf-profile-only' : selectedSource, count: 1 }); if (request === selectionRequest) persona = value; }
    catch(e) { error = e instanceof Error ? e.message : 'Could not select a persona'; }
    finally { busy = false; }
  }
  async function start(comparison?: Record<string, unknown>) {
    busy = true; error = '';
    try {
      let base: any = { mode, engine: 'fabric', harness, model_route: route, source: selectedSource,
        personas: selectedSource === 'generated' ? selectedIds.length || 1 : persona?.source_ids?.length || selectedIds.length || 1,
        story_id: storyId, strategies: ['concise'], turns: 3,
        source_ids: selectedSource === 'generated' ? selectedIds : persona?.source_ids ?? selectedIds };
      if (selectedSource === 'generated') { base.generated_job_id = generatedJob?.job_id; base.source_ids = selectedIds.length ? selectedIds : [generatedJob.result.records[0].profile.uuid]; }
      if (generatedJob && selectedSource !== 'generated' && !comparison) base.overlay_job_id = generatedJob.job_id;
      if (comparison && run) { parent = run; base = { ...run.spec, parent_run_id: run.run_id, ...comparison }; }
      run = await labApi('runs', base);
      step = 1;
    } catch(e) { error = e instanceof Error ? e.message : 'Could not start the story'; }
    finally { busy = false; }
  }
  async function evaluate() {
    if (!run) return;
    evaluationBusy = true; error = '';
    try { const value = await labApi('evaluate', { run_id: run.run_id }); run = { ...run, evaluation: value }; }
    catch(e) { error = e instanceof Error ? e.message : 'Evaluation failed'; }
    finally { evaluationBusy = false; }
  }
  function prepareDeployment() {
    try { managedStory = prepareManagedStory(run, deploymentEpisode || run.episodes[0]?.episode_id); error = ''; }
    catch(e) { error = e instanceof Error ? e.message : 'Could not prepare the saved story'; }
  }
  onMount(() => {
    ready = true;
    void labApi('stories').then(value => stories = value).catch(e => error = e.message);
    const id = new URLSearchParams(location.search).get('story_run');
    if (id) void labApi('run?id=' + encodeURIComponent(id)).then(value => { run = value; storyId = value.spec.story_id ?? 'photography'; });
    let polling = false;
    const timer = setInterval(async () => {
      if (polling || !run || !['queued','running'].includes(run.status)) return;
      polling = true;
      try { const value = await labApi('run?id=' + run.run_id); run = value;
        const url = new URL(location.href); url.searchParams.set('story_run', value.run_id); void goto(url, { state: {}, shallow: true, replace: true }); }
      catch(e) { error = e instanceof Error ? e.message : 'Progress unavailable'; }
      finally { polling = false; }
    }, 1500);
    return () => clearInterval(timer);
  });
</script>

<div class="lab-stack">
  <div class="lab-note"><strong>North Star</strong> · Build a citizen-focused application, then explain how its data, agent, tools, model routing, evaluation and sandbox work together. Inspecting this story's saved evidence makes no new model calls.</div>
  <div class="lab-grid">
    <section class="lab-card" aria-label="Guided walkthrough steps"><div class="lab-eyebrow">One story / Seven views</div><h2>Follow the whole application</h2>
      {#each steps as item, index}<button disabled={!ready} class:current={step === index} class="lab-step" onclick={() => step = index}><span class="lab-step-number">{index + 1}</span><span><strong>{item[0]}</strong><small>{item[1]}</small></span></button>{/each}
    </section>
    <section class="lab-card"><div class="lab-eyebrow">Selected experiment</div><h2>{effectiveScenario?.title ?? run?.story?.title ?? generatedRecord?.scenario?.story_title ?? story?.title ?? 'A first photography class'}</h2>
      {#if run}<div class="lab-badges"><span class="lab-badge">{run.spec.mode === 'live' ? 'Live inference' : 'Scripted offline execution'}</span><span class="lab-badge">{run.status.replaceAll('_',' ')}</span><span class="lab-badge">{run.calls} / 120 calls</span></div><div class="lab-path">Experiment · {run.run_id}</div><p>{run.source_notice}</p><div class="lab-actions"><button class="lab-button" onclick={() => onreview(run.run_id)}>Open saved experiment</button>{#if running}<button class="lab-button danger" onclick={async () => run = await labApi('cancel', { run_id: run.run_id })}>Cancel story</button>{/if}</div>{#if run.error}<div class="lab-error">{run.error}</div>{/if}{#each run.episodes ?? [] as episode}<div class="lab-badges"><span class="lab-badge">{episode.strategy}</span><span class="lab-badge">{episode.status}</span></div>{#if episode.error}<div class="lab-error">{episode.error}</div>{/if}{/each}
      {:else}<p>Choose a learner and scenario, then execute one bounded conversation. The following views explain that same saved experiment.</p><div class="lab-badges"><span class="lab-badge">No inference on startup</span><span class="lab-badge">Explicit live execution</span><span class="lab-badge">Fresh memory per condition</span></div>{/if}
      {#if parent}<p class="lab-muted">This is a deliberate comparison with experiment {parent.run_id}. Source inputs and the catalogue are reused; target memory is fresh.</p>{/if}
      <CodeReference source="north-star" label="Read the project North Star" />
    </section>
  </div>
  {#if error}<div class="lab-error" role="alert">{error}</div>{/if}
  {#if step === 0}
    <section class="lab-card"><div class="lab-eyebrow">01 / Inputs</div><h2>A distinct citizen story</h2><label class="lab-label">Teaching story<select bind:value={storyId}>{#each stories as item}<option value={item.id}>{item.title}</option>{/each}</select></label><p>{story?.lesson}</p><div class="lab-note">Expected behaviour: {story?.expected}</div>
      <div class="lab-actions"><button class="lab-button" onclick={sample} disabled={!ready || busy || selectionBusy || selectedSource === 'generated'}>Sample a different learner</button><button class="lab-button" onclick={ondata}>Explore and extend the dataset</button></div>
      {#if selectionBusy}<p class="lab-loading">Locking selected source rows…</p>{:else if selectedSource === 'generated' && generatedRecord}<h3>Selected synthetic profile</h3><div class="lab-path">{generatedRecord.profile.uuid}</div><pre class="lab-code">{pretty(generatedRecord.profile)}</pre>{:else if persona}<h3>Locked source input</h3><div class="lab-path">{persona.source_ids?.join(', ')}</div><pre class="lab-code">{pretty(persona.records?.map((item: any) => item.profile) ?? persona.rows)}</pre>{:else}<p class="lab-muted">A live run samples from the available original corpus unless you lock a profile in the data workbench. Offline execution uses a clearly labelled scripted scenario.</p>{/if}
      {#if generatedJob}<div class="lab-note">Saved Data Designer input · {generatedJob.job_id}. Generated hypotheses remain separate from the original profile.{#if generatedRecord?.scenario} This selected scenario replaces the teaching story's goal and budget with <strong>{generatedRecord.scenario.learning_goal}</strong> and <strong>S${generatedRecord.scenario.budget_sgd}</strong>. Review it before starting.{/if}</div>{/if}
      <div class="lab-grid"><label class="lab-label">Story inference<select bind:value={mode} onchange={() => modeChosen = true} disabled={!ready}><option value="live">Live model execution</option><option value="demo">Scripted offline execution</option></select></label><label class="lab-label">Harness managed by Fabric<select bind:value={harness}><option value="deepagents">LangChain Deep Agents</option><option value="hermes">Hermes · isolated runtime required</option></select></label></div>
      <label class="lab-label">Model routing<select bind:value={route}><option value="fixed">Fixed model · baseline</option><option value="switchyard">Switchyard via LiteLLM · configured proxy required</option></select></label>
      <p class="lab-muted">One persona by default, up to three conversation turns, four advisor tool rounds per reply and a shared 120-call ceiling. Simulator and judge calls count too.</p>
      <button class="lab-button primary" onclick={() => start()} disabled={!ready || busy || selectionBusy || running}>{busy ? 'Preparing…' : mode === 'live' ? 'Start one live citizen story' : 'Start one offline citizen story'}</button>
      <CodeReference source="personas" label="Persona selection code" /><CodeReference source="usersim" label="How UserSim owns the conversation loop" />
    </section>
  {:else if step === 1}
    <section class="lab-card"><div class="lab-eyebrow">02 / Conversation</div><h2>Read the story and its sources</h2><p>UserSim receives the selected synthetic profile. The advisor receives public learner messages and accesses course facts through MCP. Hidden simulator profiles and judge instructions are not passed to the advisor.</p>{#if run?.events?.some((event: any) => event.type === 'episode_started')}<RunTrace run={run} bind:selectedEpisode={deploymentEpisode} />{:else}<div class="lab-empty">Start a story in step 1 to inspect its saved conversation.</div>{/if}</section>
  {:else if step === 2 || step === 3}
    <section class="lab-card"><div class="lab-eyebrow">{step === 2 ? '03 / Observable execution' : '04 / Harness management'}</div><h2>{step === 2 ? 'Trace what actually executed' : 'Fabric connects the application to a harness'}</h2><p>{step === 2 ? 'Follow native Relay scopes and inspect exact tool inputs and results. Application usage includes simulator and judge calls that may sit outside the target trace.' : 'The typed configuration selects the harness, tools and models. A persistent runtime owns one conversation; a separate condition receives fresh memory. These records show actual lifecycle evidence.'}</p>{#if run}<EvidencePanel runId={run.run_id} />{:else}<div class="lab-empty">Run a story first. No illustrative trace is substituted for native evidence.</div>{/if}</section>
  {:else if step === 4}
    <EvaluationPanel evaluation={run?.evaluation} onrequest={evaluate} busy={evaluationBusy || running || !run} />
  {:else if step === 5}
    <section class="lab-card"><div class="lab-eyebrow">06 / Controlled changes</div><h2>Another run needs a reason</h2><p>Reopening evidence does not require a new conversation. A changed harness, routing policy or generated scenario does. These actions reuse the saved source inputs and catalogue while starting fresh target memory.</p><div class="lab-actions"><button class="lab-button" onclick={() => start({ harness: run?.spec.harness === 'hermes' ? 'deepagents' : 'hermes', model_route: 'fixed', comparison_reason: 'Compare harnesses with the same source inputs, model and catalogue.' })} disabled={!run || running || run.spec.model_route === 'switchyard'}>Compare the other harness</button><button class="lab-button" onclick={() => start({ model_route: 'switchyard', comparison_reason: 'Change fixed model routing to Switchyard; retain source inputs and harness.' })} disabled={!run || running}>Compare model routing</button><button class="lab-button" onclick={ondata}>Create a Data Designer variation</button>{#if generatedJob && run}<button class="lab-button primary" onclick={() => start({ overlay_job_id: generatedJob.job_id, comparison_reason: 'Apply the approved generated scenario to the same original source profile.' })} disabled={running}>Compare approved scenario overlay</button>{/if}</div><div class="lab-grid"><label class="lab-label">Comparison total budget in SGD<input type="number" min="0" bind:value={comparisonBudget} /></label><div class="lab-actions"><button class="lab-button" onclick={() => start({ budget_override_sgd: comparisonBudget, comparison_reason: 'Change only the explicit total budget; retain original persona, harness, model routing and catalogue.' })} disabled={!run || running}>Compare this budget</button></div></div><p class="lab-muted">Generated model replies remain stochastic even with identical inputs. A small comparison describes these runs, not population demand or human behaviour.</p><CodeReference source="designer" /><CodeReference source="routing" /></section>
  {:else if step === 6}
    {#if run}<section class="lab-card" aria-label="Saved story deployment handoff"><h2>Carry this saved story into a new managed condition</h2><p>Choose one saved episode. Preparation copies its original structured constraints, first public learner input and harness/routing selection. It creates no resource, sends no model request and restores no conversation memory. The managed agent uses its separately packaged catalogue.</p><label class="lab-label">Saved episode for deployment<select value={deploymentEpisode || run.episodes[0]?.episode_id} onchange={event => deploymentEpisode = event.currentTarget.value}>{#each run.episodes as episode, index}<option value={episode.episode_id}>Conversation {index + 1} · {episode.strategy} · {episode.status}</option>{/each}</select></label><button class="lab-button primary" onclick={prepareDeployment} disabled={running || !run.episodes.length}>Prepare saved story for deployment</button></section>{/if}
    <DeploymentPanel storyCondition={managedStory} />
  {/if}
  <div class="lab-actions"><button class="lab-button" disabled={step === 0} onclick={() => step--}>Previous lesson</button><button class="lab-button" disabled={step === steps.length - 1} onclick={() => step++}>Next lesson · reuse saved evidence</button></div>
</div>
