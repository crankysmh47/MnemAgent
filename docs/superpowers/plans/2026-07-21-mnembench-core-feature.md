# MnemBench Core Feature Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish MnemBench as a core MnemAgent feature, document its v1-to-v2 evolution, remove obsolete repository language, and ship the pending judge activity-persistence fix.

**Architecture:** Add one canonical product narrative that links to existing numerical evidence instead of copying it. Update the two navigation entry points and the recording checklist, then validate the already-written activity restoration changes independently before committing and pushing the branch.

**Tech Stack:** Markdown, Node.js built-in test runner, Express, browser ES modules, Git.

## Global Constraints

- MnemBench v1 is the public `crankysmh47/MnemBench` repository.
- MnemBench v2 currently lives under this repository's `eval/` directory; do not claim a separate v2 repository exists.
- DeepSeek judge evidence and Alibaba Qwen evidence remain explicitly separated.
- Numerical claims link to `docs/BENCHMARKS.md` and `docs/evidence/MNEMBENCH_V2_RESULTS.md`.
- MnemBench and MnemCode remain optional proof surfaces around the reusable MnemAgent MCP memory layer.
- No paid model calls are used during verification.

---

### Task 1: Canonical MnemBench narrative

**Files:**
- Create: `docs/MNEMBENCH.md`

**Interfaces:**
- Consumes: existing evidence in `docs/BENCHMARKS.md`, `docs/evidence/MNEMBENCH_V2_RESULTS.md`, `docs/ARCHITECTURE.md`, and `eval/`.
- Produces: the canonical link target for the README navigation updates in Task 2.

- [ ] **Step 1: Write the MnemBench product document**

Create a document with these exact sections: `What MnemBench proves`, `How it evolved`, `Version boundary`, `What v2 evaluates`, `How the four surfaces fit together`, `Evidence and reproduction`, `Current limitations`, and `Direction after the hackathon`.

The evolution section must state that v1 began as a compact portable recall benchmark and v2 expanded evaluation to scoped, cross-session lifecycle behavior. The limitations section must distinguish stable Postgres smoke results from live provider runs and state that gains vary by scenario.

- [ ] **Step 2: Verify every relative link**

Run a PowerShell Markdown-link check over `docs/MNEMBENCH.md` and confirm every repository-relative target exists. Expected result: `broken_links=0`.

- [ ] **Step 3: Review claims against evidence**

Compare the new document with `docs/BENCHMARKS.md` and `docs/evidence/MNEMBENCH_V2_RESULTS.md`. Expected result: no new score, date, provider, or repository claim lacking an existing evidence source.

### Task 2: Judge-facing navigation and terminology

**Files:**
- Modify: `README.md`
- Modify: `docs/README.md`
- Modify: `docs/DEMO_VIDEO_PRODUCTION_SCRIPT.md`

**Interfaces:**
- Consumes: `docs/MNEMBENCH.md` from Task 1.
- Produces: an above-the-fold four-surface product model and direct navigation to the benchmark evolution.

- [ ] **Step 1: Promote the four product surfaces in the root README**

Add a compact table near the judge evidence block defining MnemAgent, MnemTree, MnemBench, and MnemCode. Link the MnemBench row to `docs/MNEMBENCH.md`. Keep setup commands and existing measured evidence unchanged.

- [ ] **Step 2: Reorder documentation navigation**

Place `MNEMBENCH.md` before `BENCHMARKS.md` in `docs/README.md`, labeling the first as product evolution and evaluation design and the second as measured runs and limitations.

- [ ] **Step 3: Remove obsolete terminology**

Replace the final legacy-repository sentence in `docs/DEMO_VIDEO_PRODUCTION_SCRIPT.md` with: `Confirm the populated tree appears, issue #1 opens publicly, chat responds, and the visible interface names MnemBench as the prepared coding task.`

- [ ] **Step 4: Verify terminology and links**

Search the tracked product and documentation files for the retired repository name. Expected result: no matches. Run the repository-relative Markdown-link checker across the three modified navigation documents. Expected result: `broken_links=0`.

### Task 3: Judge activity persistence verification

**Files:**
- Modify: `openclaw-harness/src/index.js`
- Modify: `openclaw-harness/src/judge-run-service.js`
- Modify: `openclaw-harness/src/public/scripts/judge-console.js`
- Modify: `openclaw-harness/test/judge-run-service.test.mjs`

**Interfaces:**
- Produces: `judgeRuns.latest(ownerSessionId)` returning the most recently created owned run or `null`; `/api/judge/session` returning `latestRun` with events and evidence; browser-local restoration keyed by judge namespace.

- [ ] **Step 1: Inspect the existing pending diff**

Confirm the diff contains only latest-run restoration, browser-local activity persistence, approval-state persistence, the broader repository-memory retrieval query, and the focused service assertion.

- [ ] **Step 2: Run focused tests**

Run `node --test test/judge-console.test.mjs test/judge-run-service.test.mjs` from `openclaw-harness`. Expected result: 8 tests, 0 failures.

- [ ] **Step 3: Run the complete harness test suite**

Run `npm test --prefix openclaw-harness` from the repository root. Expected result: all tests pass with no paid model calls.

- [ ] **Step 4: Check source formatting**

Run `git diff --check`. Expected result: no whitespace errors.

### Task 4: Final documentation audit and publication

**Files:**
- Review all files changed by Tasks 1-3.

**Interfaces:**
- Consumes: all prior task deliverables.
- Produces: one reviewed implementation commit pushed to `origin/MnemCode`.

- [ ] **Step 1: Human-language review**

Review the new prose for inflated claims, repetitive conclusions, vague attribution, excessive headings, and em-dash overuse. Rewrite any sentence that reads like promotional copy rather than technical documentation.

- [ ] **Step 2: Inspect final scope**

Run `git status --short` and `git diff --stat`. Expected files are the four judge-persistence files, their focused test, the new MnemBench document, and the three navigation/recording documents. No credential, generated output, dependency, or benchmark-result file may be present.

- [ ] **Step 3: Commit under the configured repository owner identity**

Verify `git config user.name` is `crankysmh47` and `git config user.email` is `annankhan741@gmail.com`. Stage only the expected files and commit with `docs: establish MnemBench as a core feature`.

- [ ] **Step 4: Push and verify**

Run `git push origin MnemCode`, then compare local `HEAD` with `git ls-remote origin refs/heads/MnemCode`. Expected result: identical commit hashes.
