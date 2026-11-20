# Standalone application runtime

Scenario 1 runs one persistent Fabric/Deep Agents application and its read-only
course MCP inside native OpenShell. UserSim and the budget gateway run on the
developer host. Helix SDK/Platform, native Guardrails, Designer generation and
Switchyard routing are not required by this preset.

Scenario 2 selects Fabric/Hermes for two public turns. The same image contains isolated Python 3.12 application/Guardrails environments and the pinned Hermes source with Python 3.14.0. Run `python integrations/hermes/bootstrap.py` first to install/verify the pinned public checkout used by the image builder. The build includes only its tracked official source files, never the host Hermes environment or session memory. Native Guardrails validates public input/output inside OpenShell and runs a separate blocked probe.

## Setup

Use Python 3.12 and the existing root lockfile. Install/configure native OpenShell
0.1.6 with a reachable gateway and its official credential store. Follow the
[OpenShell documentation](https://docs.nvidia.com/openshell/about/overview);
an installed CLI alone is not readiness. Install an original HF or Singapore NGC
Extended dataset according to [persona setup](../../docs/personas.md).

Configure the fixed/support aliases using the retained
[LiteLLM setup](../proxy/README.md) and local environment. The operator's proxy
URL/key never enter the browser or agent image. No proxy is started by inspection.
Build the reusable image explicitly:

```bash
uv sync --locked
uv run python integrations/openshell/build.py
uv run learning-lab guide status
npm --prefix web run dev
```

The build hands Docker an allowlisted temporary context, not the checkout.
It contains locked runtime code, the public course snapshot and advisor skill;
it excludes `.env`, private data, profiles and run artifacts. Runtime code and
dependencies live under immutable `/opt/lab`; `/workspace` is writable.
Rebuild after changing packaged code, the skill or dependencies. The native
runtime's returned image-manifest hashes must match before inference is admitted.

Optional server-only settings: `LAB_OPENSHELL_IMAGE` (default
`citizen-learning-advisor:0.8.0`), `LAB_OPENSHELL_WORKSPACE` (default `default`),
`LAB_OPENSHELL_STATE_DIR` (the existing local store root), and
`LAB_REPOSITORY_URL` (a repository URL override for source links).
Existing native operator configuration is respected; these settings do not
create a gateway. Never pass them as browser paths or advisor tool arguments.

## One explicit condition

In **Integration Map → Simulate a Session**, check prerequisites, select a source
and lock one random original. **Start live photography simulation** creates new
run/condition/episode identities. Only the public UserSim message and constraints
extracted from that message reach the advisor; private profile/OCEAN context
stays with the simulator. The same Fabric runtime serves the entire conversation.

The [policy](policy.yaml) allows the in-sandbox loopback model bridge. The bridge
uses authenticated native `sandbox exec` stdin/stdout to the host budget gateway;
no broad host ingress or provider credential is added to the sandbox. All roles
use the existing bounded gateway; only the assistant's provider-visible tool
schemas are restricted to the three course tools. Native Relay records remain
unchanged. The loopback bridge is a developer integration, not a provider service.

Native YAML/admission/version records, world-readable-file and unlisted-egress
denial probes, Fabric configuration/plan/Doctor, native Relay bytes and checksums
are saved under the selected run. An ordinary connection timeout/refusal does
not pass the network-denial check. The supported allowed operation is the actual
model/tool conversation, not a claim inferred from policy configuration.

Cancellation waits for an in-flight native creation before cleanup. Only the
condition's exact name, full run ownership label and saved native identity may
be deleted. Ambiguous creation or failed cleanup retains a workload guard;
**Recover and verify cleanup** is explicit and cannot steal a live owner's run.
Closing a panel/browser does not cancel the host worker. Stopping the server
ends its ownership; partial evidence/recovery requirements remain visible.

## Inspect without executing

**Trace a Request** opens a saved run through nine teaching stages. It never
replays inference. Gateway calls, public turns and native tools have separate
identities; missing native span correlations are not invented. Application
assertions inspect the frozen catalogue and saved reply without Helix or a model
judge. UserSim's own stop-judge activations remain labelled separately.

Code links derive the developer's GitHub repository and committed revision;
new unpublished files display publication pending plus the actual working-tree
excerpt. Run source hashes distinguish that excerpt from recorded code. The
user-authorised [fixed sanitized packs](../../recordings/README.md) now provide
GitHub log permalinks and verified in-app previews. Private-run logs retain their
existing opaque-ID/local API behavior. Future live-log changes are deferred;
raw private runs stay ignored.

See [verification](../../docs/verification.md) for actual results, preserved
failed attempts and the separate historical Docker host-ingress limitation.
