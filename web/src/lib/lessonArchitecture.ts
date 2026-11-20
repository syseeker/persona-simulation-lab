/** The architecture and the teaching panel share operation IDs and evidence contracts.
 * A lesson is a view onto cooperating components, never a second architecture.
 */
import { stages, scenarios } from './content';

export type ScenarioId = 'photography' | 'boardgames' | 'dreamjob';
export type LessonId = 'persona' | 'situation' | 'build' | 'run' | 'investigate' | 'evaluate' | 'routing' | 'safeguards' | 'deploy';
export type Operation = {
  id: string; title: string; owner: string; concept: string; input: string; output: string;
  config: string; check: string; call?: string; configCall?: string; proof: string[];
};
export type Component = {
  id: string; title: string; simple: string; kind: string; purpose: string;
  architecture: string; workflow?: string; operations: Operation[];
};
const op = (id: string, title: string, owner: string, concept: string, input: string, output: string,
  config: string, check: string, proof: string[], call = id, configCall = call): Operation =>
  ({ id, title, owner, concept, input, output, config, check, proof, call, configCall });

export const components: Component[] = [
  { id:'personas', title:'Nemotron Personas', simple:'Test person', kind:'data',
    purpose:'Keep one identifiable synthetic person constant while testing the advisor.',
    architecture:'https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer',
    workflow:'https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg',
    operations:[
      op('persona.source','Load the original distribution','Application · Arrow dataset reader',
        'HF profile-only and NGC Extended are different inputs. Loading a file is application logic, not a NeMo generation call.',
        'An explicitly selected distribution and revision.','Original source rows; never generated replacements.',
        'Source distribution, revision and installed dataset location.','Compare the recorded distribution and revision before comparing a row.', ['source-lock.json']),
      op('persona.select','Select and inspect a person','Application · sample_personas',
        'Choose an original from the eligible source and inspect it before running the test.',
        'Source rows and explicit selection filters.','One synthetic test person.',
        'Sampling filters and source scope.','Read the actual selected profile. A sampling seed alone does not identify the same person.', ['source-lock.json']),
      op('persona.lock','Verify and lock the original','Application · lock_personas',
        'A content hash detects a changed row and makes the chosen input reproducible.',
        'Selected source identity and original row.','An immutable source-lock receipt.',
        'Distribution + revision + original SHA-256.','Match the original hash against the installed distribution. Missing originals stay unavailable.', ['source-lock.json']),
    ] },
  { id:'situation', title:'Authored situation', simple:'Test situation', kind:'data',
    purpose:'Specify what the person wants to learn and which constraints the test supplies.',
    architecture:'https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md',
    operations:[
      op('situation.authored','Supply the learning goal and constraints','Application · scenario preset',
        'A profile is not a request. We supply a concrete learning goal instead of treating a background trait as a stated need.',
        'A test person plus the selected story.','Goal, schedule, spending constraints and disclosure rules.',
        'Scenario preset; public-turn limit.','Keep source traits, supplied constraints and generated wording separate.', ['situation.json']),
      op('situation.bind','Bind the situation without changing the original','Application · bind_scenario',
        'Attach scenario context to a derived simulator input. Preserve the original separately.',
        'Locked original and scenario context.','A resolved input for this conversation.',
        'Selected authored situation or explicitly selected Designer overlay.','The advisor must not receive this private resolved row.', ['situation.json','usersim-setup.json']),
    ] },
  { id:'designer', title:'NeMo Data Designer', simple:'Test situation', kind:'data',
    purpose:'Generate explicitly hypothetical situation fields when the scenario needs richer test variation.',
    architecture:'https://docs.nvidia.com/nemo/datadesigner/v0.10.0/concepts/architecture-performance',
    operations:[
      op('designer.schema','Define seed data and closed schemas','Application → Data Designer configuration',
        'Schemas constrain generated fields; they do not turn a hypothetical salary or brand interest into a source fact.',
        'Original seed row, allowed brands and salary-band schema.','A configured generation job.',
        'LLMStructuredColumnConfig; preferred_brands and monthly_salary_range_sgd.',
        'Inspect allowed values and the original-to-overlay boundary.', ['designer-configuration.json']),
      op('designer.generate','Generate the requested fields','Data Designer SDK · create / generation callbacks',
        'Use a separate compatible SDK environment and retain generation failures and warnings.',
        'Seed data and column configuration.','Generated overlay plus native generation records.',
        'Explicit model, bounded batch and requested columns.','A saved overlay alone does not prove the SDK generated it.', ['designer-output.json','designer-generation.json']),
      op('designer.lineage','Validate and retain lineage','Application · validate_generated_payload',
        'Validate the generated result and save it separately from its original parent.',
        'Generated fields, schema and parent hash.','Validated derived input, or a visible failure.',
        'Closed values, parent identity and salary disclosure rule.','Check parent hash, original preservation and explicit overlay selection.', ['designer-lineage.json']),
    ] },
  { id:'usersim', title:'NeMo UserSim', simple:'Simulated learner', kind:'runtime',
    purpose:'Turn a private test profile and situation into public learner messages, then react to the advisor.',
    architecture:'https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/architecture/overview.md',
    workflow:'https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md',
    operations:[
      op('usersim.prepare','Resolve persona, behaviour and probe','Application → UserSim preparation',
        'Preparation combines the selected input with the learning-advisor probe. It does not yet run a conversation.',
        'Locked profile, supplied situation and native behaviour fields.','Prepared simulator configuration and episode preamble.',
        'locale=en_SG; learning_advisor probe; scenario turn limit.',
        'Compare locale, probe options, limits and the profile-only flag.', ['usersim-setup.json'], 'usersim.prepare','usersim.prepare'),
      op('usersim.probe','Apply the custom learning-advisor hooks','Application probe · inherited engine',
        'Our hooks describe the learner goal. The inherited UserSim engine owns turn generation, checking and stopping.',
        'Private persona and situation.','Instructions for generating a public learner message.',
        'Custom get_user_system_prompt and assistant-system hooks; original behavioural preamble.',
        'Private profile and hidden salary stay in the simulator. Only a public message crosses into the advisor.', ['usersim-setup.json'], 'usersim.probe','usersim.prepare'),
      op('usersim.loop','Generate/check a turn and process the reply','UserSim · external conversation runtime',
        'advance() requests the next activation. User/gate/judge work stays separate from the advisor activation delegated to Fabric.',
        'Prepared context, previous public messages and the previous advisor reply.','Next public learner turn, reply judgement or stop decision.',
        'Turn/attempt limits and user-language checking; no pre-generated follow-up conversation.',
        'Compare activation order and public messages. One assistant activation can contain multiple model/tool calls.', ['usersim-activations.jsonl','public-conversation.json','usersim-setup.json'], 'usersim.loop','usersim.prepare'),
      op('usersim.finalize','Stop and save the trajectory','UserSim · runtime.finalize()',
        'Keep early stops, warnings and incomplete conversations. Do not invent a missing final reply.',
        'Completed activations or the stop condition.','Saved outcome and public trajectory.',
        'Public-turn limit and native stop conditions.','Compare n_turns and warnings. Native simulated-tool counts do not count the advisor’s MCP calls.', ['usersim-setup.json','public-conversation.json']),
    ] },
  { id:'fabric', title:'NeMo Fabric', simple:'Citizen advisor', kind:'runtime',
    purpose:'Give the application one configuration and execution interface across supported harnesses.',
    architecture:'https://docs.nvidia.com/nemo/fabric/latest/about-nemo-fabric/overview',
    workflow:'https://docs.nvidia.com/nemo/fabric/adapter-contract/overview',
    operations:[
      op('fabric.config','Build FabricConfig and resolve the adapter','Application → FabricConfig',
        'The application chooses a harness and connects instructions, model access, MCP and observability through typed configuration.',
        'Selected harness, model connection, course tools and instructions.','Saved Fabric configuration; resolved adapter.',
        'adapter_id; model provider/name; chat input, message output; timeout; tool allowlist; Relay config.',
        'Compare the selected adapter and enabled tool names, not just a successful import.', ['framework-config.json','fabric-config.json']),
      op('fabric.plan','Plan and check the runtime','Application → Fabric.plan() / doctor()',
        'Inspect resolution and preflight before starting the runtime. A plan is not proof of a successful conversation.',
        'FabricConfig.','Plan with adapter capabilities and a Doctor outcome.',
        'Preinstalled adapter and compatible interpreter.','Check resolved adapter, supported inputs/outputs and any Doctor errors.', ['fabric-plan.json','fabric-doctor.json'], 'fabric.plan','fabric.config'),
      op('fabric.start','Start one persistent runtime','Application → start_runtime()',
        'Reuse one runtime and thread across public turns. Changing the harness changes the adapter, not the caller contract.',
        'Checked FabricConfig and run-specific artifact directory.','Runtime and thread identity; startup receipt.',
        'ADAPTER_PYTHON where required; generated Relay configuration path.',
        'Match runtime/thread identities across startup, invocation and cleanup.', ['fabric-lifecycle.jsonl','runtime-receipt.json'], 'fabric.start','fabric.config'),
      op('fabric.invoke','Invoke with a RunRequest','Application → runtime.invoke(RunRequest)',
        'Pass only the public learner message and public constraints. The selected adapter owns the harness invocation.',
        'Public message, persistent thread and bounded runtime.','An invocation identity and an awaited RunResult.',
        'RunRequest message; shared runtime; timeout/internal-step bounds.',
        'Match the public input and invocation identity to the native harness events.', ['fabric-invocations.json','fabric-lifecycle.jsonl','public-conversation.json'], 'fabric.invoke','fabric.config'),
      op('fabric.result','Read the normalized RunResult','Application ← Fabric adapter contract',
        'Fabric normalizes the adapter result. The application still validates whether it contains usable public advice.',
        'Harness result.','Runtime status, normalized output and the extracted public reply.',
        'Message output schema; public-answer validation.','Compare status, output.response and the public transcript. Transport success alone is insufficient.', ['fabric-invocations.json','public-conversation.json'], 'fabric.result','fabric.config'),
    ] },
  { id:'harness', title:'Selected agent harness', simple:'Citizen advisor', kind:'runtime',
    purpose:'Perform the actual model/tool loop behind Fabric’s common interface.',
    architecture:'https://docs.langchain.com/oss/python/deepagents/overview',
    workflow:'https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/src/nemo_fabric_adapters/deepagents/adapter.py',
    operations:[
      op('harness.context','Connect instructions and course tools','Application configuration → selected adapter',
        'Expose a small read-only course surface. Available tools and tools actually used are different facts.',
        'Application instructions and MCP server definition.','Selected harness with tool access and conversation context.',
        'search_courses, get_course_details, compare_courses; global execution allowlist.',
        'Compare configured tools with native called-tool records. Do not assume delegation or long-term memory was used.', ['framework-config.json','native-tools.json'], 'harness.context','fabric.config'),
      op('harness.loop','Run the model/tool loop and return a reply','SDK-owned harness · invoked through Fabric',
        'The harness chooses a course tool when needed and uses returned facts to answer. Our application waits at the Fabric call.',
        'Public message, model responses and course results.','Native model/tool events and harness reply.',
        'Selected adapter; instructions; tool and internal-turn bounds.',
        'Deep Agents and Hermes should produce different native records while preserving the same Fabric application call.', ['relay-scopes.json','native-tools.json','fabric-invocations.json'], 'fabric.invoke','harness.policy'),
    ] },
  { id:'mcp', title:'Course MCP', simple:'Course information', kind:'tools',
    purpose:'Let the advisor retrieve course information through application-owned read-only tools.',
    architecture:'https://modelcontextprotocol.io/docs/learn/architecture',
    operations:[
      op('mcp.search','Search using public constraints','Application tool · FastMCP',
        'A real tool result connects the recommendation to catalogue facts. Unknown costs stay unknown.',
        'Requested subject, budget and schedule.','Matching dated course records, or an honest no-match.',
        'Read-only search schema; public preferences only.',
        'Compare actual arguments, returned courses and cited sources with the public request.', ['native-tools.json','catalogue-snapshot.json'], 'mcp.search','harness.context'),
      op('mcp.details','Retrieve one course’s details','Application tool · FastMCP',
        'Inspect a known listing without inventing availability or personal eligibility.',
        'A catalogue course identifier.','Published facts and explicit unknowns.',
        'Read-only detail schema.','An enabled tool need not have been called. Look for its native record.', ['native-tools.json'], 'mcp.details','harness.context'),
      op('mcp.compare','Compare supported options','Application tool · FastMCP',
        'Compare actual catalogue entries rather than inferring employer endorsement or outcome guarantees.',
        'Known course identifiers and public constraints.','A fact-based comparison.',
        'Read-only comparison schema.','Confirm the selected IDs and fields in the real tool result.', ['native-tools.json'], 'mcp.compare','harness.context'),
    ] },
  { id:'catalogue', title:'Frozen course catalogue', simple:'Course information', kind:'tools',
    purpose:'Preserve the exact published facts available during the test.',
    architecture:'https://www.onepa.gov.sg/courses',
    operations:[
      op('catalogue.freeze','Freeze facts and source links','Application · catalogue snapshot',
        'A fixed snapshot makes tool output and evaluation comparable. Provenance does not guarantee current availability.',
        'Source-linked course listings.','Run-specific snapshot and content hash.',
        'Catalogue revision/date; permitted course fields.',
        'Use this recording’s snapshot, not a later provider page, when reproducing the check.', ['catalogue-snapshot.json']),
    ] },
  { id:'gateway', title:'Application inference gateway', simple:'Model access', kind:'models',
    purpose:'Bound model work and keep simulator, advisor and judge accounting distinct.',
    architecture:'https://docs.litellm.ai/docs/routing',
    operations:[
      op('models.admit','Admit and bound each model call','Application · budget gateway',
        'Workload ceilings and tool-schema filtering are our gateway’s responsibilities, not guarantees supplied by LiteLLM.',
        'A role-labelled model request.','Admitted call or an explicit refusal.',
        '120-call cap; 1,024 output-token ceiling; retries disabled; permitted tool schemas.',
        'Compare role, requested alias, status and tool surface. Keep unknown usage visible.', ['usage.json']),
      op('models.request','Send the request and record usage','Application → LiteLLM-compatible endpoint',
        'Record the actual selected provider model and usage separately from native Relay instrumentation.',
        'Admitted public/model request.','Response, timing, usage or a visible error.',
        'Fixed or routed alias; host-side credentials.','A gateway call ID is not automatically a native Relay span ID.', ['usage.json']),
    ] },
  { id:'litellm', title:'LiteLLM proxy', simple:'Model access', kind:'models',
    purpose:'Resolve model aliases and dispatch to the configured provider.',
    architecture:'https://docs.litellm.ai/docs/routing',
    operations:[
      op('models.alias','Resolve alias and dispatch to provider','LiteLLM · proxy configuration',
        'The same application endpoint can expose a fixed alias or a candidate group. Fixed dispatch is not routing optimization.',
        'Requested alias and provider inventory.','Provider response and actual model identity.',
        'model_list; fixed advisor/support aliases or the explicit routed candidate group.',
        'Compare requested alias and selected model in the call ledger.', ['usage.json'], 'models.alias'),
    ] },
  { id:'routing', title:'NeMo Switchyard', simple:'Model access', kind:'models',
    purpose:'Choose among candidates inside the LiteLLM routing integration.',
    architecture:'https://nvidia-nemo.github.io/Switchyard/mechanics_of_libsy/',
    workflow:'https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md',
    operations:[
      op('routing.policy','Load candidates and routing policy','Application plugin → Switchyard',
        'Routing changes model strategy without creating another conversational agent.',
        'Candidate inventory and selected policy.','Configured routing stage.',
        'Pinned StageRoutingPlugin integration; efficient-first policy and escalation settings.',
        'Confirm endpoint access and distinct candidates before interpreting a comparison.', ['routing-configuration.json']),
      op('routing.decision','Decide, dispatch and retain the decision','Switchyard stage → LiteLLM candidate',
        'The selected candidate may stay the same across requests. Actual native decisions, not installation, demonstrate routing.',
        'Unchanged public request and candidate inventory.','Selected deployment, response and decision metadata.',
        'Keep harness, public inputs and catalogue controlled.',
        'Compare native decision, actual provider model, usage and evaluation. Inventory changes are a separate variable.', ['routing-decisions.json','usage.json'], 'routing.decision','routing.policy'),
    ] },
  { id:'relay', title:'NeMo Relay', simple:'Execution records and checks', kind:'evidence',
    purpose:'Instrument the harness and export native agent/model/tool relationships.',
    architecture:'https://docs.nvidia.com/nemo/relay/latest/about-nemo-relay/architecture',
    workflow:'https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/about-nemo-relay/architecture.mdx',
    operations:[
      op('relay.configure','Attach native observability','Application configuration → Fabric adapter',
        'Relay attaches to execution; it is not another mandatory request hop between the advisor and model.',
        'Relay configuration and an instrumented harness.','Native scope events written to the configured sink.',
        'Generated observability config; ATOF file sink; full payloads disabled.',
        'Verify configuration and actual exported events. Do not attach the same instrumentation twice.', ['framework-config.json','relay-scopes.json'], 'relay.configure','fabric.config'),
      op('relay.scopes','Read parent-linked native scopes','Relay events → application reader',
        'Request, agent, model and tool scopes reveal order and ownership without guessing missing joins.',
        'Native scope starts/ends and parent identities.','Observed event tree with status and missing-correlation notices.',
        'Run-scoped native artifacts; preserve original UUIDs.',
        'Follow the parent chain and tool events for this turn. Keep gateway accounting separate.', ['relay-scopes.json'], 'relay.scopes','relay.configure'),
      op('relay.tools','Inspect actual tool inputs and outputs','Relay tool events → application reader',
        'A native completed tool record is stronger evidence than the advisor saying it searched.',
        'Tool-call and tool-result events.','Tool name, arguments, returned facts and status.',
        'Same native run and parent scope.',
        'Compare tool arguments and returned sources against the saved public reply.', ['native-tools.json'], 'relay.tools','relay.configure'),
    ] },
  { id:'records', title:'Recorded evidence', simple:'Execution records and checks', kind:'evidence',
    purpose:'Keep one reviewed demo pack tied to this scenario, source revision and run.',
    architecture:'https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/architecture/overview.md',
    operations:[
      op('records.read','Verify and open this scenario’s recording','Application · immutable pack reader',
        'Reading a recording never reruns a model. Missing scenario evidence cannot fall back to a different story.',
        'Tagged scenario/run and manifest hashes.','Verified public conversation and allowlisted evidence.',
        'One curated demo pack; separate companion projection; no latest-run fallback.',
        'Check scenario/run identity, manifest integrity and source-hash comparison.', ['run.json','runtime-receipt.json']),
    ] },
  { id:'checks', title:'Application assertions', simple:'Execution records and checks', kind:'evidence',
    purpose:'Check saved advice against public requirements and the facts that were available.',
    architecture:'https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/architecture/overview.md',
    operations:[
      op('checks.evaluate','Compare expected and observed behaviour','Application · deterministic assertions',
        'A completed reply is not necessarily correct. These checks do not use a model or Helix.',
        'Saved public conversation, frozen facts and native evidence.','Criterion-level expected/actual values, reasons and coverage.',
        'Scenario criteria; exact source/constraint and narrow phrase checks.',
        'Inspect each reason and coverage limit. In-loop UserSim judges and optional post-loop UserSim evaluation are separate.', ['evaluation.json']),
    ] },
  { id:'helix', title:'Helix evaluation', simple:'Execution records and checks', kind:'evidence',
    purpose:'Define and execute evaluations over saved outputs, separately from managed deployment.',
    architecture:'https://docs.nvidia.com/nemo-helix/v0.10/documentation/home',
    workflow:'https://docs.nvidia.com/nemo-helix/v0.9/documentation/evaluate-models',
    operations:[
      op('helix.evaluate','Define, run and inspect evaluation','Application → Helix Evals SDK',
        'Helix evaluation is one part of a broader platform. Retained SDK reference code does not establish a retail-learning result.',
        'Saved replies, frozen facts and explicit evaluation criteria.','Native evaluation results, execution errors and criterion coverage.',
        'Evaluator definition and compatible local SDK environment; managed jobs only when explicitly selected.',
        'Require actual criterion-level results for this scenario. A narrow exact-match example cannot certify a whole response.', ['helix-evaluation.json']),
    ] },
  { id:'guardrails', title:'NeMo Guardrails · input / output', simple:'Behavioural safeguards', kind:'runtime',
    purpose:'Apply configured behavioural checks at the advisor’s public input/output boundaries.',
    architecture:'https://docs.nvidia.com/nemo/guardrails/latest/about-nemo-guardrails-library/how-it-works',
    workflow:'https://docs.nvidia.com/nemo/guardrails/latest/reference/guardrails-sequence-diagrams',
    operations:[
      {id:'guardrails.check',title:'Load policy, check and return a decision',owner:'Application → native LLMRails.check_async',
        concept:'Allow a legitimate learning request; demonstrate a credential-disclosure refusal in a separate negative condition.',
        input:'Selected policy and public input/output.',output:'Native allow/change/reject decision or a visible checker error.',
        config:'Pinned Guardrails 0.24.1 in an isolated process inside OpenShell. Custom Colang input/output flows use deterministic credential and assurance rules without model generation.',
        check:'Compare the native status, blocking rail, executed action, configuration hashes and purpose. These narrow custom rules do not establish general safety coverage.',proof:['guardrails-config.json','guardrails-decisions.jsonl','guardrails-probe.json'],call:'guardrails.check',configCall:'guardrails.config'},
    ] },
  { id:'platform', title:'Helix managed operations', simple:'Managed operations', kind:'deployment',
    purpose:'Manage registration, deployment, sessions and cleanup outside the advisor process.',
    architecture:'https://docs.nvidia.com/nemo-helix/v0.10/documentation/home',
    workflow:'https://docs.nvidia.com/nemo-helix/v0.10/documentation/agents/deploy-agents',
    operations:[
      op('platform.register','Register and deploy the application','Application → Helix Platform',
        'Register a reusable application package, not an image containing a private persona.',
        'Agent recipe, selected harness and public configuration.','Agent and deployment identities.',
        'Explicit Platform connection and OpenShell execution profile.',
        'Require a new scenario-specific registration and deployment receipt.', ['platform-registration.json','platform-deployment.json'], 'platform.register','platform.deploy'),
      op('platform.session','Open a session, invoke and clean up','Application → Helix session lifecycle',
        'A managed condition starts new memory. It cannot pretend to resume a local conversation’s private state.',
        'Deployment identity and explicitly selected public constraints.','Session replies and confirmed resource cleanup.',
        'Session ownership; invocation input; exact deployment cleanup.',
        'Match agent/deployment/session IDs and cleanup. Closing an inspector must not terminate a session.', ['platform-session.json','platform-cleanup.json'], 'platform.session','platform.deploy'),
    ] },
  { id:'openshell', title:'OpenShell · trusted supervisor', simple:'Controlled execution', kind:'deployment',
    purpose:'Enforce file, process and network access around the untrusted advisor, harness and course tools.',
    architecture:'https://docs.nvidia.com/openshell/v0.1.6/about/architecture',
    operations:[
      op('openshell.create','Create the sandbox with policy','Application → native OpenShell',
        'The trusted supervisor mediates the sandboxed workload. Host UserSim and credentialed model access stay outside.',
        'Reusable image and explicit operational policy.','Sandbox identity and effective policy revision.',
        'File/network rules; image/source hashes; standalone or managed creation.',
        'Inspect effective loaded YAML and runtime identity, not just the intended policy file.', ['sandbox-identity.json','effective-policy.json','effective-policy.yaml'], 'openshell.create','openshell.yaml'),
      op('openshell.execute','Execute the advisor and course tools inside','Application → native exec transport',
        'Keep the persistent Fabric runtime and MCP tools inside the boundary for the whole conversation.',
        'Sandbox identity, public constraints and the bounded host bridge.','Actual model/tool activity in the sandbox.',
        'Native exec; host-side credentials; permitted artifact paths.',
        'Correlate image/runtime identity with the allowed conversation and native tool evidence.', ['runtime-receipt.json','native-tools.json'], 'openshell.execute','openshell.yaml'),
      op('openshell.probe','Verify allowed/denied operations and cleanup','Application → native enforcement probes',
        'Policy intention and enforced denial are different evidence. Preserve cleanup failures and ownership.',
        'Loaded policy, allowed conversation and denied-operation probes.','Allow/deny results and confirmed cleanup.',
        'Exact sandbox identity; file and network probes; bounded cleanup.',
        'Look for policy-denial errors, not generic connectivity failures. Human approval/reload was not demonstrated in photography.', ['boundary-probes.json','cleanup.json'], 'openshell.probe','openshell.yaml'),
    ] },
];

export const componentById = Object.fromEntries(components.map(c => [c.id,c]));
export const operationById = Object.fromEntries(components.flatMap(c => c.operations.map(o => [o.id,{...o,component:c.id}])));
export const lessonIds = stages.map(s=>s.id) as LessonId[];
export const scenarioIds = scenarios.map(s=>s.id) as ScenarioId[];
export function preset(id:string) { return scenarios.find(s=>s.id===id)!.preset; }
export function componentUsed(id:string, scenario:string) {
  const p=preset(scenario);
  return id==='designer' ? p.designer : id==='routing' ? p.routing==='switchyard' : id==='guardrails' ? p.guardrails : ['helix','platform'].includes(id) ? p.helix : id==='checks' ? !p.helix : true;
}
export function componentTitle(id:string, scenario:string) {
  return id==='harness' ? preset(scenario).harness==='hermes' ? 'Hermes' : 'LangChain Deep Agents' : componentById[id]?.title || id;
}
export function architectureUrl(id:string,scenario:string) {
  return id==='harness' && preset(scenario).harness==='hermes' ? 'https://hermes-agent.nousresearch.com/docs/' : componentById[id]?.architecture;
}
export function sourceId(id:string,scenario:string) {
  if(id==='checks.evaluate'&&scenario==='boardgames')return 'checks.boardgames';
  return id==='harness.context' && preset(scenario).harness==='hermes' ? 'hermes.environment' : operationById[id]?.call;
}
export function resolveComponent(id:string) {
  return ({people:'personas',testpeople:'personas',simulator:'usersim',application:'fabric',deepagents:'harness',hermes:'harness',courses:'mcp',models:'gateway',evidence:'relay',providers:'litellm',budget:'gateway',standalone:'openshell',transport:'openshell'} as Record<string,string>)[id] || id;
}

export type Lesson = { id:LessonId; why:string; input:string; action:string; output:string; design:string; checks:string[]; operations:string[]; notUsed?:string; };
export function lessonFor(scenario:string,id:string):Lesson {
  const p=preset(scenario), photo=scenario==='photography', retail=scenario==='dreamjob';
  const harness=p.harness==='hermes'?'Hermes':'LangChain Deep Agents';
  const lessons:Record<LessonId,Omit<Lesson,'id'>> = {
    persona:{why:'Choose the person whose needs we want to test.',input:'An original Singapore synthetic profile from the chosen distribution.',
      action:'Inspect the selected person, then preserve the distribution, revision and original content hash.',
      output:'The exact original selected for this scenario, when its installed source can be verified.',
      design:'Selection and hashing are application-owned. UserSim has not run; no learner message or advisor call is needed to choose a person.',
      checks:['Compare name/background with the original row and match its recorded hash.','A missing source must stay unavailable; do not substitute a plausible person.'],operations:['persona.source','persona.select','persona.lock']},
    situation:{why:'Give that person a concrete reason to talk to the advisor.',
      input:photo?'Original profile + beginner photography, Saturday and a budget under S$50.':retail?'Original profile + a retail-skills story and explicitly hypothetical salary/brand fields.':'Original profile + a request to learn to play board games.',
      action:retail?'Generate and select a validated Designer overlay, bind disclosure rules, then prepare UserSim.':'Attach the authored situation, then resolve UserSim persona, behaviour and learning-advisor probe configuration.',
      output:'A prepared test situation. The saved opening message shows how UserSim worded it when the loop later ran in Step 4.',
      design:'Original traits, supplied constraints and generated message wording are separate. UserSim phrases the request; it does not invent the supplied goal or budget.',
      checks:[retail?'Verify schema, native generation result, parent lineage and explicit overlay selection.':'No standalone Designer generation job is expected in this preset.','Compare the supplied situation, resolved UserSim setup and saved public opening.'],
      operations:retail?['persona.lock','situation.authored','designer.schema','designer.generate','designer.lineage','situation.bind','usersim.prepare','usersim.probe']:['persona.lock','situation.authored','situation.bind','usersim.prepare','usersim.probe'],
      notUsed:retail?undefined:'Data Designer enrichment is skipped. UserSim’s installed dependencies are a separate matter.'},
    build:{why:'Connect the advisor to its model and course information.',input:`${harness}, the read-only course tools, model access and application instructions.`,
      action:'Build FabricConfig, inspect the plan and Doctor result, then start one persistent selected runtime.',output:'A configured adapter, runtime/thread identity and connected course-tool surface.',
      design:'Fabric is the common application interface. Adapter configuration differs by harness; the application invokes the same runtime contract.',
      checks:['Compare adapter_id, model connection, input/output schemas, tool allowlist and timeout.','Match the plan, Doctor outcome and startup identity. A plan alone is not an execution.'],
      operations:['fabric.config','fabric.plan','fabric.start','harness.context','relay.configure','models.alias']},
    run:{why:'See the learner’s request become a source-linked answer.',input:`${scenarios.find(s=>s.id===scenario)!.turns.length} public ${photo?'turn':'turns'}; the advisor receives public messages, not the private persona.`,
      action:'UserSim generates/checks a message → Fabric invokes the selected harness → the harness calls model/tools → Fabric returns a normalized result → UserSim judges and continues or stops.',
      output:photo?'The saved learner request and actual photography reply.':retail?'A three-turn conversation: explore learning, disclose salary, then state budget and schedule.':'Two public turns that preserve an honest no-match and distinguish playing games from designing them.',
      design:'Follow-ups are generated after earlier replies. Keep a persistent harness thread. Native stop judges are not the saved-response evaluation in Step 6.',
      checks:[retail?'Salary stays private until public turn 2; the explicit spending limit arrives in turn 3.':'Check the actual public constraints, returned course facts and final answer.','Compare RunRequest/public input, invocation ID, RunResult and the public reply.'],
      operations:['usersim.loop','fabric.invoke','harness.loop','models.admit','models.request','models.alias','mcp.search','catalogue.freeze','fabric.result','usersim.finalize',...(p.guardrails?['guardrails.check']:[])]},
    investigate:{why:'Understand why the advisor gave this answer.',input:'The selected public turn and its recorded execution.',action:'Follow native request → agent → model/tool scopes; compare the tool’s facts with the reply. Read simulator activations and gateway usage separately.',
      output:'An attributable event path, actual tool results and visible missing correlations.',design:'Relay instruments the harness rather than acting as a downstream request service. Native scope IDs and gateway call IDs are different identities.',
      checks:['Check parent/child scope relationships, ordering and tool arguments/results.','Do not invent a model-call join when the recording does not establish one.'],operations:['relay.scopes','relay.tools','fabric.invoke','fabric.result','models.request','records.read']},
    evaluate:{why:'Check whether the advice respected the request and available evidence.',input:'Saved public conversation + frozen course facts + execution evidence.',action:retail?'Run explicit criteria through Helix evaluation and retain native results.':'Run application-owned assertions over saved outputs; no new advisor or model call.',
      output:'Expected and observed values, reasons, failures and coverage for each criterion.',design:'UserSim’s in-loop judges, optional post-loop UserSim eval/report and our saved-response evaluation are distinct mechanisms. Helix also supports managed operations; it is not just a scorer.',
      checks:['Read each criterion and its limits; a completed response or high aggregate score is insufficient.',retail?'Require a scenario-specific Helix call/configuration and native criterion results.':'These application assertions do not establish proximity, seats or personal funding eligibility.'],
      operations:['records.read','catalogue.freeze',retail?'helix.evaluate':'checks.evaluate'],notUsed:retail?undefined:'Helix and optional post-loop UserSim evaluation are not used in this preset.'},
    routing:{why:retail?'Compare model strategies without rebuilding the advisor.':'Understand the fixed model route used by this baseline.',
      input:retail?'Identical public inputs, catalogue and harness; an explicit candidate inventory.':'The fixed advisor alias and configured provider model.',
      action:retail?'Load the Switchyard policy in LiteLLM, inspect the actual decision and compare replies/usage/evaluation.':'LiteLLM resolves the fixed alias. No optimization experiment was performed.',
      output:retail?'Native selected-model decisions and separately labelled comparison results.':'The requested alias, actual model and usage from the saved calls.',
      design:'A routing-policy comparison keeps inventory controlled. Fixed Nemotron versus a Gemma/GLM pool also changes inventory. Selecting the same model is a valid routing result.',
      checks:[retail?'Require native decision metadata and actual provider selection, not just a configured plugin.':'Do not expect a Switchyard decision in this preset.','Keep harness comparisons separate from routing comparisons.'],
      operations:retail?['routing.policy','routing.decision','models.alias','models.request','helix.evaluate']:['models.alias','models.request'],notUsed:retail?undefined:'Switchyard is not used; routing optimization was not performed.'},
    safeguards:{why:'Decide which public requests or replies the application should allow, change or reject.',input:p.guardrails?'A legitimate learning conversation and a separate credential-disclosure policy probe.':'Application instructions, allowed tools and public messages.',
      action:p.guardrails?'Load native input/output policy, run configured checks and record their decisions.':'Apply the existing instructions and tool restrictions; native Guardrails is omitted.',
      output:p.guardrails?'Native check decisions or explicit errors; the legitimate conversation remains a separate condition.':'Application restrictions, without a native Guardrails decision.',
      design:'Behavioural checks, Relay instrumentation and OpenShell operational access are different boundaries. Explain later does not mean apply later: enabled checks surround execution from the start.',
      checks:[p.guardrails?'Require the native API call, effective configuration, executed actions and matching decisions; unavailable evidence does not count as coverage.':'Inspect enabled tools and the actual provider-bound tool surface.','A no-match is normal learning advice, not a blocked policy request.'],
      operations:p.guardrails?['guardrails.check','harness.context','records.read']:['harness.context','models.admit'],notUsed:p.guardrails?undefined:'Native Guardrails is intentionally not used in photography.'},
    deploy:{why:'Understand where the advisor runs and what it can access.',input:'Reusable application image, selected harness, course tools and an explicit operational policy.',
      action:p.helix?'Register/deploy through Helix, create a new session, then verify its OpenShell boundary and cleanup.':'Create standalone OpenShell, run the persistent advisor/tools inside and verify allowed/denied operations and cleanup.',
      output:'Runtime identity, effective policy, actual enforcement results and cleanup ownership.',
      design:'The trusted supervisor is outside the sandboxed advisor workload. UserSim and credentialed model access stay host-side. This boundary is applied before Step 4 even though taught here.',
      checks:['Compare effective YAML/revision with the runtime identity and allow/deny results.','A failed connection alone is not policy enforcement. Confirm cleanup; keep unresolved ownership visible.',...(p.helix?['A new managed condition uses selected public constraints, not copied private persona data or local memory.']:[])],
      operations:[...(p.helix?['platform.register','platform.session']:[]),'openshell.create','openshell.execute','openshell.probe'],notUsed:p.helix?undefined:'Helix managed operations are omitted; this preset uses standalone OpenShell.'},
  };
  return {id:id as LessonId,...lessons[id as LessonId]};
}

export type SimpleBlock = { id:string; title:string; kind:string; purpose:string; members:string[]; rows:{title:string;operation:string}[]; };
export function simpleBlocks(scenario:string):SimpleBlock[] {
  const p=preset(scenario);
  return [
    {id:'person',title:'Test person',kind:'data',purpose:'Who are we testing with?',members:['personas'],rows:[{title:'Inspect a synthetic person',operation:'persona.select'},{title:'Keep the same original',operation:'persona.lock'}]},
    {id:'situation-block',title:'Test situation',kind:'data',purpose:'What do they want to learn?',members:['situation','designer'],rows:[{title:'Supply the goal and constraints',operation:'situation.authored'},{title:p.designer?'Add hypothetical details':'Keep source and situation separate',operation:p.designer?'designer.generate':'situation.bind'}]},
    {id:'learner',title:'Simulated learner',kind:'runtime',purpose:'How does the person take part?',members:['usersim'],rows:[{title:'Prepare the test conversation',operation:'usersim.prepare'},{title:'Generate messages and react',operation:'usersim.loop'}]},
    {id:'advisor',title:'Citizen advisor',kind:'runtime',purpose:'Turn a public request into advice.',members:['fabric','harness'],rows:[{title:'Connect the selected agent',operation:'fabric.config'},{title:'Use tools and return a reply',operation:'fabric.invoke'}]},
    {id:'courses',title:'Course information',kind:'tools',purpose:'Retrieve facts the answer can support.',members:['mcp','catalogue'],rows:[{title:'Look up matching courses',operation:'mcp.search'},{title:'Keep the facts and source links',operation:'catalogue.freeze'}]},
    {id:'models',title:'Model access',kind:'models',purpose:'Reach models within call limits.',members:['gateway','litellm','routing'],rows:[{title:'Limit and account for calls',operation:'models.admit'},{title:p.routing==='switchyard'?'Choose a model strategy':'Use the fixed model route',operation:p.routing==='switchyard'?'routing.decision':'models.alias'}]},
    {id:'evidence',title:'Execution records and checks',kind:'evidence',purpose:'Understand and assess the result.',members:['relay','records','checks','helix'],rows:[{title:'Follow what actually happened',operation:'relay.scopes'},{title:'Check the saved advice',operation:p.helix?'helix.evaluate':'checks.evaluate'}]},
  ];
}

export type ArchitectureEdge = {id:string;source:string;target:string;label:string;kind:'prep'|'request'|'telemetry'|'control';operations:string[]; guard?:boolean; routed?:boolean; managed?:boolean;};
const edge=(id:string,source:string,target:string,label:string,kind:ArchitectureEdge['kind'],operations:string[],extra:Partial<ArchitectureEdge>={}):ArchitectureEdge=>({id,source,target,label,kind,operations,...extra});
export const architectureEdges:ArchitectureEdge[]=[
  edge('person-situation','personas','situation','Locked original','prep',['situation.bind']),
  edge('person-designer','personas','designer','Original seed','prep',['designer.schema','designer.generate'],{managed:true}),
  edge('designer-situation','designer','situation','Selected overlay','prep',['designer.lineage','situation.bind'],{managed:true}),
  edge('situation-learner','situation','usersim','Situation + private context','prep',['usersim.prepare','usersim.probe']),
  edge('learner-advisor','usersim','fabric','Public message → RunRequest','request',['usersim.loop','fabric.invoke']),
  edge('advisor-learner','fabric','usersim','RunResult → public reply','request',['fabric.result','usersim.finalize']),
  edge('fabric-harness','fabric','harness','Configure / invoke adapter','prep',['fabric.config','fabric.plan','fabric.start','harness.context','harness.loop','fabric.invoke','fabric.result']),
  edge('harness-tools','harness','mcp','Tool request / result','request',['harness.loop','mcp.search','mcp.details','mcp.compare']),
  edge('tools-facts','mcp','catalogue','Read frozen facts','request',['mcp.search','mcp.details','mcp.compare','catalogue.freeze']),
  edge('harness-model','harness','gateway','Advisor model calls','request',['harness.loop','models.admit','models.request']),
  edge('learner-model','usersim','gateway','Simulator / judge calls','request',['usersim.loop','models.request']),
  edge('gateway-proxy','gateway','litellm','Requested alias','request',['models.request','models.alias']),
  edge('proxy-routing','litellm','routing','Policy → selected candidate','request',['routing.policy','routing.decision'],{routed:true}),
  edge('harness-relay','harness','relay','Instrumentation attachment','telemetry',['relay.configure','relay.scopes','relay.tools','harness.loop']),
  edge('relay-records','relay','records','Native scopes / tool facts','telemetry',['relay.scopes','relay.tools','records.read']),
  edge('gateway-records','gateway','records','Separate role / usage ledger','telemetry',['models.request','records.read']),
  edge('learner-records','usersim','records','Public trajectory / activations','telemetry',['usersim.finalize','records.read']),
  edge('records-checks','records','checks','Saved replies + frozen facts','telemetry',['checks.evaluate']),
  edge('records-helix','records','helix','Evaluation input / results','telemetry',['helix.evaluate'],{managed:true}),
  edge('input-guard','usersim','guardrails','Public input / checked reply','request',['guardrails.check'],{guard:true}),
  edge('guard-advisor','guardrails','fabric','Allowed message / output check','request',['guardrails.check'],{guard:true}),
  edge('supervisor-workload','openshell','fabric','Enforced workload boundary','control',['openshell.create','openshell.execute','openshell.probe']),
  edge('platform-supervisor','platform','openshell','Managed deployment / session','control',['platform.register','platform.session'],{managed:true}),
];
export function edgesFor(scenario:string) {
  const p=preset(scenario);
  return architectureEdges.filter(e=>(!e.guard||p.guardrails)&&(!e.routed||p.routing==='switchyard')&&(!e.managed||p.helix)
    && !(p.guardrails&&['learner-advisor','advisor-learner'].includes(e.id)));
}
export function lessonsUsing(component:string,scenario:string) {
  return lessonIds.filter(id=>lessonFor(scenario,id).operations.some(op=>operationById[op].component===component));
}
