# LiteLLM and Switchyard integration

The application owns its inference budget. LiteLLM owns the model proxy and
provider credentials; the pinned experimental Switchyard plugin owns routing.
No model or proxy starts at application import.

The upstream source is fixed at `9e8408c9e06baf146b63cecda14959a30c34697b`,
with LiteLLM `1.102.0`. It must be built from source because the published
Switchyard package does not contain this example's decision-only API.

```bash
python integrations/proxy/bootstrap.py
uv run python integrations/proxy/launch.py
# Explicit infrastructure action, after configuration validates:
uv run python integrations/proxy/launch.py --start --build
```

Set `LAB_PROXY_API_KEY` to a secret of at least 24 characters. `launch.py` uses
the existing NVIDIA key and NIM model configuration for its default local
reference profile without copying secrets into tracked configuration. Override
`LAB_{FIXED,SUPPORT,CAPABLE,EFFICIENT}_{MODEL,API_BASE,API_KEY}` in the environment
to use NIM, a Brev OpenAI-compatible endpoint, or a supported frontier provider.
Use LiteLLM model names such as `openai/<exact-model>` for OpenAI-compatible
endpoints. Endpoint and model access must be verified before a live story.

Set `LAB_PROXY_BASE_URL=http://127.0.0.1:4000/v1` in the application environment
once the proxy is ready. The public aliases are `lab-advisor-fixed`,
`lab-advisor-routed`, and `lab-support`. The routed alias has exactly two
distinct models, ordered capable then efficient. The fixed aliases bypass
Switchyard. A Stage routing decision is not evidence of cost or quality gains;
inspect actual calls and compare with a fixed-model baseline.

No retries or fallback policy is configured. The plugin logs only decision
metadata. Compose passes only selected inference credentials, binds loopback,
and does not receive persona datasets or host HF/NGC credentials.

The pinned public LiteLLM response-header callback returns actual
`routing_plugin_signals.switchyard` as bounded URL-safe-base64 JSON in
`x-lab-routing-decision`. It excludes prompts, request patches and response
content. Missing native metadata produces no decision header. The application's
Gateway saves this response-specific evidence next to the admitted call;
configuration alone cannot establish that Switchyard selected a deployment.

`launch.py` also reads the ignored `.private/v02-runtime.env` for locally generated
runtime credentials. Empty NIM model settings use the explicit lab defaults;
provider-only names such as `openai/` fail inventory validation before launch.

Stop only this lab container with `docker stop proxy-litellm-1`; source,
images and run evidence remain available. No volume deletion is required.

[Official integration and limitations](https://github.com/NVIDIA-NeMo/Switchyard/blob/9e8408c9e06baf146b63cecda14959a30c34697b/examples/litellm/README.md).
