# Isolated Hermes harness

Run `python integrations/hermes/bootstrap.py` to prepare the official Hermes
v0.22.7 commit and install its dependencies, maintained Fabric adapter `0.6.1`,
Relay `0.11.1` and MCP `1.30.0` in a project-local Python 3.14 environment.
The bootstrap uses the upstream source lock's dependency override checker;
it does not run a conversation or expose provider credentials.

The root Fabric runtime discovers this environment's installed adapter
descriptor through `DiscoveryConfig.local_paths` and launches it using
`ADAPTER_PYTHON`. The root application stays on Python 3.12. The descriptor is
the same Fabric release as the root runtime; do not combine dependency files.

`tools.enabled` uses the Hermes native `mcp-catalogue` toolset. Verify exactly
the three read-only catalogue tools after discovery before calling a runtime
ready. Memory/session-search, terminal, filesystem and delegation tools are not
part of that selected toolset. Each Fabric runtime owns a separate Hermes state
directory and session database; test within-session continuity and cross-session
isolation independently.

The public Hermes managed-scope overlay in `managed/config.yaml` selects one
API attempt (`api_max_retries: 1`) and disables the additional recovery ladder.
`HERMES_STREAM_RETRIES=0` disables transport stream retries. Fabric 0.6.1 does
not expose those fields in its harness settings schema, so the lab uses the
supported `HERMES_MANAGED_DIR` bootstrap environment instead. The local adapter
receives this explicit repository directory; packaged Hermes images copy the
same file under root-owned `/workspace/hermes-managed`. The OpenAI client also
uses its maintained per-request `max_retries=0` behavior. These settings do not
change model/tool budgets or introduce a fallback model.

`uv.lock` records the adapter environment; the official Hermes checkout and its
own `uv.lock` record the harness. `.venv/installation.json` reports the installed
commit/versions, explicitly separate from runtime verification. Both source and
local environments are ignored by Git.

[Maintained adapter](https://github.com/NVIDIA/NeMo-Fabric/blob/v0.6.1/adapters/python/hermes/README.md).
