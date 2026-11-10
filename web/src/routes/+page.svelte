<script lang="ts">
  import { onMount } from 'svelte';
  import { renderMarkdown } from '#lib/markdown.ts';
  import type { Course, Run, Status } from '#lib/types.ts';

  let tab = $state('advisor');
  let hydrated = $state(false);
  let status = $state<Status | null>(null);
  let catalogue = $state<Course[]>([]);
  let mode = $state('demo');
  let engine = $state('direct');
  let goal = $state('');
  let budget = $state<number | undefined>();
  let area = $state('');
  let busy = $state(false);
  let error = $state('');
  let session = $state<string | null>(null);
  let messages = $state<{ role: string; content: string }[]>([]);
  let matches = $state<Course[]>([]);
  let personas = $state(1);
  let paired = $state(false);
  let enrichment = $state(false);
  let source = $state('hf-profile-only');
  let active = $state<Run | null>(null);
  let runs = $state<Run[]>([]);

  async function api<T>(path: string, body?: unknown): Promise<T> {
    const response = await fetch('/api/' + path, body === undefined ? {} : {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body)
    });
    const value = await response.json();
    if (!response.ok) throw new Error(value.error ?? 'Request failed');
    return value;
  }

  function resetChat() { messages = []; matches = []; session = null; error = ''; }
  function changeMode() { resetChat(); if (mode !== 'live') enrichment = false; }

  async function send(event: SubmitEvent) {
    event.preventDefault();
    if (!goal.trim() || busy) return;
    busy = true; error = '';
    const question = goal.trim();
    messages = [...messages, { role: 'user', content: question }]; goal = '';
    try {
      const reply = await api<{ session_id: string; content: string; matches: { course: Course }[] }>('chat', {
        session_id: session, mode, engine, preferences: {
          goal: question, ...(budget !== undefined ? { budget_sgd: budget } : {}),
          ...(area.trim() ? { planning_area: area.trim() } : {})
        }
      });
      session = reply.session_id;
      messages = [...messages, { role: 'assistant', content: reply.content }];
      matches = reply.matches.map((m) => m.course);
    } catch (e) { error = e instanceof Error ? e.message : 'Could not contact the advisor'; }
    finally { busy = false; }
  }

  async function startRun() {
    resetChat();
    busy = true; error = '';
    try {
      active = await api<Run>('runs', { mode, engine, source, personas,
        enrichment, strategies: paired ? ['concise', 'clarification-first'] : ['concise'] });
      runs = await api<Run[]>('runs');
    } catch (e) { error = e instanceof Error ? e.message : 'Could not start simulation'; }
    finally { busy = false; }
  }

  async function viewRun(id: string) {
    try { active = await api<Run>('run?id=' + encodeURIComponent(id)); tab = 'results'; }
    catch (e) { error = e instanceof Error ? e.message : 'Could not load results'; }
  }

  async function cancel() {
    if (!active) return;
    try { active = await api<Run>('cancel', { run_id: active.run_id }); }
    catch (e) { error = e instanceof Error ? e.message : 'Could not cancel'; }
  }

  async function evaluateRun() {
    if (!active) return;
    busy = true; error = '';
    try { await api('evaluate', { run_id: active.run_id }); active = await api<Run>('run?id=' + active.run_id); }
    catch (e) { error = e instanceof Error ? e.message : 'Evaluation failed'; }
    finally { busy = false; }
  }

  onMount(() => {
    hydrated = true;
    let mounted = true;
    let polling = false;
    Promise.all([api<Status>('status'), api<Course[]>('catalogue'), api<Run[]>('runs')])
      .then(([s, c, r]) => { if (mounted) { status = s; catalogue = c; runs = r; } })
      .catch((e) => { error = e.message; });
    const poll = setInterval(async () => {
      if (polling || !active || !['queued', 'running'].includes(active.status)) return;
      const id = active.run_id;
      polling = true;
      try {
        const fresh = await api<Run>('run?id=' + id);
        if (mounted) {
          if (active?.run_id === id) active = fresh;
          runs = runs.map(run => run.run_id === id ? fresh : run);
        }
      }
      catch (e) { if (mounted) error = e instanceof Error ? e.message : 'Progress unavailable'; }
      finally { polling = false; }
    }, 1500);
    return () => { mounted = false; clearInterval(poll); };
  });

  function price(c: Course) {
    if (c.price_max_sgd === null) return 'Fee to confirm';
    return c.price_min_sgd === c.price_max_sgd ? `S$${c.price_max_sgd}` : `S$${c.price_min_sgd}–${c.price_max_sgd}`;
  }
</script>

<svelte:head><title>Learning Lab · Singapore</title><meta name="description" content="Explore Singapore learning opportunities and test a course advisor with synthetic personas." /></svelte:head>

<div class="app-shell">
  <aside class="sidebar">
    <a class="brand" href="/" aria-label="Learning Lab home"><span class="brand-mark">L<span>↗</span></span><strong>Learning<br />Lab<span class="brand-sub">SINGAPORE</span></strong></a>
    <div class="side-label">YOUR WORKSPACE</div>
    <nav aria-label="Main navigation">
      {#each [{ id: 'advisor', number: '01', label: 'Try the advisor' }, { id: 'simulation', number: '02', label: 'Run a simulation' }, { id: 'results', number: '03', label: 'Review results' }] as item}
        <button disabled={!hydrated} class:chosen={tab === item.id} onclick={() => { tab = item.id; error = ''; }}><span>{item.number}</span>{item.label}</button>
      {/each}
    </nav>
    <div class="side-note"><span class="small-star">✳</span><h3>A place to learn by building.</h3><p>Explore courses, simulate conversations and understand how an agent makes a recommendation.</p></div>
    <div class="side-footer"><span class="status-dot"></span> Local learning environment</div>
  </aside>

  <main>
    <header><div class="breadcrumb">PERSONA SIMULATION LAB <span>/</span> LEARNING ADVISOR</div><span class="pill">PERSONAL PROJECT</span></header>
    <section class="intro">
      <div><div class="eyebrow">LEARN SOMETHING THAT MOVES YOU</div><h1>{tab === 'advisor' ? 'Your next chapter starts here.' : tab === 'simulation' ? 'Meet your simulated learners.' : 'Every conversation tells a story.'}</h1><p>{tab === 'advisor' ? 'Find a new skill for work, a creative pursuit or a class close to home.' : tab === 'simulation' ? 'Test the same advisor with Singapore profiles and compare its approach.' : 'Inspect saved conversations, experiment outcomes and trace evidence.'}</p></div>
      <div class="intro-art" aria-hidden="true"><div class="orbit"></div><span class="art-leaf leaf-one"></span><span class="art-leaf leaf-two"></span><span class="art-dot"></span><span class="art-line"></span></div>
    </section>

    <div class="toolbar"><div class="mode-group"><label for="mode">INFERENCE</label><select id="mode" bind:value={mode} onchange={changeMode} disabled={busy}><option value="demo">Offline demo</option><option value="live">Live NVIDIA NIM</option></select></div><div class="mode-group"><label for="engine">ADVISOR RUNTIME</label><select id="engine" bind:value={engine} onchange={resetChat} disabled={busy}><option value="direct">Deep Agents</option><option value="relay">Deep Agents + Relay</option><option value="fabric">Fabric + Relay</option></select></div><span class="connection"><span class:ready={status?.nim_key_present} class="status-dot"></span>{status?.nim_key_present ? 'NIM key configured' : 'NIM key not configured'}</span></div>
    {#if mode === 'demo'}<div class="mode-notice">Offline demo uses scripted responses through the real harness and course tools. Select live NIM for generated conversations.</div>{/if}
    {#if error}<div class="error" role="alert">{error}</div>{/if}
    {#if tab === 'simulation'}
      <label class="checkbox-label"><input type="checkbox" bind:checked={enrichment} disabled={mode !== 'live' || source !== 'hf-profile-only'} />Add Data Designer learning-preference hypotheses (live HF profile-only runs)</label>
    {/if}

    {#if tab === 'advisor'}
      <div class="advisor-grid"><section class="card chat-card"><div class="card-heading"><span class="advisor-icon">✳</span><div><h2>Let’s find your next learning opportunity</h2><p>Tell the advisor what you’d like to explore.</p></div>{#if messages.length}<button class="text-button" onclick={resetChat} disabled={busy}>New chat</button>{/if}</div>
        <div class="conversation" aria-live="polite">
          {#if messages.length === 0}<div class="welcome"><span class="welcome-icon">↗</span><h3>A little curiosity goes a long way.</h3><p>You could build confidence with Excel, try photography or pick up something entirely new.</p><div class="suggestions">{#each ['Build my Excel skills', 'Try a photography class', 'Learn baking near Yishun'] as example}<button disabled={!hydrated} onclick={() => goal = example}>{example}<span>↗</span></button>{/each}</div></div>{/if}
          {#each messages as message}<article class:from-user={message.role === 'user'} class="message"><span class="message-label">{message.role === 'user' ? 'YOU' : 'LEARNING ADVISOR'}</span><div>{@html renderMarkdown(message.content)}</div></article>{/each}
          {#if busy}<div class="thinking" role="status">The advisor is checking the catalogue<span>…</span></div>{/if}
        </div>
        <form onsubmit={send}><label class="sr-only" for="goal">Your learning goal</label><div class="input-row"><input id="goal" bind:value={goal} placeholder="What would you like to learn?" maxlength="3000" disabled={busy} /><button class="send-button" type="submit" disabled={busy || !goal.trim()} aria-label="Send learning goal">↗</button></div><p class="input-footnote">Recommendations use a curated snapshot. Check details with the provider.</p></form>
      </section><aside class="preferences card"><div class="mini-label">MAKE IT YOURS</div><h2>A few helpful details</h2><p>Share what matters to you. You can leave these open.</p><label for="budget">Budget, before funding <span>optional</span></label><div class="budget-input"><span>S$</span><input id="budget" type="number" min="0" bind:value={budget} placeholder="e.g. 150" /></div><label for="area">Preferred area <span>optional</span></label><input id="area" bind:value={area} placeholder="e.g. Tampines" /><div class="info-note"><strong>Your eligibility stays yours to confirm.</strong><p>The advisor can explain published facts. A profile alone cannot establish funding entitlement.</p></div><div class="snapshot"><span class="snapshot-number">{catalogue.length || '—'}</span><div>curated opportunities<br /><small>Snapshot · {status?.snapshot_date ?? 'loading'}</small></div></div></aside></div>
      {#if matches.length}<section class="opportunities"><div class="section-title"><h2>From the catalogue</h2><span>Official sources for your own review</span></div><div class="course-grid">{#each matches as course}<article class="course-card"><span class="course-kind">{course.kind === 'community' ? 'COMMUNITY CLASS' : 'SKILLS & CAREER'}</span><h3>{course.title}</h3><p>{course.provider}</p><div class="course-price">{price(course)}{#if course.extra_cost_sgd !== null}<small> + S${course.extra_cost_sgd} materials</small>{/if}</div><p class="course-schedule">{course.schedule_note}</p><a href={course.source_url} target="_blank" rel="noreferrer">View official listing <span>↗</span></a></article>{/each}</div></section>{/if}
    {:else if tab === 'simulation'}
      <div class="simulation-grid"><section class="card setup"><div class="mini-label">CONTROLLED EXPERIMENT</div><h2>One advisor. Different perspectives.</h2><p>Start small, inspect a conversation, then compare two approaches using the same saved profiles.</p><label for="source">Persona source</label><select id="source" bind:value={source} onchange={() => enrichment = false}><option value="hf-profile-only">Singapore HF profiles · no OCEAN conditioning</option><option value="ngc">NGC Extended · requires local dataset setup</option></select><p class="field-help">Profiles are synthetic. Results describe the model’s behaviour under the selected test conditions.</p><label for="personas">Profiles / demo scenarios</label><select id="personas" bind:value={personas}><option value={1}>1 · first conversation</option><option value={3}>3 · small coverage panel</option></select><label class="checkbox-label"><input type="checkbox" bind:checked={paired} /> Compare concise and clarification-first strategies</label><div class="run-budget"><span>{personas * (paired ? 2 : 1)} episodes</span><span>Up to 3 turns each</span><span>120-call total cap</span></div><button class="primary-button" onclick={startRun} disabled={busy || !!active && ['running', 'queued'].includes(active.status)}>{busy ? 'Preparing…' : 'Start simulation'} <span>↗</span></button></section><section class="card experiment-status"><div class="mini-label">RUN PROGRESS</div>{#if active}<span class="run-state">{active.status.replaceAll('_', ' ')}</span><h2>{active.episodes.length} of {active.spec.personas * active.spec.strategies.length} episodes saved</h2><p>{active.source_notice}</p><div class="progress-track"><span style:width={`${Math.min(100, active.episodes.length / (active.spec.personas * active.spec.strategies.length) * 100)}%`}></span></div><p>{active.calls} of 120 model calls</p>{#if active.error}<div class="error">{active.error}</div>{/if}<div class="run-actions"><button class="secondary-button" onclick={() => viewRun(active!.run_id)}>Inspect conversation</button>{#if ['queued', 'running'].includes(active.status)}<button class="text-button danger" onclick={cancel}>Cancel run</button>{/if}</div>{:else}<span class="large-glyph">◎</span><h2>Ready when you are.</h2><p>Your run’s progress and partial results are saved locally, including failures and cancellations.</p>{/if}</section></div>
    {:else}
      <div class="results-grid"><section class="card run-list"><h2>Saved experiments</h2>{#if !runs.length}<p>No experiments yet. Run a simulation to begin.</p>{/if}{#each runs as run}<button class:selected={active?.run_id === run.run_id} onclick={() => viewRun(run.run_id)}><strong>{run.spec.mode === 'demo' ? 'Offline demo' : 'Live NIM'} · {run.spec.engine}</strong><span>{run.status.replaceAll('_', ' ')} · {run.episodes.length} episodes</span><small>{new Date(run.started_at).toLocaleString()}</small></button>{/each}</section><section class="card transcript"><h2>Conversation & outcomes</h2>{#if active}<p class="field-help">{active.source_notice}</p><div class="run-budget"><span>{active.status.replaceAll('_', ' ')}</span><span>{active.calls} calls</span></div>{#if active.error}<div class="error">{active.error}</div>{/if}{#if active.episodes.length}<details class="episode-outcomes"><summary>Episode outcomes</summary>{#each active.episodes as episode}<div class="episode-outcome"><strong>{episode.strategy}</strong><span>{episode.status.replaceAll('_', ' ')}</span>{#if episode.error}<p>{episode.error}</p>{/if}{#if episode.outcome?.n_assistant_inline_failures}<p>{episode.outcome.n_assistant_inline_failures} response-quality findings from UserSim. Inspect the conversation.</p>{/if}</div>{/each}</details>{/if}{#if active.models}<p class="field-help model-note">Advisor model: {active.models.assistant}</p>{/if}{#each active.events ?? [] as event}{#if event.type === 'episode_started'}<div class="episode-divider">{event.strategy} · fresh episode</div>{:else if event.type === 'message'}<article class:from-user={event.role === 'user'} class="message"><span class="message-label">{event.role === 'user' ? 'SIMULATED LEARNER' : 'ADVISOR'}</span><div>{@html renderMarkdown(event.content ?? "")}</div></article>{/if}{/each}{:else}<div class="empty-results"><span class="large-glyph">◌</span><p>Select an experiment to read its conversations.</p></div>{/if}</section></div>
    {/if}
    {#if tab === 'results' && active && !['running', 'queued'].includes(active.status)}
      <section class="card setup" style="margin-top:24px"><div class="section-title"><h2>Local Helix checks</h2><button class="secondary-button" onclick={evaluateRun} disabled={busy}>{busy ? 'Scoring…' : 'Evaluate saved replies'}</button></div><p>Checks cover catalogue IDs and links, funding claims and unsupported fee assurances. Read the conversation to assess the remaining facts.</p>{#if active.evaluation}{#each Object.entries(active.evaluation.summary) as [condition, summary]}<div class="run-budget"><span>{summary.passed} of {summary.criteria} checks passed</span><span>{condition}</span></div>{/each}{/if}{#each active.episodes as episode}<p class="field-help">{episode.strategy} · {episode.status.replaceAll('_', ' ')}</p>{/each}</section>
    {/if}
    <footer>Built for curious minds. <span>Singapore Personas · UserSim · NVIDIA NeMo</span></footer>
  </main>
</div>

<style>
  :global(*){box-sizing:border-box} :global(body){margin:0;background:#f8faf8;color:#1c332b;font-family:Inter,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:14px;-webkit-font-smoothing:antialiased} :global(button),:global(input),:global(select){font:inherit} :global(button),:global(select){cursor:pointer} :global(button:disabled){opacity:.5;cursor:wait} :global(button:focus-visible),:global(a:focus-visible),:global(input:focus-visible),:global(select:focus-visible){outline:3px solid #86bca6;outline-offset:3px} :global(a){color:inherit}
  .app-shell{display:grid;grid-template-columns:240px 1fr;min-height:100vh}.sidebar{padding:34px 24px 22px;background:#fff;border-right:1px solid #e5ebe5;display:flex;flex-direction:column;position:sticky;top:0;height:100vh}.brand{display:flex;gap:12px;align-items:center;text-decoration:none;margin-bottom:64px}.brand-mark{background:#174e40;color:white;width:44px;height:46px;border-radius:12px;font-size:33px;padding-left:9px;position:relative;line-height:47px}.brand-mark span{position:absolute;font-size:20px;top:-7px;right:6px}.brand strong{font-size:19px;line-height:21px;letter-spacing:-.5px}.brand-sub{display:block;font-size:8px;letter-spacing:2.4px;font-weight:500;margin-top:5px;color:#6e7f75}.side-label,.mini-label{font-size:10px;letter-spacing:1.6px;color:#7a8a80;font-weight:650}.side-label{margin:0 12px 14px}nav{display:flex;flex-direction:column;gap:7px}nav button{border:0;background:transparent;text-align:left;color:#62716a;padding:14px 11px;border-radius:8px;font-size:13px;display:flex;gap:13px;align-items:center}nav button>span{font-size:10px;font-weight:500;opacity:.65}nav button.chosen{background:#edf4ec;color:#164d3c;font-weight:650}.side-note{margin-top:auto;padding:24px 12px 30px}.small-star{font-size:28px;color:#6b8b57}.side-note h3{font-family:Georgia,serif;font-weight:400;font-size:21px;line-height:1.35;margin:15px 0 10px}.side-note p{font-size:12px;line-height:1.8;color:#829086}.side-footer{font-size:10px;color:#829086;border-top:1px solid #edf0ea;padding:22px 7px 0;display:flex;align-items:center;gap:7px}.status-dot{display:inline-block;width:6px;height:6px;background:#b0baaf;border-radius:50%}.status-dot.ready,.side-footer .status-dot{background:#679778}main{padding:0 48px;max-width:1550px;width:100%;margin:auto}header{display:flex;align-items:center;justify-content:space-between;height:86px;border-bottom:1px solid #e7ece5}.breadcrumb{font-size:9px;letter-spacing:1.4px;font-weight:600;color:#89948a}.breadcrumb span{margin:0 13px;color:#bac3b9}.pill{border:1px solid #dbe5d8;background:#fff;border-radius:50px;padding:7px 12px;font-size:8px;letter-spacing:1px;color:#71806f}.intro{display:flex;justify-content:space-between;align-items:center;padding:46px 0 34px;gap:20px}.eyebrow{font-size:9px;letter-spacing:1.8px;color:#72906b;font-weight:650;margin-bottom:14px}h1{font-family:Georgia,"Times New Roman",serif;font-weight:400;font-size:clamp(30px,3vw,44px);line-height:1.18;letter-spacing:-1.4px;margin:0 0 14px}.intro p{color:#7d8b80;font-size:13px;margin:0;line-height:1.8}.intro-art{position:relative;width:130px;height:110px;flex-shrink:0;margin-right:25px}.orbit{border:1px solid #dbe6d3;border-radius:50%;width:100px;height:100px;position:absolute;left:20px;top:5px}.art-leaf{position:absolute;width:35px;height:58px;border-radius:0 38px 0 38px;background:#a7bd83;transform:rotate(25deg)}.leaf-one{top:19px;left:52px}.leaf-two{top:48px;left:24px;background:#416b4d;transform:rotate(76deg)}.art-dot{position:absolute;width:12px;height:12px;background:#d8b785;right:4px;top:12px;border-radius:50%}.art-line{position:absolute;width:58px;height:1px;background:#6d8b63;top:71px;left:48px;transform:rotate(-64deg)}.toolbar{display:flex;gap:26px;align-items:center;border-bottom:1px solid #e4eae1;padding:12px 0 17px}.mode-group{display:flex;gap:10px;align-items:center}.mode-group label{font-size:8px;letter-spacing:1px;color:#86947f;font-weight:600}.toolbar select{background:transparent;border:0;color:#365240;font-size:12px;padding:5px;max-width:220px}.connection{margin-left:auto;font-size:10px;color:#87937f;display:flex;align-items:center;gap:7px}.mode-notice{font-size:11px;color:#7c897a;padding:13px 0 18px;line-height:1.6}.advisor-grid{display:grid;grid-template-columns:minmax(0,1fr) 268px;gap:24px}.card{border:1px solid #e0e7dc;border-radius:12px;background:white;box-shadow:0 3px 12px #25402003}.chat-card{display:flex;flex-direction:column;min-height:492px}.card-heading{display:flex;align-items:center;gap:12px;padding:22px 25px;border-bottom:1px solid #edf1e9}.advisor-icon{width:35px;height:35px;border-radius:50%;background:#edf3e6;color:#617f4a;font-size:25px;text-align:center;line-height:35px}h2{font-size:14px;margin:0 0 7px;font-weight:600;letter-spacing:-.15px}.card-heading p{font-size:11px;color:#8d998b;margin:0}.conversation{flex:1;padding:26px 25px;min-height:280px;max-height:640px;overflow:auto}.welcome{max-width:440px;margin:0 auto;padding:15px 0}.welcome-icon{font-size:26px;color:#8da776}.welcome h3{font-family:Georgia,serif;font-size:25px;font-weight:400;letter-spacing:-.4px;margin:18px 0 12px}.welcome p{font-size:12px;color:#8a9787;line-height:1.9;max-width:320px}.suggestions{display:flex;flex-direction:column;gap:9px;margin-top:22px;max-width:340px}.suggestions button{border:1px solid #e5eadf;background:#fbfcf9;text-align:left;padding:11px 13px;border-radius:7px;font-size:11px;color:#607254;display:flex;justify-content:space-between}.suggestions button:hover{border-color:#a7bd97;background:#f2f6ed}.message{padding:16px 17px;background:#f6f8f2;border:1px solid #e8eddf;border-radius:9px;margin-bottom:15px;white-space:normal;font-size:12px;line-height:1.8;overflow-wrap:anywhere}.message.from-user{background:#edf3ed;margin-left:40px;border-color:#e0e9df}.message-label{font-size:8px;letter-spacing:1.2px;color:#7b916b;display:block;font-weight:650;margin-bottom:7px}.thinking{font-size:12px;color:#7d9072;padding:10px}form{padding:0 23px 15px}.input-row{border:1px solid #dae2d3;display:flex;align-items:center;border-radius:9px;background:#fcfdfa;padding:7px}input{min-width:0}.input-row input{border:0;background:transparent;flex:1;outline:0;padding:8px 9px;font-size:12px}.send-button{border:0;border-radius:6px;background:#215841;color:#fff;width:34px;height:34px;font-size:23px}.input-footnote{font-size:9px;color:#9aa593;margin:9px 0 0;text-align:center}.preferences{padding:26px 22px}.preferences h2{font-family:Georgia,serif;font-size:22px;font-weight:400;margin-top:14px}.preferences>p{font-size:11px;color:#8a9782;line-height:1.8;margin-bottom:25px}.preferences label,.setup>label{display:block;font-size:11px;color:#4f6446;margin:21px 0 10px}.preferences label>span{font-size:9px;color:#a0aa96;margin-left:5px}.preferences input,.setup>select{border:1px solid #e0e6d8;background:#fff;width:100%;padding:12px;border-radius:6px;color:#304b28;font-size:12px}.budget-input{border:1px solid #e0e6d8;border-radius:6px;display:flex;align-items:center;padding-left:12px;font-size:11px;color:#94a089}.budget-input input{border:0}.info-note{background:#f4f7ec;border-radius:7px;padding:15px 13px;margin-top:27px;font-size:10px;color:#6e7d5d;line-height:1.7}.info-note strong{font-weight:600}.info-note p{margin:6px 0 0;color:#8b977e}.snapshot{display:flex;align-items:center;gap:12px;border-top:1px solid #e7ecdf;margin-top:25px;padding-top:20px;font-size:10px;line-height:1.9;color:#869375}.snapshot-number{font-family:Georgia,serif;font-size:34px;color:#64804e}.snapshot small{font-size:9px;color:#a1aa97}.text-button{border:0;background:transparent;color:#7a8d6b;font-size:10px;padding:9px;margin-left:auto}.section-title{display:flex;justify-content:space-between;align-items:center;margin:28px 0 16px}.section-title span{font-size:10px;color:#99a18e}.course-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}.course-card{background:white;border:1px solid #e2e8db;border-radius:9px;padding:21px;display:flex;flex-direction:column}.course-kind{color:#799261;font-size:8px;letter-spacing:1.2px}.course-card h3{font-size:14px;line-height:1.5;margin:13px 0 7px;font-weight:600}.course-card>p{font-size:11px;color:#909c81;line-height:1.6}.course-price{font-size:16px;margin:12px 0 0;color:#3e5b30}.course-price small{font-size:10px;color:#93a181}.course-schedule{flex:1}.course-card a{font-size:10px;text-decoration:none;border-top:1px solid #e7ecdf;padding-top:14px;margin-top:14px;color:#5a7643;display:flex;justify-content:space-between}footer{padding:30px 0 25px;font-size:9px;color:#a3ac9a;display:flex;justify-content:space-between;gap:16px}.simulation-grid{display:grid;grid-template-columns:1.1fr 1fr;gap:24px}.setup,.experiment-status{padding:30px}.setup h2,.experiment-status h2{font-family:Georgia,serif;font-size:25px;font-weight:400;line-height:1.4;margin:13px 0}.setup>p,.experiment-status>p{font-size:12px;line-height:1.9;color:#87977b}.setup>select{font-size:12px}.field-help{font-size:10px!important;color:#93a186!important;line-height:1.8}.checkbox-label{display:flex!important;gap:9px;align-items:center;font-size:11px!important;line-height:1.7}.checkbox-label input{accent-color:#2b6147;width:14px;height:14px}.run-budget{display:flex;gap:9px;flex-wrap:wrap;margin:24px 0}.run-budget span{padding:7px 10px;border-radius:5px;background:#f1f5eb;color:#7c8e68;font-size:9px}.primary-button{background:#245a42;border:0;color:#fff;border-radius:7px;width:100%;padding:14px 17px;text-align:left;display:flex;justify-content:space-between;font-size:12px}.secondary-button{background:white;border:1px solid #dce4d2;color:#5f764c;border-radius:6px;padding:11px 15px;font-size:11px}.run-state{display:inline-block;border-radius:40px;background:#edf5e5;padding:8px 12px;color:#6e8a50;font-size:10px;margin-top:25px;text-transform:capitalize}.progress-track{height:5px;background:#edf2e6;border-radius:5px;margin-top:30px;overflow:hidden}.progress-track span{display:block;height:100%;background:#819f61;transition:width .4s}.run-actions{display:flex;align-items:center;gap:15px;margin-top:25px}.danger{color:#ad6b56}.large-glyph{display:block;font-family:Georgia,serif;font-size:65px;color:#a6b899;margin:30px 0 20px}.results-grid{display:grid;grid-template-columns:270px 1fr;gap:24px}.run-list{padding:25px 18px}.run-list h2{margin:0 8px 20px}.run-list>p{font-size:12px;line-height:1.8;color:#9aa58d}.run-list button{border:1px solid transparent;background:transparent;text-align:left;border-radius:7px;width:100%;padding:13px 12px;margin:4px 0;display:flex;flex-direction:column;gap:7px;color:#5f7550}.run-list button.selected{border-color:#e0e9d4;background:#f4f8ed}.run-list strong{font-size:11px;font-weight:600}.run-list button>span{font-size:10px;color:#8b9d79}.run-list small{font-size:9px;color:#a0ac94}.transcript{padding:28px;min-height:440px}.episode-divider{font-size:9px;color:#92a07f;letter-spacing:1px;border-bottom:1px solid #e8eddf;margin:26px 0 17px;padding-bottom:12px;text-transform:uppercase}.empty-results{padding:35px;text-align:center;color:#92a184;font-size:12px}.error{padding:13px 17px;border:1px solid #ebd4cc;background:#fdf4ef;color:#9b5b44;border-radius:7px;font-size:12px;line-height:1.8;margin-bottom:18px}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}
  .episode-outcomes{font-size:11px;line-height:1.7;margin:18px 0;color:#62775a}.episode-outcomes summary{cursor:pointer}.episode-outcome{padding:10px 0;border-bottom:1px solid #e4ebdc;overflow-wrap:anywhere}.episode-outcome>span{display:block;color:#8b977e}.episode-outcome p{font-size:10px;margin:6px 0}.model-note{overflow-wrap:anywhere}
  .message :global(p){margin:0 0 .8em}.message :global(p:last-child){margin-bottom:0}.message :global(ul),.message :global(ol){padding-left:1.5em;margin:.6em 0}.message :global(a){color:#215841;text-decoration:underline;text-underline-offset:2px}.message :global(pre){overflow-x:auto;white-space:pre;padding:10px;background:#edf1e8;border-radius:5px}.message :global(table){display:block;overflow-x:auto;border-collapse:collapse}.message :global(td),.message :global(th){padding:5px;border:1px solid #dbe3d3}
  @media(min-width:1500px){main{padding:0 66px}}@media(max-width:1100px){.sidebar{padding:28px 16px}.app-shell{grid-template-columns:200px 1fr}main{padding:0 28px}.advisor-grid{grid-template-columns:minmax(0,1fr) 235px;gap:17px}.intro-art{display:none}.toolbar{gap:10px}.mode-group{gap:4px}.connection{display:none}.course-grid{grid-template-columns:repeat(2,1fr)}}@media(max-width:800px){.app-shell{display:block}.sidebar{position:static;height:auto;padding:18px 22px;border-right:0;border-bottom:1px solid #e4eadc}.brand{margin:0}.brand strong{font-size:15px;line-height:16px}.brand br{display:none}.brand-sub{font-size:7px;margin-top:3px}.brand-mark{width:34px;height:35px;font-size:25px;line-height:35px}.side-label,.side-note,.side-footer{display:none}nav{flex-direction:row;margin-top:20px;gap:6px;justify-content:space-between}nav button{font-size:11px;padding:10px 9px;gap:7px}main{padding:0 22px}header{height:60px}.breadcrumb{font-size:7px}.pill{font-size:7px}.intro{padding:28px 0}h1{font-size:33px}.advisor-grid,.simulation-grid,.results-grid{grid-template-columns:1fr}.preferences{display:block}.preferences>p{margin-bottom:15px}.snapshot{margin-top:20px}.toolbar{flex-wrap:wrap}.mode-group{flex:1;min-width:170px}.toolbar select{font-size:11px}.course-grid{grid-template-columns:1fr}.preferences .info-note{margin-top:20px}.chat-card{min-height:480px}.section-title{align-items:flex-start;gap:12px}.section-title span{max-width:130px;text-align:right}.run-list{max-height:280px;overflow:auto}footer{font-size:8px}.card-heading{padding:18px}.card-heading h2{font-size:12px}.conversation{padding:21px 18px}}
</style>
