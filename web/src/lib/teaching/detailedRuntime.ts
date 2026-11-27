import type {TeachingPage} from './types';

export function runtimeLibraries(scenario:string):Record<string,TeachingPage> {
  const board=scenario==='boardgames', retail=scenario==='dreamjob';
  return {
    fabric:{title:'NeMo Fabric',intro:'Fabric gives our application one way to configure and call different agent harnesses. We supply a FabricConfig, check the selected adapter and start a runtime. The application can then send a RunRequest and await a RunResult while the harness performs the model/tool work.',sections:[
      {paragraphs:[
        board
          ? 'This preset selects Hermes. The application still uses the same Fabric configuration, planning, startup and invoke call sites used by Deep Agents; the adapter ID, interpreter and harness-specific settings change. This is the concrete benefit of the adapter contract, rather than a claim that the two harnesses behave identically.'
          : 'This preset selects LangChain Deep Agents through its maintained adapter. Keeping the application at Fabric’s interface makes a later harness comparison possible without writing a second outer conversation driver.',
        'The [[url:https://docs.nvidia.com/nemo/fabric/v0.6.1/about-nemo-fabric/overview|Fabric 0.6.1 architecture]] separates configuration normalization, execution lifecycle and result normalization. Those are SDK responsibilities. Our source selection, course policy, call budget, public-answer validation and saved evidence remain application responsibilities. A common interface reduces coupling while still requiring adapter-specific testing.'
      ]}
    ]},
    harness:{title:board?'Hermes':'LangChain Deep Agents',intro:board
      ? 'Hermes is the harness that runs the board-game advisor. It sends requests to the model, executes permitted course tools and keeps context between the two public turns. Fabric’s adapter connects this loop to the application’s common invocation interface.'
      : 'Deep Agents is the harness that carries out the advisor’s model and tool conversation. It receives the public request, lets the model request a permitted course tool and returns a reply. Fabric’s adapter connects this loop to our application.',sections:[
      {paragraphs:[board
        ? 'The [[url:https://hermes-agent.nousresearch.com/docs/|Hermes documentation]] describes broader memory, skills and automation capabilities. This preset deliberately exposes only the course MCP toolset, disables deferred tool search and disables its additional recovery ladder. We do not claim that long-term memory, scheduling or unrelated built-in skills ran.'
        : 'The [[url:https://docs.langchain.com/oss/python/deepagents/overview|Deep Agents architecture]] includes planning, filesystem context and subagents. Those available features are not evidence that this demo used them: the application restricts the model-facing tool surface and execution allowlist to the three course tools.',
        retail
          ? 'Retail also separates the native model proposal from the delivered response. When required budget or study days are missing, the application asks for clarification before invoking the harness. Otherwise a genuine native result and its returned course facts feed the application’s source summary. These separate paths prevent a direct clarification or corrected public answer from being mistaken for native model behaviour.'
          : 'The tradeoff is deliberate: a narrow harness surface is easier to review and constrain, but this example cannot establish how the harness would perform as an unrestricted general-purpose assistant.'
      ]}
    ]},
    mcp:{title:'Course MCP',intro:'The agent needs a defined way to ask for course information. Our MCP server exposes three functions with typed inputs and results. The adapter connects the harness to that server, while our application code implements each catalogue operation.',sections:[
      {paragraphs:[
        'The server exposes search_courses, get_course_details and compare_courses. It cannot enrol the learner, browse arbitrary sites, change listings or retrieve private persona fields. Explicit public constraints override conflicting model arguments, so the model cannot quietly relax the stated spending limit or study days.',
        'The [[url:https://modelcontextprotocol.io/docs/learn/architecture|MCP architecture]] explains client/server discovery and invocation. In this lab the stdio server runs inside the same OpenShell workload as the harness. A discovered tool is merely available; only its actual request and returned domain result demonstrate use.'
      ]}
    ]},
    gateway:{title:'Application inference gateway',intro:'Before a model request reaches the proxy, our gateway checks that the application may make it. It applies the attempt and output limits, controls the tool schemas sent to the provider and records the result. These controls are application code, separate from Fabric and LiteLLM.',sections:[
      {paragraphs:[
        'Each admitted request gets a run-wide number and a role, such as learner, advisor, judge or Designer. The advisor’s first request can therefore be global call 3 because learner generation and a UserSim check happened first. One public reply may require several advisor requests; an application-written clarification requires none. Read role and public-turn context together before interpreting a call count.',
        'The [[call:models.admit|gateway implementation]] owns the 120-attempt workload cap, 1,024-token ceiling and four tool rounds per advisor turn. Bounded HTTP-429 recovery is an explicit comparison-call setting; other paths retain the default of no application retry. Relay records execution structure separately, so gateway call IDs are not automatic native trace-span joins.'
      ]}
    ]},
    litellm:{title:'LiteLLM proxy',intro:'LiteLLM lets the application request a model by an alias such as the fixed advisor route. Its loaded configuration maps that name to a provider deployment. We can change the deployment at this connection point without changing the citizen application’s invocation code.',sections:[
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
    'fabric.config':{title:'Build the typed FabricConfig',intro:'Prepare the settings Fabric needs before it can start an agent. Our build_config function creates the actual FabricConfig object accepted by the installed SDK. Its nested classes group related settings inside that object; they are not a sequence of processing stages.',sections:[
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
        'Fabric consumes the Python object we constructed. The application also serializes [[cap:CAP-FAB-01|its effective settings]] so we can inspect that decision later. The public fabric-config.json selects safe fields from that saved object; [[file:framework-config.json|framework-config.json]] is a shorter teaching summary. Neither public file is loaded as runtime input or provides a complete replay configuration. The code link shows where settings are supplied, while the JSON links show what the selected execution retained.',
        board
          ? 'Hermes uses the mcp-catalogue selector, a compatible adapter interpreter and native reasoning/recovery settings. Those differences belong in configuration; they do not require a different application invoke contract.'
          : retail
            ? 'Comparison aliases omit a shared Deep Agents reasoning_effort so LiteLLM’s candidate-specific policies remain effective. The fixed baseline retains its own setting. Comparing those objects is more useful than assuming that one setting is valid for every hosted model.'
            : 'Deep Agents uses the three course function names as its execution allowlist. Provider-visible schema filtering is enforced separately by the gateway because the installed adapter can still advertise built-in tools.'
      ]}
    ]},
    'fabric.plan':{title:'Plan and check the runtime',intro:'With the configuration ready, ask Fabric which adapter and capabilities it will use. Then run Doctor to check the prerequisites for that plan. This gives the application a chance to stop on a setup problem before starting the conversation.',sections:[
      {paragraphs:[
        '[[call:fabric.plan|FabricTarget’s preflight]] calls Fabric.plan with the typed configuration and base directory, then awaits Fabric.doctor. The resolved descriptor and capability plan belong to the SDK; our code saves both reports and stops when Doctor returns fail.',
        '[[cap:CAP-FAB-03|The plan and Doctor reports]] let you compare the adapter identity, supported input/output contract and dependency findings. A pass establishes the inspected prerequisites, not successful model access or correct course advice. For Hermes, confirm the selected descriptor/interpreter rather than expecting the Deep Agents descriptor to appear.'
      ]}
    ]},
    'fabric.start':{title:'Start one persistent runtime',intro:'Start the agent using the configuration that passed preflight. Fabric returns a runtime the application can keep open and call again. Reusing it across the scenario’s turns gives the harness a continuing conversation rather than starting from scratch for each message.',sections:[
      {paragraphs:[
        '[[call:fabric.start|FabricTarget startup]] awaits Fabric.start_runtime and enters the returned runtime’s asynchronous context. Fabric and the selected adapter own their worker/harness setup; the application owns the surrounding OpenShell process, generated Relay configuration path and cleanup on failures.',
        '[[cap:CAP-FAB-04|The lifecycle/startup evidence]] distinguishes configuration saved, plan/preflight and runtime started. A startup receipt is the useful output here; the conversation and invocation results occur later. The explicit ADAPTER_PYTHON and Relay configuration path are compatibility requirements of the pinned integration, not universal requirements of every Fabric release.'
      ]}
    ]},
    'fabric.invoke':{title:'Invoke with a RunRequest',intro:'When the learner sends a public message, the application packages it as a RunRequest and calls the open Fabric runtime. The adapter translates that request into the selected harness’s call. The application uses this same interface for Deep Agents and Hermes.',sections:[
      {paragraphs:[
        '[[call:fabric.invoke|FabricTarget.reply]] creates RunRequest with the public input and relay_session_root, captures it, then awaits runtime.invoke(request=request). Public Preferences travel in the application’s explicit input channel; the original persona, simulator instructions and undisclosed overlay are excluded. The adapter translates the normalized request into its harness call.',
        retail
          ? 'Before this call, [[call:retail.response.clarify|the missing-constraint branch]] can produce a confirmed application-only clarification. That turn has no native request/result. The next genuine invocation acknowledges the previously delivered application response, because native harness memory also retains its unpresented proposal. Public turn and invocation sequence are therefore recorded separately.'
          : 'The runtime persists across the public turns. A RunRequest is the input to one agent invocation; it is not one provider call, because the harness may perform multiple model/tool exchanges before returning.',
        ...(retail ? ['For a standalone retail recommendation with a public budget and study days, [[call:retail.retrieval.arm|the application arms an initial search requirement]]. [[call:retail.retrieval.enforce|The gateway policy]] forces the first provider response to select search_courses through structured tool_choice; the harness must then execute the real MCP call. The requirement clears after a validated selection, so subsequent exchanges can finish normally within the existing tool limit. [[cap:CAP-MCP-02|The provider-visible schema/choice capture]] shows this application decision. It is not autonomous model tool selection, and the separate managed condition does not enable this policy.'] : []),
        '[[cap:CAP-FAB-05|The captured request boundary]] preserves the actual request fields with a public-safe projection. Match its public_turn and request ID to [[cap:CAP-FAB-06|the returned invocation record]]; do not match by array position when an application-only turn is present.'
      ]}
    ]},
    'fabric.result':{title:'Read the normalized RunResult',intro:'Awaiting the invocation gives the application a RunResult. Fabric presents the selected harness’s result through this common object, including status, runtime identities, output and available usage or errors. The application reads it before deciding what can be delivered to the learner.',sections:[
      {paragraphs:[
        '[[call:fabric.result|The result-handling code]] saves the complete boundary result before extracting result.output.to_dict() and its response. It stops for non-succeeded runtime status, empty/provider-error content or malformed tool-call text. These are different failure mechanisms from a valid answer that misses a course constraint.',
        retail
          ? '[[call:retail.response.render|RetailResponseBoundary.apply]] preserves the original proposal privately and prepares an explicitly application-owned source summary from validated returned course facts. Output Guardrails must pass before [[call:retail.response.confirm|confirm_delivery]] acknowledges that response. [[cap:CAP-FAB-07|Presentation settings/decisions]] retain the generated policy and native-versus-delivered distinction. A source-summary pass is evidence about this delivery boundary, not a claim that the proposal obeyed every instruction.'
          : 'The public reply is the validated extracted response, while native tool scopes and gateway accounting remain separate evidence. Do not read an absent normalized usage field as zero or invent a tool call from a fluent answer.',
        '[[cap:CAP-FAB-06|The RunResult capture]] shows the SDK boundary. [[file:fabric-invocations.json|The invocation companion]] shows selected normalized fields and, when a proposal was not presented, its hash and the confirmed delivery hash instead of private proposal text.'
      ]}
    ]},
    'harness.context':{title:'Connect instructions and course tools',intro:board
      ? 'Give Hermes the advisor instructions, model connection and course MCP toolset. Its managed configuration keeps this three-tool application small by turning off deferred tool search and additional automatic recovery. Once connected, the runtime is ready for the first public message.'
      : 'Give the Deep Agents adapter the advisor instructions, runtime skill path, model connection and course MCP registration. These settings prepare its context and available tools. We can then distinguish this setup from the tool calls made later while answering a learner.',sections:[
      {paragraphs:[
        board
          ? '[[call:harness.context|The harness setup]] selects the Hermes environment and mcp-catalogue toolset. [[cap:CAP-HER-01|The run-bound managed/native YAML]] shows deferred tool search off, a single API attempt and disabled auto-recovery. [[cap:CAP-HER-02|Native adapter output]] is a separate record of the resolved harness settings.'
          : '[[call:harness.context|The MCP registration]] adds the three course tools and the runtime skill to the adapter’s context. [[cap:CAP-DA-01|The Deep Agents adapter settings]] show the selected policy. The installed adapter gates execution globally; our provider boundary additionally withholds built-in filesystem/subagent schemas.',
        'Instructions tell the advisor how to use evidence and express uncertainty; tool access determines what facts it can actually obtain. Keep those mechanisms separate when debugging: changing prompt wording cannot grant a missing MCP tool, and adding a tool cannot establish that the model used it.'
      ]}
    ]},
    'harness.loop':{title:'Run the model/tool loop and return a reply',intro:'The harness first sends the public request and available tools to the model. If the model requests a permitted tool, the harness executes it and sends the returned information back into context. The model can then continue or finish its reply.',sections:[
      {paragraphs:[
        `[[call:fabric.invoke|The application’s wait point]] remains the same for ${board?'Hermes':'Deep Agents'}. Harness-internal tool/model execution is SDK-owned, while the application gateway limits tool rounds and model attempts. This small course task does not demonstrate every planning, delegation or memory capability the harness offers.`,
        '[[file:native-tools.json|Observed tool requests/results]] and [[file:relay-scopes.json|native harness scopes]] establish which exchanges occurred. A successful tool result with an empty search is a valid result; an invalid_input payload is an argument problem that a bounded subsequent tool call may repair. Neither should be rewritten as a fabricated course match.'
      ]}
    ]},
    'mcp.connect':{title:'Connect and discover course tools',intro:'Before the agent can search the catalogue, connect it to the course MCP server. The application supplies the server command and environment. The adapter launches the connection, discovers its tools and makes their schemas available to the harness.',sections:[
      {paragraphs:[
        '[[call:mcp.connect|add_mcp_server]] points catalogue at the project interpreter running learning_lab.course_mcp. Environment settings supply the frozen catalogue path and the public-preferences channel. The server’s actual tools/list handler records discovery; it does not run an extra diagnostic client or a course search just to create evidence.',
        '[[cap:CAP-MCP-01|The connection settings]] explain where the server came from. [[cap:CAP-MCP-02|Discovery and provider-schema captures]] show two different surfaces: what the MCP client discovered and what our gateway actually exposed to the model. A schema appearing in discovery is not evidence of a business-tool call.'
      ]}
    ]},
    'mcp.search':{title:'Search using public constraints',intro:'A search asks which saved courses fit the learner’s stated goal and constraints. The model supplies search arguments, and our server combines them with trusted public preferences before reading the catalogue. This prevents a search from silently relaxing an explicit budget or study day.',sections:[
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
    'mcp.details':{title:'Retrieve one course’s details',intro:'Once the advisor has a course ID, it can request that listing’s full saved details. The tool returns the known fee, duration, prerequisites, source link and any unknown fields so the advisor can discuss that specific option.',sections:[
      {paragraphs:[
        '[[call:mcp.details|get_course_details]] retrieves the stable ID and adds constraint notes based on the current public preferences. Its result is a course object with fields directly on that object. It does not wrap that record in a matches list, so a generic matches-only viewer would misread a valid details result.',
        '[[cap:CAP-MCP-03|The native tool evidence]] shows whether details was actually invoked and which fields came back. A returned record can describe an option that exceeds the budget; the constraint note and public answer must explain that conflict. Unknown intake or funding eligibility stays unknown even when the fee is known.'
      ]}
    ]},
    'mcp.compare':{title:'Compare supported options',intro:'When two or three known courses need comparison, request their records together. The advisor can then discuss differences using the same saved facts. Each option must already have a valid catalogue ID; the comparison tool does not create a new recommendation.',sections:[
      {paragraphs:[
        '[[call:mcp.compare|compare_courses]] validates the number and uniqueness of IDs, then returns each course’s details and constraint notes. The domain result is a list of course records, sometimes nested in the MCP text-content envelope. Decode that envelope before interpreting the records; an absent matches field is expected for this tool.',
        'Use [[cap:CAP-MCP-03|the actual comparison result]] to distinguish known duration/fee differences from missing information. A course with an unknown duration cannot be labelled shorter merely because another listed programme is long. If this tool was only available and never called, its configuration establishes capability rather than an observed comparison.'
      ]}
    ]},
    'models.admit':{title:'Admit and bound each model call',intro:'Before sending a model request, check whether the experiment still has permission to make it. Our gateway admits the attempt, assigns its role and applies the configured limits. Any permitted retry must pass through this same accounting step.',sections:[
      {paragraphs:[
        '[[call:models.admit|Budget.admit and the gateway]] allocate a role-labelled attempt and refuse work once the shared 120-attempt cap is exhausted. The gateway caps output at 1,024 tokens, limits advisor tool rounds to four and filters provider-visible tool schemas. These limits are independent of UserSim’s public-turn limit and Fabric’s internal-turn setting.',
        '[[cap:CAP-GW-01|The effective gateway settings]] show which controls this condition enabled; [[cap:CAP-MCP-02|provider schema captures]] show the exposed/withheld tool surface. A schema filtered before dispatch and a forbidden returned tool call rejected after dispatch are distinct checks. Credentials remain on the host, outside the agent’s tools.'
      ]}
    ]},
    'models.request':{title:'Send the request and record usage',intro:'Send the admitted request to the proxy and wait for the provider’s response. The gateway records which alias was requested, which model answered, how long the request took and the usage returned by the provider. Failed attempts remain in the same record.',sections:[
      {paragraphs:[
        retail
          ? '[[call:models.request|Gateway.complete]] sends the bounded request with host-side credentials, captures safe status/rate-limit metadata and preserves failed attempts. SDK/provider retries are disabled. Requested-pool retail comparison calls enable at most two retries for HTTP 429 within a 300-second total request deadline. Their scheduled delays are 30 and 60 seconds; a valid Retry-After can extend a delay, but a required wait above 60 seconds or beyond the remaining deadline stops the call. Each retry consumes another admitted attempt; exhausted budgets and other failures stop. The baseline, managed condition and diagnostic pool retain a 50-second request deadline with application recovery disabled.'
          : '[[call:models.request|Gateway.complete]] sends the bounded request with host-side credentials and records safe provider status/error metadata before returning or raising. This preset keeps application recovery disabled as well as SDK/provider retries. A provider failure is preserved for diagnosis instead of repeatedly running until an answer appears.',
        '[[cap:CAP-GW-02|The call records]] retain logical request ID, attempt/retry linkage, selected model, usage and any native routing decision. An application-only clarification contributes zero inference calls. A gateway ID does not prove a Relay span relationship, and absent provider usage remains unknown rather than becoming a zero-cost claim.'
      ]}
    ]},
    'models.alias':{title:'Resolve alias and dispatch to provider',intro:'The application requests an alias rather than embedding provider details in the conversation code. LiteLLM looks up that alias in its loaded model_list and sends the request to the configured hosted endpoint. This is where model connection settings take effect.',sections:[
      {paragraphs:[
        retail
          ? '[[call:models.alias|The retail alias definitions]] keep fixed-candidate and capable-access aliases separate from the two-deployment routed group. Fixed and routed versions of each candidate use the same per-model reasoning settings. The shared Fabric builder deliberately avoids overriding those candidate-specific settings.'
          : '[[call:models.alias|The proxy aliases]] map the fixed advisor and support roles to their configured deployments. This preset does not ask Switchyard to choose among candidates, so a completed proxy call is fixed dispatch rather than routing optimization.',
        '[[cap:CAP-LLM-03|Loaded YAML and resolved effective settings]] identify the configured process state without publishing credentials. Compare the requested alias to the selected model in [[file:usage.json|actual call accounting]]. A model appearing in inventory does not establish access, tool-loop completion or the quality of its response.'
      ]}
    ]}
  };
}
