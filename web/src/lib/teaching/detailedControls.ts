import type {TeachingPage} from './types';

export function controlLibraries(scenario:string):Record<string,TeachingPage> {
  const retail=scenario==='dreamjob', rails=scenario!=='photography';
  return {
    routing:{title:'NeMo Switchyard',intro:retail
      ? 'Switchyard selects a deployment within LiteLLM’s candidate group. It changes the model-selection policy for the same advisor request; it is not another learner, agent harness or mandatory conversation hop.'
      : 'This scenario uses a fixed model route and does not invoke Switchyard. Its answer can still pass through LiteLLM, but alias dispatch alone is not routing optimization.',sections:[
      {paragraphs:[
        'The application plugin delegates two-candidate groups to the pinned StageRoutingPlugin. Fixed one-candidate groups bypass that selection stage. Policy settings describe when an efficient candidate may be selected or escalated; native decision metadata and the actual provider model establish what happened on a request.',
        'The [[url:https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md|pinned LiteLLM integration]] is the upstream contract. The experiment controls public messages, frozen catalogue and harness while comparing fixed/routed policies within one inventory. A separate capable-model access condition tests serving; it does not prove that the policy selected that model or improved answer quality.'
      ]}
    ]},
    relay:{title:'NeMo Relay',intro:'Relay instruments execution at the selected harness. Its parent-linked scopes reveal observed agent, model and tool activity. The application’s public conversation, lifecycle records and call accounting answer related questions, but they are different evidence sources.',sections:[
      {paragraphs:[
        'The [[url:https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/about-nemo-relay/architecture.mdx|Relay 0.11.1 architecture]] separates instrumentation from event processing/export. In this integration Fabric attaches the native observability configuration to the adapter. The application reads the resulting ATOF file stream and publishes a bounded projection.',
        'No collector-backed Phoenix or OTLP dashboard is configured for these recordings. Parent UUIDs can establish relationships that were actually captured; a gateway call ID cannot be converted into a native span ID by guesswork. Relay’s optional middleware features are also separate from the Guardrails checks and OpenShell enforcement used here.'
      ]}
    ]},
    records:{title:'Recorded evidence',intro:'This is application infrastructure for reviewing a completed experiment. It selects one curated demo for the chosen scenario and opens its immutable, sanitized evidence. Reading it never drives UserSim, invokes Fabric or deploys an agent.',sections:[
      {paragraphs:[
        'A native capture preserves a boundary object or event. A public projection omits private fields. A teaching companion interprets a selected subset without turning it into a new runtime input. Keeping those roles explicit lets you review the implementation without mistaking a friendly summary for the complete SDK payload.',
        'Manifest-bound, scenario/run-specific reads prevent accidental cross-scenario evidence or arbitrary local-file access. This adds a little publication machinery, but it gives code review a stable reference while raw profiles, prompts and unpresented model proposals remain private. Future live-run directory browsing is outside this recorded guide.'
      ]}
    ]},
    checks:{title:'Application assertions',intro:retail
      ? 'Retail defines deterministic criterion inputs in application code and scores them through Helix, rather than invoking the standalone photography/board-games assertion path represented by this block. The distinction is between the rule’s definition and the selected scoring mechanism.'
      : 'These are deterministic tests of the saved application behaviour. They compare explicit public requirements and returned facts with the delivered reply. Their purpose is to make a small set of failures reproducible, not to certify every semantic claim in an answer.',sections:[
      {paragraphs:[
        'Photography checks budget/schedule grounding, source use and uncertainty. Board games checks the original play goal and honest no-match handling. These functions belong to our application; neither executing them nor saving a fraction makes them a UserSim evaluator or a native Guardrails policy.',
        retail
          ? 'Retail extracts its own criterion inputs and uses Helix to score them. The underlying application checks still have explicit coverage limits. Native model proposal findings remain separate from the source-only response delivered by the application.'
          : 'UserSim’s in-loop helpfulness judgement can disagree with these assertions because it asks a different question. A reply can respect the catalogue and still offer weak guidance. Retaining that disagreement is more useful than deleting the judge warning or broadening a narrow pass claim.'
      ]}
    ]},
    helix:{title:'Helix evaluation',intro:retail
      ? 'Helix evaluates saved criterion data in this part of the lab. Its broader platform also manages agents, deployments and sessions, which have their own operational lifecycle. Evaluation is therefore one connected use of Helix, rather than its entire role.'
      : 'This preset uses application assertions and does not invoke Helix evaluation. The retail preset introduces native local scoring and a separately submitted durable evaluation job over saved criterion data.',sections:[
      {paragraphs:[
        'Our application defines expected and observed values from saved replies, facts and execution records. The compatible local Helix Evals SDK runs ExactMatchMetric over those values. A durable Platform job submits the same kind of saved dataset through a separate API. Neither path regenerates the learner conversation.',
        'The [[url:https://docs.nvidia.com/nemo-helix/v0.10/documentation/home|Helix platform architecture]] and [[url:https://docs.nvidia.com/nemo-helix/v0.9/documentation/evaluate-models|evaluation workflow]] explain the surrounding services. Running a narrow deterministic criterion through Helix does not expand its coverage into universal semantic validation. Definition, scoring, job submission and terminal result remain distinct states.'
      ]}
    ]},
    guardrails:{title:'NeMo Guardrails · input / output',intro:rails
      ? 'Guardrails evaluates the public input/output at an application boundary using explicitly configured rails. Here the native Colang engine executes small deterministic actions for credential-disclosure requests, credential-shaped output and selected employment assurances. The application owns the meaning of those rules.'
      : 'Photography does not load native Guardrails. Its instructions, course-only tools and application assertions are still useful controls, but they must not be labelled as executed Guardrails decisions.',sections:[
      {paragraphs:[
        'The [[url:https://docs.nvidia.com/nemo/guardrails/v0.24.1/about-nemo-guardrails-library/how-it-works|Guardrails architecture]] allows different rail types and model-based checks. This integration selects input/output rails through check_async and performs no model generation inside the checker. A pass covers those configured patterns only.',
        retail
          ? 'Baseline/comparison rails run inside their application sandbox. The separate Helix-managed condition checks input/output at its host caller boundary. Source-only retail rendering is another application policy; output rails must permit that candidate before it becomes a confirmed public delivery.'
          : 'The legitimate board-games conversation and the credential-disclosure negative probe are separate conditions. Keeping their purposes distinct demonstrates a policy rejection without making the normal learner appear malicious. OpenShell network/filesystem denial remains an operational control, not a behavioural rail.'
      ]}
    ]},
    platform:{title:'Helix managed operations',intro:retail
      ? 'The managed condition asks Helix to register the application package, create a deployment, open a session, invoke it and clean up the condition-owned resources. This control plane operates outside the advisor process; OpenShell contains the deployed workload.'
      : 'This preset starts its own standalone OpenShell workload and does not register or deploy through Helix. Managed agent operations are introduced by retail as a separate condition, rather than being inferred from ordinary local Fabric execution.',sections:[
      {paragraphs:[
        'The [[url:https://docs.nvidia.com/nemo-helix/v0.10/documentation/agents/deploy-agents|Helix deployment workflow]] separates the agent recipe, deployment and session. Registering a recipe is not the same as starting a session; reaching the Platform API is not proof that the requested executor or provider works.',
        'Our managed recipe contains application code, frozen course facts and a public constraint channel, not the private simulator persona. It starts fresh session memory with an explicitly selected public request. The test therefore demonstrates managed execution without pretending to resume the local three-turn conversation’s internal state.',
        'An older Docker-based deployment trial could not reach the host’s Helix and model-admission services, so it never produced a verified advisor invocation. That preserved transport failure concerns the separate Docker deployment path; it does not describe the OpenShell conditions reviewed here.'
      ]}
    ]},
    openshell:{title:'OpenShell · trusted supervisor',intro:'OpenShell enforces an execution boundary around the advisor, selected harness and course tools. Its trusted supervisor mediates the workload’s access to files/processes and network destinations. UserSim and the credentialed provider gateway remain host-side in the standalone application path.',sections:[
      {paragraphs:[
        'The [[url:https://docs.nvidia.com/openshell/v0.1.6/about/architecture|OpenShell 0.1.6 architecture]] distinguishes the sandboxed workload from the trusted machinery enforcing policy. Our policy permits a narrow model bridge and designated writable artifacts instead of giving the agent general provider credentials or unrestricted egress.',
        retail
          ? 'Retail uses both a standalone sandbox for the baseline/comparisons and a separate Helix-managed OpenShell deployment. Their owners, identities and cleanup receipts must remain separate. A baseline probe cannot establish the managed policy’s enforcement.'
          : 'The standalone application owns creation and exact-resource cleanup. This boundary adds setup and transport complexity, but policy failure stops execution rather than depending on the model to obey a request not to access a file.'
      ]}
    ]}
  };
}

export function controlOperations(scenario:string):Record<string,TeachingPage> {
  const retail=scenario==='dreamjob', rails=scenario!=='photography';
  return {
    'routing.policy':{title:'Load candidates and routing policy',intro:retail
      ? 'A routing experiment starts with an explicit inventory and decision policy. This integration keeps two candidate deployments in the routed alias while retaining single-deployment fixed aliases for controlled comparisons.'
      : 'Routing optimization is not performed in this preset. The fixed route avoids changing the model while testing the basic citizen-advisor behaviour; no Switchyard decision should be expected in its logs.',sections:[
      {paragraphs:[
        '[[call:routing.policy|LabRoutingPlugin]] constructs StageRoutingPlugin with efficient_first, confidence_threshold=0.5, recent_window=3 and only_on_wrong_signal_escalation enabled. It delegates only a two-distinct-candidate group; a one-candidate alias is fixed dispatch and any other candidate count is rejected.',
        '[[cap-run:CAP-SW-01|The recorded routing configuration]] binds policy to the observed proxy inventory. The selected replacement pool uses MiniMax as efficient and Mistral as capable, with different provider reasoning settings kept equal between each model’s fixed/routed deployment. Historical Gemma/GLM probes are labelled historical access diagnostics, not verification of this inventory.'
      ]}
    ]},
    'routing.decision':{title:'Decide, dispatch and retain the decision',intro:retail
      ? 'At request time, Switchyard’s stage operates inside the LiteLLM routing integration. It chooses among the configured deployments and returns decision signals; LiteLLM then dispatches the request. The application does not substitute its own local if/else model picker and call that a native decision.'
      : 'No candidate selection is executed for this fixed-route preset. The native decision mechanism below belongs to the retail experiment; its decisions and comparison records must not be borrowed to explain this scenario’s model calls.',sections:[
      {paragraphs:[
        '[[call:routing.decision|The stage.run call]] receives the native routing context. The response callback extracts bounded scalar decision metadata and returns it in a dedicated evidence header. The host gateway saves that decision beside the actual selected model and request accounting, without exporting the model prompt or request patch.',
        '[[cap-run:CAP-SW-02|The comparison outcomes]] separate fixed-candidate, switchyard, capable-access and the different-inventory diagnostic conditions. Compare execution, cleanup, criterion results and actual selected models within the same pool. Choosing the efficient model repeatedly can be a valid observed policy outcome; installation, a plugin setting or a successful capable-access probe is insufficient proof of a routed choice.'
      ]}
    ]},
    'relay.configure':{title:'Attach native observability',intro:'Observability must attach before the harness executes. The application supplies Relay settings through Fabric, so the maintained adapter instruments its own agent/model/tool lifecycle. Relay is attached to that work rather than inserted as a separate model-request hop.',sections:[
      {paragraphs:[
        '[[call:relay.configure|config.enable_relay]] selects observability version 4, disables full payloads and enables an append-only ATOF file sink under the run’s fabric-traces directory. The pinned adapter also needs the generated fabric-relay.json path passed through its environment; attaching another independent tracer would risk duplicate instrumentation.',
        '[[cap:CAP-REL-01|The effective Relay configuration]] is the configuration artifact for this operation. Actual events are a later output, not something a saved configuration proves. These demos do not configure an OTLP collector, so there is no corresponding Phoenix trace URL to supply.'
      ]}
    ]},
    'relay.scopes':{title:'Read parent-linked native scopes',intro:'The saved stream contains scope starts and ends. Pairing those native events reveals what completed, failed or remained incomplete, while their parent UUIDs identify the enclosing observed work. This is how the guide turns a raw event stream into an execution tree.',sections:[
      {paragraphs:[
        '[[call:relay.scopes|relay_scopes]] groups by native UUID and category, pairs start/end events, computes recorded duration and keeps missing-parent/incomplete-scope notices. The reader is application code; it does not invent missing parent events or rerun the operation to obtain a cleaner trace.',
        retail
          ? '[[file:relay-scopes.json|The public tree]] is a sanitized projection of [[cap:CAP-REL-02|the private native stream]]. Gateway accounting remains a separate identity space. For an application-only clarification there is deliberately no native agent span to display; run-wide context must not be presented as that turn’s execution.'
          : '[[file:relay-scopes.json|The public tree]] is a sanitized projection of [[cap:CAP-REL-02|the private native stream]]. Use the observed parent chain to follow model/tool nesting. Gateway accounting remains a separate identity space, and a run-wide tree must not be relabelled as proof of a selected turn without an attributable boundary.'
      ]}
    ]},
    'relay.tools':{title:'Inspect actual tool inputs and outputs',intro:'A tool event provides the important bridge between a public recommendation and the catalogue facts behind it. The advisor saying “I searched” is not evidence of execution; the native paired tool scope is.',sections:[
      {paragraphs:[
        '[[call:relay.tools|native_tool_records]] selects observed tool scopes and decodes the native result envelopes. It retains the tool name, arguments, scope UUID, status and returned domain data. The guide may associate scopes with an invocation only where the captured boundary establishes that relationship.',
        'Read [[file:native-tools.json|the decoded tool evidence]] according to the called function: search returns matches/exclusions, details returns one course and comparison returns a list. A completed MCP exchange can still carry invalid_input, and an empty successful search is an honest no-match.',
        ...(retail?['The separately managed Helix condition uses native Intake span IDs in platform-trace.json. Those identify a different session and evidence source; they cannot be joined to the local baseline’s Relay tree by similar tool names.']:[])
      ]}
    ]},
    'records.read':{title:'Verify and open this scenario’s recording',intro:'The guide opens the exact curated pack selected for this scenario. It verifies the pack’s identity and manifest-bound files before reading them, so a missing retail result cannot fall back to a photography recording.',sections:[
      {paragraphs:[
        '[[call:records.read|The recording reader]] accepts canonical run IDs and manifest-listed filenames, checks scenario/run identity and hashes, and refuses symbolic or arbitrary file paths. The companion has its own manifest and references the same recording. This is file inspection, with no execution service involved.',
        '[[file:run.json|The run record]] identifies the experiment, while [[file:runtime-receipt.json|the startup receipt]] identifies the contained runtime. Public conversation, native projections, application-only delivery receipts and comparison/managed evidence keep distinct roles. Private artifacts can be reported as privately available without exposing a filesystem path or their original contents.'
      ]}
    ]},
    'checks.evaluate':{title:'Compare expected and observed behaviour',intro:retail
      ? 'Retail does not invoke the standalone assertion runner shown by this block. Its criteria are extracted by application code and scored through Helix. This keeps criterion meaning separate from the scoring API and avoids presenting two labels as two independent validations.'
      : 'Evaluation starts from explicit questions about the answer, rather than from its transport status. For each criterion, the application computes an observed value from saved replies, course facts and attributable execution, then records the expected value, reason and coverage.',sections:[
      {paragraphs:[
        scenario==='boardgames'
          ? '[[call:checks.evaluate|The board-games assertions]] check that the original play goal is retained, the follow-up is distinguished from video-game design and a valid native search supports the no-match. A fluent but invented board-game course should not pass simply because two turns completed.'
          : retail
            ? 'Retail’s application-derived criterion inputs are scored in the Helix path. This standalone assertions block is used by photography/board games; it is not a second independent semantic validator for the retail transcript.'
            : '[[call:checks.evaluate|The photography assertions]] examine source grounding, budget/day constraints, explicit unknowns and real native search evidence. This is deterministic saved-output checking, without another model call.',
        '[[file:evaluation.json|Criterion-level results]] explain what was tested and why a row passed or failed. Narrow phrase/ID/URL checks cannot prove all financial or educational reasoning correct. Keep UserSim’s helpfulness flags separately visible: agreement with the catalogue and helpful conversation are related but different outcomes.'
      ]}
    ]},
    'helix.evaluate':{title:'Define, run and inspect evaluation',intro:retail
      ? 'The application first extracts explicit criterion values from the saved retail interaction. Helix then scores those values through its real evaluation SDK. This separates the meaning of a test from the engine that computes and stores its score.'
      : 'No Helix scoring is invoked for this preset. Its saved assertions remain application results. The native evaluation mechanism below is used for retail, without re-running the conversation.',sections:[
      {paragraphs:[
        '[[call:helix.evaluate|The isolated evaluator]] creates ExactMatchMetric with reference/candidate templates pointing to item.expected and item.output, then calls Evaluator.run_sync with the saved rows and RunConfig(parallelism=1). [[cap:CAP-HX-02|The evaluator settings]] preserve those actual metric/configuration values; they are not model-generation prompts.',
        '[[cap:CAP-HX-01|Criteria and native row scores]] connect each application criterion ID to its Helix result and any metric error. The delivered response’s checks and the native proposal’s rule findings are separate. Exact agreement on an extracted boolean proves that criterion, not general correctness of the original prose.'
      ]}
    ]},
    'helix.job':{title:'Submit and inspect a durable evaluation job',intro:retail
      ? 'The durable path sends saved criterion data to Helix Platform instead of computing only in the local process. It demonstrates job submission, observation and persisted results while keeping the conversation itself fixed.'
      : 'This preset submits no durable Helix evaluation job. The managed scoring path below belongs to retail, where it demonstrates job submission and observation over already saved criterion values without generating another conversation.',sections:[
      {paragraphs:[
        '[[call:helix.job|The job client]] constructs the same ExactMatchMetric/RunConfig shape, creates an Evaluator from the Platform client and submits the bounded dataset. It records the submitted definition before waiting for a terminal status, with separate pending/job time bounds and cancellation handling. Submission alone is not a completed evaluation.',
        '[[cap:CAP-HX-03|The job configuration and outcome]] show the dataset binding, native job identity, status and returned score/error. This job has no generation target and makes no inference calls. A failed job stays failed even if local scoring over the same rows succeeded.'
      ]}
    ]},
    'guardrails.check':{title:'Load policy, check and return a decision',intro:rails
      ? 'The application sends public text to an isolated native Guardrails worker at the selected input or output boundary. The worker executes the configured Colang flow and deterministic action, then returns the native decision. If the checker fails or the required action does not execute, the application refuses unchecked continuation.'
      : 'Native Guardrails is unused in photography. Its policy files may exist in the repository for other presets, but there is no photography decision to infer from their existence.',sections:[
      {paragraphs:[
        '[[call:guardrails.check|LLMRails.check_async]] receives only public messages and the explicitly selected INPUT or OUTPUT rail type. RailsConfig is built from [[call:guardrails.config|config.yml]] and rails.co; the application registers the named credential/assurance actions. [[cap:CAP-GR-01|The effective policy capture]] preserves the loaded YAML/Colang and execution location. There is no model call inside these rules.',
        '[[cap:CAP-GR-02|Native decisions and the separate negative probe]] show status, executed action and purpose. An input credential-disclosure block is not the same test as a legitimate course conversation passing. In retail, a validated presentation candidate becomes delivered only after output rails pass; a blocked candidate must not be acknowledged to the next turn as though the learner saw it.'
      ]}
    ]},
    'platform.register':{title:'Register and deploy the application',intro:retail
      ? 'The managed path turns a packaged advisor into a named Helix deployment. Packaging, registration and deployment are separate transformations: the recipe defines the agent; registration stores that definition; deployment selects where it will execute.'
      : 'This preset does not register a Helix deployment. Its standalone runtime is created directly through OpenShell, so the following managed operation belongs to the retail extension.',sections:[
      {paragraphs:[
        '[[call:platform.register|The registration bridge]] loads the final agent.yaml, validates AgentConfig and translates it through the maintained agent plugin before registration. Unlike the local Fabric snapshot, this YAML is an actual declarative input that is translated into Fabric configuration. [[cap:CAP-PLAT-02|The submitted agent recipe]] and [[cap:CAP-PLAT-04|registration/package receipts]] identify the prepared code, model/tool setup and frozen catalogue.',
        '[[call:platform.deploy|Deployment creation]] selects the condition-owned environment and OpenShell execution mode, then waits for native readiness. [[cap:CAP-PLAT-01|Effective client/executor settings]] and [[cap:CAP-PLAT-03|provider/environment setup]] explain the surrounding connection. The image contains no private persona; a reachable server or successful registration alone does not establish a running sandbox.'
      ]}
    ]},
    'platform.session':{title:'Open a session, invoke and clean up',intro:retail
      ? 'A deployment can serve multiple sessions, so the managed condition opens its own fresh session and binds every invocation and trace read to that identity. It sends a developer-selected public request with the already explicit spending/weekend constraints, rather than replaying private local memory.'
      : 'No Helix session is opened by this standalone preset. The managed lifecycle below belongs to retail and must retain its own session, invocation and cleanup records, rather than treating this scenario’s local runtime as a managed session.',sections:[
      {paragraphs:[
        '[[call:platform.session|The session bridge]] creates the session and invokes the deployment. The caller validates the native reply, obtains complete native Intake tool evidence for that exact session, builds the application-owned source response and runs output checks before confirming delivery. [[file:platform-invocation.json|The invocation projection]] distinguishes that public response from the unpresented native proposal.',
        '[[cap:CAP-PLAT-05|Session operations and cleanup]] retain requests/results, native session identity and exact-resource removal. The provider, environment, deployment and any newly owned registration are tracked before mutation so interrupted creation can be recovered. Ending the inspector is not a cleanup operation; lifecycle ownership stays with the managed runner.'
      ]}
    ]},
    'openshell.create':{title:'Create the sandbox with policy',intro:'Creation asks the trusted OpenShell supervisor to start a condition-owned workload under an explicit policy. The application saves the intended resource identity before the request, because a cancelled or timed-out create operation may still have created a real resource.',sections:[
      {paragraphs:[
        '[[call:openshell.create|NativeSandbox creation]] submits the selected image and [[cap:CAP-OS-01|requested policy YAML]], with ownership labels and automatic provider injection disabled. It then reads the sandbox identity and loaded policy from native operations. The policy permits designated read-only paths, writable workspace/tmp paths and the narrow loopback model bridge.',
        retail
          ? '[[cap:CAP-OS-02|Effective policy and sandbox identity]] describe what loaded, rather than merely what the source policy intended. For the separate managed condition, Helix owns creation and [[cap:CAP-OS-03|its managed enforcement records]] must be inspected independently. Supervisor trust and sandbox workload access are different sides of this boundary.'
          : '[[cap:CAP-OS-02|Effective policy and sandbox identity]] describe what loaded, rather than merely what the source policy intended. Supervisor trust and sandbox workload access are different sides of this boundary. This standalone preset supplies no Helix-managed creation receipt.'
      ]}
    ]},
    'openshell.execute':{title:'Execute the advisor and course tools inside',intro:'The advisor, persistent selected harness and course MCP subprocess must execute inside the enforced boundary for the conversation. Running only a wrapper inside OpenShell while calling an unrestricted host agent would not demonstrate that containment.',sections:[
      {paragraphs:[
        '[[call:openshell.execute|The native exec transport]] starts learning_lab.sandbox_runtime through a persistent duplex channel. Public messages enter that runtime; model requests cross the authenticated bridge to the host gateway, where provider credentials remain. Course tools read the copied frozen catalogue and public preference channel inside the workload.',
        '[[file:runtime-receipt.json|The runtime receipt]] identifies the running image and source manifest before inference. [[file:native-tools.json|Native course operations]] demonstrate business work, while bounded native artifact export retains settings/results before teardown. Helix-managed execution uses its deployment/session transport instead of claiming that the standalone exec process ran there.'
      ]}
    ]},
    'openshell.probe':{title:'Verify allowed/denied operations and cleanup',intro:'Enforcement verification tests the loaded boundary, then confirms that condition-owned resources were removed. Successful course work proves a permitted path; a policy file by itself proves neither that path nor a denied operation.',sections:[
      {paragraphs:[
        '[[call:openshell.probe|The native probe]] attempts a world-readable file outside the permitted policy and an unrelated network destination. Only permission-denial evidence counts as a demonstrated denial; a generic timeout or missing destination is insufficient. [[file:boundary-probes.json|The probe receipt]] preserves each observation separately from the legitimate conversation.',
        retail
          ? '[[file:cleanup.json|Standalone cleanup]] records runtime/process termination and native resource absence by exact identity. The managed variant uses [[cap:CAP-OS-03|its own policy/probes/cleanup]] under Helix ownership. A reply may be correct while cleanup fails, so these operational results must not disappear into an overall answer score.'
          : '[[file:cleanup.json|Standalone cleanup]] records runtime/process termination and native resource absence by exact identity. A reply may be correct while cleanup fails, so these operational results must not disappear into an overall answer score. Inspectors read those receipts without gaining ownership of the running resource.'
      ]}
    ]}
  };
}
