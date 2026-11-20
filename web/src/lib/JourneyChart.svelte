<script lang="ts">
  import { stages } from './content';
  let { onselect }: { onselect: (stage: number) => void } = $props();
  const phases = [
    { title: 'Prepare', subtitle: 'People, situations and the agent', start: 0 },
    { title: 'Run and understand', subtitle: 'Conversation, evidence and checks', start: 3 },
    { title: 'Improve and deploy', subtitle: 'Routing, safeguards and access', start: 6 }
  ];
</script>

<nav class="journey-chart" aria-label="The nine development lessons">
  <div class="journey-phases" aria-hidden="true">
    {#each phases as phase}
      <div class="journey-phase"><h3>{phase.title}</h3><p>{phase.subtitle}</p><span class="phase-band"></span></div>
    {/each}
  </div>
  <ol class="journey-timeline">
    {#each stages as lesson, index}
      <li class:above={index % 2 === 0} class:below={index % 2 === 1}>
        <button onclick={() => onselect(index)} title={lesson.pain}>
          <span class="step-number" aria-hidden="true">{index + 1}</span>
          <span class="step-label">{lesson.title}</span>
        </button>
      </li>
    {/each}
  </ol>
</nav>

<style>
  .journey-chart { margin: 6px 0 20px; }
  .journey-phases { display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 5px; }
  .journey-phase { min-width: 0; }
  h3 { margin: 0 10px 3px; font-size: 16px; line-height: 1.3; }
  p { margin: 0 10px 14px; color: var(--muted); font-size: 12px; line-height: 1.5; }
  .phase-band { display:block; height:6px; border-radius:6px; background:#bfe3d8; }
  .journey-phase:nth-child(2) .phase-band { background:#91d7ca; }
  .journey-phase:nth-child(3) .phase-band { background:linear-gradient(90deg,#6db9ae,#36988e); }
  .journey-timeline { position:relative; display:grid; grid-template-columns:repeat(9,minmax(0,1fr)); list-style:none; padding:0; margin:20px 0 0; }
  .journey-timeline::before { content:''; position:absolute; left:5.5556%; right:5.5556%; top:112px; height:3px; background:linear-gradient(90deg,#b0e2d5,#50bea9,#008b7e); pointer-events:none; }
  li { min-width:0; position:relative; }
  button { position:relative; display:grid; grid-template-rows:96px 34px 96px; justify-items:center; align-items:center; width:100%; padding:0 3px; border:0; background:transparent; border-radius:5px; color:var(--ink); font-family:inherit; cursor:pointer; }
  .step-number { grid-row:2; grid-column:1; display:grid; place-items:center; box-sizing:border-box; width:34px; height:34px; border:1px solid #087f7b; border-radius:50%; color:#006e6a; background:#fff; font-size:16px; font-weight:650; z-index:1; }
  .step-number::before { content:''; position:absolute; left:50%; height:23px; width:1px; background:#328f8a; }
  .above .step-number::before { top:73px; }
  .below .step-number::before { top:130px; }
  .step-label { grid-column:1; max-width:100%; padding:0 2px; text-align:center; font-size:16px; font-weight:650; line-height:1.18; overflow-wrap:normal; }
  .above .step-label { grid-row:1; align-self:end; margin-bottom:34px; }
  .below .step-label { grid-row:3; align-self:start; margin-top:34px; }
  button:hover .step-number { background:#e9f6f1; }
  button:hover .step-label { color:var(--teal); }
  button:focus-visible { outline:2px solid var(--teal); outline-offset:3px; }
  @media (max-width:880px) {
    .journey-phases { display:none; }
    .journey-timeline { grid-template-columns:1fr; gap:6px; margin-top:8px; padding:4px 0; }
    .journey-timeline::before { left:19px; right:auto; top:25px; bottom:25px; height:auto; width:3px; background:linear-gradient(#b0e2d5,#50bea9,#008b7e); }
    button { display:flex; gap:18px; min-height:49px; padding:5px 4px; }
    .step-number { flex:0 0 34px; }
    .step-number::before { display:none; }
    .above .step-label,.below .step-label { margin:0; text-align:left; font-size:14px; line-height:1.4; }
    li:nth-child(3n + 1)::before { display:block; margin:12px 0 8px 56px; color:var(--teal); font-size:12px; font-weight:650; }
    li:first-child::before { content:'Prepare'; margin-top:0; }
    li:nth-child(4)::before { content:'Run and understand'; }
    li:nth-child(7)::before { content:'Improve and deploy'; }
  }
</style>
