# Sponsored Judge Experience Design

## Goal

Give hackathon judges an authentic, low-friction agent experience: chat with an OpenClaw agent, teach it durable rules, watch a private MnemTree populate, start a fresh session, direct a bounded coding task, inspect retrieved memory and test evidence, and explicitly approve one draft pull request.

## Product decision

The hackathon build uses server-sponsored DeepSeek V4 Flash and a server-owned, repository-scoped GitHub credential. It does not accept model keys, GitHub tokens, or OpenRouter credentials from judges. BYOK and GitHub App installation are post-hackathon scope.

Each authenticated browser receives:

- an opaque one-hour judge session;
- a private `judge-<random>` memory namespace;
- 30 sponsored chat turns;
- 5 sponsored coding runs;
- 5 draft-PR publication allowances;
- a displayed reserved allowance of `$0.55`.

The allowance is a product quota, not a claim of exact provider billing. The server reserves `$0.01` per chat turn and `$0.05` per coding run. This remains enforceable even when OpenClaw reports zero provider cost.

## Judge flow

1. The public page loads `demo-brain` and a validated, zero-cost WebPort replay.
2. The judge enters the shared access code. The server issues an HttpOnly, Secure, SameSite=Strict cookie plus an in-memory CSRF token.
3. The UI switches the tree to the judge's private namespace and shows the sponsored allowance.
4. The judge chats with the agent. Every turn uses a distinct OpenClaw session ID while retaining the same memory namespace.
5. The agent stores durable preferences and repository rules through MnemAgent MCP tools. The tree refreshes after each completed turn.
6. The judge starts a fresh chat session and verifies that the agent recalls earlier rules.
7. The judge starts the prepared WebPort issue #11 coding task. The API returns `202 Accepted` immediately and the UI polls ordered events.
8. The agent retrieves repository memory, creates an isolated workspace, writes or runs the regression test, applies bounded edits, runs fixed allowlisted tests, and exposes the diff.
9. Activity, Memory, and Changes are real tabs backed by server evidence. They are never decorative.
10. The judge reviews the exact diff and passing tests, checks an explicit confirmation box, and clicks `Open draft PR`.
11. The server obtains a five-minute diff-bound approval token from the broker and opens one draft PR. It never pushes to `main` or creates a ready PR.
12. The workspace expires after completion, publication, or timeout. The judge namespace expires from the browser session but remains available for the demo window unless reset by the operator.

## Architecture

The browser talks only to the harness. The harness owns judge sessions, quotas, chat/run orchestration, polling, replay data, and the approval endpoint. OpenClaw receives the private memory namespace and run ID through a bounded operating contract. The MnemAgent MCP URL is environment-configured so cloud containers use `http://mnemos-mcp:8001/mcp`, while host development can use loopback.

The broker remains the only component with the GitHub token. The OpenClaw agent can call structured broker MCP tools but cannot access a generic shell, browser, host filesystem, credential, PR-opening endpoint, or GitHub token. Broker MCP calls post redacted event envelopes to a harness-internal callback. The harness records workspace ID, files, diff, test outputs, and safe activity labels for the owning run.

## Evidence model

Each run stores bounded in-memory evidence:

```text
run: id, ownerSessionId, namespace, status, mode, model, createdAt
activity: ordered id, sequence, type, timestamp, safe detail
memory: scope, entity, relation, value, retrievedAt
changes: workspaceId, diff, files, tests, approval state, PR URL
quota: chatTurnsRemaining, codingRunsRemaining, publicationsRemaining, reservedUsdRemaining
```

No API key, GitHub token, authorization header, raw cookie, HMAC secret, complete prompt, or unbounded tool output may enter evidence or logs.

## Replay and failure behavior

The repository includes one immutable validated replay derived from WebPort issue #11 and draft PR #13. Public users can inspect it without authentication or model spend. If a live model, MCP, broker, runner, or GitHub operation fails, the UI reports the failed stage and offers the validated replay. It never silently labels replay as live.

Chat and coding requests are asynchronous. The initial request returns immediately. Polling uses monotonic event IDs and stops on `completed`, `failed`, or `interrupted`. A coding run has a six-minute deadline. One coding run may execute globally at a time on the small ECS instance.

## Security constraints

- Judge access is rate-limited per IP and locks after five failed access-code attempts.
- All mutable judge endpoints require the signed session cookie, matching CSRF token, same-origin request, and resource ownership.
- Input schemas bound chat messages to 2,000 characters and coding direction to 4,000 characters.
- A judge cannot choose a repository, branch, workflow file, test command, base branch, PR readiness state, or GitHub identity.
- Only `crankysmh47/WebPort` and issue #11 are enabled for the hackathon build.
- Publication requires passing test evidence, a non-empty diff, an explicit confirmation, an unused publication quota, and a current diff-bound token.
- Public cloud ports are only 80/443. Memory API, MCP, Postgres, and broker remain internal or loopback-bound.
- Production startup rejects missing or default judge secrets.

## UI layout

The MnemTree remains visually dominant on the left. The right workbench contains, in order:

1. identity and sponsored allowance;
2. compact chat transcript and composer;
3. `Start fresh session` and `Run prepared coding task` actions;
4. status line;
5. functional Activity, Memory, and Changes tabs;
6. approval control inside Changes only after passing evidence.

The bottom Memory Lens remains the quiet, collapsible ribbon already implemented. It reflects the currently selected leaf and does not duplicate the workbench transcript.

## Documentation truth

`main` becomes the submission branch. The README leads with the live URL, video, five-minute judge flow, architecture, real PR evidence, benchmarks, and deployment proof. Until deployment and video URLs exist, they remain explicitly marked as owner actions rather than implied completed work. The judge guide describes only controls verified by automated and browser tests.

## Acceptance criteria

- A judge can authenticate without receiving any provider or GitHub secret.
- Thirty chat turns can populate and recall a private namespace across fresh OpenClaw sessions.
- Starting a coding run returns within one second and events become visible through polling.
- Activity, Memory, and Changes render different real evidence.
- The cloud OpenClaw container reaches both `mnemos-mcp` and `workspace-broker` by service DNS.
- A failed or exhausted run exposes an honestly labeled replay.
- One passing tested diff can become one draft PR only after explicit approval.
- Attempts to access another judge's run or namespace return a generic authorization error.
- Full Python, harness, broker, runner, cloud Compose, OpenClaw config, browser, security, secret, and commit-author checks pass before merge.
