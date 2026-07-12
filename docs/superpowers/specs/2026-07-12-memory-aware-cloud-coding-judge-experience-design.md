# Memory-aware cloud coding judge experience design

## 1. Objective

Turn MnemAgent into a judge-ready, single-use-case agent product: an OpenClaw coding maintainer that reads a prepared GitHub issue, works in an isolated cloud workspace, runs bounded tests, opens a draft pull request after explicit approval, and remembers repository conventions and review corrections across later sessions.

The result must make the agent loop visible, preserve the existing MnemTree as the visual soul of the product, run on one low-cost Alibaba ECS instance, and remain safe enough to expose during the judging window.

## 2. Build scope

### Required for submission

- Judge landing and access-code gate.
- Current populated `demo-brain` read-only archive.
- Collapsible OpenClaw-backed coding workbench.
- Conversation, activity, changes, and memory views.
- One allowlisted public demonstration repository.
- Three prepared coding issues.
- One ephemeral workspace at a time.
- Structured repository read, search, patch, test, diff, push, and draft-PR tools.
- Core and repository memory scopes.
- DeepSeek default model with a global USD 5 usage circuit breaker.
- Qwen/DashScope remains configured and evidenced as the Alibaba/Qwen submission path.
- GitHub fine-grained token restricted to the demonstration repository.
- Exact judge walkthrough, video script, architecture, and security documentation.

### Explicit non-goals

- No browser terminal.
- No arbitrary shell.
- No arbitrary repository URL.
- No private judge repositories.
- No arbitrary MCP server installation.
- No arbitrary provider base URL or general BYOK.
- No direct pushes to `main`.
- No PR merge capability.
- No package installation during a judge run.
- No deployment execution from the coding workspace.
- No multi-agent orchestration.
- No more than one concurrent coding run on the submission instance.

Future capabilities appear in documentation only: GitHub App installation flow, private repositories, curated MCP catalog, generic BYOK, multi-repository work, and larger concurrent runner pools.

## 3. Deployment decision

- Use Alibaba Cloud Hong Kong, outside mainland China ICP filing requirements.
- Use one 2-vCPU/4-GiB spot ECS instance with the bid ceiling set to the normal pay-as-you-go price.
- Use a 40-GiB system disk, pay-by-traffic public bandwidth, and a 5-Mbps cap.
- Keep one private Standard LRS OSS bucket with a 30-day lifecycle on `agent_runtime/backups/`.
- Run PostgreSQL, MnemAgent API, MnemAgent MCP, visualizer, OpenClaw Gateway, workspace broker, runner controller, and Caddy on the one instance.
- Add 4 GiB encrypted swap on ECS. Set `vm.swappiness=10`.
- Allow one active workspace and queue additional coding requests.
- Keep the public application on ports 80/443 only. SSH is restricted to the owner IP. API, MCP, Gateway, PostgreSQL, and workspace broker remain loopback or Compose-internal.
- Spot interruption handling uploads a final PostgreSQL dump and workspace manifest to OSS when the five-minute interruption notice is detected. Draft branches and PRs already pushed to GitHub survive instance loss.

Spot billing does not exempt mainland-hosted public websites from ICP filing. The deployment must not use a mainland China region.

## 4. Judge journey

### 4.1 Arrival

`GET /` shows the judge landing state, not an unexplained archive.

Above the fold:

- Official logo and MnemAgent name.
- `Track 1: MemoryAgent` label.
- One sentence: `A coding agent that remembers how your repository wants to be maintained.`
- Alibaba Cloud deployment badge based on sanitized health.
- Primary action: `Try the coding agent`.
- Secondary action: `Explore its memory`.
- Text links: architecture, benchmark evidence, cloud proof, GitHub, MIT license, video.

The landing page must not make claims whose final URL/evidence is absent. Missing external evidence displays `Pending final deployment proof`, never a dead link.

### 4.2 Access

- Public users may explore `demo-brain` read-only without a code.
- Interactive coding requires a shared judge access code.
- `POST /judge/session` accepts `{ accessCode }` with a 64-byte maximum.
- Successful validation issues a signed `HttpOnly; Secure; SameSite=Strict; Path=/` cookie.
- Cookie lifetime is 45 minutes, extended only while an agent run is active, with an absolute maximum of 90 minutes.
- Five failed attempts per IP in 15 minutes trigger a 30-minute lockout.
- Access-code comparison is constant-time.
- Logs record only allow/deny, IP hash, and timestamp; never the code or cookie.

### 4.3 Guided proof

After access, the judge sees four numbered checkpoints:

1. `Teach the repository` — establish conventions.
2. `Let the agent work` — run issue 1 and open a draft PR.
3. `Correct the maintainer` — provide review feedback that revises memory.
4. `Start fresh` — run issue 2 in a new OpenClaw session and observe the learned convention applied automatically.

Each checkpoint has one primary button, a two-sentence explanation, and an authoritative completion signal. Judges may skip the guide and use free-form chat within the same safety bounds.

## 5. Desktop and responsive layout

### 5.1 Desktop at 1280px and wider

The application remains viewport-contained:

```text
58px header
┌──────────────────────────────────────────┬───────────────────────────┐
│                                          │                           │
│             MnemTree stage               │     Agent workbench       │
│             minmax(0, 1fr)               │     420–480px             │
│                                          │                           │
├──────────────────────────────────────────┤                           │
│ Memory Lens, 168px collapsed / 320px max │                           │
└──────────────────────────────────────────┴───────────────────────────┘
56px activity/history rail
```

- New CSS variable `--agent-w: clamp(420px, 34vw, 480px)`.
- The current observation margin is removed from the right grid column.
- The agent workbench occupies the right column permanently on desktop and can collapse to a 56px vertical rail.
- The tree stage retains at least 640px width. When the viewport cannot satisfy tree and workbench minimums, switch to tablet layout rather than shrinking the tree further.
- The current right-side narrative, selected-memory detail, vital signs, and legend move into `Memory Lens`, a bottom dock belonging to the tree column.
- `Memory Lens` tabs: `Selected`, `Archive`, `Legend`.
- Collapsed Memory Lens shows the selected memory statement, scope chip, vitality, and relationship count in one line.
- Expanded height is capped at 40% of the tree column and scrolls internally.
- The current sediment timeline becomes a 56px global activity rail. It shows agent events and memory events in a single chronological stream.

### 5.2 Tablet from 768px through 1279px

- Workbench becomes a right overlay drawer of `min(440px, 88vw)`.
- Tree uses the full viewport width.
- A fixed `Agent` pill opens the drawer.
- Memory Lens remains a bottom dock, collapsed by default.
- Only one overlay may be expanded at a time.

### 5.3 Mobile below 768px

- Header contains logo, connection state, and compact menu.
- Main content uses three top-level tabs: `Agent`, `Memory`, `Evidence`.
- Default authenticated tab is `Agent`; default public tab is `Memory`.
- Memory tab retains the existing full-height botanical stage.
- Selected-memory content uses the existing bottom-sheet pattern.
- Agent activity and changes are nested tabs inside the Agent view.
- Minimum interactive target is 44px.
- No horizontal page scrolling.

## 6. Agent workbench

### 6.1 Header

- Title: `Repository maintainer`.
- Repository badge: `crankysmh47/MnemAgent-Agent-Lab`.
- Model badge: exact configured model.
- Session status: `Ready`, `Thinking`, `Using a tool`, `Awaiting approval`, `Complete`, or `Degraded`.
- Budget indicator: judge turns remaining, not dollars.
- Reset control requires confirmation when a run is active.

### 6.2 Tabs

#### Conversation

- User and agent messages.
- Three prepared scenario cards above the empty composer.
- Composer maximum 2,000 characters.
- Submit disabled during a tool approval or when global budget is exhausted.
- Stop button cancels the active model stream and prevents new tool calls, but does not kill an already-running allowed test command; its result is recorded and ignored by the cancelled turn.

#### Activity

Every OpenClaw event renders as a compact step:

- plan created;
- MCP tool requested;
- approval requested/resolved;
- tool started/completed/failed;
- model response started/completed;
- memory proposed/accepted/rejected/revised;
- workspace created/cleaned;
- PR prepared/opened.

Each event includes timestamp, human label, duration when applicable, and a collapsible sanitized payload. Never show tokens, GitHub credentials, file-system host paths, raw environment variables, or full model prompts.

#### Changes

- Workspace branch.
- Files changed with additions/deletions.
- Unified diff capped at 400 visible lines; larger diffs show a truncation notice.
- Test command and exit code.
- Draft PR title, body preview, and final link.
- `Approve draft PR` is the only control that can cause a GitHub write after the coding turn begins.

#### Memory

- `Recalled before work` section.
- `Learned during work` section.
- Scope chips: `Core` and `Repository`.
- Status: proposed, accepted, revised, rejected, fading.
- Direct link/animation focus into the corresponding tree memory.

### 6.3 Visible agentic narrative

Agent responses never hide tool use behind a spinner. The activity rail must make this sequence obvious:

```text
Issue read → repository inspected → memory searched → plan formed → files patched
→ tests executed → diff reviewed → approval requested → draft PR opened → lesson stored
```

## 7. Core and repository memory scopes

### 7.1 Data model

Add to `semantic_graph`, `memory_events`, `episodic_logs`, and `prospective_memories`:

- `scope_type TEXT NOT NULL DEFAULT 'core' CHECK (scope_type IN ('core', 'repository'))`.
- `scope_id TEXT NOT NULL DEFAULT 'core'`.

Canonical repository scope ID is lower-case `owner/name`, for example `crankysmh47/mnemagent-agent-lab`.

Change belief uniqueness from:

```text
(user_id, entity_source, relation)
```

to:

```text
(user_id, scope_type, scope_id, entity_source, relation)
```

Migrations must preserve every existing belief as `core/core`. SQLite and PostgreSQL remain behaviorally compatible.

### 7.2 Semantics

Core memories apply across repositories:

- communication preferences;
- general coding preferences;
- stable persona facts;
- universal approval preferences.

Repository memories apply only while that repository is active:

- naming conventions;
- architecture decisions;
- approved commands;
- dependency policy;
- ownership boundaries;
- prior rejected approaches;
- reviewer corrections;
- file-specific lessons.

A repository memory may not overwrite a core memory. Contradictions resolve only within the same `user_id + scope_type + scope_id + entity + relation` key. The agent may explicitly promote a stable repository lesson to core only after user approval; the judge experience does not expose promotion.

### 7.3 Retrieval budget

The active coding context retrieves at most six beliefs:

- Up to four repository-scoped beliefs.
- Up to two core beliefs.
- Unused repository slots may be filled by core beliefs.
- Core slots are never filled by another repository's beliefs.
- Exact current contradictions and explicit task entities outrank general utility.
- Repository ID is mandatory for every coding-agent memory search and store.

### 7.4 MnemTree representation

- Core memories grow from the trunk and inner roots.
- Repository memories form the active canopy.
- A scope switch animates the canopy transition but keeps the core trunk stable.
- Core chip uses antique brass and moss.
- Repository chip uses mineral blue and lichen green.
- Scope is orthogonal to existing category shapes. Preference/persona/system-state shapes do not change.
- Search can span `Current repository`, `Core`, or `Both`; default is `Both` with repository matches ranked first.
- Header states `Core: N · Repository: N · Showing N of total`.

## 8. Demonstration repository

Create public repository `crankysmh47/MnemAgent-Agent-Lab` with:

```text
AGENTS.md
README.md
package.json
package-lock.json
src/config.js
src/server.js
test/config.test.js
test/server.test.js
```

- Node 20, CommonJS or ESM chosen once and documented.
- No runtime dependency beyond Node standard library.
- `npm test` completes in under five seconds.
- Baseline branch protection prevents direct main pushes.
- All prepared issues are solvable by editing at most three files and 120 lines.

Prepared issues:

1. `Add bounded retry configuration` — environment variable, validation, and tests.
2. `Add request timeout configuration` — must reuse learned pure validation convention.
3. `Add request-size protection` — prospective reminder asks the agent to mention security documentation.

Issue 1 intentionally permits two naming choices. Judge feedback establishes `RETRY_LIMIT` and `small pure validation functions`. Issue 2 is scored on whether the new session applies both without being reminded.

## 9. GitHub integration

### 9.1 Hackathon credential

Use one fine-grained GitHub token restricted to `MnemAgent-Agent-Lab`:

- Metadata: read.
- Contents: read/write.
- Issues: read.
- Pull requests: read/write.

No Actions, administration, deployments, environments, secrets, packages, webhooks, organization, or other repository access.

The token exists only in the workspace broker environment. It is never placed in the runner environment, browser, OpenClaw prompt, MCP output, logs, memory, or Git remote URL persisted on disk.

### 9.2 Write policy

- Repository allowlist contains exactly `crankysmh47/MnemAgent-Agent-Lab`.
- Branches use `mnemagent-judge/<issue-number>/<session-short-id>`.
- Base branch is `main` only.
- Draft PRs only.
- No force push.
- No merge.
- No deletion of branches or repository content.
- PR title prefix: `[MnemAgent Judge]`.
- PR body includes task, plan, files, tests, recalled memories, learned memories, and the fact that it was generated by the demonstration agent.
- Judge must approve the exact branch, diff summary, test result, PR title, and PR body before push/PR creation.

## 10. Cloud workspace architecture

### 10.1 Components

#### Judge web application

Owns browser session, presentation, access-code validation, SSE consumption, and approval UX. It does not execute Git, tests, or GitHub writes.

#### OpenClaw Gateway

Owns the agent session and model/tool loop. It is loopback-only. It receives a fixed tool allowlist for the coding agent.

#### Workspace broker

A small Node service running as a locked-down systemd unit on ECS, bound to `127.0.0.1:8010`. It is the sole owner of GitHub credentials and the sole component allowed to create workspaces or GitHub branches.

Broker authentication uses a 256-bit HMAC service token. Requests have a 60-second timestamp window and unique nonce. Replayed nonces are rejected.

#### Runner container

Prebuilt image `mnemagent-judge-runner` contains Git, Node 20, npm, ripgrep, and a patch utility. It contains no cloud CLI, Docker CLI, SSH client, curl/wget, compilers unnecessary for the demo, or GitHub credential.

### 10.2 Workspace lifecycle

1. Broker receives allowlisted repository and issue number.
2. Broker checks the one-workspace semaphore.
3. Broker creates UUIDv4 workspace ID and directory under `/var/lib/mnemagent/workspaces/<id>`.
4. Broker performs a shallow clone of `main` using a one-shot credential helper.
5. Broker removes the helper and verifies the remote URL contains no credential.
6. Broker creates the judge branch.
7. OpenClaw uses structured workspace tools to inspect and patch files.
8. Tests run in the runner container with the workspace mounted read/write.
9. Diff and status are calculated by the broker.
10. Judge approval permits one push and one draft-PR creation.
11. Broker redacts credentials, writes a final manifest, and deletes the workspace within five minutes of completion.
12. A sweeper deletes abandoned workspaces older than 45 minutes on startup and every ten minutes.

### 10.3 Runner restrictions

Run with:

```text
--rm
--network none
--read-only
--cap-drop ALL
--security-opt no-new-privileges
--memory 768m
--memory-swap 768m
--cpus 0.75
--pids-limit 128
--user 10001:10001
--tmpfs /tmp:rw,noexec,nosuid,size=128m
--volume <workspace>:/workspace:rw
--workdir /workspace
```

- One runner at a time.
- Hard execution timeout 120 seconds per command.
- Maximum total command time 300 seconds per workspace.
- stdout/stderr capped at 256 KiB per command.
- Only commands declared in the demo repository `AGENTS.md` and matched by exact argv are allowed.
- Submission allowlist: `npm test`, `npm test -- --test-name-pattern <safe-alphanumeric-pattern>`, and `node --check <workspace-relative-js-file>`.
- Shell metacharacters, redirection, command substitution, absolute paths, `..`, environment assignments, and additional arguments are rejected.

### 10.4 Structured workspace tools

Expose these tools to OpenClaw:

- `repo_get_issue(issue_number)`.
- `workspace_create(issue_number)`.
- `workspace_list_files(path=".", depth=3)`.
- `workspace_read_file(path, start_line=1, max_lines=300)`.
- `workspace_search(query, path=".", max_results=50)`.
- `workspace_apply_patch(patch)`.
- `workspace_run_test(command_id, test_name_pattern=None)`.
- `workspace_get_diff(max_lines=400)`.
- `workspace_prepare_pr(title, body)`.
- `workspace_open_draft_pr(approval_token)`.
- `workspace_cleanup()`.

The model never receives a generic `exec`, `shell`, `write_file`, or arbitrary URL tool.

### 10.5 Patch limits

- Patch parser accepts unified patches only.
- Paths must already exist in the repository, except one new test file under `test/`.
- Symlinks are rejected.
- Maximum five files touched.
- Maximum 500 changed lines globally.
- Maximum 200 changed lines in one file.
- Binary changes rejected.
- Files over 256 KiB rejected.
- `.git`, `.github/workflows`, lockfiles, secrets, Dockerfiles, deployment files, and dot-env files are immutable in judge mode.

## 11. OpenClaw orchestration

Create a dedicated agent profile `judge-coder` with:

- Fixed system instructions.
- Only MnemAgent MCP, read-only GitHub issue tool, and structured workspace tools.
- No browser, general filesystem, process execution, cron, messaging channel, package install, or administrative tools.
- Repository ID and judge namespace injected by trusted server context, never accepted from model output.
- Tool approval required for `workspace_open_draft_pr` only; all bounded read/patch/test tools are pre-approved.

State machine:

```text
READY
→ ISSUE_LOADED
→ MEMORY_RECALLED
→ PLAN_READY
→ WORKSPACE_READY
→ EDITING
→ TESTING
→ REVIEWING_DIFF
→ AWAITING_PR_APPROVAL
→ PR_OPENED
→ LESSONS_CONSOLIDATED
→ COMPLETE
```

Failure states transition to `DEGRADED` with a retryable boundary, not back to an earlier state silently.

The agent may attempt at most two patch/test cycles. If tests still fail, it presents the failing result and may open a draft PR only if the judge explicitly approves a failing draft; the default approval control remains disabled.

## 12. Event protocol

### 12.1 Endpoints

- `POST /api/judge/runs` creates a run from `{ issueNumber, message }`.
- `GET /api/judge/runs/:runId` returns sanitized state.
- `GET /api/judge/runs/:runId/events` is SSE with `Last-Event-ID` resumption.
- `POST /api/judge/runs/:runId/stop` cancels future agent/tool activity.
- `POST /api/judge/runs/:runId/approve-pr` accepts the current approval challenge.
- `POST /api/judge/runs/:runId/reset` cleans workspace and starts a new OpenClaw session.
- `GET /api/judge/scenarios` returns prepared scenario metadata.

### 12.2 Event shape

```json
{
  "id": "evt_01",
  "runId": "run_01",
  "sequence": 1,
  "type": "tool.completed",
  "phase": "testing",
  "label": "Tests passed",
  "timestamp": "2026-07-12T12:00:00Z",
  "durationMs": 842,
  "payload": { "command": "npm test", "exitCode": 0 }
}
```

- Sequence is monotonically increasing per run.
- Events persist for 24 hours or until submission teardown.
- Client deduplicates by event ID.
- Payload schema is allowlisted per event type; unknown fields are discarded server-side.
- SSE sends a keepalive every 15 seconds.

## 13. Model and spending controls

- Default model is the already-tested DeepSeek model with the lowest reliable cost. Exact model name is an environment variable and shown in UI.
- Qwen/DashScope remains the memory extraction/submission proof provider when configured.
- No BYOK in the submission UI.
- Maximum 20 conversational turns per judge session.
- Maximum two coding runs per judge session.
- Maximum ten successful coding runs globally.
- Maximum input 2,000 characters.
- Maximum model output 2,000 tokens per turn.
- Maximum tool calls 24 per coding run.
- Global soft stop at USD 4.25 estimated usage.
- Global hard stop at USD 4.50 estimated usage.
- Remaining USD 0.50 is owner verification reserve.
- Hard stop changes interactive UI to read-only replay mode and explains that the live evaluation allowance is exhausted.
- Usage ledger stores provider, model, input tokens, output tokens, estimated cost, run ID, and timestamp, never prompts or credentials.

## 14. Memory consolidation from coding work

The agent cannot store arbitrary chain-of-thought. It proposes compact facts only.

Allowed repository memory relations:

- `uses_convention`;
- `prefers_pattern`;
- `forbids_dependency`;
- `approved_command`;
- `owns_responsibility`;
- `supersedes`;
- `reviewer_prefers`;
- `failed_because` when confirmed by deterministic tool output.

Every proposal includes evidence source: issue, explicit judge message, AGENTS.md, test result, or PR review. Model-only inference has conviction at most 0.39 and is rejected by the existing 0.4 salience gate.

Explicit judge corrections use conviction 1.0. AGENTS.md facts use 0.95. Passing deterministic tests use 0.9 for command success. A single transient failure uses at most 0.3 and does not become semantic memory.

## 15. Failure and recovery behavior

- GitHub unavailable: keep local diff, show `GitHub unavailable`, allow retry for ten minutes, then upload sanitized patch artifact to OSS before cleanup.
- Model unavailable: retain workspace, stop new edits, show current plan/diff, allow one retry.
- MnemAgent unavailable: coding run does not start; judge can use read-only replay.
- Tests timeout: kill runner, record timeout, permit one patch cycle.
- Browser disconnect: run continues; SSE resume reconstructs activity.
- Spot interruption: stop new runs, reject approvals, push already-approved work if safe, dump Postgres, upload manifests to OSS, and terminate workspaces.
- Budget exhausted: no new model call; existing public demo and recorded replay remain available.
- Concurrent request: return queue position 1 and estimated start based on the active run deadline; queue holds at most two requests, then returns 429.
- Cleanup failure: quarantine workspace permissions, remove network access, alert owner, retry every minute.

## 16. Security requirements

- Shared judge access code and signed cookie.
- CSRF token on every state-changing browser request.
- Origin and Host allowlists.
- Content Security Policy without `unsafe-eval`.
- HTML and Markdown sanitized before rendering.
- Rate limits per IP and per judge session.
- GitHub token server-side only.
- Provider keys server-side only.
- No secrets in prompts, tool payloads, SSE, logs, errors, memory, diffs, or PRs.
- Repository, branch, file, command, and tool allowlists enforced outside the model.
- Approval challenge is single-use, bound to run ID, exact diff hash, PR metadata hash, and five-minute expiry.
- Recompute diff hash immediately before push.
- Audit events record actor session, action, resource, outcome, and timestamp without sensitive content.
- Dependency and container vulnerability scan before deployment.

## 17. Judge proof scenarios and acceptance outcomes

### Scenario A: first maintenance task

Judge runs issue 1. Agent reads issue, searches empty repository memory, patches within limits, passes tests, requests approval, opens a draft PR, and stores no invented convention.

### Scenario B: review learning

Judge says: `Use RETRY_LIMIT in this repository, keep validation in small pure functions, and avoid new dependencies.` Agent updates the first branch, passes tests, and stores three repository memories with explicit-message evidence.

### Scenario C: fresh-session improvement

Judge starts a new OpenClaw session and runs issue 2. Agent recalls all three repository memories before planning, uses the correct naming and validation pattern without another reminder, passes tests, and exposes the recall in Activity and Memory tabs.

### Scenario D: contradiction

Judge changes the convention from `RETRY_LIMIT` to `RETRY_ATTEMPTS`. The current repository belief becomes `RETRY_ATTEMPTS`; the superseded value is visible as revision history but excluded from active retrieval.

### Scenario E: salience defense

Judge says `Maybe use a validation library someday.` The candidate is rejected and no dependency is added.

## 18. Automated verification

### Memory scope

- Existing rows migrate to `core/core`.
- Same entity/relation may exist in core and one repository without collision.
- Contradiction in repository A does not affect core or repository B.
- Retrieval never leaks repository B into repository A.
- Six-belief budget and 4/2 preference are deterministic.

### Workspace broker

- Reject non-allowlisted repository.
- Reject second active workspace.
- Reject path traversal, symlink, binary, protected path, oversized patch, excess files, and excess lines.
- Runner has no network and cannot see GitHub token.
- Only exact allowed commands run.
- Timeout, output cap, CPU, memory, PID, and cleanup limits are enforced.
- Diff hash changes invalidate approval.
- PR is draft and branch prefix is correct.

### Judge web

- Public demo cannot mutate.
- Bad access code rate-limits.
- Cookie and CSRF policy work.
- SSE reconnect deduplicates and resumes.
- Agent states, tool calls, tests, approval, PR, and memory events render accessibly.
- Desktop, tablet, and mobile layouts contain scrolling correctly.
- Reduced motion preserves meaning.
- Budget exhaustion becomes replay mode.

### End to end

- Scenario A completes under four minutes.
- Scenario C completes under four minutes.
- At least one real draft PR is created in the demo repository.
- New session demonstrably recalls repository conventions.
- MnemTree core trunk remains stable while repository canopy changes.
- Full Python, Node, browser, Compose, Caddy, and shell verification stays green.

## 19. Documentation and judge-question defense

Root README order:

1. Track, value statement, live demo, and video.
2. Memory-aware coding-agent scenario.
3. Architecture diagram.
4. Exact judge flow.
5. Why memory changes the second PR.
6. Storage, retrieval, contradiction, forgetting, and context limits.
7. Workspace and GitHub security boundary.
8. Benchmark evidence and limitations.
9. Alibaba deployment proof.
10. Five-minute local run.
11. Future scope.

Documentation must answer:

- Why OpenClaw rather than a custom chat loop?
- How is this more than RAG?
- What makes the second task better?
- How are core and repository memories isolated?
- How are contradictions and stale conventions handled?
- Why can the agent not damage the repository?
- Where do tests run and what can they access?
- What happens when spot ECS is reclaimed?
- What happens when the model budget is exhausted?
- Why is arbitrary MCP installation excluded?
- How would GitHub App, BYOK, private repositories, and larger runners be added later?

## 20. Terra execution rules

- Work on a `codex/` or `terra/` feature branch, never directly on `main` until verification.
- Preserve the official logo, creamy palette, botanical forms, loading choreography, vines, water, grass, current spinner, search, and tree centering.
- Do not resurrect the old cortical/neon dashboard.
- Use test-driven development for each behavior.
- Commit after each independently passing subsystem.
- Never print `.env`, GitHub token, model keys, access code, session secret, or database password.
- Do not expand scope when a future-scope item is encountered; document it and continue.
- Do not expose a terminal or generic command endpoint as a shortcut.
- Do not claim the judge console is complete until a real issue-to-draft-PR run and a fresh-session memory reuse run pass end to end.

## 21. Implementation sequence

1. Add memory scope migration and scoped API/MCP contracts.
2. Add scoped retrieval, contradiction, event, graph summary, and MnemTree scope rendering.
3. Create and verify the demonstration repository and three issues.
4. Build the runner image and structured workspace broker with security tests.
5. Add GitHub push/draft-PR approval transaction.
6. Configure the locked-down OpenClaw `judge-coder` agent and event adapter.
7. Add judge session authentication, CSRF, limits, usage ledger, and circuit breaker.
8. Recompose the UI: landing, agent workbench, Memory Lens, activity rail, responsive tabs.
9. Wire SSE, prepared scenarios, approval UX, replay mode, and memory animations.
10. Add spot interruption backup and workspace cleanup.
11. Run complete security, scale, failure, browser, and end-to-end verification.
12. Update README, diagrams, proof, video script, and submission checklist.
13. Deploy the verified commit, create one real draft PR, record the video, insert final URLs, and tag the submission release.

This sequence is strict because every later layer depends on the security and scope contracts established earlier.
