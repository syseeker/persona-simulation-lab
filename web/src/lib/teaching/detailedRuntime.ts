import type {TeachingPage} from './types';

export function runtimeLibraries(scenario:string):Record<string,TeachingPage> {
  const board=scenario==='boardgames', retail=scenario==='dreamjob';
  return {
    fabric:{title:'NeMo Fabric',intro:'Fabric is the application’s common agent interface. It accepts a typed configuration, resolves the chosen adapter, manages an agent runtime and returns a normalized result. The actual reasoning and tool loop belongs to the selected harness behind that adapter.',sections:[
      {paragraphs:[
        board
          ? 'This preset selects Hermes. The application still uses the same Fabric configuration, planning, startup and invoke call sites used by Deep Agents; the adapter ID, interpreter and harness-specific settings change. This is the concrete benefit of the adapter contract, rather than a claim that the two harnesses behave identically.'
          : 'This preset selects LangChain Deep Agents through its maintained adapter. Keeping the application at Fabric’s interface makes a later harness comparison possible without writing a second outer conversation driver.',
        'The [[url:https://docs.nvidia.com/nemo/fabric/v0.6.1/about-nemo-fabric/overview|Fabric 0.6.1 architecture]] separates configuration normalization, execution lifecycle and result normalization. Those are SDK responsibilities. Our source selection, course policy, call budget, public-answer validation and saved evidence remain application responsibilities. A common interface reduces coupling while still requiring adapter-specific testing.'
      ]}
    ]},
    harness:{title:board?'Hermes':'LangChain Deep Agents',intro:board
      ? 'Hermes performs the advisor’s model/tool conversation behind Fabric’s adapter. The board-games test uses one persistent runtime for the two public turns, so the follow-up can refer to the original goal. This demonstrates conversation continuity, not a scheduled companion or cross-session memory system.'
      : 'LangChain Deep Agents performs the advisor’s inner model/tool loop behind Fabric’s adapter. In this application its useful task is to inspect the public request, call bounded course tools and use their returned facts to form a reply.',sections:[
      {paragraphs:[board
        ? 'The [[url:https://hermes-agent.nousresearch.com/docs/|Hermes documentation]] describes broader memory, skills and automation capabilities. This preset deliberately exposes only the course MCP toolset, disables deferred tool search and disables its additional recovery ladder. We do not claim that long-term memory, scheduling or unrelated built-in skills ran.'
        : 'The [[url:https://docs.langchain.com/oss/python/deepagents/overview|Deep Agents architecture]] includes planning, filesystem context and subagents. Those available features are not evidence that this demo used them: the application restricts the model-facing tool surface and execution allowlist to the three course tools.',
        retail
          ? 'Retail also separates the native model proposal from the delivered response. When required budget or study days are missing, the application asks for clarification before invoking the harness. Otherwise a genuine native result and its returned course facts feed the application’s source summary. These separate paths prevent a direct clarification or corrected public answer from being mistaken for native model behaviour.'
          : 'The tradeoff is deliberate: a narrow harness surface is easier to review and constrain, but this example cannot establish how the harness would perform as an unrestricted general-purpose assistant.'
      ]}
    ]},
    mcp:{title:'Course MCP',intro:'MCP gives the harness a typed, read-only interface to our catalogue. The application implements the tool functions; the maintained agent adapter connects them to the harness. The protocol transports requests and results, while our domain code decides what counts as a valid search or course.',sections:[
      {paragraphs:[
        'The server exposes search_courses, get_course_details and compare_courses. It cannot enrol the learner, browse arbitrary sites, change listings or retrieve private persona fields. Explicit public constraints override conflicting model arguments, so the model cannot quietly relax the stated spending limit or study days.',
        'The [[url:https://modelcontextprotocol.io/docs/learn/architecture|MCP architecture]] explains client/server discovery and invocation. In this lab the stdio server runs inside the same OpenShell workload as the harness. A discovered tool is merely available; only its actual request and returned domain result demonstrate use.'
      ]}
    ]},
    gateway:{title:'Application inference gateway',intro:'The gateway is our application’s model boundary. It accounts for each model attempt, limits output and tool work, filters the provider-visible schemas and forwards requests using host-side credentials. It is not a NeMo SDK component and its restrictions are not guarantees supplied by the model proxy.',sections:[
      {paragraphs:[
        'Separating learner, advisor, judge and Designer roles makes usage understandable. A single agent turn can require several model attempts, while an application-only clarification requires none. Recorded usage may be unknown; a missing token count must not be rewritten as zero.',
        'The [[call:models.admit|gateway implementation]] owns the 120-attempt workload cap, 1,024-token ceiling and four tool rounds per advisor turn. Bounded HTTP-429 recovery is an explicit comparison-call setting; other paths retain the default of no application retry. Relay records execution structure separately, so gateway call IDs are not automatic native trace-span joins.'
      ]}
    ]},
    litellm:{title:'LiteLLM proxy',intro:'LiteLLM maps an application alias to a configured provider deployment. That lets the advisor use one OpenAI-compatible model endpoint while the operator controls which hosted model sits behind it. The alias is a logical name, not proof of the model that actually answered.',sections:[
      {paragraphs:[
        retail
          ? 'The baseline and support aliases remain separate from the retail comparison pool. The selected replacement comparison inventory assigns MiniMax M3.1 Flash the efficient role and Mistral Large 4 the capable role. Their per-deployment reasoning settings live in proxy configuration, and the application omits a shared reasoning override for those comparison aliases.'
          : 'This scenario uses a fixed advisor route and a separate fixed support route for simulator/judge work. A proxy can expose several aliases without this particular application optimizing among them.',
        'The [[url:https://docs.litellm.ai/docs/proxy/configs|LiteLLM configuration model]] describes aliases, deployments and environment-backed provider settings. Loaded YAML plus resolved nonsecret settings show the actual deployment inventory; a current source template alone cannot establish what a historical process loaded.'
      ]}
    ]}
  };
}

export function runtimeOperations(scenario:string):Record<string,TeachingPage> {
  const board=scenario==='boardgames', retail=scenario==='dreamjob';
  return {
    'fabric.config':{title:'Build the typed FabricConfig',intro:'build_config creates the actual installed Fabric SDK object that planning and startup consume. It is not an application-specific JSON document that another function later translates into Fabric. Its nested classes validate related settings inside one object; they are not a sequence of processing stages.',sections:[
      {paragraphs:[
        `[[call:fabric.config|build_config]] selects ${board?'nvidia.fabric.hermes':'nvidia.fabric.langchain.deepagents'}, an OpenAI-compatible model connection, replacement system instructions, a writable local workspace and a chat-input/message-output contract. Discovery selects where descriptors may be found; actual adapter resolution belongs to planning. Constructing this object performs no conversation inference.`,
        `${retail?'The builder initially sets RuntimeConfig.timeout_seconds=120; the retail sandbox raises it to 600 before planning and startup, so the effective captured configuration contains timeout_seconds=600.':'This preset keeps RuntimeConfig.timeout_seconds=120 from the builder.'} RuntimeConfig.max_turns=24 bounds the internal agent loop, separately from this scenario’s ${retail?'three':board?'two':'one'} public learner turn${retail||board?'s':''}. ModelConfig specifies temperature zero and at most 1,024 output tokens; the gateway’s individual-request deadline is a separate control.`
      ],rows:[
        ['MetadataConfig / DiscoveryConfig','Name the agent and locate adapter descriptors; Hermes adds its compatible local descriptor directory.'],
        ['HarnessConfig / ModelConfig','Choose the adapter and harness settings; define the default provider, model alias, endpoint and credential environment-variable name.'],
        ['InstructionsConfig / InstructionConfig','Supply the application system policy in replacement mode. These are instructions, not private simulator persona input.'],
        ['EnvironmentConfig / RuntimeConfig','Set workspace and permitted environment bindings, then the input/output contract and internal execution bounds.'],
        ['ToolsConfig / MCP / Relay','Apply the global tool allowlist, register the catalogue stdio server and attach observability through the SDK’s configuration methods.']
      ]},
      {paragraphs:[
        '[[cap:CAP-FAB-01|The captured typed settings]] are serialized after construction for review. The public fabric-config.json is an allowlisted projection, and [[file:framework-config.json|framework-config.json]] is an additional teaching summary. Neither public file is loaded as runtime input or is a complete replay configuration. To change behaviour, change the builder or its explicit inputs, then inspect a new run’s effective settings.',
        board
          ? 'Hermes uses the mcp-catalogue selector, a compatible adapter interpreter and native reasoning/recovery settings. Those differences belong in configuration; they do not require a different application invoke contract.'
          : retail
            ? 'Comparison aliases omit a shared Deep Agents reasoning_effort so LiteLLM’s candidate-specific policies remain effective. The fixed baseline retains its own setting. Comparing those objects is more useful than assuming that one setting is valid for every hosted model.'
            : 'Deep Agents uses the three course function names as its execution allowlist. Provider-visible schema filtering is enforced separately by the gateway because the installed adapter can still advertise built-in tools.'
      ]}
    ]},
    'fabric.plan':{title:'Plan and check the runtime',intro:'Planning answers which adapter and capabilities Fabric resolves from the configuration. Doctor checks whether that planned runtime has the prerequisites to start. Keeping both before startup gives you a specific preparation error instead of discovering a missing dependency halfway through a conversation.',sections:[
      {paragraphs:[
        '[[call:fabric.plan|FabricTarget’s preflight]] calls Fabric.plan with the typed configuration and base directory, then awaits Fabric.doctor. The resolved descriptor and capability plan belong to the SDK; our code saves both reports and stops when Doctor returns fail.',
        '[[cap:CAP-FAB-03|The plan and Doctor reports]] let you compare the adapter identity, supported input/output contract and dependency findings. A pass establishes the inspected prerequisites, not successful model access or correct course advice. For Hermes, confirm the selected descriptor/interpreter rather than expecting the Deep Agents descriptor to appear.'
      ]}
    ]},
    'fabric.start':{title:'Start one persistent runtime',intro:'Startup turns the checked configuration into a reusable agent runtime. The runtime is kept open across this scenario’s public turns, so the next request can use the same conversation context. Creating a new runtime for each message would change the test’s memory behaviour.',sections:[
      {paragraphs:[
        '[[call:fabric.start|FabricTarget startup]] awaits Fabric.start_runtime and enters the returned runtime’s asynchronous context. Fabric and the selected adapter own their worker/harness setup; the application owns the surrounding OpenShell process, generated Relay configuration path and cleanup on failures.',
        '[[cap:CAP-FAB-04|The lifecycle/startup evidence]] distinguishes configuration saved, plan/preflight and runtime started. A startup receipt is the useful output here; the conversation and invocation results occur later. The explicit ADAPTER_PYTHON and Relay configuration path are compatibility requirements of the pinned integration, not universal requirements of every Fabric release.'
      ]}
    ]},
    'fabric.invoke':{title:'Invoke with a RunRequest',intro:'An invocation crosses from the application’s public conversation into the selected agent runtime. The same call works with Deep Agents or Hermes because Fabric’s adapter contract hides the harness-specific invocation mechanics.',sections:[
      {paragraphs:[
        '[[call:fabric.invoke|FabricTarget.reply]] creates RunRequest with the public input and relay_session_root, captures it, then awaits runtime.invoke(request=request). Public Preferences travel in the application’s explicit input channel; the original persona, simulator instructions and undisclosed overlay are excluded. The adapter translates the normalized request into its harness call.',
        retail
          ? 'Before this call, [[call:retail.response.clarify|the missing-constraint branch]] can produce a confirmed application-only clarification. That turn has no native request/result. The next genuine invocation acknowledges the previously delivered application response, because native harness memory also retains its unpresented proposal. Public turn and invocation sequence are therefore recorded separately.'
          : 'The runtime persists across the public turns. A RunRequest is the input to one agent invocation; it is not one provider call, because the harness may perform multiple model/tool exchanges before returning.',
        ...(retail ? ['For a standalone retail recommendation with a public budget and study days, [[call:retail.retrieval.arm|the application arms an initial search requirement]]. [[call:retail.retrieval.enforce|The gateway policy]] forces the first provider response to select search_courses through structured tool_choice; the harness must then execute the real MCP call. The requirement clears after a validated selection, so subsequent exchanges can finish normally within the existing tool limit. [[cap:CAP-MCP-02|The provider-visible schema/choice capture]] shows this application decision. It is not autonomous model tool selection, and the separate managed condition does not enable this policy.'] : []),
        '[[cap:CAP-FAB-05|The captured request boundary]] preserves the actual request fields with a public-safe projection. Match its public_turn and request ID to [[cap:CAP-FAB-06|the returned invocation record]]; do not match by array position when an application-only turn is present.'
      ]}
    ]},
    'fabric.result':{title:'Read the normalized RunResult',intro:'When invoke completes, Fabric returns a normalized RunResult containing runtime status, identities, output and available usage/error information. A successful runtime status says that execution completed; the application still has to decide whether the returned output is usable public advice.',sections:[
      {paragraphs:[
        '[[call:fabric.result|The result-handling code]] saves the complete boundary result before extracting result.output.to_dict() and its response. It stops for non-succeeded runtime status, empty/provider-error content or malformed tool-call text. These are different failure mechanisms from a valid answer that misses a course constraint.',
        retail
          ? '[[call:retail.response.render|RetailResponseBoundary.apply]] preserves the original proposal privately and prepares an explicitly application-owned source summary from validated returned course facts. Output Guardrails must pass before [[call:retail.response.confirm|confirm_delivery]] acknowledges that response. [[cap:CAP-FAB-07|Presentation settings/decisions]] retain the generated policy and native-versus-delivered distinction. A source-summary pass is evidence about this delivery boundary, not a claim that the proposal obeyed every instruction.'
          : 'The public reply is the validated extracted response, while native tool scopes and gateway accounting remain separate evidence. Do not read an absent normalized usage field as zero or invent a tool call from a fluent answer.',
        '[[cap:CAP-FAB-06|The RunResult capture]] shows the SDK boundary. [[file:fabric-invocations.json|The invocation companion]] shows selected normalized fields and, when a proposal was not presented, its hash and the confirmed delivery hash instead of private proposal text.'
      ]}
    ]},
    'harness.context':{title:'Connect instructions and course tools',intro:board
      ? 'The Hermes adapter receives the application’s policy, model connection and course MCP toolset. Its compatible managed configuration is important: the small three-tool application does not need deferred tool discovery or the harness’s wider recovery ladder.'
      : 'The Deep Agents adapter receives the application instructions, skill path, model connection and course MCP registration. This prepares the model’s context and tool access; it does not mean a planning tool, subagent or course lookup has already executed.',sections:[
      {paragraphs:[
        board
          ? '[[call:harness.context|The harness setup]] selects the Hermes environment and mcp-catalogue toolset. [[cap:CAP-HER-01|The run-bound managed/native YAML]] shows deferred tool search off, a single API attempt and disabled auto-recovery. [[cap:CAP-HER-02|Native adapter output]] is a separate record of the resolved harness settings.'
          : '[[call:harness.context|The MCP registration]] adds the three course tools and the runtime skill to the adapter’s context. [[cap:CAP-DA-01|The Deep Agents adapter settings]] show the selected policy. The installed adapter gates execution globally; our provider boundary additionally withholds built-in filesystem/subagent schemas.',
        'Instructions tell the advisor how to use evidence and express uncertainty; tool access determines what facts it can actually obtain. Keep those mechanisms separate when debugging: changing prompt wording cannot grant a missing MCP tool, and adding a tool cannot establish that the model used it.'
      ]}
    ]},
    'harness.loop':{title:'Run the model/tool loop and return a reply',intro:'Inside one Fabric invocation, the selected harness alternates between the model and permitted tools. A tool request is executed, its actual result is placed back in context and the model can answer or request another permitted operation. The outer application waits at the common Fabric call.',sections:[
      {flow:['Public request enters the selected harness','Model answers or requests a course tool','The permitted tool returns facts or a structured error','The harness continues or returns its reply']},
      {paragraphs:[
        `[[call:fabric.invoke|The application’s wait point]] remains the same for ${board?'Hermes':'Deep Agents'}. Harness-internal tool/model execution is SDK-owned, while the application gateway limits tool rounds and model attempts. This small course task does not demonstrate every planning, delegation or memory capability the harness offers.`,
        '[[file:native-tools.json|Observed tool requests/results]] and [[file:relay-scopes.json|native harness scopes]] establish which exchanges occurred. A successful tool result with an empty search is a valid result; an invalid_input payload is an argument problem that a bounded subsequent tool call may repair. Neither should be rewritten as a fabricated course match.'
      ]}
    ]},
    'mcp.connect':{title:'Connect and discover course tools',intro:'Connection gives the selected harness a real MCP client/server relationship before it can retrieve course facts. The application registers one named stdio server; the adapter owns launching/connecting it and presenting the discovered tool schemas to the harness.',sections:[
      {paragraphs:[
        '[[call:mcp.connect|add_mcp_server]] points catalogue at the project interpreter running learning_lab.course_mcp. Environment settings supply the frozen catalogue path and the public-preferences channel. The server’s actual tools/list handler records discovery; it does not run an extra diagnostic client or a course search just to create evidence.',
        '[[cap:CAP-MCP-01|The connection settings]] explain where the server came from. [[cap:CAP-MCP-02|Discovery and provider-schema captures]] show two different surfaces: what the MCP client discovered and what our gateway actually exposed to the model. A schema appearing in discovery is not evidence of a business-tool call.'
      ]}
    ]},
    'mcp.search':{title:'Search using public constraints',intro:'A search converts a natural-language subject plus typed constraints into a deterministic shortlist from the frozen catalogue. The model chooses the query, but trusted public preferences prevent it from dropping the learner’s stated spending limit or study days.',sections:[
      {paragraphs:[
        '[[call:mcp.search|search_courses]] normalizes weekday names/numbers, validates Preferences and applies the trusted constraint channel before calling the matcher. Known fee/day conflicts are excluded; keyword overlap ranks the remaining records. Unknown fees or timetable remain explicit confirmation requirements rather than proof of fit.',
        'The [[cap:CAP-MCP-03|actual request/result]] must be read by domain shape: matches contains course records, matched terms and confirmation notes; excluded explains filtered entries. An empty successful matches list means no supported match. error_kind=invalid_input means invalid arguments, even when that payload also contains an empty matches list.',
        retail
          ? '[[cap:CAP-MCP-04|Per-invocation public preferences]] show when the explicit budget and weekend days entered the tool boundary. Salary-only clarification has no native search, and salary must never become a numeric budget.'
          : board
            ? 'The shortlist is a reproducible catalogue search, not an open-web search. Refusing to equate a video-game design course with learning to play is a legitimate outcome of this bounded source.'
            : 'The public photography constraints remain authoritative even when the model uses a broader search phrase. A returned listing with unknown material fees still needs that uncertainty explained; the base course price alone cannot establish a confirmed total.'
      ]}
    ]},
    'mcp.details':{title:'Retrieve one course’s details',intro:'The details tool resolves a known course ID to its complete frozen record. This is useful when the advisor needs the exact fee, duration, prerequisites or source URL after identifying an option. It is not a second relevance search.',sections:[
      {paragraphs:[
        '[[call:mcp.details|get_course_details]] retrieves the stable ID and adds constraint notes based on the current public preferences. Its result is a course object with fields directly on that object. It does not wrap that record in a matches list, so a generic matches-only viewer would misread a valid details result.',
        '[[cap:CAP-MCP-03|The native tool evidence]] shows whether details was actually invoked and which fields came back. A returned record can describe an option that exceeds the budget; the constraint note and public answer must explain that conflict. Unknown intake or funding eligibility stays unknown even when the fee is known.'
      ]}
    ]},
    'mcp.compare':{title:'Compare supported options',intro:'Comparison retrieves two or three distinct known course IDs so the advisor can discuss their published differences. It does not invent a ranked option or convert a learner’s aspiration into an employer requirement.',sections:[
      {paragraphs:[
        '[[call:mcp.compare|compare_courses]] validates the number and uniqueness of IDs, then returns each course’s details and constraint notes. The domain result is a list of course records, sometimes nested in the MCP text-content envelope. Decode that envelope before interpreting the records; an absent matches field is expected for this tool.',
        'Use [[cap:CAP-MCP-03|the actual comparison result]] to distinguish known duration/fee differences from missing information. A course with an unknown duration cannot be labelled shorter merely because another listed programme is long. If this tool was only available and never called, its configuration establishes capability rather than an observed comparison.'
      ]}
    ]},
    'models.admit':{title:'Admit and bound each model call',intro:'Admission happens before the provider request, including any permitted rate-limit retry. It is the application’s control over how much work a test can perform, rather than an inference-time feature supplied by Fabric or LiteLLM.',sections:[
      {paragraphs:[
        '[[call:models.admit|Budget.admit and the gateway]] allocate a role-labelled attempt and refuse work once the shared 120-attempt cap is exhausted. The gateway caps output at 1,024 tokens, limits advisor tool rounds to four and filters provider-visible tool schemas. These limits are independent of UserSim’s public-turn limit and Fabric’s internal-turn setting.',
        '[[cap:CAP-GW-01|The effective gateway settings]] show which controls this condition enabled; [[cap:CAP-MCP-02|provider schema captures]] show the exposed/withheld tool surface. A schema filtered before dispatch and a forbidden returned tool call rejected after dispatch are distinct checks. Credentials remain on the host, outside the agent’s tools.'
      ]}
    ]},
    'models.request':{title:'Send the request and record usage',intro:'Dispatch forwards an admitted request to the selected proxy/provider and records what happened. The requested alias, actual selected model, status, latency and usage help distinguish a serving failure from bad course advice or a failed policy check.',sections:[
      {paragraphs:[
        retail
          ? '[[call:models.request|Gateway.complete]] sends the bounded request with host-side credentials, captures safe status/rate-limit metadata and preserves failed attempts. SDK/provider retries are disabled. Requested-pool retail comparison calls enable at most two retries for HTTP 429 within a 300-second total request deadline. Their scheduled delays are 30 and 60 seconds; a valid Retry-After can extend a delay, but a required wait above 60 seconds or beyond the remaining deadline stops the call. Each retry consumes another admitted attempt; exhausted budgets and other failures stop. The baseline, managed condition and diagnostic pool retain a 50-second request deadline with application recovery disabled.'
          : '[[call:models.request|Gateway.complete]] sends the bounded request with host-side credentials and records safe provider status/error metadata before returning or raising. This preset keeps application recovery disabled as well as SDK/provider retries. A provider failure is preserved for diagnosis instead of repeatedly running until an answer appears.',
        '[[cap:CAP-GW-02|The call records]] retain logical request ID, attempt/retry linkage, selected model, usage and any native routing decision. An application-only clarification contributes zero inference calls. A gateway ID does not prove a Relay span relationship, and absent provider usage remains unknown rather than becoming a zero-cost claim.'
      ]}
    ]},
    'models.alias':{title:'Resolve alias and dispatch to provider',intro:'The alias separates the application’s model choice from provider credentials and deployment details. LiteLLM resolves that name against its loaded model_list and dispatches to the configured OpenAI-compatible hosted endpoint.',sections:[
      {paragraphs:[
        retail
          ? '[[call:models.alias|The retail alias definitions]] keep fixed-candidate and capable-access aliases separate from the two-deployment routed group. Fixed and routed versions of each candidate use the same per-model reasoning settings. The shared Fabric builder deliberately avoids overriding those candidate-specific settings.'
          : '[[call:models.alias|The proxy aliases]] map the fixed advisor and support roles to their configured deployments. This preset does not ask Switchyard to choose among candidates, so a completed proxy call is fixed dispatch rather than routing optimization.',
        '[[cap:CAP-LLM-03|Loaded YAML and resolved effective settings]] identify the configured process state without publishing credentials. Compare the requested alias to the selected model in [[file:usage.json|actual call accounting]]. A model appearing in inventory does not establish access, tool-loop completion or the quality of its response.'
      ]}
    ]}
  };
}
