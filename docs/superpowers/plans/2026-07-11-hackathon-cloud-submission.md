# Hackathon Cloud Submission Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a scalable searchable memory archive, a secure Alibaba ECS deployment appliance, and judge-first submission documentation without replacing OpenClaw's terminal-led agent experience.

**Architecture:** Bound graph reads at the Python API, progressively disclose large archives in the existing botanical visualizer, and place the current services plus a pinned OpenClaw gateway behind Caddy on ECS. The terminal remains the primary proof surface; authenticated browser routes provide a no-install fallback.

**Tech Stack:** Python 3.11, FastAPI, PostgreSQL 16/pgvector, vanilla JavaScript/Node 20, OpenClaw, Docker Compose, Caddy, Alibaba ECS/OSS, pytest, Node test runner.

## Global Constraints

- Preserve the current serene MnemTree visual language and populated `demo-brain` experience.
- Render at most 150 individual memories and 120 ambient edges.
- Use individual mode through 120 memories, hybrid mode through 500, and summary-first mode above 500.
- Keep `demo-brain` read-only in cloud mode and reject arbitrary query-string namespaces.
- Expose only ports 80 and 443 publicly; keep PostgreSQL, API, MCP, and OpenClaw control traffic private.
- Keep terminal/OpenClaw as the primary walkthrough; do not build a replacement chat.
- Never log or commit API keys, access codes, tokens, OSS secrets, or generated password hashes.
- All commits use `crankysmh47 <annankhan741@gmail.com>` as the sole author.

---

### Task 1: Bounded archive read model

**Files:**
- Modify: `mcp-memory-server/src/memory/api_data.py`
- Modify: `mcp-memory-server/src/main.py`
- Modify: `mcp-memory-server/src/storage/schema.postgres.sql`
- Modify: `mcp-memory-server/src/storage/schema.sql`
- Test: `tests/test_api_data.py`
- Test: `tests/test_api_main.py`

**Interfaces:**
- Produces: `get_graph_data(user_id, db_path=None, *, query="", category=None, lifecycle=None, cursor=None, limit=150, focus_id=None, include_summary=True) -> dict[str, Any]`.
- Produces response fields: `total_beliefs`, `returned_beliefs`, `next_cursor`, `archive_revision`, `summary`, `render_mode`, and `truncated`, while retaining `beliefs`, `edges`, and existing counters.

- [ ] **Step 1: Write failing API-data tests**

Add fixtures containing 121 and 501 beliefs. Assert the default result never exceeds 150 beliefs or 120 ambient edges, mode thresholds are exact, summary totals equal the full archive, search finds a belief outside the initial page, and `focus_id` forces inclusion.

- [ ] **Step 2: Verify the tests fail**

Run: `python -m pytest tests/test_api_data.py -q`
Expected: failures for the new keyword arguments and metadata.

- [ ] **Step 3: Implement bounded queries and summaries**

Normalize `limit` to `1..150`; apply user/category/lifecycle/search predicates in SQL; select priority rows using focus, match, vitality, updated time, and id; derive a stable cursor from the final score/id pair; aggregate category/lifecycle counts in SQL; run `_build_graph_edges` only over returned beliefs and slice ambient edges to 120 while retaining focused direct edges.

- [ ] **Step 4: Expose validated FastAPI query parameters**

Add `q`, `category`, `lifecycle`, `cursor`, `limit`, `focus_id`, and `include_summary` to `/api/graph/{user_id}` with `limit=Query(150, ge=1, le=150)` and forward them by keyword.

- [ ] **Step 5: Add search indexes**

Add a PostgreSQL GIN expression index over lower-cased entity/relation/value/category text and a compatible SQLite composite lookup index without changing existing migrations destructively.

- [ ] **Step 6: Verify and commit**

Run: `python -m pytest tests/test_api_data.py tests/test_api_main.py -q`
Expected: all tests pass.

Commit: `feat: bound archive graph reads`

### Task 2: Searchable progressively disclosed MnemTree

**Files:**
- Modify: `openclaw-harness/src/public/index.html`
- Modify: `openclaw-harness/src/public/scripts/api.js`
- Modify: `openclaw-harness/src/public/scripts/archive-store.js`
- Modify: `openclaw-harness/src/public/scripts/memory-model.js`
- Modify: `openclaw-harness/src/public/scripts/layout.js`
- Modify: `openclaw-harness/src/public/scripts/main.js`
- Create: `openclaw-harness/src/public/scripts/interactions/archive-search.js`
- Modify: `openclaw-harness/src/public/styles/base.css`
- Modify: `openclaw-harness/src/public/styles/archive-stage.css`
- Modify: `openclaw-harness/src/public/styles/responsive.css`
- Test: `openclaw-harness/test/api.test.mjs`
- Test: `openclaw-harness/test/archive-store.test.mjs`
- Test: `openclaw-harness/test/layout.test.mjs`
- Create: `openclaw-harness/test/archive-search.test.mjs`

**Interfaces:**
- Produces: `createArchiveSearch({ input, clearButton, status, onSearch, onSelect })` with 250 ms debounce, `/` focus, Escape clear, and arrow navigation.
- Extends: `fetchArchive(userId, options)` to encode the Task 1 graph query.
- Extends normalized graph with `totalBeliefs`, `returnedBeliefs`, `nextCursor`, `renderMode`, `summary`, and `truncated`.

- [ ] **Step 1: Write failing search, normalization, and scale tests**

Assert query encoding, debounce cancellation, keyboard behavior, server-result selection, metadata normalization, deterministic layouts at 100/500/1000/5000 input sizes, and maximum 150 nodes.

- [ ] **Step 2: Verify tests fail**

Run: `npm test --prefix openclaw-harness`
Expected: failures for missing search module and unbounded layout.

- [ ] **Step 3: Implement the accessible search control**

Add a labelled header search input, clear button, live result status, and result list. Encode search via `URLSearchParams`, abort stale requests with `AbortController`, highlight matches, focus/center selection, and restore the prior page when cleared.

- [ ] **Step 4: Bound layout and add aggregate buds**

Sort deterministically, preserve selected/search/recent/high-vitality nodes, cap individual forms at 150, group omitted items by category/lifecycle, create bounded aggregate bud records, and replace global all-pairs collision work for large inputs with fixed branch slots plus spatial buckets.

- [ ] **Step 5: Preserve narrative and state**

Display `Showing {returned} of {total} memories`; retain search, selection, zoom, and filters while pages change; keep focused direct relationships and the observation narrative coherent.

- [ ] **Step 6: Verify browser behavior and commit**

Run: `npm test --prefix openclaw-harness`
Run: `node openclaw-harness/scripts/check-visualizer.mjs`
Expected: Node suite and browser smoke pass with the MnemTree visible.

Commit: `feat: add scalable archive search`

### Task 3: Judge authentication and namespace boundary

**Files:**
- Modify: `openclaw-harness/src/index.js`
- Create: `openclaw-harness/src/judge-auth.js`
- Create: `openclaw-harness/src/public/judge.html`
- Modify: `openclaw-harness/test/api.test.mjs`
- Create: `openclaw-harness/test/judge-auth.test.mjs`
- Modify: `config/env.template`

**Interfaces:**
- Produces: signed cookie `mnemagent_judge` scoped to the harness, containing namespace and expiry.
- Produces: `POST /judge/session`, `DELETE /judge/session`, and sanitized `GET /health`.
- Allows: public read-only `demo-brain`; authenticated session namespace; rejects every other browser namespace in cloud mode.

- [ ] **Step 1: Write failing auth tests**

Cover constant-time access-code comparison, signature/expiry rejection, five-attempt rate limit, secure cookie flags in cloud mode, public demo reads, demo mutation denial, arbitrary-user denial, and session namespace mapping.

- [ ] **Step 2: Verify tests fail**

Run: `npm test --prefix openclaw-harness`
Expected: missing auth module and cloud route-policy failures.

- [ ] **Step 3: Implement minimal judge sessions**

Use Node `crypto.createHmac('sha256', sessionSecret)` over base64url JSON `{ namespace, exp }`; compare codes and signatures with `timingSafeEqual`; store only an in-memory IP attempt window; issue `HttpOnly; SameSite=Strict; Path=/` cookies and `Secure` in cloud mode.

- [ ] **Step 4: Enforce namespace policy and sanitized health**

Resolve browser requests to `demo-brain` or the signed namespace; never forward arbitrary `user` values in cloud mode; strip internal URLs, tokens, stack traces, and user-specific counts from public health.

- [ ] **Step 5: Verify and commit**

Run: `npm test --prefix openclaw-harness`
Expected: all auth and existing UI tests pass.

Commit: `feat: secure judge archive sessions`

### Task 4: Alibaba ECS cloud appliance

**Files:**
- Create: `compose.cloud.yml`
- Create: `docker/Caddyfile`
- Create: `docker/openclaw.Dockerfile`
- Create: `.env.cloud.example`
- Create: `scripts/deploy-cloud.sh`
- Create: `scripts/verify-cloud.sh`
- Create: `scripts/reset-judge.sh`
- Modify: `docker-compose.yml`
- Modify: `config/openclaw/openclaw.json`

**Interfaces:**
- Consumes mandatory environment variables: `MEMORY_DOMAIN`, `AGENT_DOMAIN`, `POSTGRES_PASSWORD`, `MNEMAGENT_API_TOKEN`, `JUDGE_ACCESS_CODE`, `JUDGE_SESSION_SECRET`, `OPENCLAW_BASIC_AUTH_HASH`, and `DASHSCOPE_API_KEY`.
- Produces: `docker compose -f docker-compose.yml -f compose.cloud.yml --profile judge-agent up -d` with only Caddy-published ports.

- [ ] **Step 1: Add cloud configuration contract tests**

Extend the verification script to fail before starting containers when secrets are absent/default, domains are invalid, or required files are missing. Add `--config-only` to render and inspect Compose configuration without credentials or network calls.

- [ ] **Step 2: Create the overlay and pinned OpenClaw image**

Remove public application/database port mappings in the overlay, add health checks/restart policies, add Caddy on 80/443, add the `judge-agent` OpenClaw profile on the private network, pin all image/package versions, and configure OpenClaw MCP as `http://mnemos-mcp:8001/mcp`.

- [ ] **Step 3: Add Caddy routing**

Route `memory` to the harness; route `agent` with hashed basic auth and WebSocket-compatible reverse proxying to OpenClaw; set CSP, frame, referrer, content-type, and HSTS headers; cap request bodies; expose no upstream addresses.

- [ ] **Step 4: Add defensive deployment/reset/verification scripts**

Use `set -Eeuo pipefail`, dependency checks, quoted variables, Compose preflight, readiness loops with deadlines, reset confirmation, and non-secret output. Verification must check TLS/auth, seven MCP tools, demo read-only policy, judge store/recall/revision flow, and public port expectations.

- [ ] **Step 5: Validate and commit**

Run: `docker compose -f docker-compose.yml -f compose.cloud.yml config --quiet`
Run: `bash -n scripts/deploy-cloud.sh scripts/verify-cloud.sh scripts/reset-judge.sh`
Expected: Compose and shell syntax validation pass.

Commit: `feat: add Alibaba ECS deployment appliance`

### Task 5: Modernize verifiable Alibaba OSS backups

**Files:**
- Modify: `mcp-memory-server/src/storage/cloud_sync.py`
- Modify: `mcp-memory-server/src/config.py`
- Modify: `requirements/prod.txt`
- Modify: `tests/test_cloud_sync.py`

**Interfaces:**
- Produces: `OssBackupClient.upload(path, object_key, metadata) -> bool` behind an injectable client protocol.
- Accepts: ECS RAM role/default credential chain or explicit environment credentials; independent endpoint, region, bucket, and prefix.

- [ ] **Step 1: Write failing fake-client tests**

Cover missing configuration, RAM/default credentials, explicit credentials, internal endpoints, prefix sanitization, PostgreSQL custom dump upload, metadata, secret-free errors, and non-blocking failure.

- [ ] **Step 2: Verify tests fail**

Run: `python -m pytest tests/test_cloud_sync.py -q`
Expected: failures for the new client seam and configuration fields.

- [ ] **Step 3: Implement current OSS client integration**

Use Alibaba Cloud's current OSS Python SDK/default credential provider, keep imports optional when backup is disabled, invoke `pg_dump --format=custom` with a temporary file, upload with application version/timestamp metadata, and return false without interrupting memory service on failure.

- [ ] **Step 4: Verify and commit**

Run: `python -m pytest tests/test_cloud_sync.py tests/test_config.py -q`
Expected: all tests pass without real Alibaba credentials.

Commit: `feat: modernize Alibaba OSS backups`

### Task 6: Judge-first documentation consolidation

**Files:**
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Create: `docs/JUDGE_GUIDE.md`
- Create: `docs/DEPLOY_ALIBABA.md`
- Create: `docs/BENCHMARKS.md`
- Create: `docs/SECURITY.md`
- Create: `docs/VIDEO_SCRIPT.md`
- Create: `docs/SUBMISSION_CHECKLIST.md`
- Modify: `docs/README.md`
- Move superseded: `docs/CLOUD.md`, `docs/CLOUD_PROOF.md`, `docs/JUDGE_DEPLOYMENT.md`, `docs/LIVE_EVAL_RESULTS.md`, `docs/MNEMBENCH_RESULTS.md`, `docs/REPORT.md`, `docs/SETUP.md`, `docs/SUBMISSION_VIDEO_PLAN.md`, `docs/VERIFICATION.md` to `docs/archive/` after preserving unique material.

**Interfaces:**
- Produces a root judge landing document whose first screen identifies Track 1, links architecture/license/proof, and shows the populated tree.
- Uses only verified benchmark numbers from committed run artifacts; labels unavailable deployment/video URLs as owner-pending text.

- [ ] **Step 1: Inventory claims and unique documentation**

Cross-check every README command against scripts and Compose, every benchmark number against committed reports, and every old document section against the canonical destination before moving it.

- [ ] **Step 2: Rewrite README in judge priority order**

Order: identity/Track/value, submission links, populated screenshot, three-minute path, architecture, track-aligned features, strongest benchmark, five-minute local start, cloud summary, security, verification, repository map, license. Remove local absolute paths, fake URLs, stale test totals, `/visualizer`, floating versions, and incorrect shell commands.

- [ ] **Step 3: Write canonical documents and architecture diagrams**

Document public/private trust boundaries, browser and terminal flows, Qwen/DashScope, MCP, persistence/recall/forgetting/contradiction algorithms, scale modes, ECS/OSS proof, threat model, exact video timestamps, rollback, and owner completion checklist.

- [ ] **Step 4: Archive superseded documents**

Move rather than delete historical reports once every unique command, result, limitation, and proof instruction is preserved. Update all internal links to canonical documents.

- [ ] **Step 5: Validate and commit**

Run repository link/command scans for `<repo-url>`, `C:\\sem4`, `/visualizer`, `openclaw@latest`, stale test totals, and broken relative Markdown targets.
Expected: no stale judge-facing references; pending external URLs are plainly labelled.

Commit: `docs: make submission judge ready`

### Task 7: Full verification, current screenshot, and publication

**Files:**
- Modify: `docs/assets/visualizer-snapshot.png`
- Modify only if verification exposes defects: files from Tasks 1-6

**Interfaces:**
- Produces a populated `demo-brain` screenshot at the README path and a clean, pushed `main`.

- [ ] **Step 1: Run complete automated verification**

Run: `python -m pytest -q`
Run: `npm test --prefix openclaw-harness`
Run: `node openclaw-harness/scripts/check-visualizer.mjs`
Run: `docker compose -f docker-compose.yml -f compose.cloud.yml config --quiet`
Run: `bash -n scripts/deploy-cloud.sh scripts/verify-cloud.sh scripts/reset-judge.sh`
Expected: every command exits zero.

- [ ] **Step 2: Inspect the live visualizer**

Use `http://127.0.0.1:3100/?user=demo-brain`; verify loading choreography, search, leaf labels, selection clarity, independent panel scrolling, responsive sizing, and tree centering at desktop and narrow widths.

- [ ] **Step 3: Capture populated screenshot**

Replace `docs/assets/visualizer-snapshot.png` with the verified populated-tree viewport, preserving legible logo, centered tree, and complete observation panel.

- [ ] **Step 4: Confirm authorship and repository state**

Run: `git log --format='%an <%ae>' <pre-hardening-commit>..HEAD | Sort-Object -Unique`
Expected: only `crankysmh47 <annankhan741@gmail.com>`.

- [ ] **Step 5: Commit final evidence and push**

Commit: `chore: finalize hackathon submission evidence`
Run: `git push origin main`
Expected: remote `main` advances to the verified local commit.

## Owner deployment completion

After repository completion, the owner supplies Alibaba ECS/DNS/DashScope/OSS credentials through the server environment, runs the documented deployment and verifier, records the public three-minute video, inserts the final deployment/video URLs, verifies GitHub About/license visibility, and creates the submission tag. These external proof items cannot be fabricated locally.
