/**
 * Authored navigation, scenario outlines and Q&A for the integration guide.
 * Static example characters/messages are not evidence. The teaching panel reads
 * the selected demo's source-resolved profile and separately recorded execution.
 */

export type NodeId =
  | 'personas' | 'designer' | 'usersim' | 'fabric' | 'deepagents' | 'hermes'
  | 'mcp' | 'catalogue' | 'gateway' | 'routing' | 'litellm' | 'providers'
  | 'relay' | 'records' | 'checks' | 'helix' | 'platform' | 'guardrails' | 'openshell';

export type StageId = 'persona' | 'situation' | 'build' | 'run' | 'investigate' | 'evaluate' | 'routing' | 'safeguards' | 'deploy';
export type ScenarioId = 'photography' | 'boardgames' | 'dreamjob';

export interface Stage {
  id: StageId;
  title: string;
  pain: string;
  component: string;
  journey: string;
  description: string;
  input: string;
  output: string;
  evidence: string;
  reference: string;
  active: NodeId[];
  edges: string[];
}

export interface Scenario {
  id: ScenarioId;
  title: string;
  short: string;
  lesson: string;
  goal: string;
  preset: {
    persona: string;
    harness: 'deepagents' | 'hermes';
    /** Teaching preset; scenario-owned recording evidence establishes execution. */
    designer: boolean;
    routing: 'fixed' | 'switchyard';
    guardrails: boolean;
    helix: boolean;
    execution: 'standalone' | 'managed';
    baseline: string;
    constraints: string;
    lesson: string;
  };
  turns: { learner: string; advisor: string }[];
}

export interface PersonaExample {
  id: string;
  label: string;
  description: string;
}

export interface FAQ {
  id: string;
  group: string;
  question: string;
  answer: string;
  /** Stable journey identity; navigation does not start an execution. */
  stage: StageId;
  component: NodeId;
}

export interface ScenarioDetail {
  input: string;
  output: string;
  description: string;
}

export const stages: Stage[] = [
  {
    id: 'persona',
    title: 'Choose a test persona',
    pain: 'How do I test people with different backgrounds without changing the learner at every step?',
    component: 'Nemotron Personas · application selection',
    journey: 'Define who the application should help',
    description: 'Inspect and lock one synthetic source profile. Keep original background separate from application constraints and generated hypotheses. The guide resolves the selected demo’s original from its recorded source identity; static example characters are not source records.',
    input: 'A country distribution and a deliberate profile selection.',
    output: 'One locked synthetic profile with its source identity and unchanged original fields.',
    evidence: 'Recorded source distribution, revision, selected original and content hash. An unavailable installed source must not be replaced with a different profile.',
    reference: 'personas',
    active: ['personas'],
    edges: [],
  },
  {
    id: 'situation',
    title: 'Create a situation',
    pain: 'How do I turn background data into a meaningful test without presenting invented traits as facts?',
    component: 'UserSim preparation · authored constraints · Data Designer',
    journey: 'Prepare data and simulate interaction',
    description: 'Photography and board games use authored requests and explicit constraints, with no Designer generation. Retail learning uses a separately generated hypothetical overlay with brand preferences and a salary band. The guide inspects saved preparation without regenerating it.',
    input: 'The preset’s authored request and constraints; only dream job adds a closed generation schema.',
    output: 'A resolved authored situation, or a separately labelled hypothetical overlay for the dream-job story.',
    evidence: 'Saved authored situation and resolved UserSim preparation. Designer preparation additionally retains generation settings, validation, output and lineage. Inspection starts no new job.',
    reference: 'designer',
    active: ['personas', 'designer', 'usersim', 'gateway', 'records'],
    edges: ['personas-designer', 'designer-usersim', 'designer-records'],
  },
{
  "id": "build",
  "title": "Build and connect the agent",
  "pain": "How do the harness, memory, model and course tools become one application?",
  "component": "Fabric · Deep Agents or Hermes · course MCP · LiteLLM",
  "journey": "Assemble the application",
  "description": "Inspect the selected Fabric configuration, adapter, tools, fixed or routed model access and isolated conversation state. One chosen harness stays alive across public turns. Building and inspecting this configuration starts no inference.",
  "input": "The preset, selected harness, dated catalogue and bounded model/tool configuration.",
  "output": "A configured persistent runtime with the selected harness and read-only course tools.",
  "evidence": "Required: configuration revision, Fabric plan/Doctor outcome, selected adapter and effective tool surface. No runtime is started here.",
  "reference": "fabric",
  "active": [
    "fabric",
    "deepagents",
    "hermes",
    "mcp",
    "catalogue",
    "gateway",
    "litellm",
    "providers",
    "openshell"
  ],
  "edges": [
    "fabric-deepagents",
    "fabric-hermes",
    "mcp-catalogue",
    "gateway-litellm",
    "litellm-providers"
  ]
},
{
  "id": "run",
  "title": "Run the application",
  "pain": "Can the assembled application handle this learner and retain context?",
  "component": "UserSim · Fabric · selected harness · course tools",
  "journey": "Execute the selected conversation",
  "description": "UserSim exchanges public turns with the citizen advisor. Native agent turns use the configured model and read-only course MCP inside OpenShell; retail’s salary-only turn uses an application clarification before agent dispatch. The selected recording, rather than static example messages, establishes the execution.",
  "input": "One locked situation and its public learner messages.",
  "output": "A saved bounded conversation with attributable tool, model and lifecycle records, plus distinct application-only turns.",
  "evidence": "Required: activation roles, public transcript, Fabric runtime identity and per-turn invoke outcomes. Private simulator context must not enter advisor inputs.",
  "reference": "usersim",
  "active": [
    "usersim",
    "fabric",
    "deepagents",
    "hermes",
    "mcp",
    "catalogue",
    "gateway",
    "litellm",
    "routing",
    "providers",
    "guardrails",
    "relay",
    "records",
    "openshell"
  ],
  "edges": [
    "usersim-fabric",
    "fabric-deepagents",
    "fabric-hermes",
    "deepagents-mcp",
    "hermes-mcp",
    "mcp-catalogue",
    "deepagents-gateway",
    "hermes-gateway",
    "gateway-litellm",
    "litellm-routing",
    "routing-litellm",
    "litellm-providers",
    "fabric-relay",
    "relay-records",
    "usersim-guardrails",
    "guardrails-fabric",
    "fabric-guardrails",
    "guardrails-usersim"
  ]
},
{
  "id": "investigate",
  "title": "Investigate execution",
  "pain": "Why did the advisor say that, and where did the calls go?",
  "component": "Relay · saved actions · model calls for the advisor, learner and judges",
  "journey": "Observe the same execution",
  "description": "Choose a saved public turn, model call or MCP request and inspect its attributable native evidence. Relay covers target execution; application records also account for simulator, checker and judge roles. Missing correlations stay explicit.",
  "input": "The selected condition, episode, public turn and saved records.",
  "output": "An attributable path from public input through tools and model calls to the reply.",
  "evidence": "Native scope identities/parents, saved tool results, model-call accounting, failures and explicit correlation limits for the selected recording.",
  "reference": "relay",
  "active": [
    "usersim",
    "fabric",
    "deepagents",
    "hermes",
    "mcp",
    "catalogue",
    "gateway",
    "relay",
    "records",
    "openshell"
  ],
  "edges": [
    "fabric-relay",
    "relay-records",
    "usersim-records",
    "gateway-records",
    "mcp-catalogue"
  ]
},
{
  "id": "evaluate",
  "title": "Evaluate behaviour",
  "pain": "Did the application behave correctly beyond completing the request?",
  "component": "Application assertions · Helix Evals in scenario 3",
  "journey": "Assess outcomes and execution",
  "description": "Inspect supported facts, stated constraints, tool use, conversation continuity and disclosure boundaries. Photography and board games use application-owned assertions without Helix. Retail learning adds actual Helix Evals scoring and explicit managed jobs when connected.",
  "input": "Saved replies, relevant trajectory evidence, disclosed constraints and frozen facts.",
  "output": "Criterion-level observations, reasons, coverage and pass/fail/error/not-applicable results.",
  "evidence": "Required: criterion definition, expected/actual values and supporting saved record. Scenario 3 additionally needs native Helix evaluation/job output. No scores are invented.",
  "reference": "checks",
  "active": [
    "records",
    "catalogue",
    "checks",
    "helix",
    "platform"
  ],
  "edges": [
    "catalogue-records",
    "records-checks",
    "checks-helix",
    "platform-helix"
  ]
},
{
  "id": "routing",
  "title": "Optimize model routing",
  "pain": "Can I change model-selection policy and still make an understandable comparison?",
  "component": "Switchyard with LiteLLM · scenario 3",
  "journey": "Compare a declared model strategy",
  "description": "The first two scenarios retain their fixed model. Retail learning illustrates native Switchyard decisions at the LiteLLM plugin boundary. An explicit comparison uses the same public inputs, harness and catalogue; actual candidate selections and usage require records.",
  "input": "The preset route, or frozen inputs and a separately named comparison condition.",
  "output": "A fixed path, or attributable routing decisions and a controlled comparison.",
  "evidence": "Required for a routed condition: requested alias, actual candidate/selection, native decision, status and usage. Fixed presets have no Switchyard decision.",
  "reference": "routing",
  "active": [
    "gateway",
    "routing",
    "litellm",
    "providers",
    "records"
  ],
  "edges": [
    "gateway-litellm",
    "litellm-routing",
    "routing-litellm",
    "litellm-providers",
    "gateway-records"
  ]
},
{
  "id": "safeguards",
  "title": "Configure behavioural safeguards",
  "pain": "Which interactions should proceed, be constrained or be refused?",
  "component": "Application restrictions · native Guardrails in scenarios 2 and 3",
  "journey": "Inspect and test behavioural policy",
  "description": "Photography keeps the application tool allowlist without native Guardrails. Board games introduces native input/output checks through a separate policy demonstration; legitimate no-match conversations stay allowed. Retail learning reuses the safeguards. Checker failure must not become an allow decision.",
  "input": "The behavioural policy, a legitimate public request and a separately selected policy probe.",
  "output": "An allowed, blocked or failed check with its actual recorded decision evidence where the preset enables Guardrails.",
  "evidence": "Policy revision, explicit check type, input/output identity, native decision and failures. Photography does not use native Guardrails; inspecting decisions never runs another check.",
  "reference": "guardrails",
  "active": [
    "usersim",
    "guardrails",
    "fabric",
    "deepagents",
    "hermes",
    "mcp",
    "records",
    "openshell"
  ],
  "edges": [
    "usersim-guardrails",
    "guardrails-fabric",
    "fabric-guardrails",
    "guardrails-usersim",
    "guardrails-records"
  ]
},
{
  "id": "deploy",
  "title": "Deploy with controlled access",
  "pain": "Can I operate the application with verified access controls?",
  "component": "Standalone OpenShell · Helix-managed operations in scenario 3",
  "journey": "Verify runtime access and lifecycle",
  "description": "Recorded agent executions contain the advisor application, selected persistent harness and course tools inside OpenShell. The first two presets use standalone control; retail adds a separate Helix-managed session. No persona or private salary is baked into an image.",
  "input": "The reusable application package, runtime configuration and explicit native access policy.",
  "output": "Native sandbox identity, actual invocation/enforcement records and confirmed cleanup.",
  "evidence": "Effective policy and loaded revision, allowed/denied probes, invocation and cleanup. Retail’s managed condition also has its own Helix lifecycle identities. Inspection deploys nothing.",
  "reference": "openshell",
  "active": [
    "platform",
    "openshell",
    "fabric",
    "deepagents",
    "hermes",
    "mcp",
    "catalogue",
    "gateway",
    "records"
  ],
  "edges": [
    "platform-openshell",
    "openshell-fabric",
    "fabric-deepagents",
    "fabric-hermes",
    "deepagents-mcp",
    "hermes-mcp",
    "mcp-catalogue",
    "platform-records"
  ]
}
];

export const legacyStageIds: StageId[] = ['persona', 'situation', 'run', 'investigate', 'routing', 'evaluate', 'deploy'];

export const scenarios: Scenario[] = [
  {
    id: 'photography',
    title: 'Find a photography class',
    short: 'Beginner photography · Saturday · S$50 before funding.',
    lesson: 'Ground one recommendation with a fixed model, inspectable application checks and standalone OpenShell; no Designer or Helix.',
    goal: 'Find a supported beginner photography option without claiming that unconfirmed materials or personal funding are included.',
    preset: {
      persona: 'Beginner photography learner · authored example',
      harness: 'deepagents',
      designer: false,
      routing: 'fixed',
      guardrails: false,
      helix: false,
      execution: 'standalone',
      baseline: 'Fixed model via LiteLLM',
      constraints: 'Saturday · S$50 before funding · confirm unknown material fees',
      lesson: 'Ground one recommendation without adding Designer or a routing experiment.',
    },
    turns: [
      {
        learner: 'I am a beginner. Can you suggest a photography class on a Saturday, within S$50 before funding?',
        advisor: 'The course snapshot captured on 10 November 2026 lists Photography and Photo Enhancement with AI (AI30) at Toa Payoh West CC, reference CC-001. Its published course fee is S$10 and its listed session is Saturday, 12 December, 14:00–17:00. Access to Gemini on a smartphone or browser is required. The material fee is unconfirmed, so I cannot guarantee an all-in total below S$50. Confirm the extra costs, a place and any personal eligibility with the provider. The sourced listing is https://www.onepa.gov.sg/courses/photography-and-photo-enhancement-with-ai-ai30-c027245625 .',
      },
    ],
  },
  {
    id: 'boardgames',
    title: 'Learn to play board games',
    short: 'Two turns · honest no-match, then clarify why video-game design is different.',
    lesson: 'Handle an honest no-match across two turns with Hermes; introduce Guardrails through a separate policy test.',
    goal: 'Learn to play board games; do not reinterpret the request as learning to design video games.',
    preset: {
      persona: 'Board-game beginner · authored example',
      harness: 'hermes',
      designer: false,
      routing: 'fixed',
      guardrails: true,
      helix: false,
      execution: 'standalone',
      baseline: 'Fixed model via LiteLLM',
      constraints: 'Playing board games · no fabricated listing · no video-game-design substitute',
      lesson: 'Preserve the learner’s intent and conversation context across two turns.',
    },
    turns: [
      {
        learner: 'Hello, I want to learn how to play board games. Is there a class in the catalogue?',
        advisor: 'This course snapshot has no supported class for learning to play board games. That is a limit of this catalogue, not proof that no suitable class exists elsewhere.',
      },
      {
        learner: 'Is a video-game design class the same as learning to play board games?',
        advisor: 'No. Learning to play board games concerns their rules, play and strategy; video-game design concerns creating digital games. It would not satisfy your original goal. I still have no supported board-game class to recommend from this snapshot, and I should not invent one.',
      },
    ],
  },
  {
    id: 'dreamjob',
    title: 'Build skills for my dream job',
    short: 'Retail learning goals · private salary band disclosed in turn 2 · explicit budget in turn 3.',
    lesson: 'Prepare traceable Designer inputs, compare routing and introduce Helix evaluation, jobs and managed operations over three public turns.',
    goal: 'Explore skills and courses towards a dream job at UNIQLO or Decathlon; the application remains a learning advisor, not a job site.',
    preset: {
      persona: 'Aspiring retail learner · authored example',
      harness: 'deepagents',
      designer: true,
      routing: 'switchyard',
      guardrails: true,
      helix: true,
      execution: 'managed',
      baseline: 'Fixed Nemotron baseline · separate Switchyard comparisons via LiteLLM',
      constraints: 'Salary band private until turn 2 · S$3,000 training budget and weekends stated in turn 3',
      lesson: 'Keep generated context private until disclosure and compare routing without changing the learner or harness.',
    },
    turns: [
      {
        learner: 'I want to learn retail sales and inventory analysis, using brands such as UNIQLO or Decathlon as familiar examples. What does the SMU data communications and visualisation programme cover, how long is it, and what is its full fee?',
        advisor: 'The dated provider snapshot lists S$20,928 over three months, with 330 learning hours. It covers data preparation, visualisation and dashboards. Personal funding eligibility and the next intake require confirmation. These learning interests establish no employer endorsement or hiring outcome.',
      },
      {
        learner: 'My hypothetical gross monthly salary band is S$2,500–3,499. I want to start with spreadsheets for sales and inventory, and I have not decided my training budget.',
        advisor: 'Salary explains your concern but is not a training budget or proof of funding eligibility. What total amount and study schedule would you like me to use when comparing shorter options?',
      },
      {
        learner: 'My total training budget is S$3,000. I can study on weekends only and would prefer shorter options.',
        advisor: 'Use S$3,000, weekend availability and shorter study as your stated constraints. Investigate sourced beginner spreadsheet or sales-analysis options and inspect their prerequisites, fees and schedules before recommending one. If the catalogue has no supported match, say so. A course is not a guarantee of a job, a pay rise or employer endorsement.',
      },
    ],
  },
];

export const personas: PersonaExample[] = [
  {
    id: 'photography-learner',
    label: 'Beginner photography learner · authored example',
    description: 'A synthetic teaching character who wants a first Saturday photography class within an explicit budget. Not a sampled dataset record or an observed resident.',
  },
  {
    id: 'boardgames-learner',
    label: 'Board-game beginner · authored example',
    description: 'A synthetic teaching character interested in playing board games. This example tests honest no-match behaviour, not a real person’s preferences.',
  },
  {
    id: 'retail-learner',
    label: 'Aspiring retail learner · authored example',
    description: 'A synthetic teaching character motivated to learn skills towards a retail ambition. Brand preferences and a salary band are hypothetical additions, not original source facts or verified employer requirements.',
  },
];

export const scenarioDetails: Record<ScenarioId, Partial<Record<StageId, ScenarioDetail>>> = {
  photography: {
    persona: {
      input: 'The selected original and authored photography situation.',
      output: 'The same learner throughout all nine stages.',
      description: 'Start with the same selected original throughout the story. The guide resolves its recorded source revision and hash from the installed dataset rather than sampling another row when you navigate.',
    },
    situation: {
      input: '“Beginner photography, Saturday, within S$50 before funding.”',
      output: 'An authored photography scenario, separate from the source profile; no Designer job.',
      description: 'Saturday and S$50 come directly from the request. This preset does not use Designer. Keep the input simple; the needed artifact is the authored request and its resolved constraints. Select the dream-job story to explore generated hypotheses.',
    },
    run: {
      input: 'One public photography request; Fabric + Deep Agents; fixed model via LiteLLM.',
      output: 'The recorded reply using saved CC-001 facts and preserving unknown material fees.',
      description: 'Follow UserSim’s recorded public message into Fabric and the harness. The saved request, native course-tool result and public answer establish what executed. Opening another teaching page makes no new model or tool call.',
    },
    investigate: {
      input: 'The photography request, then the corresponding model, MCP and catalogue exchanges.',
      output: 'A clear path from Saturday/S$50 constraints to the S$10 listing and unconfirmed material fee.',
      description: 'Use Trace a Request to follow the saved search arguments, CC-001 result, source URL and attributable Relay scopes. Highlights explain the flow; the matching recording establishes the observed execution.',
    },
    routing: {
      input: 'The photography preset’s fixed model through LiteLLM.',
      output: 'The fixed path stays unchanged; there is no Switchyard condition or decision.',
      description: 'Keeping routing fixed is intentional: this story teaches sourced course facts. Inspect the saved fixed dispatch without starting another run. Retail learning has the separate Switchyard comparison.',
    },
    evaluate: {
      input: 'The saved reply, original Saturday/S$50 constraints and frozen CC-001 facts.',
      output: 'Recorded application assertions for a supported ID/URL, schedule and honest fee uncertainty.',
      description: 'Check the listing and material-fee caveat before reading the recorded criterion results. A S$10 published fee is not proof of a S$10 all-in cost. Assertions retain expected/actual values and supporting facts. This preset uses no Helix SDK or Platform.',
    },
    deploy: {
      input: 'The reusable Deep Agents application and explicit standalone OpenShell policy.',
      output: 'A standalone sandbox with its own invocation, enforcement and cleanup evidence.',
      description: 'The selected photography recording includes standalone OpenShell policy, invocation, enforcement and cleanup evidence without Helix services. It establishes that recorded execution, rather than current service readiness. Inspection creates no resource.',
    },
  },
  boardgames: {
    persona: {
      input: 'The selected original and authored board-games situation.',
      output: 'A stable learner whose intent is not silently rewritten.',
      description: 'Keep the request about playing board games. The selected recording retains its own original source identity and hash; static teaching characters are not substitutes for that profile.',
    },
    situation: {
      input: '“I want to learn how to play board games.”',
      output: 'An authored two-turn no-match situation, with no Designer job.',
      description: 'The first request asks to play board games; the follow-up asks whether video-game design is equivalent. No generated traits are needed. Preserve that authored intent and context instead of adding generation or inventing catalogue coverage.',
    },
    run: {
      input: 'Two public turns in one conversation; Fabric + Hermes; fixed model via LiteLLM.',
      output: 'A recorded no-match followed by the distinction between playing board games and designing digital games.',
      description: 'The saved conversation keeps the original playing goal across two Hermes invocations without Designer or routing changes. Review whether the follow-up preserves the no-match and explains the irrelevant substitute. Navigation starts no new invocation.',
    },
    investigate: {
      input: 'The original request, its search result and the follow-up exchange when actually recorded.',
      output: 'Evidence that the second answer retains the original goal without inventing a class.',
      description: 'Inspect the selected recording’s native tool result and both public turns. The learner’s mention of video-game design is a clarification, not permission to replace the goal. Preserve missing native correlations rather than attaching an unrelated trace.',
    },
    routing: {
      input: 'The same fixed model through LiteLLM for both Hermes turns.',
      output: 'No routing change: the lesson remains conversation context and an honest no-match.',
      description: 'Do not introduce a model-policy experiment to answer this follow-up. Both turns intentionally retain the fixed path. Select the dream-job story to inspect Switchyard; different scenarios are not a controlled harness comparison.',
    },
    evaluate: {
      input: 'Both saved public turns and the actual catalogue search evidence.',
      output: 'Recorded checks for the initial no-match and consistent intent through the follow-up.',
      description: 'A supported no-match can be useful. Check that the second answer explains the skill difference without inventing a video-game-design listing or treating it as a match. Missing search evidence is distinct from a confirmed empty result; no checks execute here.',
    },
    deploy: {
      input: 'The reusable Hermes application, public conversation context and restricted course tools.',
      output: 'A standalone OpenShell conversation; no Helix SDK or Platform is required.',
      description: 'The board-games recording has its own Hermes runtime, effective policy, invocation, enforcement and cleanup records. Photography’s evidence cannot substitute for those records. OpenShell restricts access; it does not create catalogue coverage.',
    },
  },
  dreamjob: {
    persona: {
      input: 'A locked original Singapore persona; derived brand interests and salary remain simulator context.',
      output: 'A stable learning persona with private additions separated from original source facts.',
      description: 'The goal is to learn selected skills towards a dream job. Do not infer actual employer requirements, vacancies or outcomes from brand interests. The advisor must not receive the hidden salary band before public turn 2.',
    },
    situation: {
      input: 'Retail skill interests; the sourced SMU programme; staged salary and budget disclosure.',
      output: 'The only preset with Designer preparation: hypothetical brand/salary columns and retained lineage.',
      description: 'Designer generates labelled brand, salary-band and learning-task hypotheses in a separate derived record. The salary band is a controlled experimental value, not inferred income. Salary stays private until turn 2; the S$3,000 budget is explicit only in turn 3. Generation records and lineage remain distinct from the original persona.',
    },
    run: {
      input: 'Three public turns: ambition/skills → salary band → S$3,000 budget, weekends and shorter options.',
      output: 'A generated learning conversation that distinguishes salary, budget and unverified employment claims.',
      description: 'The baseline uses Fabric + Deep Agents and fixed Nemotron through LiteLLM. Separate named conditions replay its saved public inputs for routing comparisons. The course tools support learning discovery. Hidden salary must not enter advisor messages before public turn 2.',
    },
    investigate: {
      input: 'The selected public turn, Designer lineage and attributable model/tool records.',
      output: 'A provenance check of salary disclosure, budget origin, model access and any sourced course claim.',
      description: 'Inspect the actual request audit before and after turn 2, native tool results and Relay records. A model must not receive the private band early or treat it as a spending limit. Inspect routing separately from Designer preparation; candidate labels and generated context do not establish a native routing decision.',
    },
    routing: {
      input: 'Frozen retail-learning inputs and Deep Agents harness for an explicit fixed-versus-Switchyard comparison.',
      output: 'Native model decisions, completed and failed conditions, actual usage and explicit availability limits.',
      description: 'Within each inventory, fixed and Switchyard conditions use identical public inputs, catalogue, harness and output limit. The MiniMax/Mistral comparison pool and separate Nemotron diagnostic keep independent results; historical Gemma/GLM failures remain recorded. Inspect native metadata and actual responses; a configured candidate or a selected model alone does not establish an improvement.',
    },
    evaluate: {
      input: 'Saved public turns, frozen provider facts, request audit and explicitly disclosed constraints.',
      output: 'Native Helix row scores, application-defined reasons/coverage and a separate durable job.',
      description: 'Check disclosure timing, actual fee/duration, explicit budget/weekends, numerical funding claims and truncation. Local SDK scoring and the Platform job read saved criteria without regenerating replies. Narrow exact-match checks do not certify every sentence; native UserSim judges remain separate.',
    },
    deploy: {
      input: 'The reusable application bundle and Helix-managed OpenShell session; private salary stays outside the image.',
      output: 'A new managed session with selected public budget/weekend constraints, native enforcement evidence and cleanup.',
      description: 'The local baseline keeps one OpenShell-contained Fabric runtime for its three turns. Helix creates a separate registration/deployment/session using a public preset and fresh memory. It does not resume that local thread or package private persona/salary data. Native policy, Intake and cleanup records identify the new condition.',
    },
  },
};

export const faqs: FAQ[] = [
  {
    id: 'why-this-stack', group: 'The learning story', stage: 'run', component: 'fabric',
    question: 'What should I learn from this sample?',
    answer: 'How one citizen-facing application connects synthetic test data, a real agent/tool boundary, models, evidence, evaluation and deployment. Begin with one photography request and keep it selected while inspecting the same flow.',
  },
  {
    id: 'one-preset', group: 'The learning story', stage: 'persona', component: 'personas',
    question: 'Why is there one preset per scenario?',
    answer: 'To teach distinct lessons without a product matrix. Photography uses Deep Agents and one turn; board games uses Hermes and two turns. Both keep fixed access through LiteLLM and skip Designer. Dream job uses Deep Agents, three turns, Designer hypotheses and a Switchyard/LiteLLM routing illustration. All harnesses are managed by Fabric.',
  },
  {
    id: 'nine-stages', group: 'The learning story', stage: 'run', component: 'usersim',
    question: 'Are the nine stages nine conversations or nine public turns?',
    answer: 'Neither. They are nine views of one scenario. Photography has one recorded UserSim exchange; board games has two turns to clarify the original goal; retail learning has three turns for salary and budget disclosure. All retain nine stages. Designer, Switchyard and Helix are introduced in retail; native Guardrails starts with board games. Reading another stage never requires another run.',
  },
  {
    id: 'trace-without-execution', group: 'The learning story', stage: 'investigate', component: 'records',
    question: 'Why can I trace a request without starting a new run?',
    answer: 'The guide reads the selected scenario’s saved execution. The highlighted route explains component cooperation; the accompanying native scopes, tool results and invocation records establish what actually happened. Reading those records makes no model or deployment call.',
  },
  {
    id: 'live-disabled', group: 'The learning story', stage: 'run', component: 'fabric',
    question: 'How is live simulation separate from recorded review?',
    answer: 'Trace a Request reads one fixed demo per scenario. Simulate a Session opens separate execution controls: check prerequisites, lock a source persona and explicitly start a new saved condition. Browsing datasets, changing lessons or opening evidence never starts that execution.',
  },
  {
    id: 'source-personas', group: 'Data and context', stage: 'persona', component: 'personas',
    question: 'Are the selected personas actual Nemotron records?',
    answer: 'Step 1 resolves the selected demo’s original synthetic Nemotron record against the installed distribution, revision and content hash. If it cannot match that source, the profile is unavailable; it does not display a substitute. Public HF profiles have no OCEAN conditioning; Singapore NGC Extended is a separate distribution. Static scenario examples are not source records.',
  },
  {
    id: 'designer-optional', group: 'Data and context', stage: 'situation', component: 'designer',
    question: 'Which scenario uses Designer?',
    answer: 'Retail learning uses recorded Designer generation of labelled brand preferences and a salary band with lineage. Photography and board games use authored requests and explicit constraints; they have no Designer generation job. The guide reads the saved generated inputs without regenerating them.',
  },
  {
    id: 'salary-only-third', group: 'Data and context', stage: 'run', component: 'usersim',
    question: 'Where do brand preferences and salary belong?',
    answer: 'Only the third scenario illustrates these hypothetical additions. UserSim can privately hold generated brand preferences and a S$2,500–3,499 gross monthly salary band. The advisor may learn the salary only through public turn 2; the S$3,000 training budget arrives separately in turn 3.',
  },
  {
    id: 'dream-job-scope', group: 'Data and context', stage: 'run', component: 'mcp',
    question: 'Does the dream-job story turn this into a job site?',
    answer: 'No. The learner’s ambition motivates learning spreadsheet, sales or inventory skills. The current tools search courses, not vacancies or employer requirements. Do not invent job listings, endorsements, salaries or a guarantee that a course leads to employment.',
  },
  {
    id: 'hypothetical-programme', group: 'Data and context', stage: 'situation', component: 'designer',
    question: 'Which retail programme facts come from the source?',
    answer: 'The selected retail snapshot records the SMU programme SF-007 as three months with a full fee of S$20,928. Check that dated source separately from the learner’s stated budget and availability. Monthly salary does not establish affordability, and a fee divided across months does not establish a payment plan or funding eligibility.',
  },
  {
    id: 'photography-fees', group: 'Execution and evidence', stage: 'investigate', component: 'catalogue',
    question: 'Does the photography listing establish a S$10 all-in price?',
    answer: 'No. The dated CC-001 snapshot records a published S$10 course fee and a Saturday session, but its material fee is unconfirmed. The advisor’s reply must preserve that uncertainty and cannot guarantee the total or personal funding eligibility.',
  },
  {
    id: 'boardgame-nomatch', group: 'Execution and evidence', stage: 'evaluate', component: 'mcp',
    question: 'Why not recommend video-game design for the board-game request?',
    answer: 'The second public turn asks exactly that distinction. Learning to play board games and learning to create digital games are different goals. Retain the original playing goal, explain the difference and preserve the honest catalogue no-match. Do not invent a class or treat the follow-up as a new recommendation target.',
  },
  {
    id: 'relay-counts', group: 'Execution and evidence', stage: 'investigate', component: 'relay',
    question: 'Why can Relay scopes and model-call totals differ?',
    answer: 'They cover different boundaries. The gateway ledger can include simulator, advisor and judge attempts, while native target telemetry covers another surface. Keep native identifiers, role labels, missing correlations and unknown usage explicit.',
  },
  {
    id: 'routing-variation', group: 'Execution and evidence', stage: 'routing', component: 'routing',
    question: 'Why does stage 7 keep the first two scenarios fixed?',
    answer: 'They already teach grounding and conversation context; another model-policy experiment would distract. Photography and board games intentionally retain fixed access through LiteLLM. Select the dream-job story for the Switchyard illustration, where a named comparison freezes source, scenario, harness and catalogue. Different stories are not a controlled harness comparison.',
  },
  {
    id: 'routing-receipt', group: 'Execution and evidence', stage: 'routing', component: 'routing',
    question: 'How do I verify which model Switchyard chose?',
    answer: 'Open retail learning’s routing lesson and compare the native decision metadata with the returned provider model, usage, reply and evaluation. The MiniMax/Mistral pool and separate Nemotron diagnostic retain independent results, alongside the historical Gemma/GLM failures. Endpoint probes do not establish a completed multi-turn comparison; failures and unknown usage remain visible. A configured pool or an unchanged selected model does not establish an improvement.',
  },
  {
    id: 'app-code', group: 'Execution and evidence', stage: 'investigate', component: 'records',
    question: 'What should each internal module’s code and log links show?',
    answer: 'Open the exact committed application call, the actual settings or a clearly labelled projection, and the selected scenario/condition’s result. The explanation distinguishes application-owned decisions from SDK work. Missing logs stay unavailable and never inherit another scenario’s evidence.',
  },
  {
    id: 'sourced-not-complete', group: 'Evaluation and boundaries', stage: 'evaluate', component: 'catalogue',
    question: 'Does a sourced fact establish complete, current advice?',
    answer: 'No. Preserve the source and capture date, unresolved fees and personal eligibility. A dated listing does not prove current seats or every checkout condition. Read the evidence behind each claim before accepting a recommendation.',
  },
  {
    id: 'helix-roles', group: 'Evaluation and boundaries', stage: 'evaluate', component: 'helix',
    question: 'How do local Helix Evals and Helix Platform differ?',
    answer: 'Helix spans agent operations, evaluation, experiments and hardening. Retail has recorded local Evals scoring, a durable evaluation job and a separate managed registration/deployment/session. The first two scenarios use application assertions without Helix. Neither deployment status nor narrow passing criteria certify the whole answer. Inspecting saved results runs no new evaluation.',
  },
  {
    id: 'openshell-history', group: 'Evaluation and boundaries', stage: 'deploy', component: 'openshell',
    question: 'Can I inspect historical photography/OpenShell evidence here?',
    answer: 'Yes. Step 9 opens the selected photography recording’s effective policy, invocation, allowed/denied probes and cleanup evidence. This demonstrates the saved standalone execution, not current service readiness. The reusable image contains application code and course tools, not a private persona.',
  },
  {
    id: 'policy-proof', group: 'Evaluation and boundaries', stage: 'deploy', component: 'openshell',
    question: 'What would establish the sandbox boundary?',
    answer: 'Effective native policy, its loaded revision, actual allowed/denied operations and cleanup evidence. Showing YAML or playing an animation is insufficient. Native network proposal review, if demonstrated, needs a real proposal, explicit decision, confirmed reload and separate retry; it cannot unlock files.',
  },
];
