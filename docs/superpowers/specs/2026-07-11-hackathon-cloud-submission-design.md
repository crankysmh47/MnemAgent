# Hackathon Cloud Submission Hardening Design

## Objective

Prepare MnemAgent for a low-friction Track 1: MemoryAgent submission and for deployment by the owner to Alibaba Cloud after the repository work is complete. The repository must provide a reproducible judge path, defensible Alibaba Cloud proof, a secure cloud topology, an accurate three-minute demo plan, scalable visualizer behavior, and a concise judge-first documentation hierarchy.

The work is organized as three independently verifiable streams that converge in the root README:

1. cloud appliance and security boundary;
2. scalable archive API and visualizer;
3. submission documentation and proof.

## Product and judge experience

### Primary technical proof

The terminal remains the primary demonstration surface in the video and technical walkthrough. It best exposes OpenClaw tool calls, MCP integration, channel integrations, cross-session behavior, and failure diagnostics.

The repository will provide exact terminal commands for:

- checking service health;
- probing the seven `mnemos` MCP tools;
- teaching facts;
- starting a separate session;
- recalling those facts;
- replacing a contradicted fact;
- rejecting a low-conviction candidate;
- inspecting the same changes in the visualizer.

No general-purpose terminal or SSH shell will be exposed to the public internet.

### Browser fallback for judges

The cloud appliance also exposes OpenClaw's browser Web UI through an authenticated reverse proxy. This is the no-install judge path. It uses the same MCP server and judge namespace as the terminal path; it is not a replacement chat implementation and must not bypass OpenClaw.

The visualizer remains a separate companion surface. A small judge landing page links to:

- `Archive demo` for the populated, read-only `demo-brain` tree;
- `Judge archive` for the resettable live namespace;
- `Agent console` for the protected OpenClaw Web UI;
- `Health` for a public, non-sensitive readiness summary;
- `Repository`, `architecture`, `benchmark evidence`, and `cloud proof`.

The repository will not attempt invasive theming of OpenClaw internals. The landing page and reverse-proxy chrome provide consistent MnemAgent branding while the embedded product remains recognizably OpenClaw.

## Alibaba Cloud topology

### Deployment target

The supported submission topology is one Alibaba Cloud ECS instance running Docker Compose. This is intentionally reproducible and easy for judges to understand. It can later evolve to managed RDS, SLB, or ACK without changing application interfaces.

The ECS stack contains:

- Caddy reverse proxy for automatic HTTPS after DNS is configured;
- MnemAgent visualizer/harness;
- MnemAgent memory API;
- MnemAgent streamable-HTTP MCP server;
- PostgreSQL 16 with pgvector;
- OpenClaw gateway and Web UI under an opt-in `judge-agent` Compose profile;
- optional scheduled OSS database snapshots.

### Public routes

The deployment uses one domain with subdomains because OpenClaw WebSocket and base-path behavior is safer when it is not rewritten under a nested path:

- `https://memory.<domain>`: judge landing page and visualizer;
- `https://agent.<domain>`: OpenClaw Web UI;
- `https://memory.<domain>/health`: sanitized aggregate readiness only.

Ports `5432`, `8000`, `8001`, and `18789` bind only to the Compose network or loopback. Security groups expose only `22`, `80`, and `443`; SSH is restricted to the owner's IP during deployment.

### Alibaba service proof

The proof code remains an actual runtime path, not a documentation-only sample. The existing OSS backup module will be updated to:

- use an ECS RAM role or environment credentials without logging secrets;
- support the current Alibaba OSS Python SDK;
- accept region, endpoint, bucket, and object prefix independently;
- prefer an internal OSS endpoint when ECS and OSS share a region;
- upload a `pg_dump --format=custom` snapshot;
- attach non-secret metadata such as application version and timestamp;
- surface backup readiness in a protected operational health response;
- include unit tests with a fake OSS client.

The README links directly to that module. Deployment documentation cites the official OSS upload and RAM permission requirements. The owner will add the final ECS URL, instance proof screenshot/video, and deployed health result after deployment.

## Authentication and tenancy

### Hackathon appliance boundary

A full account system is out of scope. The judge appliance uses a deliberately limited boundary:

- a shared judge access code for the landing page and live judge archive;
- a server-side signed, secure, HTTP-only judge session after access-code validation;
- Caddy basic authentication on the separate OpenClaw Web UI subdomain, using a deployment-generated credential;
- a read-only public `demo-brain` route that cannot mutate memories;
- one resettable `judge-*` namespace for interactive evaluation;
- mandatory `MNEMAGENT_API_TOKEN` in cloud mode between trusted services;
- application-level rate limits on access-code attempts and mutating judge routes;
- request-body limits and security headers at the proxy;
- no raw `user_id` authorization based only on a query parameter;
- no public database, memory API, MCP, gateway control endpoint, or shell.

The visualizer server maps the authenticated session to its permitted namespace. `?user=demo-brain` remains supported for the read-only demo. Other user IDs are rejected unless they match the signed judge session.

### Production evolution

`docs/SECURITY.md` will explicitly state that a multi-user product must replace the shared judge code with OIDC, map subject claims to canonical user IDs, and enforce tenant claims at every API boundary. The hackathon appliance must not be described as a full production identity system.

## Cloud configuration and reproducibility

The repository will add:

- `compose.cloud.yml` layered over the existing local Compose file;
- `docker/Caddyfile` with documented domain placeholders, TLS, OpenClaw basic authentication, WebSocket proxying, request limits, and security headers;
- an opt-in `openclaw` service under the `judge-agent` Compose profile, built from a repository Dockerfile and pinned to the tested OpenClaw version;
- `.env.cloud.example` containing safe placeholders and generated-secret instructions;
- `scripts/deploy-cloud.sh` for Linux ECS deployment;
- `scripts/verify-cloud.sh` for health, MCP, visualizer, auth, and namespace checks;
- `scripts/reset-judge.sh` as a Linux equivalent of the current PowerShell reset path;
- health checks and restart policies for every long-running service;
- image/version pinning rather than floating `latest` dependencies;
- a migration step that runs before the application becomes ready;
- backup scheduling instructions that do not require a permanently running cron container when systemd timers are available.

Local `docker compose up` behavior remains compatible. Cloud-only security requirements activate through `compose.cloud.yml` and `MNEMAGENT_ENV=cloud`.

## First-time walkthrough

The judge path must not require Python, Node.js, OpenClaw installation, or MCP registration when using the deployed appliance.

### Deployed path

1. Open the judge landing page.
2. Enter the temporary access code.
3. Open the populated archive to understand the visual vocabulary.
4. Open the agent console and teach three facts.
5. start a fresh OpenClaw session;
6. ask for those facts and observe MCP recall;
7. replace one fact and verify contradiction handling;
8. open the live judge archive and search for the changed memory.

### Repository test path

The root README provides one Linux/macOS command and one Windows command. Both paths:

- validate prerequisites before mutation;
- copy a safe environment template;
- fail clearly when the Qwen/DashScope key is absent;
- build the stack;
- wait for readiness;
- seed only `demo-brain`;
- register MCP with a pinned OpenClaw version;
- print exact URLs and verification commands.

Documentation must not contain local developer paths, placeholder repository URLs, outdated expected test totals, incorrect shell/PowerShell invocations, or an unsupported `/visualizer` path.

## Scalable archive API

### Current limitation

The existing graph endpoint loads every belief, constructs affinity edges with quadratic loops, and sends the entire result to a frontend layout with quadratic collision resolution. This is acceptable for the current demo but not for hundreds or thousands of memories.

### New read model

The existing `/api/graph/{user_id}` response remains backward compatible for small archives. It gains query parameters:

- `q`: search text;
- `category` and `lifecycle` filters;
- `cursor`: stable pagination cursor;
- `limit`: requested individual nodes, capped at `150`;
- `focus_id`: always include a selected node and its immediate context;
- `include_summary`: include category and lifecycle aggregate counts.

The response adds:

- `total_beliefs`;
- `returned_beliefs`;
- `next_cursor`;
- `archive_revision`;
- `summary` with category/lifecycle counts and average vitality;
- `render_mode`: `individual`, `hybrid`, or `summary`;
- `truncated`: boolean.

Thresholds are fixed and documented:

- `0–120`: individual mode;
- `121–500`: hybrid mode with at most 150 individual nodes;
- `501+`: summary-first mode with individual nodes loaded through search, focus, or branch expansion.

Selected nodes, explicit search matches, newly changed nodes, and high-vitality nodes have priority. Remaining nodes become category/lifecycle aggregates. Ambient relationships are capped at 120; every direct relationship for a focused node remains available.

### Query and edge performance

- Add a PostgreSQL GIN text-search index over entity source, relation, entity target, and category.
- Search is always scoped by `user_id` and active node threshold.
- Pagination uses a stable score/id cursor rather than offset pagination.
- Graph edges are built only for the bounded visible node set.
- Large-archive summaries use SQL aggregation rather than loading every row into Python.
- `archive_revision` derives from the newest relevant memory event ID/timestamp and active belief count.
- Metrics no longer call the unbounded graph builder.
- SQLite retains a compatible bounded fallback for local tests.

## Visualizer search and progressive disclosure

### Search surface

A compact search field appears in the dashboard header. It includes:

- accessible label and keyboard shortcut `/`;
- 250ms debounce;
- result count and loading state;
- clear control and `Escape` behavior;
- search over statements, source entity, relation, target entity, and category;
- arrow-key navigation through results;
- server-backed search when the archive is truncated;
- highlighting of matches and their direct relationships;
- centering and revealing a selected result;
- restoration of the previous archive view when cleared.

Search never mutates memory and never searches across namespaces.

### Tree scaling

The renderer keeps the current botanical appearance but stops attempting to draw every memory.

- Maximum 150 individual memory forms in the DOM.
- Aggregate buds represent hidden groups and display their count.
- Selecting an aggregate requests that branch page and replaces only that aggregate's visible slice.
- Layout is deterministic across refreshes.
- Branch-slot placement replaces the global all-pairs collision pass for large sets.
- Collision checks use bounded spatial buckets.
- Relationship paths are generated only for visible or focused nodes.
- Loading another branch preserves selection, zoom, filters, and search.
- The observation panel always reports total archive size separately from rendered node count.

The visualizer displays `Showing 150 of 4,812 memories` so aggregation cannot be mistaken for data loss.

### Scale acceptance targets

Fixture tests cover 100, 500, 1,000, and 5,000 memories. At 5,000 memories:

- API response contains at most 150 individual nodes and 120 ambient edges;
- frontend DOM contains at most 150 memory forms plus bounded aggregates;
- layout contains no unbounded nested loop over all archive memories;
- search returns the expected target even if it is not in the initial page;
- selected/search-matching nodes remain individually visible;
- response generation and layout complete within explicit test budgets on the CI runner.

## Documentation hierarchy

### Root README order

1. MnemAgent name, logo, Track 1 identification, and one-sentence value.
2. Submission links table: live demo, video, Alibaba proof, architecture, license, and optional blog.
3. Populated `demo-brain` visualizer screenshot.
4. Three-minute judge path.
5. Architecture diagram.
6. Track-aligned feature table: storage, recall, forgetting, contradiction handling, and context limits.
7. Best verified benchmark result with methodology link.
8. Five-minute local start.
9. Cloud deployment summary.
10. Security and tenancy statement.
11. Verification commands.
12. Repository map and deeper docs.
13. License.

Unknown external URLs are displayed as `Deployment pending owner upload` or `Video pending owner upload`, never as fake links.

### Canonical judge documents

- `docs/ARCHITECTURE.md`: components, data flow, memory algorithms, failure behavior, and scale design.
- `docs/JUDGE_GUIDE.md`: deployed and local walkthroughs.
- `docs/DEPLOY_ALIBABA.md`: ECS, DNS, TLS, RAM, OSS, reset, rollback, and proof steps.
- `docs/BENCHMARKS.md`: strongest verified results, run configuration, limitations, and source reports.
- `docs/SECURITY.md`: threat model, judge boundary, secrets, tenancy, and production evolution.
- `docs/VIDEO_SCRIPT.md`: exact three-minute sequence and proof shots.
- `docs/SUBMISSION_CHECKLIST.md`: criteria-to-evidence matrix and owner-supplied final links.

Existing overlapping setup, cloud, proof, benchmark, and video documents are merged into these canonical files. Historical reviews and superseded reports move to `docs/archive/`. Files are deleted only when their unique information has been preserved.

### Claims and benchmark discipline

- The README leads with the strongest real, reproducible benchmark result.
- Dry-run results are never presented as model-performance evidence.
- Every headline number links to run notes, provider/model configuration, scenario count, and limitations.
- MnemBench repositories are described accurately and only linked if publicly reachable.
- The product repository retains only judge-relevant summaries; research-scale catalogs remain in benchmark repositories.

## Architecture diagram

The README and `docs/ARCHITECTURE.md` include a judge-readable diagram showing:

Judge browser or terminal → Caddy → OpenClaw gateway/Web UI → MnemAgent MCP → Memory API → PostgreSQL/pgvector → DashScope/Qwen, with the visualizer querying the bounded archive API and the backend optionally snapshotting to Alibaba OSS.

Trust boundaries, public/private routes, and user namespace mapping appear in the detailed diagram.

## Repository and submission metadata

- Preserve the MIT `LICENSE` at repository root.
- Verify GitHub recognizes the license.
- Update the GitHub About description, topics, homepage, and deployment URL after the owner provides the final domain.
- Keep the repository public before submission.
- Add a release-style submission tag after final deployment verification.
- Ensure all screenshots use the populated current visualizer.

## Verification and failure handling

### Automated verification

- Python unit and integration tests.
- Node visualizer and browser tests.
- Compose config validation for local and cloud overlays.
- container health and dependency checks.
- auth boundary tests for demo, judge, and arbitrary user IDs.
- secret/default-password preflight failures in cloud mode.
- scale fixtures and performance budgets.
- broken-link and documentation-command checks.
- Alibaba OSS client tests without real credentials.

### Deployment verification

The Linux cloud verifier checks:

- only intended ports are public;
- HTTPS and security headers;
- unauthenticated judge routes are rejected;
- demo archive is read-only;
- judge namespace starts empty;
- OpenClaw sees exactly seven MnemAgent tools;
- a store, cross-session recall, contradiction, and rejection flow;
- populated demo and live judge visualizers;
- Qwen/DashScope model identity;
- optional OSS snapshot upload and object metadata.

### Graceful failure

- The landing page reports a component as unavailable without exposing internal URLs or secrets.
- The visualizer distinguishes auth failure, empty archive, degraded metrics/events, and backend failure.
- OpenClaw/MCP failure instructions identify the failed boundary.
- Backup failure never blocks memory serving, but appears in protected operational health.
- Search cancellation aborts stale requests.

## Owner-supplied items after repository completion

The repository work can be completed without cloud credentials. The owner must later provide:

- Alibaba ECS instance and region;
- DNS domain or subdomains;
- DashScope API key;
- generated application, API, and judge-access secrets;
- optional OSS bucket and RAM role;
- final public deployment URL;
- public three-minute video URL;
- ECS/OSS proof screenshots or recording;
- optional blog/social URL.

The submission checklist gives exact locations for each value and refuses to label the submission complete while required external URLs are absent.
