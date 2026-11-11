<script lang="ts">
  import type { Run, RunTrace } from '#lib/types.ts';
  import { renderMarkdown } from '#lib/markdown.ts';
  let { run }: { run: Run } = $props();
  let chosen = $state('');
  let trace = $state<RunTrace | null>(null);
  let loading = $state(false);
  let error = $state('');
  const episodes = $derived(run.events?.filter(event => event.type === 'episode_started') ?? []);
  const selected = $derived(episodes.find(episode => episode.episode_id === chosen) ?? episodes[0]);
  const labels: Record<string, string> = {
    age: 'Age', occupation: 'Occupation', planning_area: 'Area', education_level: 'Education',
    skills_and_expertise_list: 'Skills', skills_and_expertise: 'Skills narrative',
    hobbies_and_interests_list: 'Interests', hobbies_and_interests: 'Interests narrative',
    career_goals_and_ambitions: 'Career ambitions'
  };
  function display(value: unknown): string {
    return value === null || value === undefined ? 'Unknown' : Array.isArray(value) ? value.join(', ')
      : typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value);
  }
  function money(value: unknown) { return value === null || value === undefined ? 'Unknown' : `S$${value}`; }
  function fee(course: RunTrace['turns'][number]['course_references'][number]['course']) {
    if (!course || course.price_min_sgd === course.price_max_sgd) return money(course?.price_max_sgd);
    return `${money(course.price_min_sgd)} to ${money(course.price_max_sgd)}`;
  }
  function theme(value: RunTrace['scenario']['theme']) { return typeof value === 'string' ? value : value?.description; }
  function otherFields(profile: Record<string, unknown>) {
    return Object.entries(profile).filter(([key]) => !['age', 'occupation', 'career_goals_and_ambitions'].includes(key)
      && !(key === 'skills_and_expertise' && profile.skills_and_expertise_list)
      && !(key === 'hobbies_and_interests' && profile.hobbies_and_interests_list));
  }
  $effect(() => {
    const runId = run.run_id;
    const episodeId = selected?.episode_id;
    const controller = new AbortController();
    trace = null; error = '';
    if (!episodeId) { loading = false; return; }
    loading = true;
    fetch(`/api/trace?run_id=${encodeURIComponent(runId)}&episode_id=${encodeURIComponent(episodeId)}`, { signal: controller.signal })
      .then(async response => {
        const data = await response.json();
        if (!response.ok) throw new Error(data.error ?? 'Could not load saved sources');
        if (!controller.signal.aborted) trace = data;
      })
      .catch(e => { if (!controller.signal.aborted) error = e instanceof Error ? e.message : 'Could not load saved sources'; })
      .finally(() => { if (!controller.signal.aborted) loading = false; });
    return () => controller.abort();
  });
</script>

<div class="trace-view">
  <p class="intro">Compare the saved profile and scenario with the generated messages, then check the advisor’s course claims against the tool results and frozen catalogue. Opening this view makes no model calls.</p>
  {#if episodes.length}
    <label for="trace-episode">Conversation to trace</label>
    <select id="trace-episode" value={selected?.episode_id} onchange={event => chosen = event.currentTarget.value}>
      {#each episodes as episode, index}<option value={episode.episode_id}>{run.spec.mode === 'demo' ? 'Scenario' : 'Profile'} {(episode.persona_index ?? index) + 1} · {episode.strategy}</option>{/each}
    </select>
  {/if}
  {#if loading}<p role="status">Loading saved sources…</p>{/if}
  {#if error}<p class="notice failure" role="alert">{error}</p>{/if}
  {#if trace}
    {#if trace.error}<div class="notice failure"><strong>This condition stopped.</strong><p>{trace.error}</p></div>{/if}
    <div class="source-grid">
      <section class="source-card" aria-label="Source persona">
        <span class="tag profile-tag">SOURCE PROFILE</span><h3>What the persona supplied</h3>
        {#if Object.keys(trace.profile).length}
          <div class="profile-basics">{#if trace.profile.age !== undefined}<span>Age {display(trace.profile.age)}</span>{/if}{#if trace.profile.occupation}<span>{display(trace.profile.occupation)}</span>{/if}</div>
          {#if trace.profile.career_goals_and_ambitions}<h4>Career ambitions</h4><p>{display(trace.profile.career_goals_and_ambitions)}</p>{/if}
          <details><summary>Other source fields</summary><dl>{#each otherFields(trace.profile) as [key, value]}<dt>{labels[key] ?? key}</dt><dd>{display(value)}</dd>{/each}</dl></details>
          <p class="help">The simulated learner receives this synthetic profile. The advisor receives the learner’s messages.</p>
        {:else}<p>{trace.mode === 'demo' ? 'Offline demos use scripted goals; no source persona was sampled.' : 'No source profile was saved.'}</p>{/if}
        <details><summary>Dataset reference</summary><p>{trace.source.distribution ?? 'Unknown distribution'}</p>{#if trace.source.dataset}<p>{trace.source.dataset}</p>{/if}{#if trace.source.revision}<p class="hash">Revision: {trace.source.revision}</p>{/if}</details>
      </section>
      <section class="source-card" aria-label="Application scenario">
        <span class="tag scenario-tag">APPLICATION SCENARIO</span><h3>What the application added</h3>
        <h4>Conversation theme</h4><p>{theme(trace.scenario.theme) ?? (trace.mode === 'demo' ? 'Scripted learning goal shown in the conversation below.' : 'No theme was saved.')}</p>
        <h4>Advisor strategy</h4><p>{trace.scenario.strategy}</p>
        {#if trace.scenario.overlay}<h4>Generated preference hypotheses</h4><pre>{display(trace.scenario.overlay)}</pre>{:else}<p class="help">No Data Designer preference overlay was used.</p>{/if}
        <h4>Catalogue evidence</h4><p>{trace.snapshot.available ? 'Frozen snapshot saved with this run.' : 'Frozen snapshot unavailable for this run.'}</p>
        {#if trace.snapshot.integrity_matches === false}<p class="notice failure">The snapshot hash differs from the saved manifest.</p>{/if}
      </section>
    </div>
    {#each trace.turns as turn}
      <section class="trace-turn" aria-label={`Turn ${turn.number}`}>
        <h3>Turn {turn.number}</h3>
        <article class="message learner"><span class="tag generated-tag">{trace.mode === 'live' ? 'GENERATED LEARNER MESSAGE' : 'SCRIPTED LEARNER MESSAGE'}</span><div>{@html renderMarkdown(turn.user)}</div></article>
        <article class="message advisor"><span class="tag generated-tag">{trace.mode === 'live' ? 'GENERATED ADVISOR REPLY' : 'SCRIPTED ADVISOR REPLY'}</span>{#if turn.assistant}<div>{@html renderMarkdown(turn.assistant)}</div>{:else}<p>No advisor reply was saved for this turn.</p>{/if}</article>
        <details class="tool-details"><summary>Saved tool steps ({turn.tools.length})</summary>
          {#if !turn.tools.length}<p>No tool steps were retained. Use the stop reason and source inputs above to inspect this condition.</p>{/if}
          {#each turn.tools as tool, index}<div class="tool-step"><h4>{index + 1}. {tool.name}</h4>{#if tool.arguments !== null}<h5>Requested arguments</h5><pre>{display(tool.arguments)}</pre>{/if}<h5>Returned facts</h5>{#if tool.result !== null}<pre>{display(tool.result)}</pre>{:else}<p>A result for this request was not saved or could not be linked.</p>{/if}</div>{/each}
        </details>
        {#if turn.course_references.length}
          <div class="fact-heading"><span class="tag facts-tag">FROZEN COURSE FACTS</span><p>Check each claim about fees, dates and eligibility against these saved records.</p></div>
          {#each turn.course_references as reference}
            <section class="fact-card" aria-label={`Course facts ${reference.id}`}>
              {#if reference.course}
                <h4>{reference.id} · {reference.course.title}</h4><p>{reference.course.provider}</p>
                <dl><dt>Published fee range</dt><dd>{fee(reference.course)}</dd><dt>Known additional costs</dt><dd>{money(reference.course.extra_cost_sgd)}</dd><dt>Cost note</dt><dd>{display(reference.course.cost_note)}</dd><dt>Start date</dt><dd>{display(reference.course.start_date)}</dd><dt>End date</dt><dd>{display(reference.course.end_date)}</dd><dt>Schedule</dt><dd>{reference.course.schedule_note}</dd><dt>Prerequisites</dt><dd>{display(reference.course.prerequisite_note)}</dd><dt>Funding</dt><dd>{reference.course.funding_note}</dd></dl>
                <a href={reference.course.source_url} target="_blank" rel="noreferrer">Official course source</a>
                <p class="help">{reference.seen_in_tool_result ? 'This ID appears in a saved tool result. Inspect that result for any exclusions or conditions.' : 'This ID appears in the reply; its use in a saved tool result is unconfirmed.'}</p>
              {:else}<h4>{reference.id}</h4><p>No record for this ID is available in the saved catalogue. Treat its course claims as unverified.</p>{/if}
            </section>
          {/each}
        {:else if turn.assistant}<p class="help">No stable course IDs were found in this reply. Inspect the saved tool results and check any named course manually.</p>{/if}
      </section>
    {/each}
    {#each trace.notices as notice}<p class="notice">{notice}</p>{/each}
  {:else if !loading && !error}<p>No conversation has been saved yet.</p>{/if}
</div>

<style>
  .trace-view{font-size:12px;color:#4e6557;line-height:1.75;overflow-wrap:anywhere}.intro{margin:0 0 20px;color:#7d8c77}.trace-view>label{display:block;font-size:11px;font-weight:600;margin-bottom:7px}select{font:inherit;color:#31533f;border:1px solid #dce5d5;background:#fff;border-radius:6px;padding:10px;width:100%;margin-bottom:20px}.source-grid{display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr);gap:14px;align-items:start}.source-card{padding:18px;border:1px solid #dfe8d7;border-radius:8px;background:#fbfcf8;min-width:0}h3{font-size:14px;color:#284d38;margin:11px 0 14px}h4{font-size:11px;color:#4c6854;margin:16px 0 6px}h5{font-size:10px;margin:12px 0 5px}p{margin:7px 0}.tag{display:inline-block;font-size:8px;font-weight:650;letter-spacing:1px;line-height:1.7;padding:4px 7px;border-radius:4px}.profile-tag{background:#e6eee0;color:#627c4d}.scenario-tag{background:#f0eadb;color:#8c7745}.generated-tag{background:#e5edf0;color:#537383}.facts-tag{background:#e4efe9;color:#447052}.profile-basics{display:flex;flex-wrap:wrap;gap:6px}.profile-basics span{padding:3px 7px;background:#eef3e8;border-radius:4px;font-size:11px}details{margin:15px 0 0}summary{cursor:pointer;font-size:11px;color:#547146}dl{margin:10px 0}dt{font-size:10px;font-weight:650;color:#6c8060;margin:11px 0 3px}dd{margin:0;color:#536b58}.help{font-size:10px;color:#8b987e;margin-top:14px}.hash{font-size:9px}.trace-turn{border-top:1px solid #e3eada;margin-top:25px;padding-top:15px}.message{border:1px solid #e0e7da;border-radius:8px;padding:15px;margin:12px 0;background:#fafcf7}.message>div{margin-top:10px}.learner{background:#f0f5ef}.advisor{background:#f8faf5}.tool-details{background:#f7f9f2;border:1px solid #e1e8d8;border-radius:7px;padding:12px}.tool-step{padding-bottom:12px;border-bottom:1px solid #e2e9db}.tool-step:last-child{border-bottom:0}pre{white-space:pre-wrap;overflow-wrap:anywhere;max-height:350px;overflow:auto;background:#eef3e8;border-radius:5px;padding:11px;font-size:10px;line-height:1.6}.fact-heading{margin:20px 0 10px}.fact-heading p{font-size:10px;color:#8a977d}.fact-card{border:1px solid #dbe6d5;border-radius:7px;padding:15px;margin:10px 0;background:#fff}.fact-card h4{margin-top:0;font-size:12px}.fact-card a{color:#386048;font-size:11px;text-underline-offset:2px}.notice{border:1px solid #e5dfca;background:#faf7ed;color:#8b7951;border-radius:6px;padding:12px;margin:15px 0}.failure{background:#fcf3ee;border-color:#ead6cc;color:#98654e}.message :global(p){margin:0 0 .8em}.message :global(p:last-child){margin:0}.message :global(ul),.message :global(ol){padding-left:1.4em}.message :global(a){color:#386048}.message :global(pre){max-width:100%;overflow:auto}.message :global(table){display:block;max-width:100%;overflow-x:auto}@media(max-width:1100px){.source-grid{grid-template-columns:1fr}}
</style>
