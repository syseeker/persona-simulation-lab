# Native public-boundary checks

`uv sync --project integrations/guardrails --locked --python 3.12` installs the
pinned `nemoguardrails==0.24.1` environment without altering UserSim's dependencies.
The reusable OpenShell image installs the same lock separately.

`runner.py` loads only `config.yml` and `rails.co`, registers custom actions, and
calls native `LLMRails.check_async` for the requested public input/output boundary.
No dialog generation or model is configured. The application client sends only
public text and retains native status, blocking rail, executed action, configuration
hashes, purpose and zero model-call count. Missing workers/checker errors stop the
condition instead of bypassing a check.

These are narrow application-owned deterministic rules executed by native Colang:
selected credential-disclosure input patterns, credential-shaped output and
selected employment-assurance phrases. They are not a general safety classifier.
The credential-disclosure probe is a separate condition event, never a learner turn.
Photography omits this integration. Board games introduces it; retail reuses it.

API and architecture: [native Python check API](https://docs.nvidia.com/nemo/guardrails/guardrails-python-sdk/nemoguardrails/rails/llm/llmrails),
[request flow](https://docs.nvidia.com/nemo/guardrails/latest/about-nemo-guardrails-library/how-it-works).
