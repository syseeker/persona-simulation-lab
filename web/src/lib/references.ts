/** Static excerpts from retained v0.2 code, refreshed 19 November 2026.
 * They explain integration ownership; they are not proof that proposed scenarios work.
 * No service calls, inference, private records or host-specific repository URLs are used.
 */
export type SourceReference = {
  title: string;
  path: string;
  symbol: string;
  snippet: string;
  ownership: string;
  upstream: { label: string; url: string }[];
  note: string;
  inputs?: string;
  outputs?: string;
};

export const references: Record<string, SourceReference> = {
"checks": {
  "title": "Application-owned assertions",
  "path": "src/learning_lab/evaluation.py",
  "symbol": "score_response",
  "snippet": "def score_response(\n    content: str, preferences: Preferences, catalogue_path: Path | None = None\n) -> dict[str, bool]:\n    if answer_outcome(content)[\"status\"] != \"valid\":\n        return {\n            key: False\n            for key in [\n                \"catalogue_grounding\",\n                \"constraint_compliance\",\n                \"eligibility_caution\",\n                \"fee_caution\",\n                \"source_citation\",\n            ]\n        }\n    content = answer_text(content)\n    content = content.translate(str.maketrans({\"\\u2011\": \"-\", \"\\u2013\": \"-\", \"\\u2010\": \"-\"}))\n    permitted = {c.id for c in all_courses(catalogue_path)}\n    matched = {\n        item[\"course\"][\"id\"] for item in search_courses(preferences, catalogue_path=catalogue_path)[\"matches\"]\n    }\n    cited = set(re.findall(r\"\\b(?:CC|SF)-\\d{3}\\b\", content))\n    lower = content.lower()\n    known_urls = {str(c.source_url) for c in all_courses(catalogue_path)}\n    urls = set(re.findall(r\"https://[^\\s)\\]>]+\", content))\n    return {\n        \"catalogue_grounding\": cited <= permitted and urls <= known_urls,\n        \"constraint_compliance\": cited <= matched,\n        \"eligibility_caution\": not bool(\n            re.search(r\"you (?:are eligible|qualify|will receive)|guaranteed (?:funding|subsidy)\", lower)\n        ),\n        \"fee_caution\": not bool(re.search(r\"no (?:additional|extra|material) (?:fees|costs)\", lower)),\n        \"source_citation\": bool(urls) if cited else True,\n    }\n",
  "ownership": "The application authors these deterministic checks against catalogue facts and explicit constraints. Running this function requires no Helix SDK or Platform. Missing evidence must remain distinct from a pass.",
  "upstream": [],
  "note": "Retained source reference only. The broader row-level evaluation and disclosure criteria still need scenario-specific implementation and actual evidence."
},
"guardrails": {
  "title": "Native Guardrails integration — planned",
  "path": "",
  "symbol": "Adapter not implemented",
  "snippet": "",
  "ownership": "NeMo Guardrails owns configured native checks. The application must call the supported input/output boundary and enforce its allow, block or error result. No native Guardrails adapter exists in this checkout.",
  "upstream": [
    {
      "label": "Guardrails package documentation",
      "url": "https://docs.nvidia.com/nemo/guardrails/latest/home"
    },
    {
      "label": "Native check API documentation",
      "url": "https://docs.nvidia.com/nemo/guardrails/latest/run-guardrailed-inference/using-python-apis/check-messages"
    }
  ],
  "note": "Illustrative interface only; no policy, decision, SDK call or enforcement is demonstrated. Application restrictions are a separate existing boundary."
},
"standalone": {
  "title": "Standalone OpenShell integration",
  "path": "src/learning_lab/sandbox.py",
  "symbol": "NativeSandbox",
  "snippet": "",
  "ownership": "The photography application owns explicit native OpenShell creation, one persistent Fabric/Deep Agents runtime, saved policy/probe records and cleanup of its labelled condition. The course tools run inside that boundary. Helix services are not used; the Hermes preset remains illustrative.",
  "upstream": [
    {
      "label": "OpenShell package documentation",
      "url": "https://docs.nvidia.com/openshell/about/overview"
    }
  ],
  "note": "Photography opens current implementation excerpts and matching local records. The retained Helix-managed package remains separate historical reference code. Inspecting this adapter never creates a sandbox."
},
  "personas": {
    "title": "Singapore persona selection",
    "path": "src/learning_lab/datasets.py",
    "symbol": "sample_personas / lock_personas",
    "snippet": "def sample_personas(source: PersonaSource = \"hf-profile-only\", count: int = 1,\n                    seed: int | None = None, filters: dict | None = None) -> dict:\n    \"\"\"Uniform reservoir sample over the actual filtered corpus, not the panel.\"\"\"\n    if not 1 <= count <= 20:\n        raise ValueError(\"Choose one to twenty profiles\")\n    if seed is not None and (not isinstance(seed, int) or isinstance(seed, bool) or not 0 <= seed <= 2**63 - 1):\n        raise ValueError(\"Sampling seed must be a nonnegative 63-bit integer\")\n    query = DatasetQuery.model_validate({**(filters or {}), \"source\": source, \"offset\": 0, \"limit\": 1})\n    dataset, expression, meta = _dataset(query)\n    chosen_seed = secrets.randbits(63) if seed is None else seed\n    rng, selected, seen = random.Random(chosen_seed), [], 0",
    "ownership": "NVIDIA supplies the synthetic persona distributions. This application owns local filtering, reservoir sampling, SHA-256 hashing and exact-row locks; these are not NeMo generation features.",
    "upstream": [
      {
        "label": "Pinned HF dataset",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer"
      },
      {
        "label": "Pinned HF revision",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/tree/a3994709410410f834bd949d643d3f2796908969"
      },
      {
        "label": "Singapore NGC Extended",
        "url": "https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg"
      }
    ],
    "note": "Current working-tree reference. HF is explicitly profile-only and has no OCEAN fields. NGC Extended is a separate distribution. A seed is not the replay guarantee: selected IDs, original rows and hashes are retained. No private rows are embedded here."
  },
  "designer": {
    "title": "Source-seeded generated columns",
    "path": "integrations/designer/learning_preferences.py",
    "symbol": "workbench_builder",
    "snippet": "for field in request[\"spec\"][\"fields\"]:\n        # The API field name is validated by the host; user descriptions remain seed text.\n        context = \"{{ generated_profile }}\" if operation == \"profiles\" else \"{{ original_profile_json }}\"\n        builder.add_column(\n            dd.LLMStructuredColumnConfig(\n                name=\"custom_\" + field[\"name\"],",
    "ownership": "NeMo Data Designer 0.10 owns native structured-column generation. The application owns the closed field specification, source seeding, schema validation, hypothetical labels and parent lineage.",
    "upstream": [
      {
        "label": "Data Designer v0.10.0 guide",
        "url": "https://github.com/NVIDIA-NeMo/DataDesigner/blob/v0.10.0/skills/data-designer/SKILL.md"
      }
    ],
    "note": "Runs in the isolated Designer environment. Salary and favourite-brand columns are generated hypotheses, not measured facts. This source excerpt does not establish that a salary-range column, later-turn disclosure or a new six-month course scenario has been implemented or verified."
  },
  "usersim": {
    "title": "UserSim activation boundary",
    "path": "src/learning_lab/simulation.py",
    "symbol": "hosted_episode",
    "snippet": "runtime = ProbeEpisodeRuntime.from_resolved_row(copy.deepcopy(row), models=host_models(gateway.mode))\n    try:\n        event = await runtime.advance()\n        while isinstance(event, ActivationRequest):\n            if event.role == \"assistant\":\n                if event.continues_turn:\n                    raise RuntimeError(\"Unexpected assistant resampling in a side-effectful external target\")\n                message = next(m[\"content\"] for m in reversed(event.messages) if m[\"role\"] == \"user\")\n                await on_event({\"role\": \"user\", \"content\": message})\n                previous = len(gateway.budget.records)\n                explicit = preferences\n                if explicit is None and constraint_overrides:\n                    explicit = Preferences(goal=message, **constraint_overrides)\n                reply = await target.reply(message, explicit) if explicit else await target.reply(message)\n                await on_event({\"role\": \"assistant\", **reply})",
    "ownership": "NeMo UserSim owns the episode/activation protocol. The application adapter sends the latest public learner message to the real advisor target and returns its actual public reply.",
    "upstream": [
      {
        "label": "UserSim v0.3.0 external runtime",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md"
      },
      {
        "label": "UserSim v0.3.0 extension API",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md"
      }
    ],
    "note": "The application does not turn the simulated user into an agent-tool owner. Source profiles, generated scenario assumptions and public conversation turns remain distinct. New staged salary disclosure is a wireframe proposal, not a verified property of this loop."
  },
  "fabric": {
    "title": "Typed harness configuration",
    "path": "src/learning_lab/fabric_target.py",
    "symbol": "build_config",
    "snippet": "config = FabricConfig(\n        metadata=MetadataConfig(name=\"singapore-learning-advisor\"),\n        discovery=discovery,\n        harness=HarnessConfig(\n            adapter_id=\"nvidia.fabric.hermes\"\n            if harness == \"hermes\"\n            else \"nvidia.fabric.langchain.deepagents\",\n            resolution=\"preinstalled\",\n            settings={\"reasoning_config\": {\"enabled\": False, \"effort\": \"none\"}, \"save_trajectories\": False}\n            if harness == \"hermes\"\n            else {\"reasoning_effort\": \"none\"},\n        ),",
    "ownership": "NeMo Fabric 0.6.1 owns native planning, Doctor checks, adapter resolution and runtime lifecycle. This application chooses the harness and supplies its bounded model, tools and Relay configuration.",
    "upstream": [
      {
        "label": "Fabric v0.6.1 Deep Agents adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/README.md"
      },
      {
        "label": "Fabric v0.6.1 release",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/releases/tag/v0.6.1"
      }
    ],
    "note": "The maintained adapter selects Deep Agents or Hermes. Fabric execution limits are internal graph/runtime limits, separate from three public conversation turns and application model-call admission. Configuration is not proof of a successful invocation."
  },
  "deepagents": {
    "title": "Direct Deep Agents harness",
    "path": "src/learning_lab/target.py",
    "symbol": "DirectTarget._start",
    "snippet": "if self.relay:\n            from nemo_relay.integrations.deepagents import add_nemo_relay_integration\n\n            kwargs = add_nemo_relay_integration(kwargs)\n        self.agent = create_deep_agent(**kwargs)",
    "ownership": "LangChain Deep Agents owns create_deep_agent and harness execution. The application supplies catalogue MCP tools, memory boundaries and read-only middleware. Native Relay wrapping is explicit.",
    "upstream": [
      {
        "label": "Deep Agents maintained repository",
        "url": "https://github.com/langchain-ai/deepagents"
      },
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "The root environment pins Deep Agents 0.7.35. The direct harness and the Fabric adapter are separate paths; the Fabric compatibility boundary additionally filters provider-visible schemas in the application Gateway. No model response is embedded in this reference."
  },
  "hermes": {
    "title": "Isolated Hermes runtime policy",
    "path": "src/learning_lab/runtime_profiles.py",
    "symbol": "hermes_runtime_environment",
    "snippet": "def hermes_runtime_environment() -> dict[str, str]:\n    managed = ROOT / \"integrations/hermes/managed\"\n    if not (managed / \"config.yaml\").is_file():\n        raise ValueError(\"The explicit Hermes retry policy is missing\")\n    return {\"HERMES_MANAGED_DIR\": str(managed), \"HERMES_STREAM_RETRIES\": \"0\"}",
    "ownership": "NousResearch Hermes supplies the agent harness; the maintained Fabric adapter integrates it. The application owns interpreter selection and the explicit bounded retry-policy directory.",
    "upstream": [
      {
        "label": "Pinned Hermes source",
        "url": "https://github.com/NousResearch/hermes-agent/tree/b200f5bc60e31588ba2cb60e288029c4a54ba5fa"
      },
      {
        "label": "Fabric v0.6.1 Hermes adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/tree/v0.6.1/adapters/python/hermes"
      }
    ],
    "note": "Local Hermes uses a separate Python 3.14 environment. The reviewed managed image has a version-specific launcher for interpreter/retry variables reset by native startup. Neither runtime installation nor a retry policy proves answer quality; the preserved managed Hermes answer had a factual failure."
  },
  "mcp": {
    "title": "Read-only course MCP surface",
    "path": "src/learning_lab/course_mcp.py",
    "symbol": "search_courses",
    "snippet": "@mcp.tool()\ndef search_courses(\n    goal: str,\n    budget_sgd: float | None = None,\n    days: list[int] | str | None = None,\n    planning_area: str | None = None,\n    known_skills: list[str] | None = None,\n    kind: Literal[\"skillsfuture\", \"community\"] | None = None,\n) -> dict:\n    \"\"\"Find up to five sourced courses; preserve unknown fees, schedules and eligibility.",
    "ownership": "The application authors the three catalogue tools and binds trusted preferences. FastMCP supplies the MCP server/protocol; MCP does not itself establish catalogue accuracy or subsidy eligibility.",
    "upstream": [
      {
        "label": "MCP Python SDK",
        "url": "https://github.com/modelcontextprotocol/python-sdk"
      }
    ],
    "note": "The current tools are search_courses, get_course_details and compare_courses. Frozen native presets or authenticated session preferences constrain model arguments. Developer controls for generation, deployment and recovery are not advisor tools. No job-search tool exists in this surface."
  },
  "catalogue": {
    "title": "Deterministic catalogue matching",
    "path": "src/learning_lab/catalogue.py",
    "symbol": "search_courses",
    "snippet": "elif prefs.budget_sgd is not None and course.price_max_sgd is not None:\n            total = course.price_max_sgd + (course.extra_cost_sgd or 0)\n            if total > prefs.budget_sgd:\n                reason = \"Published upper fee including known extras exceeds the budget\"",
    "ownership": "The application owns the dated provider snapshot, validation, deterministic matching and catalogue hash. Course providers own the original published facts; this filter is not an NVIDIA SDK feature.",
    "upstream": [
      {
        "label": "NUS published short-course source",
        "url": "https://www.stat.nus.edu.sg/education/cet/short-course/"
      },
      {
        "label": "onePA official course catalogue",
        "url": "https://www.onepa.gov.sg/courses"
      }
    ],
    "note": "Known extras are added; absent costs and funding eligibility remain unknown. The working catalogue does not verify the planned six-month, roughly S$20,000 example. Newly researched courses require an explicit dated snapshot before an implementation can recommend them."
  },
  "gateway": {
    "title": "Application inference admission",
    "path": "src/learning_lab/inference.py",
    "symbol": "Gateway.complete",
    "snippet": "async def complete(self, payload: dict, role=\"assistant\") -> dict:\n        record = await self.budget.admit(role, self.mode)\n        record[\"model\"] = payload.get(\"model\")\n        started = time.perf_counter()\n        payload = {**payload, \"max_tokens\": min(int(payload.get(\"max_tokens\", 1024)), 1024), \"stream\": False}\n        # The local gateway is the single admission boundary, including Fabric adapter calls.\n        payload.pop(\"max_completion_tokens\", None)",
    "ownership": "This application owns atomic call admission, output caps, roles, usage/error records and optional tool-schema filtering. LiteLLM/provider transport and native Switchyard routing are separate components.",
    "upstream": [
      {
        "label": "LiteLLM proxy documentation",
        "url": "https://docs.litellm.ai/docs/simple_proxy"
      }
    ],
    "note": "Every admitted attempt is counted before dispatch, including failed requests; missing usage stays unknown. The routed path fails if the proxy is absent. Model-call limits are not token-price guarantees, and the Gateway is not a synthetic routing policy."
  },
  "routing": {
    "title": "Native Switchyard Stage decisions",
    "path": "integrations/proxy/lab_routing.py",
    "symbol": "LabRoutingPlugin.run",
    "snippet": "async def run(self, context):\n        count = len(set(context.candidate_models))\n        if count == 1:\n            context.signals[\"learning_lab\"] = {\"route\": \"fixed\", \"candidate_count\": 1}\n            return context\n        if count != 2:\n            raise ValueError(\"The lab routing group must have exactly two distinct candidates\")\n        result = await self.stage.run(context)\n        decision = result.signals.get(\"switchyard\", {})",
    "ownership": "The pinned experimental Switchyard Stage plugin owns the routing decision. This application wrapper separates one-model fixed groups from exactly two-model routed groups and exposes bounded native decision metadata.",
    "upstream": [
      {
        "label": "Pinned Switchyard LiteLLM integration",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/tree/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm"
      }
    ],
    "note": "Current Stage routing requires two distinct candidates, with capable then efficient declaration order. A three-model policy is a proposed extension. A label, fabricated difficulty hint or configured alias is not evidence that Switchyard selected a model."
  },
  "litellm": {
    "title": "Fixed and routed proxy aliases",
    "path": "integrations/proxy/litellm.yaml",
    "symbol": "model_list / router_settings",
    "snippet": "router_settings:\n  num_retries: 0\n  fallbacks: []\n  context_window_fallbacks: []\n  plugins:\n    - lab_routing.ROUTING_PLUGIN\nlitellm_settings:\n  callbacks:\n    - lab_routing.ROUTING_PLUGIN\n  num_retries: 0\n  set_verbose: false\n  turn_off_message_logging: true",
    "ownership": "LiteLLM owns provider transport and proxy aliases. This application authors the provider-independent aliases, explicit no-fallback configuration and Switchyard plugin wiring.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "Model names, provider endpoints and credentials are supplied by the operator. NIM/Brev/frontier hosting is independent of Helix Platform hosting. This static configuration does not prove provider readiness, candidate quality, a native decision or support for three candidates."
  },
  "relay": {
    "title": "Native Relay integration hook",
    "path": "src/learning_lab/target.py",
    "symbol": "DirectTarget._start / relay_config",
    "snippet": "if self.relay:\n            from nemo_relay.integrations.deepagents import add_nemo_relay_integration\n\n            kwargs = add_nemo_relay_integration(kwargs)",
    "ownership": "NeMo Relay supplies native instrumentation and scope relationships. The application enables it, selects sinks and projects bounded evidence without inventing missing parent/session links.",
    "upstream": [
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "Local native capture uses relay.jsonl; managed deployments query native Intake instead of claiming a local file export. Fabric 0.6.1 Hermes does not forward the Platform session root, so its native workspace export cannot currently be attributed to a managed session. Missing correlation does not mean the exporter was disabled."
  },
  "records": {
    "title": "Application evidence persistence",
    "path": "src/learning_lab/evidence.py",
    "symbol": "save_evidence",
    "snippet": "def save_evidence(path: Path, value, *, append=False):\n    path.parent.mkdir(parents=True, exist_ok=True)\n    with path.open(\"a\" if append else \"w\") as file:\n        file.write(json.dumps(sanitize(value), default=str, ensure_ascii=False) + \"\\n\")",
    "ownership": "The application owns persisted ledgers, sanitization, artifact allowlists and UI projections. Native Relay/Intake remains the owner of its original events and IDs; an application record is not a replacement native trace.",
    "upstream": [],
    "note": "Current source is shown, not private traces or datasets. Saved artifacts are inspected without new inference. Preserve original rows, generated overlays, failed replies, missing usage and unassigned native records. A working-tree excerpt may differ from the revision that produced an older run."
  },
  "helix": {
    "title": "Local Helix evaluation SDK",
    "path": "integrations/helix/evaluate.py",
    "symbol": "evaluate",
    "snippet": "def evaluate(rows: list[dict]) -> dict:\n    if not rows:\n        raise ValueError(\"No evaluation rows supplied\")\n    result = Evaluator().run_sync(\n        metrics=[ExactMatchMetric(reference=\"{{item.expected}}\", candidate=\"{{item.output}}\")],\n        dataset=rows,\n        config=RunConfig(parallelism=1),\n    )\n    return result.model_dump(mode=\"json\")",
    "ownership": "The application authors transparent applicable criterion rows from saved replies and frozen facts. Helix Evals SDK 0.9.1 executes the ExactMatch metric. These narrow assertions do not certify the whole answer.",
    "upstream": [
      {
        "label": "Helix 0.9.1 Evals SDK",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.9.1/packages/nhx_evals_sdk"
      }
    ],
    "note": "The isolated evaluation environment is separate from Helix Platform 0.10.0. Missing/unsupported criteria remain distinct from passed or failed assertions. Evaluating saved replies does not start a fresh advisor or establish new model quality."
  },
  "platform": {
    "title": "Helix Platform SDK bridge",
    "path": "src/learning_lab/deployment.py",
    "symbol": "PlatformBridge.call",
    "snippet": "async def call(self, operation: str, **arguments) -> dict:\n        if operation not in OPERATIONS:\n            raise ValueError(\"Unsupported Platform operation\")\n        python = platform_python()",
    "ownership": "Helix is a control plane spanning agent operations, evaluation, experiments and hardening. This retained bridge exposes agents, deployments, sessions and native Intake; additional managed evaluation jobs are planned. The application owns the explicit local/remote subprocess bridge, admission leases, durable session guard and bounded cleanup/recovery orchestration.",
    "upstream": [
      {
        "label": "Helix 0.10.0 release",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/releases/tag/0.10.0"
      },
      {
        "label": "Helix deployment guide",
        "url": "https://docs.nvidia.com/nemo-helix/latest/documentation/agents/deploy-agents/"
      }
    ],
    "note": "Native SDK operations live in integrations/platform/bridge.py. Package, register, deploy, invoke and close are explicit actions. Status/configuration alone proves neither model execution nor sandbox enforcement. A logical SDK close is not sufficient proof that failed native work stopped."
  },
  "openshell": {
    "title": "Reviewed agent-and-tool image boundary",
    "path": "integrations/platform/package_agent.py",
    "symbol": "prepare_bundle",
    "snippet": "# Copy an explicit allowlist; never copy .env, personas, runs or the root\n    # dependency manifest (which would pull UserSim into the Platform image).\n    copied = {}\n    for name in (\"catalogue.py\", \"course_mcp.py\", \"settings.py\"):\n        source = ROOT / \"src/learning_lab\" / name\n        shutil.copyfile(source, package / name)\n        copied[f\"src/learning_lab/{name}\"] = hashlib.sha256(source.read_bytes()).hexdigest()",
    "ownership": "The application owns minimal image packaging, root-owned files and the hash-checked public preset. OpenShell owns native sandbox enforcement through the Helix executor. The checked-in policy intent file is documentation, not enforcement proof.",
    "upstream": [
      {
        "label": "OpenShell v0.1.6 source",
        "url": "https://github.com/NVIDIA/OpenShell/tree/v0.1.6"
      },
      {
        "label": "Helix 0.10.0 source",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.10.0"
      }
    ],
    "note": "The verified native path uses the official encrypted credential store and a frozen photography/S$50/Saturday preset. Dynamic Docker invocation remains unverified on this host; dynamic OpenShell callbacks have a pinned external-driver compatibility limit. Do not imply new salary/preferences scenarios are deployed by showing this package code."
  },
  "application": {
    "title": "Shared application service boundary",
    "path": "src/learning_lab/service.py",
    "symbol": "LabService",
    "snippet": "class LabService:\n    def __init__(self, runs: Path | None = None):\n        self.runs = runs or ROOT / \"runs\"\n        self.tasks: dict[str, asyncio.Task] = {}\n        self.run_state: dict[str, dict] = {}\n        self.lock = asyncio.Lock()",
    "ownership": "This application owns the citizen workflow and shared service orchestration. SvelteKit routes, the persistent Python worker, CLI and developer MCP call shared services; NVIDIA components supply their own narrower native responsibilities.",
    "upstream": [
      {
        "label": "SvelteKit Node adapter",
        "url": "https://svelte.dev/docs/kit/adapter-node"
      }
    ],
    "note": "This isolated wireframe does not invoke LabService or any provider. The current working application is v0.2. Brand/salary derived fields, progressive disclosure and new scenario outcomes shown in the design must stay labelled proposals until implemented and verified."
  },
  "providers": {
    "title": "Operator-configured inference providers",
    "path": "integrations/proxy/launch.py",
    "symbol": "configured_environment",
    "snippet": "def configured_environment(source=None) -> dict[str, str]:\n    env = dict(os.environ if source is None else source)\n    main_model = env.get(\"NIM_MODEL\") or \"nvidia/nemotron-3.5-lightning-30b-a3b\"\n    support_model = env.get(\"NIM_USER_MODEL\") or \"nvidia/nemotron-3-nano-omni-30b-a3b-reasoning\"\n    for role, model in (\n        (\"FIXED\", main_model),\n        (\"SUPPORT\", support_model),\n        (\"CAPABLE\", main_model),\n        (\"EFFICIENT\", support_model),\n    ):\n        env.setdefault(f\"LAB_{role}_MODEL\", \"openai/\" + model)\n        env.setdefault(f\"LAB_{role}_API_BASE\", env.get(\"NIM_BASE_URL\", \"https://integrate.api.nvidia.com/v1\"))\n        env.setdefault(f\"LAB_{role}_API_KEY\", env.get(\"NVIDIA_API_KEY\", \"\"))\n    return env",
    "ownership": "Inference providers own model serving. LiteLLM adapts transport. This application supplies explicit provider/model/endpoint environment references and validates inventory; the wireframe hosts no provider.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "NIM defaults are source configuration, not availability evidence. Brev and frontier endpoints are configurable paths, not live-verified deployments. No credentials or environment values are embedded."
  }
};

/** Exact human module titles from IntegrationGraph; compact titles are explicit aliases. */
export const moduleReferences: Record<string, SourceReference> = {
  "personas/Load source": {
    "title": "Load source",
    "path": "src/learning_lab/datasets.py",
    "symbol": "_dataset",
    "snippet": "def _dataset(query: DatasetQuery):\n    meta = _description(query.source)\n    if not meta[\"ready\"]:\n        raise ValueError(meta.get(\"reason\", \"Dataset is not ready\") + \". \" + meta[\"setup\"])\n    dataset = pads.dataset([str(path) for path in _paths(query.source)], format=\"parquet\")\n    expression = None\n\n    def add(part):\n        nonlocal expression",
    "ownership": "NVIDIA supplies the synthetic persona distributions. This application owns local filtering, reservoir sampling, SHA-256 hashing and exact-row locks; these are not NeMo generation features.",
    "upstream": [
      {
        "label": "Pinned HF dataset",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer"
      },
      {
        "label": "Pinned HF revision",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/tree/a3994709410410f834bd949d643d3f2796908969"
      },
      {
        "label": "Singapore NGC Extended",
        "url": "https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg"
      }
    ],
    "note": "The application reads the selected installed distribution; it does not download it or infer missing OCEAN fields. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An explicit HF profile-only or Singapore NGC Extended query.",
    "outputs": "The validated local corpus, filter expression and source metadata."
  },
  "personas/Sample & preview": {
    "title": "Sample & preview",
    "path": "src/learning_lab/datasets.py",
    "symbol": "sample_personas",
    "snippet": "for batch in dataset.scanner(columns=[\"uuid\"], filter=expression, batch_size=8192,\n                                 use_threads=False).to_batches():\n        for source_id in batch.column(0).to_pylist():\n            seen += 1\n            if len(selected) < count:\n                selected.append(str(source_id))\n            else:\n                index = rng.randrange(seen)\n                if index < count:\n                    selected[index] = str(source_id)\n    if seen < count:\n        raise ValueError(f\"Only {seen} profiles match these filters; requested {count}\")\n    locked = lock_personas(source, selected)",
    "ownership": "NVIDIA supplies the synthetic persona distributions. This application owns local filtering, reservoir sampling, SHA-256 hashing and exact-row locks; these are not NeMo generation features.",
    "upstream": [
      {
        "label": "Pinned HF dataset",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer"
      },
      {
        "label": "Pinned HF revision",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/tree/a3994709410410f834bd949d643d3f2796908969"
      },
      {
        "label": "Singapore NGC Extended",
        "url": "https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg"
      }
    ],
    "note": "This is application-owned reservoir sampling, not a NeMo synthetic-row generator. Exact rows and hashes support replay. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Source, filters, count and optional seed.",
    "outputs": "Selected original IDs resolved into previewable records."
  },
  "personas/Lock identity": {
    "title": "Lock identity",
    "path": "src/learning_lab/datasets.py",
    "symbol": "lock_personas",
    "snippet": "matching = dataset.to_table(filter=pc.is_in(pads.field(\"uuid\"), value_set=pa.array(source_ids))).to_pylist()\n    by_id = {str(row[\"uuid\"]): row for row in matching}\n    if len(by_id) != len(matching):\n        raise ValueError(\"Source IDs are not unique in this dataset\")\n    if any(source_id not in by_id for source_id in source_ids):\n        raise ValueError(\"One or more selected IDs do not exist in this distribution\")\n    records = [_record(by_id[source_id], meta) for source_id in source_ids]\n    return {\"source\": source, \"dataset\": meta[\"dataset\"], \"source_revision\": meta[\"revision\"],\n            \"source_ids\": source_ids, \"rows\": [by_id[source_id] for source_id in source_ids], \"records\": records,\n            \"lock_sha256\": profile_hash(records), \"inference_calls\": 0}",
    "ownership": "NVIDIA supplies the synthetic persona distributions. This application owns local filtering, reservoir sampling, SHA-256 hashing and exact-row locks; these are not NeMo generation features.",
    "upstream": [
      {
        "label": "Pinned HF dataset",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer"
      },
      {
        "label": "Pinned HF revision",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/tree/a3994709410410f834bd949d643d3f2796908969"
      },
      {
        "label": "Singapore NGC Extended",
        "url": "https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg"
      }
    ],
    "note": "The application resolves and hashes actual selected rows. A locked synthetic profile does not establish a real person or behaviour. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Distinct IDs from one source distribution.",
    "outputs": "Ordered records, source revision and lock SHA-256."
  },
  "designer/Define columns": {
    "title": "Define columns",
    "path": "src/learning_lab/workbench.py",
    "symbol": "DesignerField",
    "snippet": "class DesignerField(StrictModel):\n    name: str = Field(min_length=1, max_length=40, pattern=r\"^[a-z][a-z0-9_]*$\")\n    type: FieldType\n    description: str = Field(min_length=1, max_length=1200)\n    minimum: FiniteFloat | None = None\n    maximum: FiniteFloat | None = None\n    choices: list[str] = Field(default_factory=list, max_length=30)\n\n    @model_validator(mode=\"after\")\n    def safe_definition(self):\n        if self.name in RESERVED or self.name.startswith(\"original_\"):\n            raise ValueError(\"Choose a new column name outside the reserved provenance fields\")\n        if self.type == \"enum\" and (not self.choices or len(self.choices) != len(set(self.choices))):\n            raise ValueError(\"An enum needs distinct nonempty choices\")",
    "ownership": "NeMo Data Designer 0.10 owns native structured-column generation. The application owns the closed field specification, source seeding, schema validation, hypothetical labels and parent lineage.",
    "upstream": [
      {
        "label": "Data Designer v0.10.0 guide",
        "url": "https://github.com/NVIDIA-NeMo/DataDesigner/blob/v0.10.0/skills/data-designer/SKILL.md"
      }
    ],
    "note": "The application prevents collisions with provenance fields. A two-bound salary-range field and later-turn disclosure remain proposed design choices. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Field names, supported types, descriptions and bounds.",
    "outputs": "A validated closed custom-field specification."
  },
  "designer/Generate scenario": {
    "title": "Generate scenario",
    "path": "integrations/designer/learning_preferences.py",
    "symbol": "workbench_builder",
    "snippet": "operation = request[\"spec\"][\"operation\"]\n    if operation != \"columns\":\n        is_profile = operation == \"profiles\"\n        builder.add_column(\n            dd.LLMStructuredColumnConfig(\n                name=\"generated_profile\" if is_profile else \"generated_scenario\",\n                model_alias=\"designer\",\n                system_prompt=system,\n                prompt=(\n                    \"Create a NEW, distinct synthetic Singapore learner profile inspired by the source. \"\n                    \"Vary the person, occupation and interests plausibly. This is generated data, not a new \"\n                    \"Nemotron source record. Do not copy the source UUID or generate OCEAN scores.\\n\"",
    "ownership": "NeMo Data Designer 0.10 owns native structured-column generation. The application owns the closed field specification, source seeding, schema validation, hypothetical labels and parent lineage.",
    "upstream": [
      {
        "label": "Data Designer v0.10.0 guide",
        "url": "https://github.com/NVIDIA-NeMo/DataDesigner/blob/v0.10.0/skills/data-designer/SKILL.md"
      }
    ],
    "note": "This configures an SDK column; later DataDesigner create/batch execution performs inference through the bounded gateway. Generated preferences remain hypotheses. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Frozen source seeds and an explicit generation operation.",
    "outputs": "Native Data Designer structured-column configuration."
  },
  "designer/Validate & link": {
    "title": "Validate & link",
    "path": "src/learning_lab/workbench.py",
    "symbol": "validate_generated_payload",
    "snippet": "if any(\n            record.get(key) != seed[key]\n            for key in (\n                \"source_id\",\n                \"source_revision\",\n                \"original_profile_json\",\n                \"original_profile_sha256\",\n                \"generation_index\",\n            )\n        ):\n            raise ValueError(\"Designer changed source lineage or reordered source records\")\n        original = json.loads(seed[\"original_profile_json\"])\n        if profile_hash(original) != seed[\"original_profile_sha256\"]:\n            raise ValueError(\"Original profile hash verification failed\")\n        generated = {}",
    "ownership": "NeMo Data Designer 0.10 owns native structured-column generation. The application owns the closed field specification, source seeding, schema validation, hypothetical labels and parent lineage.",
    "upstream": [
      {
        "label": "Data Designer v0.10.0 guide",
        "url": "https://github.com/NVIDIA-NeMo/DataDesigner/blob/v0.10.0/skills/data-designer/SKILL.md"
      }
    ],
    "note": "Application-owned validation rejects changed lineage; typed fields and new generated identities are checked later in this function. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Generated rows and their original frozen seeds.",
    "outputs": "Rows whose identity, order and original-profile hash are preserved."
  },
  "usersim/Activate profile": {
    "title": "Activate profile",
    "path": "src/learning_lab/simulation.py",
    "symbol": "hosted_episode",
    "snippet": "runtime = ProbeEpisodeRuntime.from_resolved_row(copy.deepcopy(row), models=host_models(gateway.mode))\n    try:\n        event = await runtime.advance()\n        while isinstance(event, ActivationRequest):\n            if event.role == \"assistant\":\n                if event.continues_turn:\n                    raise RuntimeError(\"Unexpected assistant resampling in a side-effectful external target\")\n                message = next(m[\"content\"] for m in reversed(event.messages) if m[\"role\"] == \"user\")\n                await on_event({\"role\": \"user\", \"content\": message})",
    "ownership": "NeMo UserSim owns the episode/activation protocol. The application adapter sends the latest public learner message to the real advisor target and returns its actual public reply.",
    "upstream": [
      {
        "label": "UserSim v0.3.0 external runtime",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md"
      },
      {
        "label": "UserSim v0.3.0 extension API",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md"
      }
    ],
    "note": "UserSim owns activation. The application owns copying the row and dispatching the external target; simulator tools do not own the advisor. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "One resolved profile/scenario and explicit models.",
    "outputs": "A native activation request or terminal event."
  },
  "usersim/Learner message": {
    "title": "Learner message",
    "path": "src/learning_lab/simulation.py",
    "symbol": "hosted_episode",
    "snippet": "message = next(m[\"content\"] for m in reversed(event.messages) if m[\"role\"] == \"user\")\n                await on_event({\"role\": \"user\", \"content\": message})\n                previous = len(gateway.budget.records)\n                explicit = preferences\n                if explicit is None and constraint_overrides:\n                    explicit = Preferences(goal=message, **constraint_overrides)\n                reply = await target.reply(message, explicit) if explicit else await target.reply(message)\n                await on_event({\"role\": \"assistant\", **reply})\n                response = {\"role\": \"assistant\", \"content\": reply[\"content\"]}",
    "ownership": "NeMo UserSim owns the episode/activation protocol. The application adapter sends the latest public learner message to the real advisor target and returns its actual public reply.",
    "upstream": [
      {
        "label": "UserSim v0.3.0 external runtime",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md"
      },
      {
        "label": "UserSim v0.3.0 extension API",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md"
      }
    ],
    "note": "Only the latest public learner message is sent to the target. This excerpt does not implement the proposed delayed salary disclosure policy. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The native activation and trusted scenario preferences.",
    "outputs": "The latest public learner message and actual advisor reply."
  },
  "usersim/Conversation state": {
    "title": "Conversation state",
    "path": "src/learning_lab/simulation.py",
    "symbol": "hosted_episode",
    "snippet": "recorded = {\"activation_id\": event.activation_id, \"response\": response}\n            if usage and all(v is not None for v in usage.values()):\n                recorded[\"usage\"] = usage\n            event = await runtime.advance(recorded)\n        return await runtime.finalize()\n    finally:\n        await runtime.close()\n",
    "ownership": "NeMo UserSim owns the episode/activation protocol. The application adapter sends the latest public learner message to the real advisor target and returns its actual public reply.",
    "upstream": [
      {
        "label": "UserSim v0.3.0 external runtime",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md"
      },
      {
        "label": "UserSim v0.3.0 extension API",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md"
      }
    ],
    "note": "The native activation ID is preserved and close runs in finally. Target memory and UserSim state are separate; missing usage is not filled in. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A target response and actual usage when available.",
    "outputs": "Correlated activation advancement, finalization and cleanup."
  },
  "fabric/Configure agent": {
    "title": "Configure agent",
    "path": "src/learning_lab/fabric_target.py",
    "symbol": "build_config",
    "snippet": "config = FabricConfig(\n        metadata=MetadataConfig(name=\"singapore-learning-advisor\"),\n        discovery=discovery,\n        harness=HarnessConfig(\n            adapter_id=\"nvidia.fabric.hermes\"\n            if harness == \"hermes\"\n            else \"nvidia.fabric.langchain.deepagents\",\n            resolution=\"preinstalled\",\n            settings={\"reasoning_config\": {\"enabled\": False, \"effort\": \"none\"}, \"save_trajectories\": False}\n            if harness == \"hermes\"\n            else {\"reasoning_effort\": \"none\"},\n        ),\n        models={",
    "ownership": "NeMo Fabric 0.6.1 owns native planning, Doctor checks, adapter resolution and runtime lifecycle. This application chooses the harness and supplies its bounded model, tools and Relay configuration.",
    "upstream": [
      {
        "label": "Fabric v0.6.1 Deep Agents adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/README.md"
      },
      {
        "label": "Fabric v0.6.1 release",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/releases/tag/v0.6.1"
      }
    ],
    "note": "This is configuration, not proof of compatible installation, endpoint readiness or a successful invocation. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A harness choice and bounded application configuration.",
    "outputs": "A typed FabricConfig with the maintained adapter ID."
  },
  "fabric/Plan & doctor": {
    "title": "Plan & doctor",
    "path": "src/learning_lab/fabric_target.py",
    "symbol": "FabricTarget.__aenter__",
    "snippet": "self.plan = self.fabric.plan(self.config, base_dir=ROOT)\n            save_evidence(self.workspace.parent / \"fabric-plan.json\", self.plan)\n            lifecycle(self.workspace.parent, \"plan_created\")\n            report = await self.fabric.doctor(self.config, base_dir=ROOT)\n            save_evidence(self.workspace.parent / \"fabric-doctor.json\", report)\n            lifecycle(self.workspace.parent, \"doctor_completed\", status=report.status)\n            if report.status == \"fail\":\n                raise RuntimeError(\"Fabric preflight failed; run learning-lab doctor for details\")",
    "ownership": "NeMo Fabric 0.6.1 owns native planning, Doctor checks, adapter resolution and runtime lifecycle. This application chooses the harness and supplies its bounded model, tools and Relay configuration.",
    "upstream": [
      {
        "label": "Fabric v0.6.1 Deep Agents adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/README.md"
      },
      {
        "label": "Fabric v0.6.1 release",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/releases/tag/v0.6.1"
      }
    ],
    "note": "Fabric owns these results. Host contract checks are narrower than actual image/deployment/inference readiness, and failed Doctor stops startup. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Typed configuration and a compatible selected interpreter.",
    "outputs": "Native plan and Doctor reports saved separately."
  },
  "fabric/Start runtime": {
    "title": "Start runtime",
    "path": "src/learning_lab/fabric_target.py",
    "symbol": "FabricTarget.__aenter__",
    "snippet": "self.runtime = await self.fabric.start_runtime(self.config, base_dir=ROOT)\n            await self.runtime.__aenter__()\n            lifecycle(self.workspace.parent, \"runtime_started\", thread_id=self.thread_id)\n            return self\n        except BaseException as exc:\n            try:\n                lifecycle(self.workspace.parent, \"runtime_start_failed\", error_type=type(exc).__name__)\n            except Exception as evidence_error:\n                # Preserve the original startup failure even if its evidence\n                # directory became unwritable. Cleanup must still run.",
    "ownership": "NeMo Fabric 0.6.1 owns native planning, Doctor checks, adapter resolution and runtime lifecycle. This application chooses the harness and supplies its bounded model, tools and Relay configuration.",
    "upstream": [
      {
        "label": "Fabric v0.6.1 Deep Agents adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/README.md"
      },
      {
        "label": "Fabric v0.6.1 release",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/releases/tag/v0.6.1"
      }
    ],
    "note": "Fabric owns the runtime; the application owns async cleanup and lifecycle records. Startup is distinct from model invocation and answer validity. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Configuration that passed preceding checks.",
    "outputs": "An entered persistent runtime or saved startup failure."
  },
  "deepagents/Application policy": {
    "title": "Application policy",
    "path": "src/learning_lab/target.py",
    "symbol": "system_prompt",
    "snippet": "def system_prompt(strategy: str) -> str:\n    skill = (ROOT / \"runtime-skills/course-advisor/SKILL.md\").read_text().split(\"---\", 2)[-1]\n    instruction = (\n        \"Offer a concise shortlist and state the unresolved constraints.\"\n        if strategy == \"concise\"\n        else \"Ask one useful clarification when key constraints are missing, then recommend suitable options. \"\n        \"Before answering, check course IDs and official links. Separate the listed fee, known extras \"\n        \"and unknown costs. When extra_cost_sgd is null, explicitly say extras are unknown; \"\n        \"never describe the listed amount as a confirmed total or say there are no extra fees.\"\n    )\n    return f\"You are a Singapore learning and community-class advisor. Keep replies under 180 words, list at most three courses, and include official links. Use short paragraphs or bullets. {instruction}\\n{skill}\"\n",
    "ownership": "LangChain Deep Agents owns create_deep_agent and harness execution. The application supplies catalogue MCP tools, memory boundaries and read-only middleware. Native Relay wrapping is explicit.",
    "upstream": [
      {
        "label": "Deep Agents maintained repository",
        "url": "https://github.com/langchain-ai/deepagents"
      },
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "This is application policy, not intrinsic Deep Agents SDK behaviour. Instructions supplement deterministic boundaries and do not prove correctness. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The explicit strategy and reviewed advisor skill.",
    "outputs": "Application system instructions for the advisor."
  },
  "deepagents/Tool allowlist": {
    "title": "Tool allowlist",
    "path": "src/learning_lab/target.py",
    "symbol": "ReadOnlyTools",
    "snippet": "class ReadOnlyTools(AgentMiddleware):\n    \"\"\"Apply the allowlist both to model exposure and to attempted execution.\"\"\"\n\n    async def awrap_model_call(self, request, handler):\n        tools = [t for t in request.tools if getattr(t, \"name\", None) in ALLOWED_TOOLS]\n        return await handler(request.override(tools=tools))\n\n    async def awrap_tool_call(self, request, handler):\n        if request.tool_call[\"name\"] not in ALLOWED_TOOLS:\n            raise ValueError(\"This advisor only has read-only course tools\")\n        return await handler(request)\n",
    "ownership": "LangChain Deep Agents owns create_deep_agent and harness execution. The application supplies catalogue MCP tools, memory boundaries and read-only middleware. Native Relay wrapping is explicit.",
    "upstream": [
      {
        "label": "Deep Agents maintained repository",
        "url": "https://github.com/langchain-ai/deepagents"
      },
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "This is direct-harness middleware. Fabric additionally needs Gateway schema filtering because its installed execution gate still advertises built-in schemas. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Advertised tools and attempted tool calls.",
    "outputs": "Only permitted course schemas and read-only execution."
  },
  "deepagents/Bounded agent loop": {
    "title": "Bounded agent loop",
    "path": "src/learning_lab/target.py",
    "symbol": "DirectTarget.reply",
    "snippet": "config[\"callbacks\"] = [NemoRelayDeepAgentsCallbackHandler()]\n                with nemo_relay.scope.scope(\"course-advisor-request\", nemo_relay.ScopeType.Agent):\n                    result = await self.agent.ainvoke(\n                        {\"messages\": [{\"role\": \"user\", \"content\": content}]}, config\n                    )\n                await nemo_relay.subscribers.flush_async()\n            else:\n                result = await self.agent.ainvoke(\n                    {\"messages\": [{\"role\": \"user\", \"content\": content}]}, config\n                )",
    "ownership": "LangChain Deep Agents owns create_deep_agent and harness execution. The application supplies catalogue MCP tools, memory boundaries and read-only middleware. Native Relay wrapping is explicit.",
    "upstream": [
      {
        "label": "Deep Agents maintained repository",
        "url": "https://github.com/langchain-ai/deepagents"
      },
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "This is the real ainvoke boundary. Call/round admission and public-answer validation surround it; transport success is insufficient. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A public message, explicit preferences and thread state.",
    "outputs": "An actual agent invocation with optional native capture."
  },
  "hermes/Isolated runtime": {
    "title": "Isolated runtime",
    "path": "src/learning_lab/runtime_profiles.py",
    "symbol": "hermes_runtime_environment",
    "snippet": "def hermes_runtime_environment() -> dict[str, str]:\n    managed = ROOT / \"integrations/hermes/managed\"\n    if not (managed / \"config.yaml\").is_file():\n        raise ValueError(\"The explicit Hermes retry policy is missing\")\n    return {\"HERMES_MANAGED_DIR\": str(managed), \"HERMES_STREAM_RETRIES\": \"0\"}\n\n",
    "ownership": "NousResearch Hermes supplies the agent harness; the maintained Fabric adapter integrates it. The application owns interpreter selection and the explicit bounded retry-policy directory.",
    "upstream": [
      {
        "label": "Pinned Hermes source",
        "url": "https://github.com/NousResearch/hermes-agent/tree/b200f5bc60e31588ba2cb60e288029c4a54ba5fa"
      },
      {
        "label": "Fabric v0.6.1 Hermes adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/tree/v0.6.1/adapters/python/hermes"
      }
    ],
    "note": "Interpreter selection is separate. Native images also have a documented launcher because startup resets image environment; this helper does not prove execution. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The isolated Python 3.14 profile and managed retry configuration.",
    "outputs": "Explicit Hermes managed-directory and retry selections."
  },
  "hermes/Discover MCP tools": {
    "title": "Discover MCP tools",
    "path": "src/learning_lab/fabric_target.py",
    "symbol": "build_config",
    "snippet": "# Hermes takes native toolset selectors here, not raw MCP function names.\n        # Its maintained adapter resolves mcp-<server> to that server's tools.\n        tools=ToolsConfig(enabled=[\"mcp-catalogue\"] if harness == \"hermes\" else TOOL_NAMES),\n    )\n    config.add_mcp_server(\n        \"catalogue\",\n        transport=\"stdio\",\n        url=sys.executable,\n        args=[\"-m\", \"learning_lab.course_mcp\"],\n        env={\n            \"LAB_PREFERENCES_FILE\": str(workspace.parent / \"preferences.json\"),\n            \"LAB_CATALOGUE_FILE\": str(catalogue_path or workspace.parent / \"catalogue-snapshot.json\"),\n        },\n    )\n    config.add_skill_path(str(ROOT / \"runtime-skills/course-advisor\"))",
    "ownership": "NousResearch Hermes supplies the agent harness; the maintained Fabric adapter integrates it. The application owns interpreter selection and the explicit bounded retry-policy directory.",
    "upstream": [
      {
        "label": "Pinned Hermes source",
        "url": "https://github.com/NousResearch/hermes-agent/tree/b200f5bc60e31588ba2cb60e288029c4a54ba5fa"
      },
      {
        "label": "Fabric v0.6.1 Hermes adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/tree/v0.6.1/adapters/python/hermes"
      }
    ],
    "note": "Hermes owns discovery/describe/call. This config enables the maintained protocol; it is not a custom discovery implementation or a captured call. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The maintained Hermes adapter and catalogue server configuration.",
    "outputs": "The native mcp-catalogue selector and stdio MCP server."
  },
  "hermes/Bounded agent loop": {
    "title": "Bounded agent loop",
    "path": "src/learning_lab/fabric_target.py",
    "symbol": "FabricTarget.reply",
    "snippet": "before = {scope[\"uuid\"] for scope in relay_scopes(self.workspace.parent)[\"scopes\"]}\n        lifecycle(self.workspace.parent, \"invocation_started\", thread_id=self.thread_id)\n        try:\n            result = await self.runtime.invoke(\n                request=RunRequest(input=message, relay_session_root=self.thread_id)\n            )\n        except BaseException as exc:\n            lifecycle(self.workspace.parent, \"invocation_failed\", error_type=type(exc).__name__)\n            save_evidence(\n                self.workspace.parent / \"reply-outcomes.jsonl\",",
    "ownership": "NousResearch Hermes supplies the agent harness; the maintained Fabric adapter integrates it. The application owns interpreter selection and the explicit bounded retry-policy directory.",
    "upstream": [
      {
        "label": "Pinned Hermes source",
        "url": "https://github.com/NousResearch/hermes-agent/tree/b200f5bc60e31588ba2cb60e288029c4a54ba5fa"
      },
      {
        "label": "Fabric v0.6.1 Hermes adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/tree/v0.6.1/adapters/python/hermes"
      }
    ],
    "note": "Application limits still apply. Managed Hermes session-to-Relay correlation is unsupported by the pinned adapter; no unified trace is invented. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A public message and the selected Fabric/Hermes runtime.",
    "outputs": "An actual native RunRequest invocation and lifecycle evidence."
  },
  "mcp/Search courses": {
    "title": "Search courses",
    "path": "src/learning_lab/course_mcp.py",
    "symbol": "search_courses",
    "snippet": "return match(\n            bound_preferences(\n                dict(\n                    goal=goal,\n                    budget_sgd=budget_sgd,\n                    days=normalize_days(days),\n                    planning_area=planning_area,\n                    known_skills=known_skills,\n                    kind=kind,\n                )\n            )\n        )",
    "ownership": "The application authors the three catalogue tools and binds trusted preferences. FastMCP supplies the MCP server/protocol; MCP does not itself establish catalogue accuracy or subsidy eligibility.",
    "upstream": [
      {
        "label": "MCP Python SDK",
        "url": "https://github.com/modelcontextprotocol/python-sdk"
      }
    ],
    "note": "This actual MCP tool delegates to application matching. No-match and unknowns stay visible; it cannot authorize booking, payment or job applications. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A goal and optional explicit course constraints.",
    "outputs": "The matcher result after trusted preference rebinding."
  },
  "mcp/Get course details": {
    "title": "Get course details",
    "path": "src/learning_lab/course_mcp.py",
    "symbol": "get_course_details",
    "snippet": "@mcp.tool()\ndef get_course_details(course_id: str) -> dict:\n    \"\"\"Return the verified snapshot and official URL for one stable course ID.\"\"\"\n    course = get_course(course_id)\n    result = course.model_dump(mode=\"json\")\n    checked = match(bound_preferences({\"goal\": course.title}))\n    result[\"constraint_notes\"] = [e[\"reason\"] for e in checked[\"excluded\"] if e[\"id\"] == course.id]\n    return result\n",
    "ownership": "The application authors the three catalogue tools and binds trusted preferences. FastMCP supplies the MCP server/protocol; MCP does not itself establish catalogue accuracy or subsidy eligibility.",
    "upstream": [
      {
        "label": "MCP Python SDK",
        "url": "https://github.com/modelcontextprotocol/python-sdk"
      }
    ],
    "note": "Details come from the curated snapshot rather than arbitrary browsing. Missing fees, schedules and individual eligibility remain unknown. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A stable course ID.",
    "outputs": "Snapshot fields, official URL and constraint notes."
  },
  "mcp/Read constraints": {
    "title": "Read constraints",
    "path": "src/learning_lab/course_mcp.py",
    "symbol": "bound_preferences",
    "snippet": "if preset_file:\n        if remote:\n            raise ValueError(\"Choose exactly one deployed learner-constraint channel\")\n        raw = Path(preset_file).read_bytes()\n        expected = os.getenv(\"LAB_PREFERENCES_PRESET_SHA256\", \"\")\n        if len(raw) > 16000 or len(expected) != 64 or hashlib.sha256(raw).hexdigest() != expected:\n            raise ValueError(\"The frozen teaching preset failed its declared integrity check\")\n        explicit = Preferences.model_validate_json(raw).model_dump(exclude_none=True)\n        for name in [\"goal\", \"budget_sgd\", \"days\", \"known_skills\", \"kind\", \"planning_area\"]:\n            if name in explicit:\n                values[name] = explicit[name]\n            elif name != \"goal\":\n                values[name] = None\n        return Preferences.model_validate(values)",
    "ownership": "The application authors the three catalogue tools and binds trusted preferences. FastMCP supplies the MCP server/protocol; MCP does not itself establish catalogue accuracy or subsidy eligibility.",
    "upstream": [
      {
        "label": "MCP Python SDK",
        "url": "https://github.com/modelcontextprotocol/python-sdk"
      }
    ],
    "note": "The shown native path is the public photography preset. Changed/missing integrity fails closed. Progressive salary disclosure is not implemented here. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The trusted preset path/hash or a separate authenticated channel.",
    "outputs": "Hard constraints overriding conflicting model-supplied values."
  },
  "catalogue/Dated snapshot": {
    "title": "Dated snapshot",
    "path": "src/learning_lab/catalogue.py",
    "symbol": "freeze_catalogue",
    "snippet": "def freeze_catalogue(path: Path) -> str:\n    path.parent.mkdir(parents=True, exist_ok=True)\n    if not path.exists():\n        path.write_bytes((ROOT / \"catalogue/courses.json\").read_bytes())\n    all_courses(path)\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef get_course(course_id: str) -> Course:",
    "ownership": "The application owns the dated provider snapshot, validation, deterministic matching and catalogue hash. Course providers own the original published facts; this filter is not an NVIDIA SDK feature.",
    "upstream": [
      {
        "label": "NUS published short-course source",
        "url": "https://www.stat.nus.edu.sg/education/cet/short-course/"
      },
      {
        "label": "onePA official course catalogue",
        "url": "https://www.onepa.gov.sg/courses"
      }
    ],
    "note": "Snapshot persistence/hashing are application-owned. New course pages require an explicit reviewed dated capture before recommendations use them. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A run-specific snapshot destination.",
    "outputs": "Validated frozen catalogue bytes and SHA-256."
  },
  "catalogue/Match constraints": {
    "title": "Match constraints",
    "path": "src/learning_lab/catalogue.py",
    "symbol": "search_courses",
    "snippet": "elif prefs.budget_sgd is not None and course.price_max_sgd is not None:\n            total = course.price_max_sgd + (course.extra_cost_sgd or 0)\n            if total > prefs.budget_sgd:\n                reason = \"Published upper fee including known extras exceeds the budget\"\n        if (\n            prefs.days is not None\n            and course.weekdays is not None\n            and not set(course.weekdays) <= set(prefs.days)\n        ):\n            reason = \"Published class days conflict with availability\"\n        if course.prerequisites and prefs.known_skills is not None:\n            if not set(course.prerequisites) <= set(prefs.known_skills):\n                reason = \"An explicit prerequisite has not been met\"\n        if reason:",
    "ownership": "The application owns the dated provider snapshot, validation, deterministic matching and catalogue hash. Course providers own the original published facts; this filter is not an NVIDIA SDK feature.",
    "upstream": [
      {
        "label": "NUS published short-course source",
        "url": "https://www.stat.nus.edu.sg/education/cet/short-course/"
      },
      {
        "label": "onePA official course catalogue",
        "url": "https://www.onepa.gov.sg/courses"
      }
    ],
    "note": "This is deterministic application matching, not LLM reasoning. It adds known extras but cannot infer funding eligibility or affordability from salary. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Published facts and trusted budget/day/prerequisite preferences.",
    "outputs": "Known conflicts excluded with explicit reasons."
  },
  "catalogue/Source links": {
    "title": "Source links",
    "path": "src/learning_lab/catalogue.py",
    "symbol": "Course",
    "snippet": "class Course(StrictModel):\n    id: str\n    title: str\n    provider: str\n    kind: Literal[\"skillsfuture\", \"community\"]\n    summary: str\n    tags: list[str]\n    source_url: HttpUrl\n    captured_on: date\n    venue: str | None = None\n    planning_area: str | None = None\n    price_min_sgd: float | None = Field(default=None, ge=0)\n    price_max_sgd: float | None = Field(default=None, ge=0)",
    "ownership": "The application owns the dated provider snapshot, validation, deterministic matching and catalogue hash. Course providers own the original published facts; this filter is not an NVIDIA SDK feature.",
    "upstream": [
      {
        "label": "NUS published short-course source",
        "url": "https://www.stat.nus.edu.sg/education/cet/short-course/"
      },
      {
        "label": "onePA official course catalogue",
        "url": "https://www.onepa.gov.sg/courses"
      }
    ],
    "note": "Providers own original facts; the application owns this snapshot. The new six-month, roughly S$20,000 example is not added by this excerpt. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A reviewed provider record, URL and capture date.",
    "outputs": "A typed course with provenance beside fee fields."
  },
  "gateway/Admit & bound calls": {
    "title": "Admit & bound calls",
    "path": "src/learning_lab/inference.py",
    "symbol": "Budget.admit",
    "snippet": "async def admit(self, role: str, mode: str) -> dict:\n        async with self.lock:\n            if self.calls >= self.limit:\n                raise BudgetExceeded(\n                    f\"Run stopped at the {self.limit}-call budget, including judges and retries\"\n                )\n            self.calls += 1\n            record = {\"call\": self.calls, \"role\": role, \"mode\": mode, \"status\": \"started\"}\n            self.records.append(record)\n            return record\n\n",
    "ownership": "This application owns atomic call admission, output caps, roles, usage/error records and optional tool-schema filtering. LiteLLM/provider transport and native Switchyard routing are separate components.",
    "upstream": [
      {
        "label": "LiteLLM proxy documentation",
        "url": "https://docs.litellm.ai/docs/simple_proxy"
      }
    ],
    "note": "This is application-owned admission, not routing or provider quota. Failures and support/judge calls count; unknown usage stays unknown. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A role-labelled attempt and workload limit.",
    "outputs": "Atomic admission evidence or rejection before dispatch."
  },
  "gateway/Limit tool schemas": {
    "title": "Limit tool schemas",
    "path": "src/learning_lab/inference.py",
    "symbol": "Gateway.complete",
    "snippet": "if role == \"assistant\" and self.allowed_tool_names is not None:\n            received = payload.get(\"tools\") or []\n            def name(tool):\n                return tool[\"function\"].get(\"name\") if isinstance(tool, dict) and isinstance(tool.get(\"function\"), dict) else None\n            names = [name(tool) for tool in received]\n            exposed = [tool for tool in received if name(tool) in self.allowed_tool_names]\n            if exposed:\n                payload[\"tools\"] = exposed\n            else:\n                payload.pop(\"tools\", None)\n            record[\"tool_surface\"] = {\n                \"source\": \"application_allowlist\", \"received\": names,\n                \"exposed\": [tool[\"function\"][\"name\"] for tool in exposed],\n                \"withheld\": [name for name in names if name not in self.allowed_tool_names],\n            }",
    "ownership": "This application owns atomic call admission, output caps, roles, usage/error records and optional tool-schema filtering. LiteLLM/provider transport and native Switchyard routing are separate components.",
    "upstream": [
      {
        "label": "LiteLLM proxy documentation",
        "url": "https://docs.litellm.ai/docs/simple_proxy"
      }
    ],
    "note": "The application compensates for the pinned Deep Agents adapter surface. Native Relay keeps the original request; its history is not rewritten. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Provider-bound assistant tools and a trusted allowlist.",
    "outputs": "Only allowed schemas plus received/exposed/withheld names."
  },
  "gateway/Record call ledger": {
    "title": "Record call ledger",
    "path": "src/learning_lab/inference.py",
    "symbol": "Gateway.complete",
    "snippet": "record.update(\n                status=\"completed\",\n                usage=result.get(\"usage\") if self.mode == \"live\" else None,\n                latency_ms=round((time.perf_counter() - started) * 1000),\n            )\n            return result\n        except BaseException as exc:\n            record[\"status\"] = \"cancelled\" if asyncio.current_task().cancelling() else \"failed\"\n            record[\"error_type\"] = type(exc).__name__\n            record[\"latency_ms\"] = round((time.perf_counter() - started) * 1000)\n            raise\n\n    async def _handle(self, request: web.Request) -> web.Response:",
    "ownership": "This application owns atomic call admission, output caps, roles, usage/error records and optional tool-schema filtering. LiteLLM/provider transport and native Switchyard routing are separate components.",
    "upstream": [
      {
        "label": "LiteLLM proxy documentation",
        "url": "https://docs.litellm.ai/docs/simple_proxy"
      }
    ],
    "note": "A completed model call is not an answer-quality verdict. Failed attempts are preserved and plausible replacement answers are never manufactured. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A completion or failure and any actual usage.",
    "outputs": "Call status, usage/unknown, latency and failure type."
  },
  "routing/Routing policy": {
    "title": "Routing policy",
    "path": "integrations/proxy/lab_routing.py",
    "symbol": "LabRoutingPlugin.__init__",
    "snippet": "class LabRoutingPlugin(LiteLLMRequestRewriter):\n    def __init__(self):\n        super().__init__()\n        self.stage = StageRoutingPlugin(\n            picker=\"efficient_first\",\n            confidence_threshold=0.5,\n            recent_window=3,\n            only_on_wrong_signal_escalation=True,\n        )\n\n    async def run(self, context):\n        count = len(set(context.candidate_models))",
    "ownership": "The pinned experimental Switchyard Stage plugin owns the routing decision. This application wrapper separates one-model fixed groups from exactly two-model routed groups and exposes bounded native decision metadata.",
    "upstream": [
      {
        "label": "Pinned Switchyard LiteLLM integration",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/tree/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm"
      }
    ],
    "note": "The maintained experimental policy owns routing. A fabricated easy/hard label is not native decision evidence; the current adapter supports exactly two routed candidates. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Native Stage settings and candidate inventory.",
    "outputs": "An efficient-first StageRoutingPlugin configuration."
  },
  "routing/Select model": {
    "title": "Select model",
    "path": "integrations/proxy/lab_routing.py",
    "symbol": "LabRoutingPlugin.run",
    "snippet": "async def run(self, context):\n        count = len(set(context.candidate_models))\n        if count == 1:\n            context.signals[\"learning_lab\"] = {\"route\": \"fixed\", \"candidate_count\": 1}\n            return context\n        if count != 2:\n            raise ValueError(\"The lab routing group must have exactly two distinct candidates\")\n        result = await self.stage.run(context)\n        decision = result.signals.get(\"switchyard\", {})\n        public_decision = {",
    "ownership": "The pinned experimental Switchyard Stage plugin owns the routing decision. This application wrapper separates one-model fixed groups from exactly two-model routed groups and exposes bounded native decision metadata.",
    "upstream": [
      {
        "label": "Pinned Switchyard LiteLLM integration",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/tree/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm"
      }
    ],
    "note": "The wrapper rejects other candidate counts. Appending a third model does not implement a valid three-way policy. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "LiteLLM context with one fixed or two distinct routed models.",
    "outputs": "A fixed context or actual native Stage result."
  },
  "routing/Decision evidence": {
    "title": "Decision evidence",
    "path": "integrations/proxy/lab_routing.py",
    "symbol": "LabRoutingPlugin.async_post_call_response_headers_hook",
    "snippet": "for key in (\"litellm_metadata\", \"metadata\"):\n            metadata = data.get(key)\n            if not isinstance(metadata, dict):\n                continue\n            signals = metadata.get(\"routing_plugin_signals\")\n            if isinstance(signals, dict) and isinstance(signals.get(\"switchyard\"), dict):\n                evidence = signals[\"switchyard\"]\n                break\n        if evidence is None:\n            return None\n        # The upstream decision structure contains a request patch in some\n        # algorithms. Only scalar decision fields are safe browser evidence.",
    "ownership": "The pinned experimental Switchyard Stage plugin owns the routing decision. This application wrapper separates one-model fixed groups from exactly two-model routed groups and exposes bounded native decision metadata.",
    "upstream": [
      {
        "label": "Pinned Switchyard LiteLLM integration",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/tree/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm"
      }
    ],
    "note": "Missing decisions stay missing. The subsequent code permits bounded scalar fields and excludes prompt/response payloads from the header. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Native routing_plugin_signals.switchyard metadata.",
    "outputs": "A response-correlated evidence envelope only when metadata exists."
  },
  "litellm/Model aliases": {
    "title": "Model aliases",
    "path": "integrations/proxy/litellm.yaml",
    "symbol": "model_list",
    "snippet": "model_list:\n  - model_name: lab-advisor-fixed\n    litellm_params:\n      model: os.environ/LAB_FIXED_MODEL\n      api_base: os.environ/LAB_FIXED_API_BASE\n      api_key: os.environ/LAB_FIXED_API_KEY\n      num_retries: 0\n  - model_name: lab-support\n    litellm_params:\n      model: os.environ/LAB_SUPPORT_MODEL\n      api_base: os.environ/LAB_SUPPORT_API_BASE\n      api_key: os.environ/LAB_SUPPORT_API_KEY\n      num_retries: 0",
    "ownership": "LiteLLM owns provider transport and proxy aliases. This application authors the provider-independent aliases, explicit no-fallback configuration and Switchyard plugin wiring.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "Variable names are configuration references, not values. Fixed harness comparison and routing are separate; no silent fallback is configured. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Explicit model/base-URL/key environment references.",
    "outputs": "Fixed advisor/support aliases; the file separately declares a routed pair."
  },
  "litellm/Switchyard hook": {
    "title": "Switchyard hook",
    "path": "integrations/proxy/litellm.yaml",
    "symbol": "router_settings / litellm_settings",
    "snippet": "router_settings:\n  num_retries: 0\n  fallbacks: []\n  context_window_fallbacks: []\n  plugins:\n    - lab_routing.ROUTING_PLUGIN\nlitellm_settings:\n  callbacks:\n    - lab_routing.ROUTING_PLUGIN\n  num_retries: 0\n  set_verbose: false\n  turn_off_message_logging: true\ngeneral_settings:\n  master_key: os.environ/LAB_PROXY_API_KEY",
    "ownership": "LiteLLM owns provider transport and proxy aliases. This application authors the provider-independent aliases, explicit no-fallback configuration and Switchyard plugin wiring.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "LiteLLM owns transport and Switchyard owns routing. Configuration does not prove proxy execution or a decision. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A validated inventory and plugin callback.",
    "outputs": "Native LiteLLM routing/callback wiring without hidden retries/fallbacks."
  },
  "litellm/Provider request": {
    "title": "Provider request",
    "path": "src/learning_lab/inference.py",
    "symbol": "Gateway.complete",
    "snippet": "endpoint = proxy or base_url()\n                record[\"provider_route\"] = \"litellm\" if proxy else \"nim-direct\"\n                if proxy:\n                    payload[\"model\"] = (\n                        \"lab-advisor-routed\" if role == \"assistant\" and self.model_route == \"switchyard\"\n                        else \"lab-advisor-fixed\" if role == \"assistant\" else \"lab-support\"\n                    )\n                record[\"requested_model\"] = payload[\"model\"]\n                response = await self._client.post(\n                    endpoint + \"/chat/completions\", json=payload,\n                    headers={\"Authorization\": f\"Bearer {key}\"},\n                )\n                if response.status_code >= 400:\n                    from .evidence import sanitize",
    "ownership": "LiteLLM owns provider transport and proxy aliases. This application authors the provider-independent aliases, explicit no-fallback configuration and Switchyard plugin wiring.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "This is the application-to-proxy call. LiteLLM resolves provider transport; a direct NIM route without proxy is separately labelled. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An admitted payload and selected alias/proxy connection.",
    "outputs": "One actual HTTP chat-completions request."
  },
  "providers/Hosted NIM": {
    "title": "Hosted NIM",
    "path": "integrations/proxy/launch.py",
    "symbol": "configured_environment",
    "snippet": "def configured_environment(source=None) -> dict[str, str]:\n    env = dict(os.environ if source is None else source)\n    main_model = env.get(\"NIM_MODEL\") or \"nvidia/nemotron-3.5-lightning-30b-a3b\"\n    support_model = env.get(\"NIM_USER_MODEL\") or \"nvidia/nemotron-3-nano-omni-30b-a3b-reasoning\"\n    for role, model in (\n        (\"FIXED\", main_model),\n        (\"SUPPORT\", support_model),\n        (\"CAPABLE\", main_model),\n        (\"EFFICIENT\", support_model),\n    ):\n        env.setdefault(f\"LAB_{role}_MODEL\", \"openai/\" + model)\n        env.setdefault(f\"LAB_{role}_API_BASE\", env.get(\"NIM_BASE_URL\", \"https://integrate.api.nvidia.com/v1\"))\n        env.setdefault(f\"LAB_{role}_API_KEY\", env.get(\"NVIDIA_API_KEY\", \"\"))\n    return env",
    "ownership": "Inference providers own model serving. LiteLLM adapts transport. This application supplies explicit provider/model/endpoint environment references and validates inventory; the wireframe hosts no provider.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "These defaults do not prove account availability or implement the proposed Super/GLM/Gemma experiment. The wireframe loads no environment or model. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Explicit NIM IDs and optional OpenAI-compatible endpoint.",
    "outputs": "Overridable fixed/support/capable/efficient configuration."
  },
  "providers/Brev endpoint": {
    "title": "Brev endpoint",
    "path": "integrations/proxy/litellm.yaml",
    "symbol": "model_list / litellm_params",
    "snippet": "# Providers, keys and endpoint values are configured by the local operator.\n# LiteLLM format: openai/<model> supports NIM and Brev OpenAI-compatible endpoints.\n# Frontier-specific LiteLLM providers may be selected using their native prefix.\nmodel_list:\n  - model_name: lab-advisor-fixed\n    litellm_params:\n      model: os.environ/LAB_FIXED_MODEL\n      api_base: os.environ/LAB_FIXED_API_BASE\n      api_key: os.environ/LAB_FIXED_API_KEY\n      num_retries: 0\n  - model_name: lab-support\n    litellm_params:",
    "ownership": "Inference providers own model serving. LiteLLM adapts transport. This application supplies explicit provider/model/endpoint environment references and validates inventory; the wireframe hosts no provider.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "This is generic endpoint configuration. It does not deploy on Brev or prove a Brev endpoint reachable, compatible or live-verified. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An explicit Brev-compatible endpoint, model and local key.",
    "outputs": "A configurable provider route when an operator supplies those values."
  },
  "providers/Frontier API": {
    "title": "Frontier API",
    "path": "integrations/proxy/validate_config.py",
    "symbol": "validate",
    "snippet": "for field in (\"model\", \"api_base\", \"api_key\"):\n                variable = model[field].removeprefix(\"os.environ/\")\n                if not environment.get(variable):\n                    raise ValueError(f\"Set {variable}; no provider call was attempted\")\n            model_id = environment[model[\"model\"].removeprefix(\"os.environ/\")]\n            if \"/\" not in model_id or not model_id.split(\"/\", 1)[1].strip():\n                raise ValueError(\n                    \"Proxy model IDs need both a LiteLLM provider prefix and a nonempty model name\"\n                )\n            resolved[group].append(model_id)\n    if len(set(resolved[\"lab-advisor-routed\"])) != 2:\n        raise ValueError(\"Switchyard needs two distinct model IDs; use fixed routing for one model\")",
    "ownership": "Inference providers own model serving. LiteLLM adapts transport. This application supplies explicit provider/model/endpoint environment references and validates inventory; the wireframe hosts no provider.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "Configuration validation is not a frontier request or capability test. Correct LiteLLM provider parameters and separate live verification remain required. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An explicit provider/model prefix and endpoint/key references.",
    "outputs": "A nonempty validated inventory or clear preflight failure."
  },
  "relay/Native scopes": {
    "title": "Native scopes",
    "path": "src/learning_lab/target.py",
    "symbol": "DirectTarget.reply",
    "snippet": "config[\"callbacks\"] = [NemoRelayDeepAgentsCallbackHandler()]\n                with nemo_relay.scope.scope(\"course-advisor-request\", nemo_relay.ScopeType.Agent):\n                    result = await self.agent.ainvoke(\n                        {\"messages\": [{\"role\": \"user\", \"content\": content}]}, config\n                    )\n                await nemo_relay.subscribers.flush_async()\n            else:\n                result = await self.agent.ainvoke(\n                    {\"messages\": [{\"role\": \"user\", \"content\": content}]}, config",
    "ownership": "NeMo Relay supplies native instrumentation and scope relationships. The application enables it, selects sinks and projects bounded evidence without inventing missing parent/session links.",
    "upstream": [
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "This enables actual native capture during execution. The wireframe contains source, not captured events; application messages alone are not Relay evidence. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A real invocation with native Relay enabled.",
    "outputs": "Native agent scopes/callback capture and flush."
  },
  "relay/Tool inputs / outputs": {
    "title": "Tool inputs / outputs",
    "path": "src/learning_lab/evidence.py",
    "symbol": "native_tool_records",
    "snippet": "result.append(\n            {\n                \"name\": scope[\"name\"],\n                \"arguments\": scope[\"input\"],\n                \"result\": content,\n                \"content\": json.dumps(content, ensure_ascii=False),\n                \"scope_uuid\": scope[\"uuid\"],\n                \"status\": scope[\"status\"],\n                \"evidence_origin\": \"native_relay\",\n            }\n        )\n    return result",
    "ownership": "NeMo Relay supplies native instrumentation and scope relationships. The application enables it, selects sinks and projects bounded evidence without inventing missing parent/session links.",
    "upstream": [
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "This application projection never infers a missing tool call from prose or creates new native records. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Observed native tool scopes in the selected artifact.",
    "outputs": "Sanitized name, actual arguments/result, UUID and evidence origin."
  },
  "relay/Parent relationships": {
    "title": "Parent relationships",
    "path": "src/learning_lab/evidence.py",
    "symbol": "relay_scopes",
    "snippet": "for (uid, category), pair in grouped.items():\n            start, end = pair.get(\"start\", {}), pair.get(\"end\", {})\n            event = start or end\n            parent = event.get(\"parent_uuid\")\n            failed = str(end.get(\"metadata\", {}).get(\"otel.status_code\", \"\")).upper() == \"ERROR\"\n            failed = failed or isinstance(end.get(\"data\"), dict) and end[\"data\"].get(\"is_error\") is True\n            scopes.append(\n                {\n                    \"id\": artifact[\"id\"] + \":\" + uid,\n                    \"uuid\": uid,\n                    \"parent_uuid\": parent,\n                    \"parent_id\": artifact[\"id\"] + \":\" + str(parent) if parent else None,\n                    \"artifact_id\": artifact[\"id\"],\n                    \"category\": category,\n                    \"name\": event.get(\"name\", category),",
    "ownership": "NeMo Relay supplies native instrumentation and scope relationships. The application enables it, selects sinks and projects bounded evidence without inventing missing parent/session links.",
    "upstream": [
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "Links come from native events. Absent phases/parents stay visible; managed Hermes session identity is not guessed from time, name or text. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Native start/end phases keyed by UUID and category.",
    "outputs": "Preserved parent IDs and completed/failed/incomplete states."
  },
  "records/Run manifest": {
    "title": "Run manifest",
    "path": "src/learning_lab/service.py",
    "symbol": "LabService.start_run",
    "snippet": "\"run_id\": run_id,\n            \"schema_version\": 2,\n            \"code_revision\": code_revision(),\n            \"story\": story(spec.story_id),\n            \"status\": \"queued\",\n            \"started_at\": now(),\n            \"spec\": spec.model_dump(),\n            \"owner_pid\": os.getpid(),\n            \"episodes\": [],\n            \"calls\": 0,\n            \"budget\": 120,\n            \"models\": {role: model_id(role) for role in [\"assistant\", \"user\", \"judge\", \"summary\"]}\n            if spec.mode == \"live\"",
    "ownership": "The application owns persisted ledgers, sanitization, artifact allowlists and UI projections. Native Relay/Intake remains the owner of its original events and IDs; an application record is not a replacement native trace.",
    "upstream": [],
    "note": "This is application bookkeeping. A commit reference does not imply uncommitted source existed there; frozen facts/hashes remain separate provenance. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The validated run specification and local source revision.",
    "outputs": "A manifest retaining story, mode, lifecycle, budget and model roles."
  },
  "records/Artifact files": {
    "title": "Artifact files",
    "path": "src/learning_lab/evidence.py",
    "symbol": "list_artifacts",
    "snippet": "def list_artifacts(folder: Path) -> list[dict]:\n    result = []\n    for path in sorted(_paths(folder) or []):\n        relative = path.relative_to(folder).as_posix()\n        kind = _FILES[path.name]\n        result.append(\n            {\n                \"id\": hashlib.sha256(relative.encode()).hexdigest()[:24],\n                \"name\": relative,\n                \"kind\": kind,\n                \"size\": path.stat().st_size,\n                \"path\": str(path.absolute()),\n                \"code_refs\": _code_refs(kind),\n            }",
    "ownership": "The application owns persisted ledgers, sanitization, artifact allowlists and UI projections. Native Relay/Intake remains the owner of its original events and IDs; an application record is not a replacement native trace.",
    "upstream": [],
    "note": "The application exposes known artifacts, not arbitrary host files. Raw private payloads are absent from the wireframe. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An allowlisted selected run/episode directory.",
    "outputs": "Opaque artifact IDs, kind, size and source references."
  },
  "records/Reopen evidence": {
    "title": "Reopen evidence",
    "path": "src/learning_lab/service.py",
    "symbol": "LabService.get_run",
    "snippet": "def get_run(self, run_id: str):\n        if not re.fullmatch(r\"[a-f0-9-]{36}\", run_id):\n            raise ValueError(\"Invalid run ID\")\n        path = self.runs / run_id / \"run.json\"\n        if not path.exists():\n            raise ValueError(\"Run not found\")\n        result = json.loads(path.read_text())\n        events = path.with_name(\"events.jsonl\")\n        result[\"events\"] = (\n            [json.loads(line) for line in events.read_text().splitlines()] if events.exists() else []\n        )\n        return result",
    "ownership": "The application owns persisted ledgers, sanitization, artifact allowlists and UI projections. Native Relay/Intake remains the owner of its original events and IDs; an application record is not a replacement native trace.",
    "upstream": [],
    "note": "This read path starts no simulation, generation or inference and does not overwrite earlier failures. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An existing run UUID.",
    "outputs": "The saved manifest and events read from disk."
  },
  "helix/Evaluate saved reply": {
    "title": "Evaluate saved reply",
    "path": "integrations/helix/evaluate.py",
    "symbol": "evaluate",
    "snippet": "def evaluate(rows: list[dict]) -> dict:\n    if not rows:\n        raise ValueError(\"No evaluation rows supplied\")\n    result = Evaluator().run_sync(\n        metrics=[ExactMatchMetric(reference=\"{{item.expected}}\", candidate=\"{{item.output}}\")],\n        dataset=rows,\n        config=RunConfig(parallelism=1),\n    )\n    return result.model_dump(mode=\"json\")",
    "ownership": "The application authors transparent applicable criterion rows from saved replies and frozen facts. Helix Evals SDK 0.9.1 executes the ExactMatch metric. These narrow assertions do not certify the whole answer.",
    "upstream": [
      {
        "label": "Helix 0.9.1 Evals SDK",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.9.1/packages/nhx_evals_sdk"
      }
    ],
    "note": "The application authors assertions; the isolated 0.9.1 SDK executes them. No fresh advisor inference or whole-answer certification is implied. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Applicable boolean criteria from saved replies.",
    "outputs": "The actual Helix Evals ExactMatch result."
  },
  "helix/Criterion reasons": {
    "title": "Criterion reasons",
    "path": "src/learning_lab/evaluation.py",
    "symbol": "evaluate_saved_run.add",
    "snippet": "def add(criterion, status, reason, evidence=None):\n                rows.append(\n                    {\n                        **base,\n                        \"criterion\": criterion,\n                        \"status\": status,\n                        \"reason\": reason,\n                        \"expected\": \"true\",\n                        \"output\": \"true\"\n                        if status == \"pass\"\n                        else \"false\"\n                        if status in {\"fail\", \"error\"}\n                        else None,\n                        \"evidence\": sanitize(evidence or {}),\n                    }",
    "ownership": "The application authors transparent applicable criterion rows from saved replies and frozen facts. Helix Evals SDK 0.9.1 executes the ExactMatch metric. These narrow assertions do not certify the whole answer.",
    "upstream": [
      {
        "label": "Helix 0.9.1 Evals SDK",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.9.1/packages/nhx_evals_sdk"
      }
    ],
    "note": "Unavailable/not-applicable evidence is not counted as pass. Aggregate scores do not replace these reasons. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An assertion, its status/reason and evidence.",
    "outputs": "Inspectable per-turn criterion rows before SDK scoring."
  },
  "helix/Failures & limits": {
    "title": "Failures & limits",
    "path": "src/learning_lab/outcomes.py",
    "symbol": "answer_outcome",
    "snippet": "def answer_outcome(content) -> dict:\n    text = answer_text(content).strip()\n    if not text:\n        return {\"status\": \"invalid\", \"code\": \"empty_answer\", \"reason\": \"No public answer was returned.\"}\n    if re.fullmatch(r\"(?:\\[ERROR\\s*:[\\s\\S]*?\\]\\s*)+\", text, re.IGNORECASE):\n        return {\n            \"status\": \"invalid\",\n            \"code\": \"model_error_text\",\n            \"reason\": \"The model returned error text as its answer. This is not proof of a local runtime exception.\",\n        }\n    pseudo_tool = bool(re.search(r\"<(?:tool_call|function[= >]|parameter[= >])\", text, re.IGNORECASE))\n    try:\n        payload = json.loads(text)",
    "ownership": "The application authors transparent applicable criterion rows from saved replies and frozen facts. Helix Evals SDK 0.9.1 executes the ExactMatch metric. These narrow assertions do not certify the whole answer.",
    "upstream": [
      {
        "label": "Helix 0.9.1 Evals SDK",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.9.1/packages/nhx_evals_sdk"
      }
    ],
    "note": "This application gate is separate from Helix execution. Literal model error text does not prove a local exception; valid text can still be factually wrong. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The actual public output.",
    "outputs": "Explicit empty-answer/model-error failures before factual checks."
  },
  "platform/Register recipe": {
    "title": "Register recipe",
    "path": "integrations/platform/bridge.py",
    "symbol": "execute.register",
    "snippet": "for relative, content in source_contents.items():\n            await files.upload_file(name=fileset, path=relative, content=content)\n        response = await client.register_agent(\n            body=RegisterAgentRequest(\n                name=name,\n                config=config,\n                config_format=\"nemo-agents-spec-v1\",\n                description=config.get(\"description\", \"\"),\n            )\n        )\n        created = response.data()\n        observed = (await client.get_agent(name=name)).data()",
    "ownership": "Helix is a control plane spanning agent operations, evaluation, experiments and hardening. This retained bridge exposes agents, deployments, sessions and native Intake; additional managed evaluation jobs are planned. The application owns the explicit local/remote subprocess bridge, admission leases, durable session guard and bounded cleanup/recovery orchestration.",
    "upstream": [
      {
        "label": "Helix 0.10.0 release",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/releases/tag/0.10.0"
      },
      {
        "label": "Helix deployment guide",
        "url": "https://docs.nvidia.com/nemo-helix/latest/documentation/agents/deploy-agents/"
      }
    ],
    "note": "Native Platform owns registration. Exact source reuse and later image readiness remain separate; registration is not a running correct agent. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Reviewed descriptor, allowlisted skill/manifest bytes and name.",
    "outputs": "Actual Files SDK uploads and RegisterAgentRequest."
  },
  "platform/Deploy agent": {
    "title": "Deploy agent",
    "path": "integrations/platform/bridge.py",
    "symbol": "execute.deploy",
    "snippet": "body = CreateAgentDeploymentRequest(\n            agent=name_of(args, \"agent\"),\n            name=name_of(args),\n            deployment_mode=mode,\n            image=image,\n            environment=environment,\n        )\n        deployment = (await client.create_deployment(body=body)).data()\n        return {\n            \"deployment\": clean(deployment),\n            \"ready\": deployment.status == \"running\",\n            \"next\": \"Poll deployment status; no inference has been performed.\",\n        }",
    "ownership": "Helix is a control plane spanning agent operations, evaluation, experiments and hardening. This retained bridge exposes agents, deployments, sessions and native Intake; additional managed evaluation jobs are planned. The application owns the explicit local/remote subprocess bridge, admission leases, durable session guard and bounded cleanup/recovery orchestration.",
    "upstream": [
      {
        "label": "Helix 0.10.0 release",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/releases/tag/0.10.0"
      },
      {
        "label": "Helix deployment guide",
        "url": "https://docs.nvidia.com/nemo-helix/latest/documentation/agents/deploy-agents/"
      }
    ],
    "note": "OpenShell and Docker are explicit modes without silent fallback. Status alone proves neither sandbox enforcement nor correct inference. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An exact image, agent, name and explicit environment/mode.",
    "outputs": "A native create-deployment response requiring status checks."
  },
  "platform/Session lifecycle": {
    "title": "Session lifecycle",
    "path": "integrations/platform/bridge.py",
    "symbol": "execute.sessions_close",
    "snippet": "if operation == \"sessions_close\":\n        from session_drain import close_session\n\n        return clean(\n            await close_session(\n                client,\n                session_identity(args),\n                required_runtime_cleanup=args.get(\"require_runtime_drain\", False),\n            )\n        )\n    if operation == \"sessions_recover\":\n        from native_cleanup import recover_session\n\n        return clean(\n            await recover_session(client, session_identity(args), receipt_path=recovery_receipt(args))\n        )",
    "ownership": "Helix is a control plane spanning agent operations, evaluation, experiments and hardening. This retained bridge exposes agents, deployments, sessions and native Intake; additional managed evaluation jobs are planned. The application owns the explicit local/remote subprocess bridge, admission leases, durable session guard and bounded cleanup/recovery orchestration.",
    "upstream": [
      {
        "label": "Helix 0.10.0 release",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/releases/tag/0.10.0"
      },
      {
        "label": "Helix deployment guide",
        "url": "https://docs.nvidia.com/nemo-helix/latest/documentation/agents/deploy-agents/"
      }
    ],
    "note": "Positive native drain is required for uncertain work. Whole-deployment recovery is explicit; runtime 404 is not treated as proof of stopped work. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An owned native session and strict-drain requirement.",
    "outputs": "Cleanup proof and logical closure, or retained blocked recovery."
  },
  "openshell/Agent / tool boundary": {
    "title": "Agent / tool boundary",
    "path": "integrations/platform/package_agent.py",
    "symbol": "customize_dockerfile",
    "snippet": "# Native OpenShell needs its WORKDIR writable for staging. Root-owned\n    # immutable children plus a sticky workdir prevent replacing packaged code\n    # or its trusted preset while keeping explicit scratch locations writable.\n    patch += \"\"\"RUN chown -R root:root /workspace && chmod -R a-w /workspace && \\\\\n    mkdir -p /workspace/workspace /workspace/artifacts /workspace/scratch && \\\\\n    chown -R agent:sandbox /workspace/workspace /workspace/artifacts /workspace/scratch && \\\\\n    chmod -R u+rwX,g+rwX /workspace/workspace /workspace/artifacts /workspace/scratch && \\\\\n    chmod 2770 /workspace/workspace /workspace/artifacts /workspace/scratch && \\\\\n    chown root:sandbox /workspace && chmod 1775 /workspace && \\\\\n    usermod -a -G sandbox agent\n\"\"\"\n    text = text.replace(marker, patch + marker)",
    "ownership": "The application owns minimal image packaging, root-owned files and the hash-checked public preset. OpenShell owns native sandbox enforcement through the Helix executor. The checked-in policy intent file is documentation, not enforcement proof.",
    "upstream": [
      {
        "label": "OpenShell v0.1.6 source",
        "url": "https://github.com/NVIDIA/OpenShell/tree/v0.1.6"
      },
      {
        "label": "Helix 0.10.0 source",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.10.0"
      }
    ],
    "note": "This excerpt authors image hardening; OpenShell owns enforcement. Separate native allow/deny probes are required, and no extra runtime tools are granted. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The reviewed minimal image and executor boundary.",
    "outputs": "Root-owned immutable code/catalogue/preset with named writable scratch."
  },
  "openshell/Network policy": {
    "title": "Network policy",
    "path": "integrations/platform/config.local.yaml",
    "symbol": "deployments.executors.lab-openshell.config",
    "snippet": "- name: lab-openshell\n      backend: openshell\n      config:\n        gateway_endpoint: http://127.0.0.1:17670\n        platform_egress:\n          host: host.docker.internal\n          port: 8080\n        serve_workdir: /tmp\n        landlock_compatibility: hard_requirement\n# For Linux, replace the platform_egress host with the address verified from the\n# sandbox. Loopback in an agent sandbox is not the host's loopback.",
    "ownership": "The application owns minimal image packaging, root-owned files and the hash-checked public preset. OpenShell owns native sandbox enforcement through the Helix executor. The checked-in policy intent file is documentation, not enforcement proof.",
    "upstream": [
      {
        "label": "OpenShell v0.1.6 source",
        "url": "https://github.com/NVIDIA/OpenShell/tree/v0.1.6"
      },
      {
        "label": "Helix 0.10.0 source",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.10.0"
      }
    ],
    "note": "This excerpt does not itself apply or verify effective native network policy. Intent metadata is not enforcement; no firewall or unrelated-egress relaxation is implied. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A trusted gateway and mandatory Platform egress origin.",
    "outputs": "Versioned executor confinement and Platform-access configuration."
  },
  "openshell/Access review": {
    "title": "Access review",
    "path": "integrations/platform/native_cleanup.py",
    "symbol": "_gateway_identity",
    "snippet": "tls = config.tls\n    # This recovery client supplies no separate bearer/OIDC identity. Its\n    # authenticated workspace proof therefore requires pinned mutual TLS.\n    if (parsed.scheme != \"https\" or config.use_insecure() or tls is None\n            or not tls.ca_cert_path or not tls.client_cert_path or not tls.client_key_path):\n        raise RecoveryBlocked(\"Native recovery requires configured mutual TLS with a CA, client certificate and key\")\n    if not Path(tls.client_key_path).is_file():\n        raise RecoveryBlocked(\"The native recovery mutual TLS client key is unavailable\")\n\n    def digest(path):\n        return hashlib.sha256(Path(path).read_bytes()).hexdigest() if path else None\n",
    "ownership": "The application owns minimal image packaging, root-owned files and the hash-checked public preset. OpenShell owns native sandbox enforcement through the Helix executor. The checked-in policy intent file is documentation, not enforcement proof.",
    "upstream": [
      {
        "label": "OpenShell v0.1.6 source",
        "url": "https://github.com/NVIDIA/OpenShell/tree/v0.1.6"
      },
      {
        "label": "Helix 0.10.0 source",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.10.0"
      }
    ],
    "note": "This operation is not implemented by this excerpt. It checks authenticated recovery access, not an interactive native policy approval/review UI. That UI remains a proposal. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The owning executor selected through trusted Platform metadata.",
    "outputs": "A fail-closed mutual-TLS precondition for native recovery."
  },
  "personas/Singapore Personas": {
    "title": "Singapore Personas",
    "path": "src/learning_lab/datasets.py",
    "symbol": "_dataset",
    "snippet": "def _dataset(query: DatasetQuery):\n    meta = _description(query.source)\n    if not meta[\"ready\"]:\n        raise ValueError(meta.get(\"reason\", \"Dataset is not ready\") + \". \" + meta[\"setup\"])\n    dataset = pads.dataset([str(path) for path in _paths(query.source)], format=\"parquet\")\n    expression = None\n\n    def add(part):\n        nonlocal expression",
    "ownership": "NVIDIA supplies the synthetic persona distributions. This application owns local filtering, reservoir sampling, SHA-256 hashing and exact-row locks; these are not NeMo generation features.",
    "upstream": [
      {
        "label": "Pinned HF dataset",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer"
      },
      {
        "label": "Pinned HF revision",
        "url": "https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/tree/a3994709410410f834bd949d643d3f2796908969"
      },
      {
        "label": "Singapore NGC Extended",
        "url": "https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg"
      }
    ],
    "note": "The application reads the selected installed distribution; it does not download it or infer missing OCEAN fields. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An explicit HF profile-only or Singapore NGC Extended query.",
    "outputs": "The validated local corpus, filter expression and source metadata."
  },
  "designer/Designer scenarios": {
    "title": "Designer scenarios",
    "path": "integrations/designer/learning_preferences.py",
    "symbol": "workbench_builder",
    "snippet": "operation = request[\"spec\"][\"operation\"]\n    if operation != \"columns\":\n        is_profile = operation == \"profiles\"\n        builder.add_column(\n            dd.LLMStructuredColumnConfig(\n                name=\"generated_profile\" if is_profile else \"generated_scenario\",\n                model_alias=\"designer\",\n                system_prompt=system,\n                prompt=(\n                    \"Create a NEW, distinct synthetic Singapore learner profile inspired by the source. \"\n                    \"Vary the person, occupation and interests plausibly. This is generated data, not a new \"\n                    \"Nemotron source record. Do not copy the source UUID or generate OCEAN scores.\\n\"",
    "ownership": "NeMo Data Designer 0.10 owns native structured-column generation. The application owns the closed field specification, source seeding, schema validation, hypothetical labels and parent lineage.",
    "upstream": [
      {
        "label": "Data Designer v0.10.0 guide",
        "url": "https://github.com/NVIDIA-NeMo/DataDesigner/blob/v0.10.0/skills/data-designer/SKILL.md"
      }
    ],
    "note": "This configures an SDK column; later DataDesigner create/batch execution performs inference through the bounded gateway. Generated preferences remain hypotheses. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Frozen source seeds and an explicit generation operation.",
    "outputs": "Native Data Designer structured-column configuration."
  },
  "designer/Lock source & lineage": {
    "title": "Lock source & lineage",
    "path": "src/learning_lab/workbench.py",
    "symbol": "validate_generated_payload",
    "snippet": "if any(\n            record.get(key) != seed[key]\n            for key in (\n                \"source_id\",\n                \"source_revision\",\n                \"original_profile_json\",\n                \"original_profile_sha256\",\n                \"generation_index\",\n            )\n        ):\n            raise ValueError(\"Designer changed source lineage or reordered source records\")\n        original = json.loads(seed[\"original_profile_json\"])\n        if profile_hash(original) != seed[\"original_profile_sha256\"]:\n            raise ValueError(\"Original profile hash verification failed\")\n        generated = {}",
    "ownership": "NeMo Data Designer 0.10 owns native structured-column generation. The application owns the closed field specification, source seeding, schema validation, hypothetical labels and parent lineage.",
    "upstream": [
      {
        "label": "Data Designer v0.10.0 guide",
        "url": "https://github.com/NVIDIA-NeMo/DataDesigner/blob/v0.10.0/skills/data-designer/SKILL.md"
      }
    ],
    "note": "Application-owned validation rejects changed lineage; typed fields and new generated identities are checked later in this function. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Generated rows and their original frozen seeds.",
    "outputs": "Rows whose identity, order and original-profile hash are preserved."
  },
  "usersim/Activate one profile": {
    "title": "Activate one profile",
    "path": "src/learning_lab/simulation.py",
    "symbol": "hosted_episode",
    "snippet": "runtime = ProbeEpisodeRuntime.from_resolved_row(copy.deepcopy(row), models=host_models(gateway.mode))\n    try:\n        event = await runtime.advance()\n        while isinstance(event, ActivationRequest):\n            if event.role == \"assistant\":\n                if event.continues_turn:\n                    raise RuntimeError(\"Unexpected assistant resampling in a side-effectful external target\")\n                message = next(m[\"content\"] for m in reversed(event.messages) if m[\"role\"] == \"user\")\n                await on_event({\"role\": \"user\", \"content\": message})",
    "ownership": "NeMo UserSim owns the episode/activation protocol. The application adapter sends the latest public learner message to the real advisor target and returns its actual public reply.",
    "upstream": [
      {
        "label": "UserSim v0.3.0 external runtime",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md"
      },
      {
        "label": "UserSim v0.3.0 extension API",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md"
      }
    ],
    "note": "UserSim owns activation. The application owns copying the row and dispatching the external target; simulator tools do not own the advisor. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "One resolved profile/scenario and explicit models.",
    "outputs": "A native activation request or terminal event."
  },
  "usersim/Public messages": {
    "title": "Public messages",
    "path": "src/learning_lab/simulation.py",
    "symbol": "hosted_episode",
    "snippet": "message = next(m[\"content\"] for m in reversed(event.messages) if m[\"role\"] == \"user\")\n                await on_event({\"role\": \"user\", \"content\": message})\n                previous = len(gateway.budget.records)\n                explicit = preferences\n                if explicit is None and constraint_overrides:\n                    explicit = Preferences(goal=message, **constraint_overrides)\n                reply = await target.reply(message, explicit) if explicit else await target.reply(message)\n                await on_event({\"role\": \"assistant\", **reply})\n                response = {\"role\": \"assistant\", \"content\": reply[\"content\"]}",
    "ownership": "NeMo UserSim owns the episode/activation protocol. The application adapter sends the latest public learner message to the real advisor target and returns its actual public reply.",
    "upstream": [
      {
        "label": "UserSim v0.3.0 external runtime",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md"
      },
      {
        "label": "UserSim v0.3.0 extension API",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md"
      }
    ],
    "note": "Only the latest public learner message is sent to the target. This excerpt does not implement the proposed delayed salary disclosure policy. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The native activation and trusted scenario preferences.",
    "outputs": "The latest public learner message and actual advisor reply."
  },
  "usersim/Isolated conversation": {
    "title": "Isolated conversation",
    "path": "src/learning_lab/simulation.py",
    "symbol": "hosted_episode",
    "snippet": "recorded = {\"activation_id\": event.activation_id, \"response\": response}\n            if usage and all(v is not None for v in usage.values()):\n                recorded[\"usage\"] = usage\n            event = await runtime.advance(recorded)\n        return await runtime.finalize()\n    finally:\n        await runtime.close()\n",
    "ownership": "NeMo UserSim owns the episode/activation protocol. The application adapter sends the latest public learner message to the real advisor target and returns its actual public reply.",
    "upstream": [
      {
        "label": "UserSim v0.3.0 external runtime",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md"
      },
      {
        "label": "UserSim v0.3.0 extension API",
        "url": "https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md"
      }
    ],
    "note": "The native activation ID is preserved and close runs in finally. Target memory and UserSim state are separate; missing usage is not filled in. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A target response and actual usage when available.",
    "outputs": "Correlated activation advancement, finalization and cleanup."
  },
  "fabric/Fabric lifecycle": {
    "title": "Fabric lifecycle",
    "path": "src/learning_lab/fabric_target.py",
    "symbol": "FabricTarget.__aenter__",
    "snippet": "self.runtime = await self.fabric.start_runtime(self.config, base_dir=ROOT)\n            await self.runtime.__aenter__()\n            lifecycle(self.workspace.parent, \"runtime_started\", thread_id=self.thread_id)\n            return self\n        except BaseException as exc:\n            try:\n                lifecycle(self.workspace.parent, \"runtime_start_failed\", error_type=type(exc).__name__)\n            except Exception as evidence_error:\n                # Preserve the original startup failure even if its evidence\n                # directory became unwritable. Cleanup must still run.",
    "ownership": "NeMo Fabric 0.6.1 owns native planning, Doctor checks, adapter resolution and runtime lifecycle. This application chooses the harness and supplies its bounded model, tools and Relay configuration.",
    "upstream": [
      {
        "label": "Fabric v0.6.1 Deep Agents adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/README.md"
      },
      {
        "label": "Fabric v0.6.1 release",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/releases/tag/v0.6.1"
      }
    ],
    "note": "Fabric owns the runtime; the application owns async cleanup and lifecycle records. Startup is distinct from model invocation and answer validity. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Configuration that passed preceding checks.",
    "outputs": "An entered persistent runtime or saved startup failure."
  },
  "deepagents/Deep Agents harness": {
    "title": "Deep Agents harness",
    "path": "src/learning_lab/target.py",
    "symbol": "DirectTarget.reply",
    "snippet": "config[\"callbacks\"] = [NemoRelayDeepAgentsCallbackHandler()]\n                with nemo_relay.scope.scope(\"course-advisor-request\", nemo_relay.ScopeType.Agent):\n                    result = await self.agent.ainvoke(\n                        {\"messages\": [{\"role\": \"user\", \"content\": content}]}, config\n                    )\n                await nemo_relay.subscribers.flush_async()\n            else:\n                result = await self.agent.ainvoke(\n                    {\"messages\": [{\"role\": \"user\", \"content\": content}]}, config\n                )",
    "ownership": "LangChain Deep Agents owns create_deep_agent and harness execution. The application supplies catalogue MCP tools, memory boundaries and read-only middleware. Native Relay wrapping is explicit.",
    "upstream": [
      {
        "label": "Deep Agents maintained repository",
        "url": "https://github.com/langchain-ai/deepagents"
      },
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "This is the real ainvoke boundary. Call/round admission and public-answer validation surround it; transport success is insufficient. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A public message, explicit preferences and thread state.",
    "outputs": "An actual agent invocation with optional native capture."
  },
  "hermes/Hermes harness": {
    "title": "Hermes harness",
    "path": "src/learning_lab/fabric_target.py",
    "symbol": "FabricTarget.reply",
    "snippet": "before = {scope[\"uuid\"] for scope in relay_scopes(self.workspace.parent)[\"scopes\"]}\n        lifecycle(self.workspace.parent, \"invocation_started\", thread_id=self.thread_id)\n        try:\n            result = await self.runtime.invoke(\n                request=RunRequest(input=message, relay_session_root=self.thread_id)\n            )\n        except BaseException as exc:\n            lifecycle(self.workspace.parent, \"invocation_failed\", error_type=type(exc).__name__)\n            save_evidence(\n                self.workspace.parent / \"reply-outcomes.jsonl\",",
    "ownership": "NousResearch Hermes supplies the agent harness; the maintained Fabric adapter integrates it. The application owns interpreter selection and the explicit bounded retry-policy directory.",
    "upstream": [
      {
        "label": "Pinned Hermes source",
        "url": "https://github.com/NousResearch/hermes-agent/tree/b200f5bc60e31588ba2cb60e288029c4a54ba5fa"
      },
      {
        "label": "Fabric v0.6.1 Hermes adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/tree/v0.6.1/adapters/python/hermes"
      }
    ],
    "note": "Application limits still apply. Managed Hermes session-to-Relay correlation is unsupported by the pinned adapter; no unified trace is invented. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A public message and the selected Fabric/Hermes runtime.",
    "outputs": "An actual native RunRequest invocation and lifecycle evidence."
  },
  "hermes/Application policy": {
    "title": "Application policy",
    "path": "src/learning_lab/target.py",
    "symbol": "system_prompt",
    "snippet": "def system_prompt(strategy: str) -> str:\n    skill = (ROOT / \"runtime-skills/course-advisor/SKILL.md\").read_text().split(\"---\", 2)[-1]\n    instruction = (\n        \"Offer a concise shortlist and state the unresolved constraints.\"\n        if strategy == \"concise\"\n        else \"Ask one useful clarification when key constraints are missing, then recommend suitable options. \"\n        \"Before answering, check course IDs and official links. Separate the listed fee, known extras \"\n        \"and unknown costs. When extra_cost_sgd is null, explicitly say extras are unknown; \"\n        \"never describe the listed amount as a confirmed total or say there are no extra fees.\"\n    )\n    return f\"You are a Singapore learning and community-class advisor. Keep replies under 180 words, list at most three courses, and include official links. Use short paragraphs or bullets. {instruction}\\n{skill}\"\n",
    "ownership": "NousResearch Hermes supplies the agent harness; the maintained Fabric adapter integrates it. The application owns interpreter selection and the explicit bounded retry-policy directory. The shared application system policy comes from target.system_prompt.",
    "upstream": [
      {
        "label": "Pinned Hermes source",
        "url": "https://github.com/NousResearch/hermes-agent/tree/b200f5bc60e31588ba2cb60e288029c4a54ba5fa"
      },
      {
        "label": "Fabric v0.6.1 Hermes adapter",
        "url": "https://github.com/NVIDIA/NeMo-Fabric/tree/v0.6.1/adapters/python/hermes"
      }
    ],
    "note": "This is application policy, not intrinsic Deep Agents SDK behaviour. Instructions supplement deterministic boundaries and do not prove correctness. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The explicit strategy and reviewed advisor skill.",
    "outputs": "Application system instructions for the advisor."
  },
  "mcp/Read-only course MCP": {
    "title": "Read-only course MCP",
    "path": "src/learning_lab/course_mcp.py",
    "symbol": "search_courses",
    "snippet": "return match(\n            bound_preferences(\n                dict(\n                    goal=goal,\n                    budget_sgd=budget_sgd,\n                    days=normalize_days(days),\n                    planning_area=planning_area,\n                    known_skills=known_skills,\n                    kind=kind,\n                )\n            )\n        )",
    "ownership": "The application authors the three catalogue tools and binds trusted preferences. FastMCP supplies the MCP server/protocol; MCP does not itself establish catalogue accuracy or subsidy eligibility.",
    "upstream": [
      {
        "label": "MCP Python SDK",
        "url": "https://github.com/modelcontextprotocol/python-sdk"
      }
    ],
    "note": "This actual MCP tool delegates to application matching. No-match and unknowns stay visible; it cannot authorize booking, payment or job applications. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A goal and optional explicit course constraints.",
    "outputs": "The matcher result after trusted preference rebinding."
  },
  "catalogue/Dated catalogue": {
    "title": "Dated catalogue",
    "path": "src/learning_lab/catalogue.py",
    "symbol": "freeze_catalogue",
    "snippet": "def freeze_catalogue(path: Path) -> str:\n    path.parent.mkdir(parents=True, exist_ok=True)\n    if not path.exists():\n        path.write_bytes((ROOT / \"catalogue/courses.json\").read_bytes())\n    all_courses(path)\n    return hashlib.sha256(path.read_bytes()).hexdigest()\n\n\ndef get_course(course_id: str) -> Course:",
    "ownership": "The application owns the dated provider snapshot, validation, deterministic matching and catalogue hash. Course providers own the original published facts; this filter is not an NVIDIA SDK feature.",
    "upstream": [
      {
        "label": "NUS published short-course source",
        "url": "https://www.stat.nus.edu.sg/education/cet/short-course/"
      },
      {
        "label": "onePA official course catalogue",
        "url": "https://www.onepa.gov.sg/courses"
      }
    ],
    "note": "Snapshot persistence/hashing are application-owned. New course pages require an explicit reviewed dated capture before recommendations use them. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A run-specific snapshot destination.",
    "outputs": "Validated frozen catalogue bytes and SHA-256."
  },
  "mcp/Budget & availability": {
    "title": "Budget & availability",
    "path": "src/learning_lab/course_mcp.py",
    "symbol": "bound_preferences",
    "snippet": "if preset_file:\n        if remote:\n            raise ValueError(\"Choose exactly one deployed learner-constraint channel\")\n        raw = Path(preset_file).read_bytes()\n        expected = os.getenv(\"LAB_PREFERENCES_PRESET_SHA256\", \"\")\n        if len(raw) > 16000 or len(expected) != 64 or hashlib.sha256(raw).hexdigest() != expected:\n            raise ValueError(\"The frozen teaching preset failed its declared integrity check\")\n        explicit = Preferences.model_validate_json(raw).model_dump(exclude_none=True)\n        for name in [\"goal\", \"budget_sgd\", \"days\", \"known_skills\", \"kind\", \"planning_area\"]:\n            if name in explicit:\n                values[name] = explicit[name]\n            elif name != \"goal\":\n                values[name] = None\n        return Preferences.model_validate(values)",
    "ownership": "The application authors the three catalogue tools and binds trusted preferences. FastMCP supplies the MCP server/protocol; MCP does not itself establish catalogue accuracy or subsidy eligibility.",
    "upstream": [
      {
        "label": "MCP Python SDK",
        "url": "https://github.com/modelcontextprotocol/python-sdk"
      }
    ],
    "note": "The shown native path is the public photography preset. Changed/missing integrity fails closed. Progressive salary disclosure is not implemented here. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "The trusted preset path/hash or a separate authenticated channel.",
    "outputs": "Hard constraints overriding conflicting model-supplied values."
  },
  "gateway/Call limits & ledger": {
    "title": "Call limits & ledger",
    "path": "src/learning_lab/inference.py",
    "symbol": "Budget.admit",
    "snippet": "async def admit(self, role: str, mode: str) -> dict:\n        async with self.lock:\n            if self.calls >= self.limit:\n                raise BudgetExceeded(\n                    f\"Run stopped at the {self.limit}-call budget, including judges and retries\"\n                )\n            self.calls += 1\n            record = {\"call\": self.calls, \"role\": role, \"mode\": mode, \"status\": \"started\"}\n            self.records.append(record)\n            return record\n\n",
    "ownership": "This application owns atomic call admission, output caps, roles, usage/error records and optional tool-schema filtering. LiteLLM/provider transport and native Switchyard routing are separate components.",
    "upstream": [
      {
        "label": "LiteLLM proxy documentation",
        "url": "https://docs.litellm.ai/docs/simple_proxy"
      }
    ],
    "note": "This is application-owned admission, not routing or provider quota. Failures and support/judge calls count; unknown usage stays unknown. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A role-labelled attempt and workload limit.",
    "outputs": "Atomic admission evidence or rejection before dispatch."
  },
  "litellm/Fixed model route": {
    "title": "Fixed model route",
    "path": "integrations/proxy/litellm.yaml",
    "symbol": "model_list",
    "snippet": "model_list:\n  - model_name: lab-advisor-fixed\n    litellm_params:\n      model: os.environ/LAB_FIXED_MODEL\n      api_base: os.environ/LAB_FIXED_API_BASE\n      api_key: os.environ/LAB_FIXED_API_KEY\n      num_retries: 0\n  - model_name: lab-support\n    litellm_params:\n      model: os.environ/LAB_SUPPORT_MODEL\n      api_base: os.environ/LAB_SUPPORT_API_BASE\n      api_key: os.environ/LAB_SUPPORT_API_KEY\n      num_retries: 0",
    "ownership": "LiteLLM owns provider transport and proxy aliases. This application authors the provider-independent aliases, explicit no-fallback configuration and Switchyard plugin wiring.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "Variable names are configuration references, not values. Fixed harness comparison and routing are separate; no silent fallback is configured. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "Explicit model/base-URL/key environment references.",
    "outputs": "Fixed advisor/support aliases; the file separately declares a routed pair."
  },
  "routing/Switchyard decision": {
    "title": "Switchyard decision",
    "path": "integrations/proxy/lab_routing.py",
    "symbol": "LabRoutingPlugin.run",
    "snippet": "async def run(self, context):\n        count = len(set(context.candidate_models))\n        if count == 1:\n            context.signals[\"learning_lab\"] = {\"route\": \"fixed\", \"candidate_count\": 1}\n            return context\n        if count != 2:\n            raise ValueError(\"The lab routing group must have exactly two distinct candidates\")\n        result = await self.stage.run(context)\n        decision = result.signals.get(\"switchyard\", {})\n        public_decision = {",
    "ownership": "The pinned experimental Switchyard Stage plugin owns the routing decision. This application wrapper separates one-model fixed groups from exactly two-model routed groups and exposes bounded native decision metadata.",
    "upstream": [
      {
        "label": "Pinned Switchyard LiteLLM integration",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/tree/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm"
      }
    ],
    "note": "The wrapper rejects other candidate counts. Appending a third model does not implement a valid three-way policy. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "LiteLLM context with one fixed or two distinct routed models.",
    "outputs": "A fixed context or actual native Stage result."
  },
  "litellm/LiteLLM → provider": {
    "title": "LiteLLM → provider",
    "path": "src/learning_lab/inference.py",
    "symbol": "Gateway.complete",
    "snippet": "endpoint = proxy or base_url()\n                record[\"provider_route\"] = \"litellm\" if proxy else \"nim-direct\"\n                if proxy:\n                    payload[\"model\"] = (\n                        \"lab-advisor-routed\" if role == \"assistant\" and self.model_route == \"switchyard\"\n                        else \"lab-advisor-fixed\" if role == \"assistant\" else \"lab-support\"\n                    )\n                record[\"requested_model\"] = payload[\"model\"]\n                response = await self._client.post(\n                    endpoint + \"/chat/completions\", json=payload,\n                    headers={\"Authorization\": f\"Bearer {key}\"},\n                )\n                if response.status_code >= 400:\n                    from .evidence import sanitize",
    "ownership": "LiteLLM owns provider transport and proxy aliases. This application authors the provider-independent aliases, explicit no-fallback configuration and Switchyard plugin wiring.",
    "upstream": [
      {
        "label": "LiteLLM routing documentation",
        "url": "https://docs.litellm.ai/docs/routing"
      },
      {
        "label": "Pinned Switchyard LiteLLM example",
        "url": "https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md"
      }
    ],
    "note": "This is the application-to-proxy call. LiteLLM resolves provider transport; a direct NIM route without proxy is separately labelled. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An admitted payload and selected alias/proxy connection.",
    "outputs": "One actual HTTP chat-completions request."
  },
  "relay/Native Relay trace": {
    "title": "Native Relay trace",
    "path": "src/learning_lab/target.py",
    "symbol": "DirectTarget.reply",
    "snippet": "config[\"callbacks\"] = [NemoRelayDeepAgentsCallbackHandler()]\n                with nemo_relay.scope.scope(\"course-advisor-request\", nemo_relay.ScopeType.Agent):\n                    result = await self.agent.ainvoke(\n                        {\"messages\": [{\"role\": \"user\", \"content\": content}]}, config\n                    )\n                await nemo_relay.subscribers.flush_async()\n            else:\n                result = await self.agent.ainvoke(\n                    {\"messages\": [{\"role\": \"user\", \"content\": content}]}, config",
    "ownership": "NeMo Relay supplies native instrumentation and scope relationships. The application enables it, selects sinks and projects bounded evidence without inventing missing parent/session links.",
    "upstream": [
      {
        "label": "Relay 0.11.1 Deep Agents guide",
        "url": "https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx"
      }
    ],
    "note": "This enables actual native capture during execution. The wireframe contains source, not captured events; application messages alone are not Relay evidence. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "A real invocation with native Relay enabled.",
    "outputs": "Native agent scopes/callback capture and flush."
  },
  "records/Saved run artifacts": {
    "title": "Saved run artifacts",
    "path": "src/learning_lab/evidence.py",
    "symbol": "list_artifacts",
    "snippet": "def list_artifacts(folder: Path) -> list[dict]:\n    result = []\n    for path in sorted(_paths(folder) or []):\n        relative = path.relative_to(folder).as_posix()\n        kind = _FILES[path.name]\n        result.append(\n            {\n                \"id\": hashlib.sha256(relative.encode()).hexdigest()[:24],\n                \"name\": relative,\n                \"kind\": kind,\n                \"size\": path.stat().st_size,\n                \"path\": str(path.absolute()),\n                \"code_refs\": _code_refs(kind),\n            }",
    "ownership": "The application owns persisted ledgers, sanitization, artifact allowlists and UI projections. Native Relay/Intake remains the owner of its original events and IDs; an application record is not a replacement native trace.",
    "upstream": [],
    "note": "The application exposes known artifacts, not arbitrary host files. Raw private payloads are absent from the wireframe. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An allowlisted selected run/episode directory.",
    "outputs": "Opaque artifact IDs, kind, size and source references."
  },
  "helix/Helix criterion checks": {
    "title": "Helix criterion checks",
    "path": "src/learning_lab/evaluation.py",
    "symbol": "evaluate_saved_run.add",
    "snippet": "def add(criterion, status, reason, evidence=None):\n                rows.append(\n                    {\n                        **base,\n                        \"criterion\": criterion,\n                        \"status\": status,\n                        \"reason\": reason,\n                        \"expected\": \"true\",\n                        \"output\": \"true\"\n                        if status == \"pass\"\n                        else \"false\"\n                        if status in {\"fail\", \"error\"}\n                        else None,\n                        \"evidence\": sanitize(evidence or {}),\n                    }",
    "ownership": "The application authors transparent applicable criterion rows from saved replies and frozen facts. Helix Evals SDK 0.9.1 executes the ExactMatch metric. These narrow assertions do not certify the whole answer.",
    "upstream": [
      {
        "label": "Helix 0.9.1 Evals SDK",
        "url": "https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.9.1/packages/nhx_evals_sdk"
      }
    ],
    "note": "Unavailable/not-applicable evidence is not counted as pass. Aggregate scores do not replace these reasons. Current working-tree reference; not verification of the proposed scenario.",
    "inputs": "An assertion, its status/reason and evidence.",
    "outputs": "Inspectable per-turn criterion rows before SDK scoring."
  }
};

// Explicit preparation for presets that deliberately skip Data Designer.
references.situation = {
  "title": "Authored situation without generation",
  "path": "src/learning_lab/stories.py",
  "symbol": "story",
  "snippet": "def story(story_id: str) -> dict:\n    if story_id not in STORIES:\n        raise ValueError(\"Unknown learning story\")\n    return STORIES[story_id]",
  "ownership": "The application owns named situations and explicit course constraints, separately from the original persona. Looking up a situation makes no Designer or model call.",
  "upstream": [],
  "note": "Retained application-owned reference. The new multi-turn guide and its backend connections remain illustrative; this lookup does not prove they executed.",
  "inputs": "An explicit teaching-scenario identity.",
  "outputs": "The authored situation without modifying the source profile."
};
moduleReferences["situation/Authored situation"] = references.situation;
moduleReferences["personas/Lock source identity"] = moduleReferences["personas/Lock identity"];
