# Building Citizen Apps with NeMo — web guide

This package serves the four-tab Integration Guide: Why NeMo Stack, Integration Map, Q&A and Datasets. The interactive map uses Svelte Flow; the nine-stage journey uses a responsive alternating timeline. The previous v0.2 browser interface remains archived.

Entry reads saved photography metadata without starting inference or deployment. Trace a Request prefers a completed fixed recording; otherwise it shows an explicit illustration. Simulate a Session opens prerequisites and a separate photography start action. Board games and retail learning remain illustrative. See the [walkthrough](../docs/learning-guide.md) for the current scope and evidence limits.

## Retained integration boundaries

- The [HTTP route](src/routes/api/%5Boperation%5D/+server.ts) maps allowlisted operations to the [persistent worker client](src/lib/server/worker.ts).
- The [journey route](src/routes/api/journey/%5Baction%5D/+server.ts) uses a separate guide-only worker and shared [JourneyService](../src/learning_lab/journey.py). Playback and source/log inspection are read-only. A managed workload remains owned by its worker when a panel closes.
- The [dataset reader](src/lib/server/datasetReader.ts) reuses the dataset-only worker for read-only installed HF and Singapore NGC catalogue, facet and page requests.
- The [Python worker](../src/learning_lab/worker.py), [CLI](../src/learning_lab/cli.py) and [developer MCP](../src/learning_lab/developer_mcp.py) use the shared application services.
- Browser API helpers, TypeScript contracts, saved-story lineage helpers and the sanitised Markdown renderer remain available for reuse. The worker and Markdown unit tests remain active.
- Explicit chat, simulation, generation and Platform operations keep their existing validation and lifecycle boundaries. Do not register the developer-control MCP service as an advisor tool.

Run the package from its existing repository location. The worker resolves the repository from the current directory or its parent; a relocated host must set `LAB_ROOT` explicitly. Existing credentials, datasets, runs and integration environments remain in their original locations.

## Run and verify

From the repository root, use the existing Python environment and pinned npm dependencies:

```sh
uv sync --locked
npm --prefix web ci
npm --prefix web run dev
```

The service checks are:

```sh
npm --prefix web run check
npm --prefix web test
npm --prefix web run test:e2e
npm --prefix web run build
```

The browser suite checks nine-stage navigation, source/log inspection, recording links, saved selection, responsive timeline layout, retained service reads and rejection of invalid requests. It starts no model workload or deployment. Playwright uses port 4173 through the existing configuration. Installed-dataset and actual-recording checks have separate receipts in the [verification record](../docs/verification.md).

Code links use this checkout's configured GitHub repository and committed source revision. Fixed log links point to the matching [sanitized recording pack](../recordings/README.md); in-app previews verify its hashes. Raw runs, source profiles and credentials stay outside Git. Future live-log linking is deferred.

Rebuild before using `npm --prefix web start`, because that command serves the generated build rather than current source. Generated output, dependencies and browser results are not source archives.

## Recover the previous interface

The [v0.2 web source snapshot](../docs/history/v0.2/web/) preserves the old page, components, styles, browser tests, configuration and lockfile. The [v0.2 archive](../docs/history/v0.2/) also preserves their matching application context.

Recover the legacy interface in a separate copy of the archived repository, using its preserved dependency versions. Do not mix its browser tests or imports into the active guide. Historical UI checks and runtime evidence do not verify the current interface.
