# Persona Lab web services

The previous v0.2 browser interface is archived. This package now retains a static service landing page, the SvelteKit HTTP boundary and the persistent Python worker bridge. The integration guide is reviewed as a separate UX artifact; it is not packaged or served here. Its explicitly approved Explore profiles view imports the narrow [dataset reader](src/lib/server/datasetReader.ts), reusing this worker and Python service for read-only catalogue, facet and page requests.

The landing page makes no API requests and starts no worker, inference or deployment. The retained API is still callable explicitly; archiving the UI does not disable application services.

## Retained integration boundaries

- The [HTTP route](src/routes/api/%5Boperation%5D/+server.ts) maps allowlisted operations to the [persistent worker client](src/lib/server/worker.ts).
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

The active browser smoke suite checks that the landing makes no API requests, reads status and catalogue metadata through the real local worker, and verifies rejection of unknown operations and invalid request shapes. It starts no model workload or Platform action. Playwright uses port 4173 through the existing configuration; it does not connect to the isolated guide preview.

Rebuild before using `npm --prefix web start`, because that command serves the generated build rather than current source. Generated output, dependencies and browser results are not source archives.

## Recover the previous interface

The [v0.2 web source snapshot](../docs/history/v0.2/web/) preserves the old page, components, styles, browser tests, configuration and lockfile. The [v0.2 archive](../docs/history/v0.2/) also preserves their matching application context.

Recover the legacy interface in a separate copy of the archived repository, using its preserved dependency versions. Do not mix its browser tests or imports into the active service-only package. Historical UI checks and runtime evidence do not verify a redesigned interface.
