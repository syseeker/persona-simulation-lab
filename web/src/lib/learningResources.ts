/** Current package documentation, separate from pinned implementation references. */
import type { StageId } from './content';
export const learningResources: Record<StageId, { label: string; url: string }[]> = {
  persona: [
    { label: 'Singapore personas · HF viewer', url: 'https://huggingface.co/datasets/nvidia/Nemotron-Personas-Singapore/viewer' },
    { label: 'Singapore Extended · NGC catalogue', url: 'https://catalog.ngc.nvidia.com/orgs/nvidia/teams/nemotron-personas/resources/nemotron-personas-dataset-en_sg' }
  ],
  situation: [
    { label: 'Data Designer documentation', url: 'https://docs.nvidia.com/nemo/datadesigner/latest/getting-started/welcome' }
  ],
  build: [
    { label: 'Fabric documentation', url: 'https://docs.nvidia.com/nemo/fabric/latest/about-nemo-fabric/overview' },
    { label: 'LangChain Deep Agents documentation', url: 'https://docs.langchain.com/oss/python/deepagents/overview' },
    { label: 'Hermes documentation', url: 'https://hermes-agent.nousresearch.com/docs/' }
  ],
  run: [
    { label: 'UserSim documentation', url: 'https://github.com/NVIDIA-NeMo/UserSim/blob/main/README.md' },
    { label: 'Fabric documentation', url: 'https://docs.nvidia.com/nemo/fabric/latest/about-nemo-fabric/overview' },
    { label: 'LangChain Deep Agents documentation', url: 'https://docs.langchain.com/oss/python/deepagents/overview' },
    { label: 'Hermes documentation', url: 'https://hermes-agent.nousresearch.com/docs/' }
  ],
  investigate: [
    { label: 'Relay documentation', url: 'https://docs.nvidia.com/nemo/relay/latest/about-nemo-relay/overview' }
  ],
  evaluate: [
    { label: 'Helix evaluation documentation', url: 'https://docs.nvidia.com/nemo-helix/latest/documentation/evaluate-models' }
  ],
  routing: [
    { label: 'Switchyard documentation', url: 'https://nvidia-nemo.github.io/Switchyard/' },
    { label: 'LiteLLM documentation', url: 'https://docs.litellm.ai/' }
  ],
  safeguards: [ { label: 'Guardrails documentation', url: 'https://docs.nvidia.com/nemo/guardrails/latest/home' } ],
  deploy: [ { label: 'Helix documentation', url: 'https://docs.nvidia.com/nemo-helix/latest/documentation/home' }, { label: 'OpenShell documentation', url: 'https://docs.nvidia.com/openshell/about/overview' } ]
};
