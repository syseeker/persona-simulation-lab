<script lang="ts">
  import { onMount, onDestroy, untrack } from 'svelte';
  import { labApi, pretty } from '#lib/api.ts';
  import { samePreferences } from '#lib/managedStory.ts';
  import type { ManagedStoryCondition, StoryPreferences } from '#lib/types.ts';
  import CodeReference from './CodeReference.svelte';
  let { storyCondition = null }: { storyCondition?: ManagedStoryCondition | null } = $props();
  let activeStory = $state<ManagedStoryCondition | null>(null), conditionId = $state('');
  let managedTurns = $state(0);
  let appliedCondition = '';
  const nativePreset: StoryPreferences = { goal: 'photography', budget_sgd: 50, days: [5] };
  let profiles = $state<any[]>([]), platform = $state<any>(null), target = $state('local');
  let harness = $state('deepagents'), deployment = $state('sg-learning-demo');
  let runtime = $state('openshell');
  let suggestedDeployment = 'sg-learning-demo';
  let image = $state('persona-lab-deepagents:0.2.0');
  let environment = $state(''), question = $state('Find a photography class and include official sources.');
  let providerUrl = $state('http://host.docker.internal:8766/v1');
  let preferencesUrl = $state('http://host.docker.internal:8766/v1/lab/preferences');
  let goal = $state('photography'), budget = $state<number | undefined>(50);
  let saturday = $state(true), frozenPreferences = $state<any>(null), retainedSession = $state<any>(null);
  let route = $state('fixed');
  let sessionId = $state(''), result = $state<any>(null), packaged = $state<any>(null);
  let inspectedSession = $state('');
  let savedJobId = $state('');
  let closeFailed = $state(false);
  let sessionTarget = 'local';
  let job = $state<any>(null), busy = $state(false), error = $state('');
  let disposed = false;
  const agent = $derived('singapore-learning-advisor-' + harness);
  const runtimeName = $derived(runtime === 'openshell' ? 'OpenShell' : 'Docker');
  const storyPreferences = $derived(activeStory?.preferences ?? null);
  const requiredPreset = $derived(frozenPreferences ?? (runtime === 'openshell' ? nativePreset : null));
  const presetMismatch = $derived(!!activeStory && !!requiredPreset && !samePreferences(storyPreferences, requiredPreset));
  const storyBlocked = $derived(!!activeStory && (!storyPreferences || presetMismatch));
  const changedCondition = $derived(!!activeStory && (harness !== activeStory.harness || route !== activeStory.model_route));
  const recoverySession = $derived(retainedSession?.session_name ?? sessionId);
  const recoveryAvailable = $derived(!!recoverySession && (closeFailed || ['uncertain', 'running'].includes(retainedSession?.invocation_state)));
  function newManagedCondition() { if (activeStory) conditionId = crypto.randomUUID(); }
  function storyReference() {
    return activeStory ? { run_id: activeStory.run_id, episode_id: activeStory.episode_id, condition_id: conditionId } : null;
  }
  $effect(() => {
    const next = storyCondition;
    if (!next || next.condition_id === appliedCondition || busy || sessionId || retainedSession) return;
    untrack(() => {
      activeStory = JSON.parse(JSON.stringify(next)); question = next.first_learner_input; managedTurns = 0;
      if (['deepagents', 'hermes'].includes(next.harness ?? '')) harness = next.harness!;
      if (['fixed', 'switchyard'].includes(next.model_route ?? '')) route = next.model_route!;
      image = 'persona-lab-' + harness + ':0.2.0'; packaged = null;
      if (next.preferences) { goal = next.preferences.goal; budget = next.preferences.budget_sgd ?? undefined; saturday = next.preferences.days?.includes(5) ?? false; }
      suggestDeployment(); conditionId = next.condition_id; appliedCondition = next.condition_id;
    });
  });
  function clearInspection() {
    inspectedSession = ''; result = null; job = null; frozenPreferences = null; error = '';
  }
  function suggestDeployment() {
    const next = harness === 'deepagents' && runtime === 'openshell' ? 'sg-learning-demo'
      : 'sg-learning' + (harness === 'hermes' ? '-hermes' : '') + (runtime === 'docker' ? '-docker' : harness === 'hermes' ? '-openshell' : '');
    if (deployment === suggestedDeployment) deployment = next;
    suggestedDeployment = next;
    clearInspection();
    newManagedCondition();
  }
  function changeHarness() {
    packaged = null; image = 'persona-lab-' + harness + ':0.2.0'; suggestDeployment();
  }
  async function closeDetachedSession() {
    if (!sessionId) return;
    const identity = sessionId; sessionId = '';
    try { await labApi('platform', { target: sessionTarget, operation: 'sessions_close', arguments: { name: identity } }); }
    catch { /* The failed operation remains in the worker's saved Platform jobs. */ }
  }
  async function cancelJob() {
    if (!job?.job_id) return;
    try { job = await labApi('platform', { target, operation: 'cancel_job', job_id: job.job_id }); }
    catch(e) { error = e instanceof Error ? e.message : 'Cancellation failed'; }
  }
  async function readSavedOperation() {
    if (busy || sessionId || retainedSession || !savedJobId.trim()) return;
    busy = true; error = ''; job = null; result = null;
    try {
      const value = await labApi('platform', { target, operation: 'job', job_id: savedJobId.trim() });
      job = value; result = value.result ?? null; error = value.error ?? '';
      if (!sessionId && !retainedSession) {
        if (['local', 'remote'].includes(value.target) && target !== value.target) { target = value.target; platform = null; }
        inspectedSession = typeof result?.session_identity?.resource_name === 'string' ? result.session_identity.resource_name : '';
        if (typeof result?.response?.model === 'string' && result.response.model) deployment = result.response.model;
      }
    } catch(e) { error = e instanceof Error ? e.message : 'Could not read the saved operation'; }
    finally { busy = false; }
  }
  function recoveryTarget() {
    const original = retainedSession ? retainedSession.scope?.[0] : sessionTarget;
    if (!['local', 'remote'].includes(original)) throw new Error('The original Platform connection is unavailable; inspect the retained session.');
    return original;
  }
  async function recoverSession() {
    if (busy || !recoveryAvailable) return;
    try { await execute('sessions_recover', { name: recoverySession }, recoveryTarget()); }
    catch(e) { error = e instanceof Error ? e.message : 'Could not identify the original Platform connection'; }
  }
  async function closeRetainedSession() {
    try { await execute('sessions_close', { name: retainedSession.session_name }, recoveryTarget()); }
    catch(e) { error = e instanceof Error ? e.message : 'Could not identify the original Platform connection'; }
  }
  async function execute(operation: string, args: Record<string, unknown> = {}, actionTarget = target) {
    busy = true; error = '';
    try {
      let value = await labApi('platform', { target: actionTarget, operation, arguments: args });
      if (value.job_id) {
        job = value;
        while (['queued','running'].includes(value.status)) {
          await new Promise(resolve => setTimeout(resolve, 1200));
          value = await labApi('platform', { target: actionTarget, operation: 'job', job_id: value.job_id }); job = value;
        }
        result = value.result ?? null;
        if (value.status !== 'completed') throw new Error(value.error ?? 'Platform action did not complete');
        value = value.result;
      }
      result = value;
      if (operation === 'status') platform = value;
      if (operation === 'package') packaged = value;
      if (operation === 'sessions_create') {
        closeFailed = false;
        managedTurns = 0;
        sessionId = value.session?.name ?? value.session?.id ?? value.session?.entity_id ?? ''; sessionTarget = actionTarget;
        inspectedSession = sessionId;
        frozenPreferences = value.deployment?.frozen_preferences ?? null;
        if (frozenPreferences && !activeStory) { goal = frozenPreferences.goal; budget = frozenPreferences.budget_sgd ?? undefined; saturday = frozenPreferences.days?.includes(5) ?? false; }
      }
      if (operation === 'invoke') managedTurns = job?.conversation_turns ?? managedTurns + 1;
      if (operation === 'sessions_recover') {
        if (value?.runtime_cleanup_confirmed !== true || value?.deployment_removed !== true || value?.session?.status !== 'closed') {
          throw new Error('Native recovery has not confirmed deployment removal and session closure; another learner remains blocked.');
        }
        target = actionTarget; platform = null;
      }
      if (['sessions_close', 'sessions_recover'].includes(operation)) {
        sessionId = ''; frozenPreferences = null; retainedSession = null; closeFailed = false;
        managedTurns = 0; if (activeStory) question = activeStory.first_learner_input;
      }
    } catch(e) {
      if (['sessions_close', 'sessions_recover'].includes(operation)) closeFailed = true;
      error = e instanceof Error ? e.message : 'Platform operation failed';
    }
    finally { busy = false; if (disposed) void closeDetachedSession(); }
  }
  onMount(() => {
    void labApi('profiles').then(value => profiles = value.profiles).catch(e => error = e.message);
    void labApi('status').then(value => {
      retainedSession = value.managed_session;
      if (value.deployment_model_url) {
        providerUrl = value.deployment_model_url;
        preferencesUrl = value.deployment_model_url + '/lab/preferences';
      }
    }).catch(e => error = e.message);
  });
  onDestroy(() => { disposed = true; if (!busy) void closeDetachedSession(); });
</script>

<div class="lab-stack">
  {#if activeStory}<section class="lab-card" aria-label="Prepared managed story"><h2>A new managed condition from the saved story</h2><p>This copies public inputs and lineage, not previous conversation memory, persona text or judge instructions. Resource creation and invocation each need an explicit action. The managed agent has its independently packaged catalogue; this is not a strict paired catalogue replay.</p><div class="lab-path">Source run · {activeStory.run_id}<br />Source episode · {activeStory.episode_id}<br />Managed condition · {conditionId}</div><pre class="lab-code">{pretty({ source_mode: activeStory.source_mode, source_strategy: activeStory.source_strategy, source_id: activeStory.source_id, source_catalogue_sha256: activeStory.catalogue_sha256, original_harness: activeStory.harness, original_model_route: activeStory.model_route, original_preferences: storyPreferences, first_learner_input: activeStory.first_learner_input })}</pre>{#if changedCondition}<p class="lab-note">Explicit new condition: the selected managed harness or model route differs from the saved experiment. Original source inputs remain unchanged.</p>{/if}{#if !storyPreferences}<p class="lab-error">Original structured preferences were not saved. Invocation is blocked; no constraints were inferred from the transcript or tool arguments.</p>{:else if presetMismatch}<p class="lab-error">The saved story does not match this deployment's frozen photography/S$50/Saturday preset. Invocation is blocked and the original preferences stay unchanged. Docker is a separate explicit dynamic-context option; invocation is unverified on this host and no fallback is automatic.</p>{/if}</section>{/if}
  <section class="lab-card" aria-label="Platform deployment workspace"><div class="lab-eyebrow">Helix / Fabric / Deployment</div><h2>Deploy the same application agent</h2><p>Helix manages registration, deployments and sessions. Fabric runs the selected harness. Choose the native OpenShell sandbox or the separate Docker runtime for the agent and its read-only catalogue tools. The UI, datasets, simulator and LiteLLM proxy remain outside that runtime.</p>
    <div class="lab-note">Model path: agent → Helix Inference Gateway → active application budget → LiteLLM/Switchyard → hosted provider. A running deployment alone does not prove its model, tools or trace delivery work.</div>
    <div class="lab-grid"><label class="lab-label">Platform connection<select bind:value={target} onchange={() => { platform = null; clearInspection(); }} disabled={busy || !!sessionId || !!retainedSession}><option value="local">Local reference Platform</option><option value="remote">Configured remote Platform</option></select></label><label class="lab-label">Packaged harness<select bind:value={harness} disabled={busy || !!sessionId || !!retainedSession} onchange={changeHarness}><option value="deepagents">LangChain Deep Agents</option><option value="hermes">Hermes</option></select></label><label class="lab-label">Deployment runtime<select bind:value={runtime} onchange={suggestDeployment} disabled={busy || !!sessionId || !!retainedSession}><option value="openshell">OpenShell · public teaching preset</option><option value="docker">Docker · dynamic preferences callback</option></select></label></div>
    <div class="lab-actions"><button class="lab-button" onclick={() => execute('status')} disabled={busy}>Check Platform readiness</button></div>
    {#if platform}<div class="lab-badges"><span class="lab-badge">{platform.ready ? 'Platform reachable' : 'Platform not ready'}</span></div><pre class="lab-code">{pretty(platform)}</pre>{/if}
    <details><summary>Installed configuration and prerequisites</summary>{#each profiles as profile}<div class="lab-check-row"><strong>{profile.label}</strong><span class="lab-badge">{profile.configured ? 'Configured · not proof of readiness' : 'Setup required'}</span><pre class="lab-code">{pretty(profile)}</pre></div>{/each}</details>
    <CodeReference source="platform" label="Inspect the typed Helix SDK bridge" />
    <CodeReference source="platform-sdk" label="Trace the actual Helix SDK calls" />
    <CodeReference source="openshell" label="Inspect the OpenShell agent and tool package" />
    <CodeReference source="recovery" label="Follow native cleanup proof and recovery" />
  </section>
  <section class="lab-card" aria-label="Saved Platform operation"><h2>Reopen saved operation evidence</h2><p>This reads a saved local job and its model-call ledger. No model calls, session creation or deployment actions occur. A saved session identity is available only for explicit evidence lookup; reading it does not reopen a conversation.</p><label class="lab-label">Saved Platform job ID<input bind:value={savedJobId} maxlength="64" placeholder="Paste a saved job UUID" disabled={busy || !!sessionId || !!retainedSession} /></label><div class="lab-actions"><button class="lab-button" onclick={readSavedOperation} disabled={busy || !!sessionId || !!retainedSession || !savedJobId.trim()}>Read saved operation</button></div>{#if inspectedSession && !sessionId}<p class="lab-note">Evidence session: {inspectedSession}. No active conversation has been restored. Read deployment logs explicitly to inspect any retained native trace.</p>{/if}</section>
  <section class="lab-card"><div class="lab-eyebrow">01 / Package and register</div><h2>Inspect what will run</h2><p>The package includes only the shared catalogue code, course facts, policy and selected harness. Personal source datasets, credentials and saved conversations are excluded.</p><label class="lab-label">Exact image reference<input bind:value={image} placeholder="registry/project/image:version" /></label><div class="lab-actions"><button class="lab-button" onclick={() => execute('package', { harness, image, build: false })} disabled={busy}>Prepare and inspect image bundle</button><button class="lab-button" onclick={() => execute('package', { harness, image, build: true })} disabled={busy}>Build local image</button><button class="lab-button" onclick={() => execute('register', { harness, name: agent })} disabled={busy || !packaged}>Register reviewed agent configuration</button></div><p class="lab-muted">These actions do not publish an image. The selected runtime must be able to access the exact image before deployment. Registration and a successful image build are separate evidence.</p></section>
  <section class="lab-card"><div class="lab-eyebrow">Connection setup</div><h2>Connect the managed agent to this application</h2><p>Helix discovers the three model aliases from the application admission bridge. The Docker environment fetches session constraints through a separate authenticated callback. The native OpenShell reference reads its reviewed, hash-checked teaching preset from the image. Use addresses reachable from the selected containers; a remote Platform needs its configured host address.</p><div class="lab-grid"><label class="lab-label">Platform-reachable model bridge URL<input bind:value={providerUrl} /></label><label class="lab-label">Sandbox-reachable preferences URL<input bind:value={preferencesUrl} /></label></div><div class="lab-actions"><button class="lab-button" disabled={busy} onclick={() => execute('configure', { provider_url: providerUrl, preferences_url: preferencesUrl })}>Configure workspace, model provider and context</button></div><p class="lab-muted">Credentials come from the host environment. The native OpenShell preset uses the official encrypted credential store and Platform inference egress. A stored provider or environment is setup evidence; the actual invocation must still succeed.</p></section>
  <section class="lab-card"><div class="lab-eyebrow">02 / Deploy</div><h2>A real managed runtime</h2><div class="lab-grid"><label class="lab-label">Deployment name<input bind:value={deployment} onchange={clearInspection} disabled={busy || !!sessionId || !!retainedSession} /></label><label class="lab-label">Stored AgentEnvironment reference<input bind:value={environment} placeholder="Optional workspace/environment" /></label></div><div class="lab-actions"><button class="lab-button primary" onclick={() => execute('deploy', { agent, name: deployment, image, mode: runtime, ...(environment ? { environment } : {}) })} disabled={busy || !!sessionId || !!retainedSession || !platform?.ready}>Deploy with {runtimeName}</button><button class="lab-button" onclick={() => execute('deployment', { name: deployment })} disabled={busy}>Refresh deployment state</button><button class="lab-button" onclick={() => execute('logs', { name: deployment, tail: 100, ...(inspectedSession ? { session_id: inspectedSession } : {}) })} disabled={busy}>Read deployment logs and native trace</button></div><p class="lab-muted">Selecting a runtime chooses its configuration; it does not prove availability or a successful invocation. Verify the selected executor, image access and actual runtime policy. OpenShell additionally requires gateway access and native filesystem/network enforcement. Failures stay visible; the application never retries with another runtime.</p></section>
  <section class="lab-card"><div class="lab-eyebrow">03 / Invoke and clean up</div><h2>Follow a deployed conversation</h2><p class="lab-note">The OpenShell reference uses a hash-checked public teaching preset: photography, S$50 total budget, Saturday. Its catalogue constraints are baked into the reviewed image. The separate Docker connection implements authenticated changing session context; live invocation remains unverified on this host.</p>{#if retainedSession && !sessionId}<div class="lab-note">An earlier session still needs confirmed cleanup: {retainedSession.session_name ?? retainedSession.error}. Another learner is blocked.</div>{#if retainedSession.session_name}<button class="lab-button" disabled={busy} onclick={closeRetainedSession}>Close the retained Platform session</button>{/if}{/if}{#if frozenPreferences}<pre class="lab-code">{pretty({ immutable_preferences: frozenPreferences })}</pre>{/if}<div class="lab-actions"><button class="lab-button" onclick={() => execute('sessions_create', { deployment, ...(activeStory ? { story_reference: storyReference() } : {}) })} disabled={busy || !!sessionId || !!retainedSession || storyBlocked}>Create a fresh Platform session</button></div><label class="lab-label">Platform session<input bind:value={sessionId} readonly placeholder="Created session identity" /></label><div class="lab-grid"><label class="lab-label">Trusted learning goal<input bind:value={goal} disabled={busy || !!sessionId || !!activeStory} /></label><label class="lab-label">Total budget in SGD<input type="number" min="0" bind:value={budget} disabled={busy || !!sessionId || !!activeStory} /></label><label class="lab-label"><span>Saturday availability</span><input type="checkbox" bind:checked={saturday} disabled={busy || !!sessionId || !!activeStory} /></label><label class="lab-label">Model routing condition<select bind:value={route} onchange={newManagedCondition} disabled={busy || !!sessionId}><option value="fixed">Fixed model baseline</option><option value="switchyard">Switchyard via LiteLLM</option></select></label></div><label class="lab-label">Deployed learner message<textarea bind:value={question} disabled={busy || !!activeStory && managedTurns === 0}></textarea></label><div class="lab-actions"><button class="lab-button primary" onclick={() => execute('invoke', { deployment, session_id: sessionId, input: question, model_route: route, preferences: activeStory ? storyPreferences : frozenPreferences ?? { goal, budget_sgd: budget ?? null, days: saturday ? [5] : null }, ...(activeStory ? { story_reference: storyReference() } : {}) })} disabled={busy || !sessionId || closeFailed || storyBlocked}>Invoke deployed agent · live calls</button><button class="lab-button" onclick={() => execute('sessions_close', { name: sessionId }, sessionTarget)} disabled={busy || !sessionId}>Close conversation session</button><button class="lab-button danger" onclick={() => execute('undeploy', { name: deployment })} disabled={busy || !!sessionId || !!retainedSession}>Undeploy this demo</button></div><p class="lab-muted">A Platform session preserves conversation memory and its original constraints for up to three turns. Leaving this workspace closes its active session. After an incomplete invocation, close it before continuing. Undeployment is asynchronous; refresh status to verify removal. Images are retained separately.</p></section>
  {#if recoveryAvailable}<section class="lab-card" aria-label="Failed deployment recovery"><h2>Recover a session that could not close</h2><p>Stop the owning failed deployment and all its sessions, then close this retained session. This is an explicit recovery action. Another learner remains blocked until authenticated native evidence confirms the runtime stopped and the deployment was removed.</p><p class="lab-path">Session: {recoverySession}</p><button class="lab-button danger" disabled={busy} onclick={recoverSession}>Stop failed deployment and close session</button></section>{/if}
  {#if busy}<div class="lab-loading" role="status">{job?.operation ?? 'Platform'} · {job?.status ?? 'checking'}… Local evidence is retained.</div>{#if job?.job_id}<button class="lab-button danger" onclick={cancelJob}>Cancel waiting for this job</button><p class="lab-muted">Cancellation closes local inference admission. A remote resource operation may already have been accepted; refresh actual deployment state before retrying.</p>{/if}{/if}
  {#if job}<div class="lab-badges"><span class="lab-badge">Job · {job.job_id}</span><span class="lab-badge">{job.calls ?? 0} model calls</span></div><details class="lab-card"><summary>Saved operation and model-call ledger</summary>{#if job.story_reference?.run_id}<p><a class="lab-link" href={'/?run=' + encodeURIComponent(job.story_reference.run_id) + '&view=conversation'}>Open source saved experiment</a></p>{/if}<p class="lab-muted">The worker retains this operation under runs/platform-jobs/{job.job_id}/job.json. Unknown token usage remains unknown; inspecting this ledger makes no inference calls.</p><pre class="lab-code">{pretty({ operation: job.operation, status: job.status, story_reference: job.story_reference, calls: job.calls, usage: job.usage, answer: job.answer, error: job.error, conversation_turns: job.conversation_turns })}</pre></details>{/if}
  {#if error}<div class="lab-error" role="alert">{error}</div>{/if}
  {#if result?.intake}<section class="lab-card"><h2>Native managed trace</h2><p>Helix Intake observations for the exact saved session. These are retrieved records; missing traces are reported as missing. Raw relay.jsonl export is a separate capability.</p><div class="lab-badges"><span class="lab-badge">{result.intake.status}</span><span class="lab-badge">{result.intake.traces?.length ?? 0} traces</span><span class="lab-badge">{result.intake.spans?.length ?? 0} spans</span></div></section>{/if}
  {#if result}<section class="lab-card" aria-label="Native Platform result"><h2>Actual operation result</h2><pre class="lab-code">{pretty(result)}</pre></section>{/if}
</div>
