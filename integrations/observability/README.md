# Local historical trace viewer

This isolated Phoenix 22.1.0 environment opens saved advisor execution traces.
It never reruns a scenario, invokes an agent, generates a reply, or runs an
evaluation. The guide's execution panel uses curated public recordings; this
separate viewer is local and includes filtered advisor model and tool I/O.

From the repository root, install the locked environment and manage it explicitly:

```bash
uv sync --frozen --project integrations/observability --python 3.12
integrations/observability/.venv/bin/python integrations/observability/manage.py inspect
integrations/observability/.venv/bin/python integrations/observability/manage.py start
integrations/observability/.venv/bin/python integrations/observability/manage.py import
integrations/observability/.venv/bin/python integrations/observability/manage.py status
integrations/observability/.venv/bin/python integrations/observability/manage.py stop
```

Open [local Phoenix](http://127.0.0.1:6006), or use the condition's link in the
guide. Import creates a separate project for each selected scenario and condition.
The currently tagged recordings contain 94 native records across nine conditions
and ten native trace groups. Only the original private captures for those selected
recordings are eligible; a checkout containing only the public packs cannot
reconstruct the private model I/O.

The viewer answers concrete execution questions: which captured model or tool
ran, its parent, its saved input/output, token counts where captured, and elapsed
time where both timestamps exist. A configured skill or available subagent is
not proof of skill execution or a spawned subagent. Gateway usage remains separate
accounting; the importer never invents a join between its call IDs and Relay spans.

## Source and display limits

The importer validates native ATOF files against the private capture manifest,
whose hash is retained in the immutable public capture manifest. It pairs actual
start/end events, maps IDs deterministically within each condition, keeps missing
parents explicit, and preserves native marks as events without duplicating stream
payload fragments. Re-import reads existing IDs, verifies their source hashes and
content, and uploads only missing spans. A successful HTTP response is followed
by read-back checks of IDs, parent links, status, attributes, times and filtered I/O.

The managed condition's raw Intake file was not hash-bound in the original pack.
Its 12 records therefore come from the hash-bound `platform-trace.json` projection.
That preserves native IDs, relationships, timestamps, token counts and three tool
results. Managed LLM input/output remains unavailable. Six managed records have
no captured end timestamp: Phoenix displays an explicitly labelled zero-length
marker with `UNSET` status, and their duration stays unknown. Intake's naive
timestamps use its installed loader's UTC convention.

Original timestamp nanoseconds remain as string attributes. Phoenix uses Python
datetimes and displays microseconds; its displayed duration can differ by less
than a microsecond from the original interval. No completion time or parent span
is inferred to fill missing evidence.

## Local storage and privacy

SQLite, logs, process ownership and the import receipt stay under the ignored
`runs/observability/` directory. Model credentials are excluded from the service
environment. HTTP binds to `127.0.0.1:6006`; gRPC binds to the same loopback address
on port 6007. `PHOENIX_TELEMETRY_ENABLED=false` and
`PHOENIX_ALLOW_EXTERNAL_RESOURCES=false` disable telemetry, external resources and
pricing updates. This local service has no authentication and must remain on
loopback.

The importer retains only advisor user/assistant/tool message context, tool
definitions and tool results. System/developer messages, source persona records,
UserSim prompts, provider headers and reasoning fields are excluded. A credential
scan fails closed before upload. Private trace payloads are never returned by the
guide API or published into `recordings/`.

`stop` signals only the PID and Linux process start identity created by this
integration. Occupied ports or an unhealthy owned process produce an error;
another process is never stopped. Restart preserves SQLite and historical IDs.
An interrupted import can be repeated. Inspect `runs/observability/phoenix.log`
if startup or read-back fails; do not replace or rerun source recordings.
