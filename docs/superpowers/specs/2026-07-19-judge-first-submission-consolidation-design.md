# Judge-first submission consolidation

Date: 2026-07-19

## Goal

Turn the current MnemAgent repository and Devpost draft into a concise, credible
Track 1 submission. A judge should understand the problem, inspect the
architecture, test persistent memory, watch that memory guide an agentic coding
run, and verify the Alibaba Cloud deployment without searching through internal
project history.

The public demonstration remains deliberately bounded. It proves the complete
agent loop without exposing provider or GitHub credentials, permitting arbitrary
shell execution, or allowing unreviewed publication.

## Product narrative

MnemAgent is a persistent memory control plane for OpenClaw agents. It retrieves
a small number of useful beliefs, resolves newer facts against stale ones inside
the correct scope, lets low-value memories decay, and exposes every lifecycle
event for inspection.

Three proof surfaces make the underlying system legible:

- **MnemTree** visualizes what the agent remembers, how memories relate, and
  which beliefs are fading.
- **MnemBench** measures recall, forgetting, interference resistance, and
  usefulness under a bounded context window.
- **MnemCode** demonstrates consequence: an OpenClaw agent recalls user and
  repository guidance, fixes a real issue inside a restricted workspace, runs
  tests, and waits for human approval before opening a draft pull request.

MnemBench and MnemCode are optional proof surfaces, not runtime dependencies.
Users may connect the MnemAgent MCP servers to an ordinary OpenClaw deployment
and retain its wider tool and integration ecosystem. MnemCode's current bounded
WebPort workflow is live; broader one-click repository and task packs remain
future work.

## Judge journey

1. The submitted HTTPS URL opens on the populated, read-only `demo-brain`
   MnemTree.
2. The judge searches and inspects a memory relationship chain without signing
   in.
3. The supplied judge code creates a private namespace with 30 chat turns, five
   coding runs, and five draft-PR approvals.
4. The judge states a durable repository convention and verifies it in a fresh
   OpenClaw session.
5. The tree switches to the private namespace and visualizes the new memory.
6. The judge starts the prepared WebPort issue. The interface exposes ordered
   issue, retrieval, edit, diff, and test evidence.
7. The judge reviews the exact diff and may explicitly approve a draft PR.
8. If live model capacity or the spot instance is unavailable, the populated
   tree, validated PR, and clearly labelled evidence remain available.

## Seven-day session contract

The signed judge cookie and server-side allowance both expire seven days after
admission. Quota state must survive application restarts so a spot recovery or
routine redeploy does not silently refresh or invalidate a judge's allowance.

The server persists only non-secret session identifiers, namespaces, expiry
timestamps, remaining quotas, and in-flight counters. Writes use an atomic
temporary-file replacement inside a dedicated Docker volume. Expired entries
are discarded on load. The signed, HttpOnly, SameSite cookie remains the source
of identity; CSRF and same-origin checks remain unchanged.

The total sponsored allowance stays bounded. Extending elapsed time does not
increase chat, coding, publication, or provider-token quotas.

## Repository information architecture

The root README is the judge landing page and follows this order:

1. one-sentence value proposition and submission links;
2. populated product screenshot;
3. three-to-five-minute judge path;
4. architecture diagram and technical differentiators;
5. MnemTree, MnemBench, and MnemCode proof;
6. verified results with limitations beside the claims;
7. Alibaba Cloud proof;
8. local reproduction and security boundary;
9. future scope and license.

The `docs` index links only current, evidence-bearing documents:

- `JUDGE_GUIDE.md`
- `ARCHITECTURE.md`
- `CLOUD_PROOF.md`
- `BENCHMARKS.md`
- `MNEMCODE_DEMO.md`
- `DEPLOY_ALIBABA.md`
- `SECURITY.md`
- `SUBMISSION_CHECKLIST.md`

Historical reports that directly substantiate benchmark claims move under an
evidence/archive area. Superseded setup notes, reviews, submission drafts,
duplicate screenshots, unused logo exports, and obsolete internal plans may be
removed from the branch. Git history remains the archival record.

## Alibaba and Qwen proof

Eligibility evidence has two explicit parts:

1. A stable repository code link visibly contains the accepted Qwen Cloud
   compatible-mode endpoint and shows how MnemAgent configures it without a
   secret.
2. `docs/CLOUD_PROOF.md` contains the public URL, sanitized instance facts,
   deployed commit, service topology, verification commands/results, and the
   Alibaba Cloud Workbench screenshot required by Devpost.

The documentation must distinguish the Qwen Cloud integration and evaluation
path from the sponsored public judge runtime, which currently uses DeepSeek V4
Flash. No claim may imply that a DeepSeek-backed run was a Qwen-backed run.

## Devpost draft

The existing project remains a draft and its video field remains untouched.
The description will be rewritten around the current Postgres/pgvector,
OpenClaw, MCP, MnemTree, MnemBench, and MnemCode implementation. It will identify
Track 1, link the live demo, repository, architecture, cloud proof, and validated
PR, and map evidence to the four published judging categories.

Custom submission fields that the connector cannot safely infer—personal
eligibility answers, dates, and the Workbench upload—remain owner actions and
will be listed explicitly rather than fabricated.

## Verification

Completion requires:

- Python, harness, broker, and runner test suites pass;
- seven-day expiry and durable allowance behavior have focused tests;
- visualizer contract and browser smoke checks pass;
- Compose cloud configuration validates;
- public HTTPS health and landing page pass;
- documentation links and local file references resolve;
- no secrets or generated files are tracked;
- the branch is pushed with the configured repository owner as commit author;
- the Devpost project is updated but not submitted.

