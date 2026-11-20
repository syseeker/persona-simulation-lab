/**
 * Authored content for the isolated UX wireframe.
 * Conversations and characters are illustrative, not dataset rows, model output,
 * recorded executions, provider claims or verified course recommendations.
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
    /** Planned teaching configuration, not evidence that a job or route executed. */
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
    description: 'Inspect, sample and lock one synthetic source profile. Keep source background separate from application constraints and generated hypotheses. These wireframe characters are authored examples; no source dataset row is loaded here.',
    input: 'A country distribution and a deliberate profile selection.',
    output: 'One locked synthetic profile with its source identity and unchanged original fields.',
    evidence: 'Required for implementation: source distribution, revision, selected record and original hash. This wireframe contains no actual source record.',
    reference: 'personas',
    active: ['personas'],
    edges: [],
  },
  {
    id: 'situation',
    title: 'Create a situation',
    pain: 'How do I turn background data into a meaningful test without presenting invented traits as facts?',
    component: 'UserSim preparation · authored constraints · Data Designer in the dream-job story',
    journey: 'Prepare data and explicit circumstances',
    description: 'Photography and board games use authored requests and explicit constraints, with no Designer step. Only the dream-job preset illustrates Designer preparation of hypothetical brand preferences and a salary band. Preserve original records and derived lineage; no generation occurs in this wireframe.',
    input: 'The preset’s authored request and constraints; only dream job adds a closed generation schema.',
    output: 'A resolved authored situation, or a separately labelled hypothetical overlay for the dream-job story.',
    evidence: 'Required: the source request and resolved scenario. Only Designer preparation additionally needs a generation specification, validation, lineage and job ledger. No job runs here.',
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
  "output": "A planned application runtime with one supported harness and read-only course tools.",
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
  "description": "UserSim exchanges public turns with one persistent advisor session. The harness uses the configured model and read-only course MCP. All planned live runs place the application and its course tools inside OpenShell. These authored messages are not execution evidence.",
  "input": "One locked situation and its public learner messages.",
  "output": "A bounded conversation with actual tool, model and lifecycle records when implemented.",
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
  "component": "Relay · saved records · role-labelled call ledger",
  "journey": "Observe the same execution",
  "description": "Choose a saved public turn, model call or MCP request and inspect its attributable native evidence. Relay covers target execution; application records also account for simulator, checker and judge roles. Missing correlations stay explicit.",
  "input": "The selected condition, episode, public turn and saved records.",
  "output": "An attributable path from public input through tools and model calls to the reply.",
  "evidence": "Required: native scope identities/parents, saved tool results, role-labelled call records, failures and correlation limits. No observed trace is loaded.",
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
  "output": "An allowed, blocked or failed check with its actual decision evidence when implemented.",
  "evidence": "Required: policy revision, explicit check type, input/output identity, native decision and failures. This wireframe runs no checker or safety model.",
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
  "description": "All planned live runs contain the advisor application, one selected persistent harness and its course tools inside OpenShell. The first two presets use standalone control; retail learning adds Helix registration, deployments, sessions and jobs. No persona or private salary is baked into an image.",
  "input": "The reusable application package, runtime configuration and explicit native access policy.",
  "output": "Native sandbox identity, actual invocation/enforcement records and confirmed cleanup.",
  "evidence": "Required: effective policy and loaded revision, allowed/denied probes, invocation and cleanup. Scenario 3 also needs actual Helix lifecycle identities. No deployment occurs in this wireframe.",
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
      baseline: 'Switchyard via LiteLLM · illustrative Gemma / GLM candidates; no native decision',
      constraints: 'Salary band private until turn 2 · S$3,000 training budget and weekends stated in turn 3',
      lesson: 'Keep generated context private until disclosure and compare routing without changing the learner or harness.',
    },
    turns: [
      {
        learner: 'My dream is to work at UNIQLO or Decathlon. I want to learn skills for retail sales and inventory analysis. Would a data programme lasting about six months and costing S$20,000 be a good learning path?',
        advisor: 'I can help you investigate learning options, but I cannot verify vacancies or those employers’ requirements from this course catalogue. Treat six months and S$20,000 as a hypothetical example, not a verified provider listing. What skills do you want to build? If useful, share a budget or a monthly income band that you are comfortable disclosing.',
      },
      {
        learner: 'My hypothetical gross monthly salary band is S$2,500–3,499. I want to start with spreadsheets for sales and inventory, and I have not decided my training budget.',
        advisor: 'That helps explain your context, but salary is not a spending limit. The hypothetical S$20,000 fee divided over six months is about S$3,333 per month; that is only arithmetic, not a quoted payment plan or an affordability judgement. What total training budget and study time can you actually commit?',
      },
      {
        learner: 'My total training budget is S$3,000. I can study on weekends and would prefer shorter options rather than commit to the illustrative six-month, S$20,000 programme.',
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
      input: 'One authored beginner who wants to learn photography.',
      output: 'The same learner throughout all nine stages.',
      description: 'Start with the learner, not a new simulation for each tool. In the connected app, inspect and lock an actual source row; retain its revision and hash. No row has been sampled by this wireframe.',
    },
    situation: {
      input: '“Beginner photography, Saturday, within S$50 before funding.”',
      output: 'An authored photography scenario, separate from the source profile; no Designer job.',
      description: 'Saturday and S$50 come directly from the request. This preset does not use Designer. Keep the input simple; the needed artifact is the authored request and its resolved constraints. Select the dream-job story to explore generated hypotheses.',
    },
    run: {
      input: 'One public photography request; Fabric + Deep Agents; fixed model via LiteLLM.',
      output: 'An authored reply using the saved CC-001 facts and preserving unknown material fees.',
      description: 'Follow UserSim’s public message into Fabric and the harness. The harness calls the model through the gateway and separately queries Course MCP for catalogue facts before replying. The needed records are the actual request, tool result and public answer. No model or tool runs in this wireframe.',
    },
    investigate: {
      input: 'The photography request, then the corresponding model, MCP and catalogue exchanges.',
      output: 'A clear path from Saturday/S$50 constraints to the S$10 listing and unconfirmed material fee.',
      description: 'Use Trace a Request to follow this one exchange. In implementation, open its saved search arguments, CC-001 result, source URL and attributable Relay scopes. Highlights here explain the intended flow; they are not observed logs.',
    },
    routing: {
      input: 'The photography preset’s fixed model through LiteLLM.',
      output: 'The fixed path stays unchanged; there is no Switchyard condition or decision.',
      description: 'Keeping routing fixed is intentional: this story teaches sourced course facts. This stage explains the choice without another run. Select the dream-job story for the Switchyard comparison; nothing routes or executes in this wireframe.',
    },
    evaluate: {
      input: 'The saved reply, original Saturday/S$50 constraints and frozen CC-001 facts.',
      output: 'Planned assertions for a supported ID/URL, schedule and honest fee uncertainty.',
      description: 'Check the listing and material-fee caveat before reading a total. A S$10 published fee is not proof of a S$10 all-in cost. The needed artifact is each application-authored assertion with expected/actual values and supporting facts. This preset uses no Helix SDK or Platform; no score is supplied here.',
    },
    deploy: {
      input: 'The reusable Deep Agents application and explicit standalone OpenShell policy.',
      output: 'A standalone sandbox with its own invocation, enforcement and cleanup evidence.',
      description: 'Historical photography/OpenShell evidence exists in the project, but is not attached to this wireframe and does not establish current readiness. This preset requires standalone OpenShell evidence without Helix services. Opening this preview creates no resource.',
    },
  },
  boardgames: {
    persona: {
      input: 'One authored learner who wants to play board games.',
      output: 'A stable learner whose intent is not silently rewritten.',
      description: 'Keep the request about playing board games. An implementation records the selected source identity and original hash; this illustrative persona is not an actual corpus row.',
    },
    situation: {
      input: '“I want to learn how to play board games.”',
      output: 'An authored two-turn no-match situation, with no Designer job.',
      description: 'The first request asks to play board games; the follow-up asks whether video-game design is equivalent. No generated traits are needed. Preserve that authored intent and context instead of adding generation or inventing catalogue coverage.',
    },
    run: {
      input: 'Two public turns in one conversation; Fabric + Hermes; fixed model via LiteLLM.',
      output: 'An authored no-match followed by a clear distinction between playing board games and designing digital games.',
      description: 'Keep the original playing goal in the same conversation when the learner asks the follow-up. This exercises context without Designer or routing changes. A useful answer preserves the no-match and rejects the irrelevant substitute. No harness invocation occurs here.',
    },
    investigate: {
      input: 'The original request, its search result and the follow-up exchange when actually recorded.',
      output: 'Evidence that the second answer retains the original goal without inventing a class.',
      description: 'Inspect the saved tool result and both public turns. The learner’s mention of video-game design is a clarification, not permission to replace the goal. No native payload is installed here. Preserve the pinned managed-Hermes correlation limit rather than attach an unrelated trace.',
    },
    routing: {
      input: 'The same fixed model through LiteLLM for both Hermes turns.',
      output: 'No routing change: the lesson remains conversation context and an honest no-match.',
      description: 'Do not introduce a model-policy experiment to answer this follow-up. Both turns intentionally retain the fixed path. Select the dream-job story to inspect Switchyard; different scenarios are not a controlled harness comparison.',
    },
    evaluate: {
      input: 'Both saved public turns and the actual catalogue search evidence.',
      output: 'Planned checks for the initial no-match and consistent intent through the follow-up.',
      description: 'A supported no-match can be useful. Check that the second answer explains the skill difference without inventing a video-game-design listing or treating it as a match. Missing search evidence is distinct from a confirmed empty result; no checks execute here.',
    },
    deploy: {
      input: 'The reusable Hermes application, public conversation context and restricted course tools.',
      output: 'A standalone OpenShell conversation; no Helix SDK or Platform is required.',
      description: 'The historical native photography preset does not represent this story. A reusable harness-compatible package and real policy/invocation records are required before claiming standalone deployment. OpenShell restricts access; it does not create catalogue coverage.',
    },
  },
  dreamjob: {
    persona: {
      input: 'An authored aspiring retail learner; hypothetical brand interests and salary are simulator context.',
      output: 'A stable learning persona with private additions separated from original source facts.',
      description: 'The goal is to learn selected skills towards a dream job. Do not infer actual employer requirements, vacancies or outcomes from brand interests. The advisor must not receive the hidden salary band before public turn 2.',
    },
    situation: {
      input: 'Retail skill interests; a hypothetical six-month/S$20,000 option; staged salary and budget disclosure.',
      output: 'The only preset with Designer preparation: hypothetical brand/salary columns and retained lineage.',
      description: 'Designer would add brand preferences and the S$2,500–3,499 gross monthly salary band as labelled hypotheses. Salary stays private until turn 2; the S$3,000 budget is explicit only in turn 3. Programme duration/fee are teaching assumptions, not provider facts. This wireframe performs no generation.',
    },
    run: {
      input: 'Three public turns: ambition/skills → salary band → S$3,000 budget, weekends and shorter options.',
      output: 'An authored learning conversation that distinguishes salary, budget and unverified employment claims.',
      description: 'The preset uses Fabric + Deep Agents and illustrates Switchyard through LiteLLM with Gemma/GLM candidates; it contains no actual model decision. The course tools support learning discovery, not job search. Hidden salary must not enter advisor messages before public turn 2.',
    },
    investigate: {
      input: 'The selected public turn, Designer lineage and attributable model/tool records when implemented.',
      output: 'A provenance check of salary disclosure, budget origin, model access and any sourced course claim.',
      description: 'Inspect advisor inputs before and after turn 2. A model must not know the private band early or treat it as a spending limit. Inspect routing separately from Designer preparation; neither candidate labels nor generated context prove a native decision. No transcript or span is observed here.',
    },
    routing: {
      input: 'Frozen retail-learning inputs and Deep Agents harness for an explicit fixed-versus-Switchyard comparison.',
      output: 'Illustrative candidates: Gemma and GLM. Native decision: null. No selected model or saving is observed.',
      description: 'Only this story illustrates policy routing through LiteLLM. Keep the scenario, disclosure sequence, catalogue and harness fixed across the named conditions. A real receipt must record the requested alias, actual candidate/selection and native decision. Candidate names here do not imply a complexity heuristic ran or a model was chosen.',
    },
    evaluate: {
      input: 'Saved public turns, hypothetical programme labels and the explicitly disclosed training constraints.',
      output: 'Planned checks for disclosure timing, supported learning suggestions and no guarantees.',
      description: 'Check that salary is not leaked before turn 2; salary alone does not establish affordability; and S$3,000/weekends guide the later answer. Flag invented requirements, job placement, endorsement, funding or salary promises. No evaluation passes are supplied here.',
    },
    deploy: {
      input: 'The reusable application bundle and Helix-managed OpenShell session; private salary stays outside the image.',
      output: 'A proposed fresh managed conversation with salary entering through public turns only.',
      description: 'Helix manages registration, deployment, sessions and explicit evaluation jobs. One OpenShell-contained Fabric harness remains alive for all three public turns. Use public context at runtime instead of a scenario-specific image; historical photography records cannot verify this lifecycle.',
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
    answer: 'Neither. They are nine views of one scenario. Photography shows one authored exchange; board games shows two turns to clarify the original goal; dream job shows three turns for salary and budget disclosure. All retain nine stages. Designer, Switchyard and Helix are introduced in retail learning; native Guardrails starts with board games. Reading another stage never requires another run.',
  },
  {
    id: 'trace-without-execution', group: 'The learning story', stage: 'investigate', component: 'records',
    question: 'Why can I trace a request when nothing has executed?',
    answer: 'This wireframe traces an explanatory route through the diagram. It contains no observed model call, tool payload or native span. A connected trace viewer must use attributable saved records and clearly distinguish them from this authored flow.',
  },
  {
    id: 'live-disabled', group: 'The learning story', stage: 'run', component: 'fabric',
    question: 'Why is live simulation disabled?',
    answer: 'This phase reviews the UI only. The wireframe reads no persona dataset and connects to no SDK, model endpoint or runtime. Live simulation can be added only as an explicit prerequisite-checked action that creates a new saved condition.',
  },
  {
    id: 'source-personas', group: 'Data and context', stage: 'persona', component: 'personas',
    question: 'Are the selected personas actual Nemotron records?',
    answer: 'No. These are authored synthetic examples. Real corpus selection must retain distribution, revision, original record and hash. Public HF profiles have no OCEAN conditioning; Singapore NGC Extended is a separate distribution.',
  },
  {
    id: 'designer-optional', group: 'Data and context', stage: 'situation', component: 'designer',
    question: 'Which scenario uses Designer?',
    answer: 'Only the dream-job story illustrates Designer generation of labelled brand preferences and a salary band with lineage. Photography and board games use authored requests and explicit constraints; they have no Designer job. Reusing saved generated inputs should not regenerate them. This wireframe generates nothing.',
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
    question: 'Is the six-month, S$20,000 programme a sourced listing?',
    answer: 'No. Both figures are illustrative assumptions in the third scenario, not a provider’s duration or fee. Monthly salary alone does not establish affordability, and dividing a fee over six months does not establish a payment plan.',
  },
  {
    id: 'photography-fees', group: 'Execution and evidence', stage: 'investigate', component: 'catalogue',
    question: 'Does the photography listing establish a S$10 all-in price?',
    answer: 'No. The dated CC-001 snapshot records a published S$10 course fee and a Saturday session, but its material fee is unconfirmed. The authored reply must preserve that uncertainty and cannot guarantee the total or personal funding eligibility.',
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
    question: 'Did Switchyard actually choose Gemma or GLM in this wireframe?',
    answer: 'No. Gemma and GLM are illustrative candidates in the dream-job routing lesson. A preview can show a requested alias and candidate pool, but native_decision must remain null with no claimed selected model. Only actual native decision metadata and attributable calls can establish an observed route; no complexity heuristic executes here.',
  },
  {
    id: 'app-code', group: 'Execution and evidence', stage: 'investigate', component: 'records',
    question: 'What should each internal module’s code and log links show?',
    answer: 'The actual pinned SDK call or honestly labelled application-owned logic, plus a repository-relative source reference. A scenario log must belong to its selected condition. This wireframe’s static source excerpts explain ownership but do not prove these authored conversations ran.',
  },
  {
    id: 'sourced-not-complete', group: 'Evaluation and boundaries', stage: 'evaluate', component: 'catalogue',
    question: 'Does a sourced fact establish complete, current advice?',
    answer: 'No. Preserve the source and capture date, unresolved fees and personal eligibility. A dated listing does not prove current seats or every checkout condition. Read the evidence behind each claim before accepting a recommendation.',
  },
  {
    id: 'helix-roles', group: 'Evaluation and boundaries', stage: 'evaluate', component: 'helix',
    question: 'How do local Helix Evals and Helix Platform differ?',
    answer: 'Helix spans agent operations, evaluation, experiments and hardening. This guide introduces its local Evals SDK and managed registration, deployments, sessions and evaluation jobs in scenario 3; the first two scenarios use application assertions without Helix. Neither a deployment status nor a narrow passing assertion certifies the whole answer. No evaluation runs in this wireframe.',
  },
  {
    id: 'openshell-history', group: 'Evaluation and boundaries', stage: 'deploy', component: 'openshell',
    question: 'Can I inspect historical photography/OpenShell evidence here?',
    answer: 'The project has historical photography deployment and enforcement evidence, but no recording or running service is attached to this wireframe. That history does not establish current readiness. New acceptance needs the reusable application, the selected harness and actual scenario-matching records; no persona-specific image is required.',
  },
  {
    id: 'policy-proof', group: 'Evaluation and boundaries', stage: 'deploy', component: 'openshell',
    question: 'What would establish the sandbox boundary?',
    answer: 'Effective native policy, its loaded revision, actual allowed/denied operations and cleanup evidence. Showing YAML or playing an animation is insufficient. Native network proposal review, if demonstrated, needs a real proposal, explicit decision, confirmed reload and separate retry; it cannot unlock files.',
  },
];
