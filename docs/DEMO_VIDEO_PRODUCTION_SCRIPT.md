# Three-minute, one-take demo script

This version needs only a normal screen recorder. Record the entire desktop once, then accelerate the two waiting sections. Do not splice together separate demonstrations or present fixture output as live output.

## Before recording

### 1. Start the local judge stack

Use PowerShell in the repository root:

```powershell
git switch MnemCode
gh auth status
.\scripts\start-demo.ps1
```

`start-demo.ps1` obtains `JUDGE_GITHUB_TOKEN` from `gh auth token` for the current process. It never prints the token or writes it into `.env`. The GitHub credential must have access only to `crankysmh47/MnemBench` and permission to read issues, write branches, and open pull requests.

Open:

```text
http://localhost:3000/?user=demo-brain
```

The local judge code is:

```text
mnemcode-local-judge
```

Use this code only in the local recording. Never show the cloud judge code, `.env`, GitHub authentication screen, token, model key, Alibaba key, or terminal history containing secrets.

### 2. Confirm readiness

Run these before the take:

```powershell
Invoke-RestMethod http://localhost:3000/health
docker compose ps
```

Expected health status: `ok`. Confirm the populated tree appears, issue #1 opens publicly, chat responds, and the visible interface names MnemBench as the prepared coding task.

### 3. Prepare one browser window

Use 100% browser zoom and hide bookmarks. Open these tabs in this exact order:

1. MnemAgent GitHub README on the `MnemCode` branch.
2. Local product: `http://localhost:3000/?user=demo-brain`.
3. Public [MnemBench issue #1](https://github.com/crankysmh47/MnemBench/issues/1), with [draft PR #2](https://github.com/crankysmh47/MnemBench/pull/2) ready in a neighboring tab as fallback evidence.
4. [`docs/CLOUD_PROOF.md`](CLOUD_PROOF.md) rendered on GitHub.
5. [`docs/BENCHMARKS.md`](BENCHMARKS.md) rendered on GitHub.

Keep the local product on the populated tree. Collapse unrelated browser sidebars. Make the pointer easy to see but do not add animated cursor effects.

### 4. Prepare the live interaction

Use a fresh local judge session. Do not pre-populate the private conversation. During the take you will type these exact messages:

```text
For MnemBench, keep every metric oriented so 1.0 means best behavior.
```

```text
What scoring convention should you follow for MnemBench?
```

Leave the MnemCode direction box empty. Its prepared prompt already asks the agent to solve issue #1 test-first.

## Recording and acceleration rule

Record continuously from beginning to end. During each model wait:

1. Finish the sentence shown below.
2. Move the pointer to an empty corner.
3. Stay silent until the result appears.
4. Continue immediately.

After recording, accelerate only those silent ranges to approximately 8×. Keep one second at normal speed before and after each accelerated range so the transition is understandable. Do not accelerate narration, typing, diffs, test results, or approval controls.

Target edited duration: `2:50–2:58`. If the take exceeds three minutes, shorten pauses first; do not remove the security boundary or deployment proof.

## The one-take script

### 0:00–0:18 — Name the problem and product

**Screen:** GitHub README, positioned at the title, populated-tree image, and “Judge start here” table.

**Action:** Start recording. Move the pointer once across the Live product, Alibaba proof, Architecture, and MnemBench issue rows without opening them.

**Say:**

> Agents lose useful context between sessions, and indiscriminate memory only replaces forgetting with noise. MnemAgent is a persistent memory control plane for OpenClaw. It stores durable beliefs, replaces stale ones, forgets low-value memories, retrieves at most six relevant facts, and exposes the evidence instead of hiding it.

### 0:18–0:38 — Show the living memory model

**Screen:** Switch to the local product tab.

**Action:** Let the loading leaf complete one full turn. Search `backend framework`. Hover the matching leaf, click it, and let the relationship chain settle. Do not pan the tree.

**Say:**

> Judges first land on this populated MnemTree, so the core idea is visible without credentials or model spend. Search reaches beyond the first graph page. A leaf is one memory; its branches expose relationships, lifecycle, confidence, and recall. Large archives switch to hybrid and summary-first rendering instead of drawing thousands of nodes at once.

### 0:38–1:20 — Prove cross-session memory

**Action:** Open the judge workbench. Enter `mnemcode-local-judge`. Paste the first prepared message and send it.

**Say while submitting:**

> The code creates a private seven-day judge namespace. This message teaches a repository-specific rule: every MnemBench metric must use one point zero for best behavior.

**Wait:** Keep silent while the first message runs. Mark this silent range for 8× acceleration.

**Action:** When the response finishes, paste the second prepared message and send it.

**Say while submitting:**

> Every chat turn starts a fresh OpenClaw conversation. There is no shared transcript for the second question, so a correct answer must come through MnemAgent retrieval.

**Wait:** Keep silent and accelerate this range later.

**Action:** When the answer appears, point to the recalled `1.0 means best` rule and then the new tree memory.

**Say:**

> The fresh session recovered both the rule and its MnemBench scope. Core preferences and repository memories cannot overwrite one another, and only a bounded set enters context.

### 1:20–2:08 — Turn memory into agentic work

**Screen:** Briefly switch to the public issue tab.

**Action:** Point to the problem and acceptance criteria, then return to the local product. Start the MnemBench task.

**Say:**

> This is a public, real defect in MnemBench. Correct contradiction handling already scores one point zero, but aggregation inverts it and reports failure. MnemCode asks OpenClaw to inspect the issue, retrieve the rule it just learned, write a regression test first, and make the smallest fix.

**Wait:** Leave the Activity panel visible while the run works. Keep silent and accelerate only the inactive gaps, not new evidence appearing.

**Action:** Select Activity, then Memory, then Changes. Pause on the retrieved rule, the regression test, the source change, and the two green Python commands.

**Say:**

> These are ordered server events, not a simulated terminal. The Memory tab shows what guided the run. Changes shows the exact test-first patch. The runner has no network, no GitHub token, and no arbitrary shell. It can run only the focused scoring test and the full pytest suite.

### 2:08–2:28 — Show the human boundary

**Action:** Point to the disabled or available approval control. Do not open another PR if the demo already has a validated one. If publication has not been exercised before, check the review confirmation but stop before the final click unless you intentionally want a draft PR.

**Say:**

> Even a successful agent cannot publish by itself. Both fixed tests must pass, then a human reviews the exact diff. The approval expires after five minutes and is cryptographically bound to that diff and pull-request metadata. Only the private broker can use the repository-limited GitHub token.

### 2:28–2:43 — Show measured value honestly

**Screen:** Switch to the benchmark tab and position it on the headline table.

**Action:** Point to `66.7% vs 23.7%`, then `91.7% vs 8.3%` project continuity.

**Say:**

> MnemBench v2 measures the same lifecycle. The stable Postgres smoke run scored sixty-six point seven versus twenty-three point seven percent. In a separate live Qwen run, project continuity scored ninety-one point seven versus eight point three. That scenario drives most of the aggregate gain, and the weaker cases remain published.

### 2:43–2:58 — Close with cloud and architecture proof

**Screen:** Switch to the Alibaba proof tab. Keep the ECS screenshot and Qwen code-proof links visible.

**Action:** Point to the Singapore ECS instance, public URL, health response, and `mcp-memory-server/src/config.py` link.

**Say:**

> The backend runs on Alibaba Cloud ECS in Singapore. This page contains the live health check, authenticated ECS evidence, architecture, and the Qwen Model Studio endpoint in source. MnemTree shows memory, MnemBench measures it, and MnemCode proves remembered experience changes what an agent does.

Stop recording immediately after the last word.

## If something fails during the take

- If the public tree is empty, reopen `?user=demo-brain`.
- If local authentication fails, restart with `scripts/start-demo.ps1`; do not reveal `.env`.
- If a model call takes more than 45 seconds, keep recording silently and accelerate the entire wait afterward.
- If the coding run fails, show the red evidence and say: `The approval remains locked when tests fail.` Then use the public issue and previously verified evidence for the remainder.
- If the spot deployment is unavailable, record locally but still show the repository's Alibaba proof page. Say clearly that the displayed live interaction is local reproduction.
- Never claim a pull request exists until GitHub returns its public URL.

## Final upload checklist

- Edited runtime is below 3:00.
- No secret, `.env` value, access code other than the documented local code, email notification, or unrelated tab is visible.
- The populated tree, cross-session recall, public issue, retrieved repository memory, diff, test evidence, human approval boundary, benchmark results, and Alibaba proof are readable.
- Accelerated sections contain only waiting, not hidden instructions or omitted failures.
- Video is public on YouTube, Vimeo, or Facebook Video.
- Devpost contains the public video URL and the private cloud judge code.
