# Sources And Compatibility

## Contents

- [Datasets And Catalogue](#datasets-and-catalogue)
- [NVIDIA Implementations](#nvidia-implementations)
- [Upstream Skills](#upstream-skills)
- [Application Framework](#application-framework)

## Datasets And Catalogue

- [NVIDIA Singapore dataset card](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore) and pinned revision `a3994709410410f834bd949d643d3f2796908969`.
- [NGC Extended en_SG](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg).
- [NUS Statistics short courses](https://www.stat.nus.edu.sg/education/cet/short-course/), [AIC business learning](https://www.aic.sg/Age-Well/Learning-and-Volunteerism/Learning-Opportunities/Business-Skills) and [AIC computer learning](https://www.aic.sg/Age-Well/Learning-and-Volunteerism/Learning-Opportunities/Computer-Skills).
- Every community offering has a specific [onePA](https://www.onepa.gov.sg/courses) source URL in `catalogue/courses.json`. Facts were captured on 10 November 2026. AIC listings are senior-oriented; provider age and intake requirements remain to be confirmed.

Attribution: NVIDIA Corporation and the dataset authors, *Nemotron-Personas-Singapore: Synthetic Personas Aligned to Real-World Distributions for Singapore*, January 2026, CC BY 4.0. Source licenses and SDK licenses are independent of this project's code license.

## NVIDIA Implementations

Stable release checks were made on 10 November 2026. These are tested pins, not an instruction to upgrade every dependency independently.

- [UserSim v0.3.0](https://github.com/NVIDIA-NeMo/UserSim/releases/tag/v0.3.0): [external runtime](https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/engine/EXTERNAL_PROBE_RUNTIME.md), [extension API](https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/extension_api.md) and [personas](https://github.com/NVIDIA-NeMo/UserSim/blob/v0.3.0/docs/personas.md).
- [Relay 0.11.1](https://github.com/NVIDIA/NeMo-Relay/releases/tag/0.11.1): [Deep Agents quick start](https://github.com/NVIDIA/NeMo-Relay/blob/0.11.1/docs/getting-started/quick-start/deep-agents.mdx).
- [Fabric v0.6.1](https://github.com/NVIDIA/NeMo-Fabric/releases/tag/v0.6.1): [maintained Deep Agents adapter](https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/deepagents/README.md).
- [Helix 0.9.1](https://github.com/NVIDIA-NeMo/nemo-helix/releases/tag/0.9.1): [Evals SDK](https://github.com/NVIDIA-NeMo/nemo-helix/tree/0.9.1/packages/nhx_evals_sdk).
- [Data Designer v0.10.0](https://github.com/NVIDIA-NeMo/DataDesigner/releases/tag/v0.10.0): authored enrichment environment. UserSim retains Data Designer 0.9.7.
- [Deep Agents](https://github.com/langchain-ai/deepagents), pinned at 0.7.35 in the root environment.

Installed SDK types and adapter descriptors were checked against the guides. Actual runtime checks established compatibility where documented in the verification record. Lockfiles preserve all transitive versions.

## Upstream Skills

The implementation used the relevant maintained guides and skill instructions. The root coaching skill records how to apply them without changing unrelated configuration.

- [Relay get started](https://github.com/NVIDIA/NeMo-Relay/blob/main/skills/nemo-relay-get-started/SKILL.md): verify actual capture, with a matching integration example.
- [Fabric integration](https://github.com/NVIDIA/NeMo-Fabric/blob/main/skills/nemo-fabric-integrate/SKILL.md): public typed config, planning, lifecycle and descriptor-based capability checks.
- [Helix Evals](https://github.com/NVIDIA-NeMo/nemo-helix/blob/0.9.1/packages/nemo_helix_ext/src/nemo_helix_ext/skills/nemo-evals/SKILL.md): SDK-first scoring, deterministic checks before model judges.
- [Helix managed agent configuration](https://github.com/NVIDIA-NeMo/nemo-helix/blob/0.9.1/packages/nemo_helix_ext/src/nemo_helix_ext/skills/nemo-agent-config/SKILL.md): declarative config and MCP custom tools.
- [Data Designer](https://github.com/NVIDIA-NeMo/DataDesigner/blob/v0.10.0/skills/data-designer/SKILL.md): inspect public schemas, validate pipelines and preserve seed records.

UserSim did not provide a repository skill file in the inspected tree; its public extension documentation and conformance helpers were used.

## Application Framework

[SvelteKit 3 configuration](https://svelte.dev/docs/kit/@sveltejs-kit-vite), [Node adapter](https://svelte.dev/docs/kit/adapter-node), and installed framework types govern the web app. The build pins SvelteKit 3.2.0, Svelte 5.57.3 and TypeScript 6.0.3. The chat renderer uses Marked with DOMPurify and rejects active markup and image tags.
