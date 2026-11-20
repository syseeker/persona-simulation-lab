# Sources and Compatibility

These pins, public guides and workarounds cover retained integrations and the repository-hosted guide. Only photography is connected for current implementation review; configuration and historical results are not current readiness. See the [active plan](../PLAN.md), [current verification](verification.md) and [separate historical evidence](history/v0.2/docs/verification.md).

Retained backend integration contracts are pinned below. Historical execution and limitations are recorded in the [v0.2 verification record](history/v0.2/docs/verification.md); installing a dependency or validating a configuration is not a live result. The [v0.1 source record](history/v0.1/docs/sources.md) preserves its earlier compatibility context.

## Contents

- [Current Learning Documentation](#current-learning-documentation)
- [Datasets And Catalogue](#datasets-and-catalogue)
- [NVIDIA Implementations](#nvidia-implementations)
- [Upstream Skills](#upstream-skills)
- [Application Framework](#application-framework)

## Current Learning Documentation

The **Why NeMo Stack** cards in **Building Citizen Apps with NeMo** use the actual HF/NGC distribution pages below and current official documentation websites. These learning destinations were checked on **20 November 2026**; the separately pinned adapter contracts remain under NVIDIA Implementations. Following current documentation does not upgrade an installed dependency.

- [Data Designer](https://docs.nvidia.com/nemo/datadesigner/latest/getting-started/welcome).
- [Fabric](https://docs.nvidia.com/nemo/fabric/latest/about-nemo-fabric/overview), [LangChain Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) and [Hermes](https://hermes-agent.nousresearch.com/docs/).
- [Relay](https://docs.nvidia.com/nemo/relay/latest/about-nemo-relay/overview).
- [Switchyard](https://nvidia-nemo.github.io/Switchyard/) and [LiteLLM](https://docs.litellm.ai/).
- [Helix overview](https://docs.nvidia.com/nemo-helix/latest/documentation/home), [evaluation](https://docs.nvidia.com/nemo-helix/latest/documentation/evaluate-models) and [agent deployment](https://docs.nvidia.com/nemo-helix/latest/documentation/agents/deploy-agents). Helix's broader operations, experiments and evaluation role is introduced by scenario 3; the first two presets omit it.
- [Behavioural Guardrails](https://docs.nvidia.com/nemo/guardrails/latest/home) and [OpenShell](https://docs.nvidia.com/openshell/about/overview). Guardrails remains a future scenario gate. Standalone photography uses OpenShell 0.1.6; its [setup and image contract](../integrations/openshell/README.md) describe the native exec bridge and policy verification.

The build/execute card links to the current [UserSim package documentation](https://github.com/NVIDIA-NeMo/UserSim/blob/main/README.md). Version-specific integration references remain in the contextual source inspector and the pinned list below.

## Datasets And Catalogue

- [NVIDIA Singapore dataset card](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore) and pinned revision `a3994709410410f834bd949d643d3f2796908969`.
- [NGC Extended en_SG](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg), artifact version `0.0.1`; [authenticated file inventory](https://api.ngc.nvidia.com/v2/org/nvidia/team/nemotron-personas/resources/nemotron-personas-dataset-en_sg/versions/0.0.1/files), [NGC authenticated download guide](https://docs.nvidia.com/ngc/latest/ngc-catalog-user-guide.html#downloading-authenticated-access-resources-via-wget-curl), [separate NVIDIA dataset terms](https://assets.ngc.nvidia.com/products/api-catalog/legal/Personas-Dataset-NVIDIA-Training-Dataset-License-Agreement-2025-11-26.pdf), and [Data Designer 0.10 person sampling](https://docs.nvidia.com/nemo/datadesigner/v0.10.0/concepts/person-sampling/). Actual original-file/schema/OCEAN verification is recorded in [persona sources](personas.md) and [current verification](verification.md).
- [NUS Statistics short courses](https://www.stat.nus.edu.sg/education/cet/short-course/), [AIC business learning](https://www.aic.sg/Age-Well/Learning-and-Volunteerism/Learning-Opportunities/Business-Skills) and [AIC computer learning](https://www.aic.sg/Age-Well/Learning-and-Volunteerism/Learning-Opportunities/Computer-Skills).
- Every community offering has a specific [onePA](https://www.onepa.gov.sg/courses) source URL in `catalogue/courses.json`. Facts were captured on 10 November 2026. AIC listings are senior-oriented; provider age and intake requirements remain to be confirmed.

HF attribution: NVIDIA Corporation and the dataset authors, *Nemotron-Personas-Singapore: Synthetic Personas Aligned to Real-World Distributions for Singapore*, January 2026, CC BY 4.0. NGC Extended has the separate NVIDIA dataset terms linked above. Source licenses and SDK licenses are independent of this project's code license.

## NVIDIA Implementations

The root and original isolated-environment pins were reviewed for v0.1 on 10 November 2026. v0.2 adds separately isolated integration profiles; do not merge environments or upgrade their dependencies independently.

- [UserSim v0.3.0](https://github.com/NVIDIA-NeMo/UserSim/releases/tag/v0.3.0): [external runtime](https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md), [extension API](https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md) and [personas](https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/personas.md).
- [Relay 0.11.1](https://github.com/NVIDIA/NeMo-Relay/releases/tag/0.11.1): [Deep Agents quick start](https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx).
- [Fabric v0.6.1](https://github.com/NVIDIA/NeMo-Fabric/releases/tag/v0.6.1): [maintained Deep Agents adapter](https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/README.md).
- [Helix 0.9.1](https://github.com/NVIDIA-NeMo/nemo-helix/releases/tag/0.9.1): [Evals SDK](https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.9.1/packages/nhx_evals_sdk).
- [Data Designer v0.10.0](https://github.com/NVIDIA-NeMo/DataDesigner/releases/tag/v0.10.0): authored enrichment environment. UserSim retains Data Designer 0.9.7.
- [Deep Agents](https://github.com/langchain-ai/deepagents), pinned at 0.7.35 in the root environment.

Installed SDK types and adapter descriptors were checked against the guides. Actual runtime checks established compatibility where documented in the verification record. Lockfiles preserve all transitive versions.

## v0.2 integration profiles

- The root Python 3.12 environment retains UserSim 0.3.0, Data Designer 0.9.7, Deep Agents 0.7.35, Fabric 0.6.1 and Relay 0.11.1. UserSim requires MCP below 2.
- [Designer environment](../integrations/designer/pyproject.toml): Data Designer 0.10.0, with native `LLMStructuredColumnConfig`, source seed files, config validation and the public create/batch callback APIs. User-facing generated fields are compiled from closed specifications; they are not executable templates.
- [Local evaluation environment](../integrations/helix/pyproject.toml): retain Helix 0.9.1's compatible older Fabric/Relay dependencies. This is local SDK scoring, separate from Platform deployment.
- [Hermes environment](../integrations/hermes/pyproject.toml): Python 3.14, Fabric 0.6.1, its maintained Hermes adapter and Relay 0.11.1. [Bootstrap](../integrations/hermes/bootstrap.py) pins [Hermes source](https://github.com/NousResearch/hermes-agent/tree/b200f5bc60e31588ba2cb60e288029c4a54ba5fa) and uses that source's dependency override/checking contract. Root Python 3.12 does not run Hermes directly.
- [Platform environment](../integrations/platform/pyproject.toml): Helix 0.10.0, Fabric 0.6.1 and Relay 0.11.0, with the exact compatible SDK/plugin set locked separately. This environment serves the explicit local/remote Platform bridge, not UserSim.
- [Proxy bootstrap](../integrations/proxy/bootstrap.py) pins the official [experimental Switchyard source](https://github.com/NVIDIA-NeMo/Switchyard/tree/9e8408c9e06baf146b63cecda14959a30c34697b). [LiteLLM aliases/config](../integrations/proxy/litellm.yaml) and the [routing plugin](../integrations/proxy/lab_routing.py) keep fixed-model versus routed experiments explicit. Config validation does not prove a routing decision occurred.
- [OpenShell intent](../integrations/platform/openshell-policy.yaml) describes the required agent/tool boundary and validation checks. It is documentation metadata; the versioned Platform executor creates the effective policy. [Platform bridge](../integrations/platform/bridge.py) and native execution/audit evidence establish what actually ran.

## Compatibility workarounds

Fabric 0.6.1's installed Deep Agents descriptor supports a global tool allowlist, not per-server filtering. Its maintained `ToolGateMiddleware` enforces that allowlist when a tool executes; it does not remove built-in tool schemas from model requests. With the pinned Deep Agents 0.7.35 runtime, the observed adapter request advertised eleven tools: eight filesystem/subagent tools and the three catalogue tools. See the [pinned adapter implementation](https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/src/nemo_fabric_adapters/deepagents/adapter.py) and the historical [v0.2 verification record](history/v0.2/docs/verification.md).

The application's [shared Gateway](../src/learning_lab/inference.py) therefore also filters assistant-role, provider-bound Deep Agents schemas to the three catalogue names. [FabricTarget](../src/learning_lab/fabric_target.py) applies this boundary to local chat and simulation; [managed sessions](../src/learning_lab/service.py) select it from the harness recorded in the actual deployment snapshot. Every affected call records `tool_surface.received`, `exposed` and `withheld` names in its usage ledger. Native Relay input remains the adapter's original request, so its eleven schemas and the provider's three schemas describe different observed boundaries. Model responses and original native traces are not rewritten to imply a successful answer.

Preserve the generated Relay configuration path and explicit adapter interpreter until a tested replacement removes the requirement. Hermes uses its maintained adapter's `mcp-catalogue` toolset selector and native discovery/describe/call protocol. Its catalogue discovery tools remain available; the Deep Agents function-name filter is not applied to Hermes.

OpenShell 0.1.6 and Helix 0.10 expose a native external-credential-driver gap: OpenShell sends generated SSH host keys and supervisor launch material through its selected credential store, while Helix's external driver accepts signed secret-reference registrations. Actual sandbox creation with that combination failed at `StoreCredential`. The maintained lab path therefore uses OpenShell's official encrypted store and an explicit frozen public learning preset, without an external preferences credential binding. Native sandbox startup, the three actual course MCP calls, frozen-input/hash checks and filesystem/unrelated-egress denial probes passed for both hardened harness images. These zero-model checks remain separate from a managed advisor conversation. A custom adapter was investigated, rejected for live launch by automatic approval review and retained only as ignored research. Credential-refresh attestation for the unused external-driver path remains false. See the historical [v0.2 verification record](history/v0.2/docs/verification.md) for application deployment evidence and limits.

Data Designer 0.10 uses schema-aware prompts/parsing for structured columns; do not assume provider-native `response_format` appears on every request. Its public runtime controls disable conversation restarts/corrections, while the native HTTP client has separate retry behaviour. A local per-job bridge returns terminal model errors and forwards each actual call to the shared budget gateway as the Designer role, without monkeypatching SDK internals.

The installed Designer SDK completes one generated row but can fail token-statistics profiling with `float(NAType)` because a one-row sample standard deviation is unavailable. The integration uses public batch-complete callbacks to retain actual completed native rows. Only this recognised post-generation profiling error may become an explicit warning after independent schema/source validation; no model calls are repeated, statistics remain unavailable and other generation/validation failures stay failures. Five-row previews avoid this one-row case.

SvelteKit 3 configuration belongs in Vite. TypeScript 6 matches the installed checker; upgrading it independently to TypeScript 7 is unsupported by that checker. The archived v0.2 browser markdown renderer used active-content restrictions.

Standalone OpenShell uses the public CLI `sandbox create/get/exec/list/delete` and `policy get` operations. Duplex `sandbox exec --no-tty --no-login-shell` keeps stdin open for the model bridge; the installed SDK's unary exec helper is unsuitable for that protocol. The effective policy allows only the in-sandbox loopback HTTP bridge, with provider access on the host. The immutable image root requires Fabric's runtime artifacts to use writable `/workspace`; editable package installation keeps MCP subprocess imports independent of inherited `PYTHONPATH`. Installed CLI/API behavior, image-manifest checks, actual denial probes and a real conversation were verified separately. No existing Helix-managed sandbox was reused or removed.

## Upstream Skills

The implementation used the relevant maintained guides and skill instructions. The root coaching skill records how to apply them without changing unrelated configuration.

- [Relay get started](https://github.com/NVIDIA/NeMo-Relay/blob/main/skills/nemo-relay-get-started/SKILL.md): verify actual capture, with a matching integration example.
- [Fabric integration](https://github.com/NVIDIA/NeMo-Fabric/blob/main/skills/nemo-fabric-integrate/SKILL.md): public typed config, planning, lifecycle and descriptor-based capability checks.
- [Helix Evals](https://github.com/NVIDIA-NeMo/nemo-helix/blob/0.9.1/packages/nemo_helix_ext/src/nemo_helix_ext/skills/nemo-evals/SKILL.md): SDK-first scoring, deterministic checks before model judges.
- [Helix managed agent configuration](https://github.com/NVIDIA-NeMo/nemo-helix/blob/0.9.1/packages/nemo_helix_ext/src/nemo_helix_ext/skills/nemo-agent-config/SKILL.md): declarative config and MCP custom tools.
- [Data Designer](https://github.com/NVIDIA-NeMo/DataDesigner/blob/v0.10.0/skills/data-designer/SKILL.md): inspect public schemas, validate pipelines and preserve seed records.

UserSim did not provide a repository skill file in the inspected tree; its public extension documentation and conformance helpers were used.

## Application Framework

[SvelteKit 3 configuration](https://svelte.dev/docs/kit/@sveltejs-kit-vite), [Node adapter](https://svelte.dev/docs/kit/adapter-node), and installed types govern the web app. The build preserves SvelteKit 3.2.0, Svelte 5.57.3 and TypeScript 6.0.3, adding the accepted wireframe's Svelte Flow 2.0.1 graph package. Saved replies use the existing Marked/DOMPurify renderer with active-markup/image restrictions.
