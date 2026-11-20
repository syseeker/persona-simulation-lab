# Helix Platform and OpenShell delivery

This environment is separate from UserSim, Data Designer, local Evals and the
Hermes adapter. Its exact Helix `0.10.0`, Fabric `0.6.1` and Relay `0.11.0`
versions are recorded in `uv.lock`. No Platform starts merely by opening the UI.

The current retail preset uses a **new condition-owned** provider, public-preset
environment, registration, deployment and session. It packages
`citizen-retail-helix:0.4.0` with public S$3,000/weekend constraints, invokes it
through the admission gateway and verifies removal of every owned resource.
It does not replace older registrations or resume the local UserSim memory.
See [retail integration](../../docs/retail-integration.md) for the executed path,
native Intake projection, Guardrails location and remaining routing limits.

`retail_evaluate.py` also submits saved criteria as an actual durable Helix job;
it performs no response generation. `build_evals_image.py` supplies the local
development task image from this environment's frozen dependencies when the
configured placeholder is absent. It refuses to replace an unowned image.
Use the release-matched official task image in other installations.

```bash
uv sync --project integrations/platform --locked --python 3.12
integrations/platform/.venv/bin/python integrations/platform/contract_check.py
integrations/platform/.venv/bin/python integrations/platform/bootstrap_local.py
```

`bootstrap_local.py --start` explicitly starts the local Helix services. Before
an OpenShell deployment, configure the gateway, sandbox-visible Platform address,
TLS and executor using the version-specific operator guide. The example config
is a starting point: host loopback inside a sandbox is a different machine.
Keep Landlock `hard_requirement`; readiness alone does not establish confinement.

The UI/CLI calls `PlatformBridge` in `src/learning_lab/deployment.py`, which
delegates through `bridge.py` to the real installed public Agents SDK. Local
default is `http://127.0.0.1:8080`, workspace `persona-lab`. Remote connections
use `LAB_HELIX_REMOTE_URL`, `LAB_HELIX_REMOTE_WORKSPACE` and
`LAB_HELIX_REMOTE_TOKEN`; remote URLs require HTTPS, and tokens never appear in
the JSON protocol or public configuration.

Native recovery against a remote Platform additionally requires
`LAB_HELIX_REMOTE_EXECUTOR_CONFIG` pointing to that Platform's existing executor
configuration. The child never inherits a host-local executor selection or falls
back to a local gateway for remote recovery. Ordinary remote status and SDK
operations do not require native executor access.

Operations are `status`, `configure`, `package`, `register`, `agent`, `deploy`, `deployment`,
`logs`, `sessions_create`, `invoke`, `sessions_close`, `sessions_recover`, `undeploy`, `delete_agent`.
`package` accepts `harness`, `image` and explicit `build`; it never publishes.
`register` reads only the generated bundle for that harness. `deploy` requires
an exact accessible image and explicit mode, defaulting to OpenShell. Creation
returns pending state: poll status before invocation. Deletion returns a
request acknowledgement: verify absence before claiming a sandbox was removed.
Repeating registration reuses the existing record only when the normalized config
and every allowlisted source byte match. A different config or source requires
review and explicit removal of the previous deployment/registration first.

`configure` accepts Platform-reachable `provider_url` ending `/v1` and sandbox-reachable
`preferences_url` exactly `/v1/lab/preferences`. Real SDK requests create the workspace,
dedicated secret references, model provider and separate Docker/OpenShell environments.
It also creates `lab-catalogue-preset`, the default OpenShell environment. It preserves
existing secrets and refuses conflicting provider/environment configuration. The controller's
model discovery remains a separate observed readiness step.

```bash
integrations/platform/.venv/bin/python integrations/platform/package_agent.py \
  --harness hermes --image persona-lab-hermes:0.2.0
```

This prepares a minimal allowlisted source bundle and native generated
OpenShell Dockerfile. Add `--build` to build locally. The Hermes image uses a
context-checked customization of the Helix template to select v0.22.7 and
Relay `0.11.1` in Python 3.14. Other image dependencies remain exactly
constrained, including Fabric `0.6.1`. No UserSim/persona dependencies, `.env`,
private data or runs enter the image. Source hashes connect the packaged MCP
implementation to the shared repository code. Packaged source, dependencies, catalogue
and public scenario are root-owned and non-writable. The sticky work directory permits
native staging while preventing replacement of its root-owned children; explicit
`workspace`, `artifacts` and `scratch` directories remain writable.

Registration uploads only `agent.yaml`, `skills/course-advisor/SKILL.md` and
`source-manifest.json` through the native Files SDK into `<agent>-ethos`. Helix
requires supporting skill text in that staged fileset even when the image already
contains it. Registration's host Doctor checks adapter descriptors, resolution and
environment; it does not prove MCP startup, image readiness or successful inference.

Managed agents reach the Helix Inference Gateway, whose dedicated lab model
provider must point to the application's `DeploymentInferenceBridge` endpoint.
The latter requires `LAB_DEPLOYMENT_GATEWAY_KEY` and rejects inference without
the exclusive active run lease. Its existing run Gateway admits each call once,
then reaches LiteLLM/Switchyard. Configure the provider and model aliases before
invocation. A separate `LAB_DEPLOYMENT_PREFERENCES_TOKEN` authenticates the read-only
trusted context endpoint. It returns only the validated active workload's preferences,
409 outside that lease, and makes zero model calls.

The default native OpenShell path uses the official encrypted credential store and
an explicit frozen public photography scenario. Its catalogue MCP reads
`/workspace/scenarios/photography/preferences.json`, validates its SHA256 from
`LAB_PREFERENCES_PRESET_SHA256`, and enforces photography, a SGD50 total budget and
Saturday availability. Missing, altered or invalid context fails closed. The immutable
deployment's environment metadata records the preferences and hash; the UI locks its
controls to that observed scenario. This path requires no context callback credential
or external credential driver. Platform model calls still pass through the active
application admission lease and LiteLLM. This demonstrates the whole application
boundary with one clearly identified scenario.

Docker uses `lab-catalogue-context-docker` and ordinary MCP secret references for
dynamic trusted preferences from the active application callback. A separate OpenShell
callback environment is retained as an unverified integration option, not the default.
Helix 0.10 rejects ordinary process/MCP secret injection for OpenShell; its supported
external provider profile uses an issued opaque `LAB_CONTEXT_TOKEN`. However, the pinned
OpenShell 0.1.6 global driver also sends its generated SSH host key to that driver, and
Helix 0.10's signed-ticket-only driver rejects that native material. Full callback
deployment therefore remains blocked before sandbox creation. A custom driver was not
launched; the maintained frozen-preset path avoids that unsupported combination.
Neither image contains provider credentials.

On the recorded local host, Docker's managed agent could start and discover the
catalogue, but both lab-owned Docker networks timed out reaching the correctly
resolved host gateway at `172.17.0.1:8080` and `:8766`. The failed Hermes Docker
invocation made zero admitted model calls. Its runtime was positively drained and
the unused deployment removed after exporting logs. Host firewall and network policy
were not changed. Dynamic Docker therefore remains unverified on this host; it needs
a Platform and application origin reachable from its container network. The explicit
native OpenShell deployment uses its maintained egress proxy and public frozen preset;
the UI does not silently switch runtimes after a failure.

The Hermes image also installs the supported managed retry overlay from
`integrations/hermes/managed/config.yaml` under root-owned
`/workspace/hermes-managed`. `HERMES_MANAGED_DIR` selects one API attempt and zero
recovery cycles; `HERMES_STREAM_RETRIES=0` disables stream retries. Those are
Hermes public interfaces, because Fabric 0.6.1's settings schema has no retry fields.

OpenShell 0.1.6 does not preserve an image's `ENV` when launching the serving
process. The Hermes-only image therefore installs `hermes_python.sh` as the
root-owned `/workspace/.venv/bin/python` launcher and preserves the original
interpreter as `python-real`. The launcher exports only the three static public
interpreter/retry selections above, then executes the original interpreter with
unchanged arguments. This version-specific image compatibility step runs before
Fabric chooses its adapter interpreter. Neither `EnvironmentSpec.env` (applied
too late) nor an unsupported `harness.settings.python` field substitutes for it.
The Deep Agents image and native SDK descriptors remain unchanged.

Fabric 0.6.1 stdio adapters do not expand MCP environment indirections. The exact,
context-checked image patch `patch_mcp_context.py` expands only `LAB_PREFERENCES_TOKEN`
from the actual `${LAB_CONTEXT_TOKEN}`. It never inherits the whole agent environment
or manufactures a gateway placeholder; source drift fails the build.

`openshell-preferences-profile.yaml` and `openshell-credentials.example.yaml` describe
only that future callback option. Its hostname must differ from Platform egress: the
native provisioner rejects a tool credential endpoint on the Platform host. Keep
`credential_refresh_verified` false unless actual native refresh is observed. These
files are not required by the selected frozen-preset deployment.

The local bootstrap enables the real Secrets AES256 provider using a stable generated
key stored only in the ignored private runtime environment. Preserve that private key
with the local state: replacing it prevents decryption of existing lab secrets. Helix
0.10's native local runner binds the selected loopback address and, when a local Docker
runtime is detected, its verified private bridge address too. It avoids an all-interface
bind; no separate forwarder or system firewall change is needed.

Create one Platform session per episode/condition. The bridge resolves its resource
name through the SDK, checks its immutable deployment ownership and uses its native
session UUID in `X-Nemo-Session-Id`. Closing first drains the owning Fabric runtime
through the maintained deployment transport, then closes its SDK record. A failed or
timed-out invocation remains quarantined until a positive native HTTP204 acknowledges
runtime shutdown; HTTP404 alone cannot establish that shutdown finished. Separate invocation,
model-content, telemetry and evaluation outcomes. Save real logs and traces;
a running deployment alone does not establish successful tools or Intake export.

When startup fails before a Fabric runtime exists, `sessions_recover` explicitly
retires the owning deployment. Its server-owned job receipt pins the immutable
session, deployment and native sandbox identities before mutation, supports retry
after partial deletion, and requires authenticated native cleanup evidence before
closing the SDK session. It cannot select an arbitrary sandbox or gateway. The
application keeps its durable quarantine until the helper confirms native cleanup,
deployment removal and a closed session; a Platform HTTP404 alone does not suffice.

`openshell-policy.yaml` records review intent, not an executable OpenShell policy.
The operator's versioned executor generates the runtime policy. Enforced denial
must be verified using audit evidence. The SDK mock contract test makes zero
network/model calls and is explicitly labelled as such.

Registration checks an explicit host projection because the image's `/workspace`
executable does not exist on the host. It preserves the registered image config and
labels image readiness unverified until actual deployment succeeds. Live evidence in
ignored `runs/platform-start-v02` distinguishes native sandbox probes, MCP-only probes,
deployed model invocations and all retained failed attempts.

`logs` accepts an optional session resource name in `session_id`. It resolves the
native UUID and verifies deployment ownership before reading actual Intake traces
and detailed spans through `AsyncIntakeClient`. Results distinguish observed,
absent and unavailable telemetry, cap each kind at 100 records, and explicitly
report `raw_relay_file_exported: false`. An observed trace may describe a failed
model call; trace presence does not establish a successful advisor response.

Fabric 0.6.1's Hermes adapter does not forward the supplied `relay_session_root`
into its native Hermes scope. Hermes can therefore export ATIF successfully under
an independent Relay session UUID while the selected Platform UUID returns no
records. The reader labels that case with unsupported correlation metadata and
keeps both identities separate; without a verified bridge, the native UUID remains
unknown to that selected session. It never fills the gap by matching timestamps,
agent names or conversation text. Owned records returned by the exact session
filter remain visible. This is a correlation limitation, not evidence that the
exporter was disabled; the separate read-only deployment diagnosis preserves an
unassigned native Hermes trace without attaching it to an episode.

[Official delivery](https://docs.nvidia.com/nemo-helix/v0.10/documentation/agents/deploy-agents)
and [OpenShell operator contract](https://docs.nvidia.com/nemo-helix/v0.10/documentation/kubernetes-deployment/setup/helm/openshell).
The pinned [OpenShell 0.1.6 profiles](https://docs.nvidia.com/openshell/v0.1.6/how-it-works/providers/profiles/)
define the exact endpoint-bound credential contract.
