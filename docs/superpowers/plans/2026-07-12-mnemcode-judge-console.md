# MnemCode judge console implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a secure, visibly agentic OpenClaw coding-maintainer demonstration with scoped memory, isolated workspaces, draft-PR approval, and a MnemTree-first judge console.

**Architecture:** Add core/repository scope to the existing memory store, use a loopback workspace broker to own GitHub writes and constrained runner containers, and make the existing Express harness a browser client of a locked-down OpenClaw judge-coder workflow. The tree stays primary; the right column becomes the agent workbench and the existing observation content becomes a bottom Memory Lens.

**Tech Stack:** Python 3.11/FastAPI/PostgreSQL/SQLite, Node 20/Express/vanilla JavaScript, OpenClaw Gateway/MCP, Docker Compose/Caddy, GitHub REST API, pytest and Node test runner.

## Global Constraints

- Branch: `MnemCode`; commits authored only by `crankysmh47 <annankhan741@gmail.com>`.
- Preserve the botanical MnemTree and existing loading, motion, search, and accessibility behavior.
- Public users may read `demo-brain`; interactive judging requires a signed access-code session.
- Render at most 150 individual memories and 120 ambient relationships.
- Core/repository memories are isolated by explicit scope; repository contradictions never modify core memories.
- One allowlisted public repository, one workspace, one runner, and draft PRs only.
- No generic shell, terminal, arbitrary MCP, arbitrary repository, arbitrary package install, or browser-exposed secrets.
- Runner has no network and cannot receive GitHub/provider credentials.
- Model use has a global USD 4.50 estimated-cost hard stop.

---

### Task 1: Scope-aware memory schema and retrieval

**Files:**
- Modify: `mcp-memory-server/src/storage/schema.sql`
- Modify: `mcp-memory-server/src/storage/schema.postgres.sql`
- Create: `mcp-memory-server/src/storage/migrations/001_memory_scopes.py`
- Modify: `mcp-memory-server/src/memory/api_data.py`
- Modify: `mcp-memory-server/src/memory/waking.py`
- Modify: `mcp-memory-server/src/memory/dreaming.py`
- Modify: `mcp-memory-server/src/main.py`
- Test: `tests/test_memory_scopes.py`
- Test: `tests/test_api_data.py`

**Interfaces:**
- `MemoryScope(scope_type: Literal['core', 'repository'], scope_id: str)`.
- `get_graph_data(..., scope_type='core', scope_id='core', include_core=False)`.
- `retrieve_scoped_beliefs(user_id, repository_id, query, limit=6) -> list[dict]` returning at most four repository and two core beliefs.

- [ ] Write failing migration and isolation tests for core defaults, same facts in two scopes, scope-local contradiction, and 4/2 retrieval.
- [ ] Run `python -m pytest tests/test_memory_scopes.py -q` and confirm failures identify missing scope contract.
- [ ] Add non-null scope columns/defaults and replace uniqueness/index contracts in SQLite and PostgreSQL migrations without losing existing rows.
- [ ] Thread scope through store/search/graph/event/prospective APIs and MCP-facing payloads; reject malformed repository IDs.
- [ ] Implement deterministic scope retrieval and cache-safe graph summaries.
- [ ] Run `python -m pytest tests/test_memory_scopes.py tests/test_api_data.py tests/test_waking.py -q`.
- [ ] Commit `feat: add core and repository memory scopes`.

### Task 2: Demonstration repository fixture

**Files:**
- Create: `judge-lab/AGENTS.md`
- Create: `judge-lab/package.json`
- Create: `judge-lab/src/config.js`
- Create: `judge-lab/src/server.js`
- Create: `judge-lab/test/config.test.js`
- Create: `judge-lab/test/server.test.js`
- Create: `judge-lab/issues/01-retry.md`
- Create: `judge-lab/issues/02-timeout.md`
- Create: `judge-lab/issues/03-request-size.md`
- Test: `judge-lab/package.json` script `test`

**Interfaces:**
- `npm test` completes under five seconds without network.
- `AGENTS.md` allows only `npm test` and `node --check` in judge runs.

- [ ] Write initial tests that fail because retry and timeout validation do not exist.
- [ ] Implement a tiny dependency-free HTTP configuration fixture with an intentional issue boundary.
- [ ] Write three issue files with acceptance criteria, expected changed files, and review-learning prompts.
- [ ] Run `npm test --prefix judge-lab` and record baseline behavior.
- [ ] Commit `test: add coding agent laboratory fixture`.

### Task 3: Runner image and workspace policy

**Files:**
- Create: `workspace-runner/Dockerfile`
- Create: `workspace-runner/command-policy.js`
- Create: `workspace-runner/patch-policy.js`
- Create: `workspace-runner/runner.js`
- Create: `workspace-runner/package.json`
- Create: `workspace-runner/test/command-policy.test.mjs`
- Create: `workspace-runner/test/patch-policy.test.mjs`
- Modify: `docker-compose.yml`
- Modify: `compose.cloud.yml`

**Interfaces:**
- `validateCommand({ commandId, testNamePattern }) -> { argv: string[] }`.
- `validatePatch(patch, workspaceRoot) -> PatchSummary` with five-file/500-line caps.
- Runner accepts JSON on stdin and returns JSON on stdout; no shell invocation.

- [ ] Write failing tests for unsafe command arguments, traversal, protected files, symlinks, oversized patches, and valid fixture changes.
- [ ] Run `npm test --prefix workspace-runner` and confirm policy tests fail before implementation.
- [ ] Implement exact-argv command policy and unified-diff parser; reject every unapproved case before filesystem writes.
- [ ] Build runner image with no network tooling and non-root user; declare Docker hardening flags in the broker launch contract.
- [ ] Run policy tests and `docker build -t mnemagent-judge-runner workspace-runner`.
- [ ] Commit `feat: add constrained workspace runner`.

### Task 4: Loopback workspace broker and GitHub transaction

**Files:**
- Create: `workspace-broker/package.json`
- Create: `workspace-broker/src/config.js`
- Create: `workspace-broker/src/session-store.js`
- Create: `workspace-broker/src/github-client.js`
- Create: `workspace-broker/src/workspace-manager.js`
- Create: `workspace-broker/src/index.js`
- Create: `workspace-broker/test/workspace-manager.test.mjs`
- Create: `workspace-broker/test/github-client.test.mjs`
- Create: `workspace-broker/test/approval.test.mjs`
- Modify: `docker-compose.yml`
- Modify: `compose.cloud.yml`
- Modify: `.env.cloud.example`

**Interfaces:**
- Loopback API `/v1/workspaces`, `/v1/workspaces/:id/files`, `/patch`, `/test`, `/diff`, `/prepare-pr`, `/open-pr`, `/cleanup`.
- HMAC headers `x-mnemcode-timestamp`, `x-mnemcode-nonce`, `x-mnemcode-signature`.
- `approval_token` binds `runId + diffHash + prMetadataHash` for five minutes.

- [ ] Write failing tests for repository allowlist, HMAC replay, one-workspace semaphore, token redaction, branch naming, expired approval, and changed-diff invalidation.
- [ ] Run `npm test --prefix workspace-broker` and confirm the broker contract is absent.
- [ ] Implement broker config requiring a demo repository, GitHub token, HMAC secret, workspace root, and runner image; exit at startup on placeholders.
- [ ] Implement shallow clone, credential helper deletion, structured file access, runner invocation, diff hashing, cleanup sweeper, and sanitized manifests.
- [ ] Implement GitHub issue read, branch push, and draft PR creation through the API; prohibit direct main writes and non-draft PRs.
- [ ] Run broker tests and a local fixture issue-to-diff flow with a fake GitHub client.
- [ ] Commit `feat: add secure coding workspace broker`.

### Task 5: OpenClaw judge-coder tools and run event adapter

**Files:**
- Create: `openclaw-harness/src/judge-run-service.js`
- Create: `openclaw-harness/src/judge-events.js`
- Create: `openclaw-harness/src/judge-policy.js`
- Modify: `openclaw-harness/src/index.js`
- Modify: `config/openclaw/openclaw.json`
- Create: `config/openclaw/judge-coder.md`
- Create: `openclaw-harness/test/judge-policy.test.mjs`
- Create: `openclaw-harness/test/judge-events.test.mjs`

**Interfaces:**
- `createJudgeRun({ sessionId, issueNumber, message }) -> JudgeRun`.
- `appendEvent(runId, event) -> JudgeEvent` with monotonic sequence.
- Express endpoints `/api/judge/scenarios`, `/api/judge/runs`, `/api/judge/runs/:id`, `/events`, `/stop`, `/approve-pr`, `/reset`.

- [ ] Write failing tests for event sequencing, session/issue validation, tool allowlist, model budget lockout, PR approval handoff, and replayable SSE payloads.
- [ ] Run `npm test --prefix openclaw-harness` and confirm missing judge modules.
- [ ] Implement server-owned judge run state, event stream, 24-hour retention, 15-second SSE keepalive, stop semantics, and a single global run semaphore.
- [ ] Configure the OpenClaw profile to use only MnemAgent, read-only GitHub issue, and structured workspace tools; prohibit generic exec and host filesystem tools.
- [ ] Implement usage ledger and USD 4.25 soft / USD 4.50 hard budget transitions to replay mode.
- [ ] Run judge-unit tests and mock issue-to-approval flow.
- [ ] Commit `feat: add observable judge coding runs`.

### Task 6: Judge session security boundary

**Files:**
- Modify: `openclaw-harness/src/cloud-policy.js`
- Create: `openclaw-harness/src/judge-auth.js`
- Modify: `openclaw-harness/src/index.js`
- Modify: `openclaw-harness/test/cloud-policy.test.mjs`
- Create: `openclaw-harness/test/judge-auth.test.mjs`
- Modify: `.env.cloud.example`
- Modify: `docker/Caddyfile`

**Interfaces:**
- `POST /judge/session`, `DELETE /judge/session`, `GET /api/judge/session`.
- Signed HTTP-only cookie with judge namespace and expiry.
- `requireJudgeSession` protects every mutable judge endpoint.

- [ ] Write failing tests for constant-time comparison, cookie flags, expiry, CSRF, five-attempt lockout, demo read-only access, arbitrary-user denial, and same-origin validation.
- [ ] Run judge auth tests and confirm no authenticated judge session exists yet.
- [ ] Implement signed sessions, CSRF double-submit token, IP-window rate limiting, trusted namespace mapping, and sanitized auth errors.
- [ ] Add Caddy headers, request cap, and production-only required-secret validation.
- [ ] Run all harness policy/auth tests.
- [ ] Commit `feat: secure interactive judge sessions`.

### Task 7: MnemTree scope rendering and Memory Lens

**Files:**
- Modify: `openclaw-harness/src/public/index.html`
- Modify: `openclaw-harness/src/public/scripts/memory-model.js`
- Modify: `openclaw-harness/src/public/scripts/layout.js`
- Modify: `openclaw-harness/src/public/scripts/main.js`
- Modify: `openclaw-harness/src/public/scripts/render/living-structure.js`
- Create: `openclaw-harness/src/public/scripts/render/memory-lens.js`
- Modify: `openclaw-harness/src/public/styles/base.css`
- Modify: `openclaw-harness/src/public/styles/archive-stage.css`
- Modify: `openclaw-harness/src/public/styles/observation-margin.css`
- Modify: `openclaw-harness/src/public/styles/responsive.css`
- Create: `openclaw-harness/test/memory-lens.test.mjs`
- Modify: `openclaw-harness/test/layout.test.mjs`

**Interfaces:**
- Normalized memory has `scopeType` and `scopeId`.
- `renderMemoryLens(root, state, activeTab)` renders `Selected`, `Archive`, and `Legend`.
- `computeArchiveLayout` gives core memories trunk/root priority and repository memories canopy priority.

- [ ] Write failing tests for scope normalization, scope-isolated search, deterministic core-root placement, repository canopy placement, lens tabs, and desktop containment.
- [ ] Run focused Node tests and confirm scope/lens contracts are missing.
- [ ] Extend memory model/layout/renderer without changing category shapes; add scope chips and scope-filtered search.
- [ ] Move narrative, detail, vital signs, and legend into a collapsible bottom Memory Lens; reduce the global activity rail to 56px.
- [ ] Verify existing loading, fall, vine, selection, tooltip, and reduced-motion tests still pass.
- [ ] Commit `feat: add scoped tree and memory lens`.

### Task 8: Agent workbench and judge landing

**Files:**
- Create: `openclaw-harness/src/public/scripts/judge-console.js`
- Create: `openclaw-harness/src/public/scripts/judge-api.js`
- Create: `openclaw-harness/src/public/scripts/render/agent-workbench.js`
- Create: `openclaw-harness/src/public/judge.html`
- Modify: `openclaw-harness/src/public/index.html`
- Modify: `openclaw-harness/src/public/scripts/main.js`
- Modify: `openclaw-harness/src/public/styles/base.css`
- Create: `openclaw-harness/src/public/styles/agent-workbench.css`
- Modify: `openclaw-harness/src/public/styles/responsive.css`
- Create: `openclaw-harness/test/judge-console.test.mjs`
- Create: `openclaw-harness/test/agent-workbench.test.mjs`

**Interfaces:**
- `createJudgeConsole({ root, api, onFocusMemory })`.
- Agent tabs `Conversation`, `Activity`, `Changes`, `Memory`.
- Public landing actions route to demo, judge access, architecture, benchmarks, proof, repository, license, and video.

- [ ] Write failing DOM tests for landing actions, access gate, activity step order, PR approval state, replay mode, scope chips, and responsive workbench behavior.
- [ ] Run Node tests and confirm console modules do not exist.
- [ ] Implement the 420–480px desktop workbench, 56px collapsible rail, tablet drawer, and mobile `Agent/Memory/Evidence` tabs.
- [ ] Implement prepared scenario cards, conversation composer, SSE subscription/reconnect, activity sanitization, diff/test display, PR approval, and memory-to-tree focus.
- [ ] Implement judge landing with no fake external links and public read-only demo route.
- [ ] Run the complete harness test suite and browser smoke test.
- [ ] Commit `feat: add MnemCode judge workbench`.

### Task 9: Docker/cloud integration, interruption handling, and documentation

**Files:**
- Modify: `docker-compose.yml`
- Modify: `compose.cloud.yml`
- Modify: `.env.cloud.example`
- Create: `scripts/spot-interruption-watch.sh`
- Create: `scripts/verify-mnemcode.sh`
- Modify: `scripts/deploy-cloud.sh`
- Modify: `scripts/verify-cloud.sh`
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/JUDGE_GUIDE.md`
- Modify: `docs/DEPLOY_ALIBABA.md`
- Modify: `docs/SECURITY.md`
- Modify: `docs/SUBMISSION_CHECKLIST.md`
- Create: `docs/MNEMCODE_DEMO.md`

**Interfaces:**
- Cloud environment variables include judge secrets, workspace HMAC secret, GitHub token, demo repository, runner image, OpenClaw endpoint, and model-cost caps.
- Spot watcher consumes Alibaba interruption metadata, blocks new runs, triggers backup, and records an event.

- [ ] Write shell/config validation tests for missing secrets, unsafe repository, unpinned runner image, and prohibited public ports.
- [ ] Run validation and confirm MnemCode cloud configuration is incomplete.
- [ ] Add services/health checks/restart policies, loopback-only broker/Gateway/MCP bindings, resource limits, and the spot watcher systemd instructions.
- [ ] Add deploy verifier coverage for judge auth, public demo read-only policy, workspace policy, one real draft PR, fresh-session recall, and OSS backup.
- [ ] Rewrite README and canonical documents around the coding-agent story; label future scope explicitly.
- [ ] Run `docker compose ... config --quiet`, shell syntax checks, Caddy validation, link scans, and documentation command scans.
- [ ] Commit `docs: prepare MnemCode judge submission`.

### Task 10: End-to-end verification and release handoff

**Files:**
- Modify only if verification finds defects from Tasks 1–9.

- [ ] Run `python -m pytest -q`.
- [ ] Run `npm test --prefix openclaw-harness`.
- [ ] Run `npm test --prefix workspace-runner` and `npm test --prefix workspace-broker`.
- [ ] Run `node openclaw-harness/scripts/check-visualizer.mjs`.
- [ ] Run local issue 1 to approved draft-PR simulation and issue 2 fresh-session memory recall simulation.
- [ ] Validate Compose, Caddy, shell scripts, access policy, and no-secret scans.
- [ ] Inspect desktop, tablet, and mobile views with a populated tree, agent activity, Memory Lens, and a completed PR state.
- [ ] Confirm all MnemCode commits have only the required author.
- [ ] Commit `chore: finalize MnemCode judge experience`.
- [ ] Push `MnemCode` and create a ready pull request only after the user provides or authorizes the demo GitHub repository/token setup.
