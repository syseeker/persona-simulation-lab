"""Explanations of integration boundaries, independent of filename extensions."""
from pathlib import PurePosixPath
import re


def artifact_semantics(requirement_id: str, artifact: dict) -> dict:
    """Describe the retained source and the representation a reader can open."""
    filename = re.sub(r'^[a-f0-9]{24}-', '', PurePosixPath(artifact.get('path', '')).name)
    filename = filename.replace('.projection.jsonl', '.jsonl').replace('.projection.json', '.json')
    filename = filename.replace('.projection.yaml', '.yaml')
    # These are the actual integration producers and consumers, not inferred
    # from a .json/.yaml suffix or a product logo.
    contracts = {
        'fabric-config.json': ('Application build_config', 'NeMo Fabric configuration and adapter resolution', 'input',
            'Captures the typed FabricConfig built by the application. The public copy omits private values; it is not a complete replacement configuration.'),
        'fabric-plan.json': ('NeMo Fabric planning', 'Application startup and developer inspection', 'output',
            'Records the resolved adapter and runtime plan returned by Fabric before conversation execution.'),
        'fabric-doctor.json': ('NeMo Fabric preflight', 'Application startup', 'output',
            'Records the SDK preflight outcome. A passing preflight establishes readiness, not a completed answer.'),
        'fabric-run-requests.jsonl': ('Application FabricTarget', 'NeMo Fabric runtime.invoke', 'input',
            'Captures the submitted RunRequest boundary for each actual agent invocation; private context is omitted from the public representation.'),
        'fabric-run-results.jsonl': ('NeMo Fabric runtime', 'Application response handling', 'output',
            'Captures normalized RunResult values or terminal errors. It is a runtime result, not a configuration file.'),
        'reply-outcomes.jsonl': ('Application response validation', 'Developer inspection and scenario checks', 'output',
            'Records how the application classified and handled a native reply. It does not configure Fabric.'),
        'retail-response-config.json': ('Application ResponseConfiguration', 'Application retail response boundary', 'input',
            'Saves the application rules for clarification and source-based presentation. These rules belong to this lab, not a NeMo SDK schema.'),
        'retail-response-decisions.jsonl': ('Application retail response boundary', 'Developer inspection and saved-response checks', 'output',
            'Records which public reply was delivered and whether an agent was invoked. Native model proposals remain separate.'),
        'fabric-relay.json': ('Application observability setup', 'NeMo Relay integration attached by Fabric', 'input',
            'Saves the Relay plugin and observability settings used to instrument the selected harness.'),
        'relay.jsonl': ('NeMo Relay instrumentation', 'Execution investigation', 'output',
            'The original is a native ATOF event stream. This public projection preserves selected scope identities, relationships and tool results; it is not an OTLP collector export.'),
        'gateway-effective-config.json': ('Application Gateway', 'Application model-admission boundary', 'input',
            'Saves the lab-owned call limits, aliases, retry policy and tool-schema boundary. This is not a LiteLLM configuration schema.'),
        'gateway-calls.jsonl': ('Application Gateway', 'Usage and request investigation', 'output',
            'Accounts for model attempts across learner, advisor and judge roles, with returned usage and latency where available. Gateway IDs are separate from Relay span IDs.'),
        'litellm-loaded.yaml': ('Operator configuration captured by the application', 'LiteLLM proxy', 'input',
            'A redacted copy of the loaded LiteLLM YAML. Environment references and credentials must be supplied locally to reproduce it.'),
        'litellm-effective-config.json': ('Application proxy inspection', 'Developer configuration review', 'output',
            'Records observed proxy settings and inventory. It is an inspection receipt, not another file submitted to LiteLLM.'),
        'routing-configuration.json': ('Application comparison setup', 'Developer experiment review', 'input',
            'Summarises the declared model inventories and Switchyard policy. The actual LiteLLM YAML and routing plugin apply those settings.'),
        'routing-comparison.json': ('Application comparison runner', 'Developer comparison review', 'output',
            'Collects separate condition outcomes, model attempts, native routing decisions and evaluation results. It is not a Switchyard input schema.'),
        'helix-criteria.json': ('Application scenario evaluator', 'Helix ExactMatchMetric', 'input',
            'Contains expected and observed values extracted by the scenario-specific application code. Helix scores those supplied values; it does not author these criteria.'),
        'helix-evaluator-config.json': ('Application evaluation setup', 'Local Helix Evals SDK', 'input',
            'Captures the exact-match metric templates and RunConfig used to score saved criterion values without a generation model.'),
        'helix-evaluation.json': ('Local Helix Evals SDK', 'Application result presentation', 'output',
            'Contains criterion-level ExactMatchMetric scores returned by the local SDK. It is separate from the durable Platform job.'),
        'evaluation.json': ('Application scenario evaluator', 'Developer acceptance review', 'output',
            'Combines application-defined expected/observed checks, explanations and coverage. A passing total applies only to those checks.'),
        'helix-job-config.json': ('Application durable evaluation submission', 'Helix Platform evaluation service', 'input',
            'Saves the metric, dataset and execution settings submitted for the separate durable evaluation job.'),
        'helix-job.json': ('Application and Helix Platform evaluation service', 'Developer job inspection', 'output',
            'Records submission identity, status and returned results for the durable evaluation job.'),
        'guardrails-config.json': ('Application safeguards setup', 'Native Guardrails RailsConfig and Colang engine', 'input',
            'Wraps the actual YAML and Colang text plus execution location. The wrapper JSON is a lab capture; its YAML/Colang contents configure native Guardrails.'),
        'guardrails-decisions.jsonl': ('Native Guardrails checks with application purpose labels', 'Public input/output delivery', 'output',
            'Records each configured check and action decision. A pass means that the configured narrow rules allowed that message.'),
        'guardrails-probe.json': ('Native Guardrails negative policy test', 'Developer enforcement review', 'output',
            'Records the separate deliberately blocked credential request, outside the ordinary learner conversation.'),
        'requested-policy.yaml': ('Application-selected access policy', 'OpenShell sandbox create', 'input',
            'The policy requested for standalone sandbox creation. Compare it with the loaded effective policy and deliberate enforcement tests.'),
        'effective-policy.yaml': ('OpenShell policy get', 'Developer access review', 'output',
            'The policy text read back from the running sandbox; it describes the loaded boundary for this condition.'),
        'effective-policy.json': ('OpenShell policy get', 'Developer access review', 'output',
            'The loaded policy, revision and native policy metadata read from the running sandbox.'),
        'platform-effective-policy.json': ('OpenShell policy get for the Helix-owned sandbox', 'Developer managed-access review', 'output',
            'The managed sandbox policy read back from OpenShell. It belongs to the Helix-managed condition, not the standalone baseline.'),
        'boundary-probes.json': ('Application deliberate sandbox probes', 'Developer enforcement review', 'output',
            'Records a forbidden file read and unrelated network connection. Permission denied establishes only the two tested boundaries.'),
        'platform-boundary-probes.json': ('Application probes inside the Helix-owned sandbox', 'Developer managed-enforcement review', 'output',
            'Records the two deliberate access-denial tests in the separate managed sandbox.'),
        'managed-client-config.json': ('Application capture of the selected Helix client and executor', 'Developer managed-configuration review', 'input',
            'Shows the client arguments and selected OpenShell executor settings retained for this condition. This is a reviewed capture of settings, not a standalone Helix input file.'),
        'managed-agent-config.json': ('Application agent registration', 'Helix agent registration API', 'input',
            'Shows the submitted native agent configuration, including harness, application instructions, model, tools and runtime. Local endpoints and private connection material are redacted.'),
    }
    contract = contracts.get(filename)
    if contract is None:
        producer, consumer = {
            'PER': ('Application persona selection', 'Application scenario preparation'),
            'SIT': ('Application authored situation', 'UserSim preparation'),
            'DD': ('Application and native Data Designer integration', 'Scenario enrichment and developer review'),
            'US': ('Application and native UserSim external runtime', 'Conversation execution and developer review'),
            'HER': ('Application and maintained Hermes adapter', 'Hermes runtime and developer review'),
            'DA': ('Application and maintained Deep Agents adapter', 'Deep Agents runtime and developer review'),
            'MCP': ('Application course MCP integration', 'Selected harness and developer review'),
            'PLAT': ('Application and Helix Platform', 'Managed deployment and developer review'),
            'OS': ('Application and OpenShell', 'Access enforcement and developer review'),
        }.get(requirement_id.split('-')[1], ('Application integration capture', 'Developer review'))
        source_role = artifact.get('source_kind', '')
        direction = ('input' if source_role in {'authored-source', 'application-input', 'native-input', 'native-request',
            'native-effective-configuration', 'redacted-loaded-source', 'redacted-submitted-source', 'requested-policy', 'public-input'}
            else 'input and output' if source_role == 'native-request-response' else 'output')
        contract = (producer, consumer, direction,
                    'Retains this operation’s configuration or execution boundary. The source schema below identifies the original format; the published representation may omit private fields.')
    producer, consumer, direction, purpose = contract
    representation = ('Redacted native configuration' if artifact.get('kind') == 'redacted-native-configuration'
                      else 'Lab-created projection of retained evidence')
    return {'producer': producer, 'consumer': consumer, 'direction': direction, 'purpose': purpose,
            'representation': representation}
