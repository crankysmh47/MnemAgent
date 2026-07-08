# MnemOS Submission Video Plan

Target length: 2:45 to 3:15.

Goal: convince judges that MnemOS is a real OpenClaw agent with persistent,
selective, inspectable memory running on Alibaba Cloud with Qwen-compatible
inference.

## Core Narrative

Most agents either forget between sessions or store too much. MnemOS gives
OpenClaw a memory layer that:

- stores only high-salience facts;
- recalls user preferences across new chats;
- overwrites stale facts instead of injecting contradictions;
- keeps prompt memory bounded;
- exposes the live belief graph visually.

## Recording Setup

Before recording on cloud:

```powershell
pwsh ./scripts/reset-cloud-memory.ps1
pwsh ./scripts/deploy-preflight.ps1
```

Record two separate videos if the submission form allows it:

- **Main demo, about 3 minutes:** product value, memory behavior, visualizer,
  and benchmark evidence.
- **Cloud proof, 30-60 seconds:** Alibaba Cloud ECS console, SSH terminal,
  Docker service health, and public ECS URL.

The exact cloud-proof checklist lives in `docs/CLOUD_PROOF.md`.

Open these tabs:

- OpenClaw chat: `http://<ecs-ip>:18789`
- Judge visualizer: `http://<ecs-ip>:3000?user=<judge-id>`
- Demo visualizer: `http://<ecs-ip>:3000?user=demo-brain`
- Repository README or `docs/REPORT.md`

Use the judge user id printed by `reset-cloud-memory.ps1`. Keep `demo-brain`
only for the rich graph beauty shot.

## Shot List

### 0:00-0:12 — Hook

Visual: OpenClaw chat in a fresh session.

Voiceover:

> Standard AI agents have a memory problem. They either forget between chats,
> or they remember everything, including stale and low-confidence noise.

Caption:

```text
Problem: agents forget, over-store, and recall stale facts.
```

### 0:12-0:30 — What MnemOS Is

Visual: `demo-brain` visualizer with the biological graph visible.

Voiceover:

> MnemOS is a persistent memory layer for OpenClaw. It decides what deserves
> storage, retrieves only useful beliefs, updates contradictions, and lets old
> memories fade.

Caption:

```text
Salience-gated memory + UCB retrieval + controlled forgetting
```

### 0:30-1:15 — Cross-Session Recall

Visual: OpenClaw chat.

Prompt 1:

```text
Call tool mnemos__memory_store three times for user_id <judge-id>:
1. {"user_id":"<judge-id>","entity":"project","relation":"codename","value":"CloudProof42","category":"preference","conviction":1.0}
2. {"user_id":"<judge-id>","entity":"backend","relation":"framework","value":"FastAPI","category":"preference","conviction":1.0}
3. {"user_id":"<judge-id>","entity":"database","relation":"type","value":"PostgreSQL","category":"preference","conviction":1.0}
Then reply in one short sentence.
```

Open a new chat/session.

Prompt 2:

```text
Use mnemos__memory_dump with user_id <judge-id>, then answer in one natural sentence:
what is my project codename, backend framework, and database? Do not print JSON.
```

Expected answer:

```text
Your project codename is CloudProof42, the backend framework is FastAPI,
and the database is PostgreSQL.
```

Voiceover:

> This is a new chat. The model is not relying on chat history. OpenClaw is
> calling MnemOS through MCP, and MnemOS is retrieving persistent user memory.

Caption:

```text
New chat. Same user. Memory persists.
```

### 1:15-1:45 — Live Memory Graph

Visual: judge visualizer at `http://<ecs-ip>:3000?user=<judge-id>`.

Actions:

- refresh after the teach step;
- show the three new belief nodes;
- hover one node;
- zoom in and out once;
- drag one node slightly;
- briefly show `demo-brain` for the richer connected graph.

Voiceover:

> The visualizer is not a second chat UI. It exposes the memory graph: beliefs,
> confidence, categories, recall count, and connections.

Caption:

```text
Beliefs are visible, inspectable, and user-scoped.
```

### 1:45-2:15 — Contradiction Handling

Visual: OpenClaw chat.

Prompt:

```text
Call tool mnemos__memory_store with exactly these arguments:
{"user_id":"<judge-id>","entity":"backend","relation":"framework","value":"Hono","category":"preference","conviction":1.0}
Then call mnemos__memory_dump with user_id <judge-id> and summarize the current backend framework in one sentence.
```

Expected answer:

```text
The current backend framework is Hono.
```

Optional proof shot: event API or graph tooltip showing contradiction metadata.

Voiceover:

> Flat memory often keeps old and new values side by side. MnemOS keys beliefs
> by user, entity, and relation, so the current backend framework replaces the
> stale one.

Caption:

```text
Contradiction resolved: FastAPI -> Hono
```

### 2:15-2:35 — Salience Gate

Visual: OpenClaw chat.

Prompt:

```text
Call mnemos__memory_store with exactly these arguments:
{"user_id":"<judge-id>","entity":"frontend_experiment","relation":"maybe_uses","value":"Svelte","category":"preference","conviction":0.2}
Then tell me whether it was stored or rejected.
```

Expected answer:

```text
The memory store operation was rejected.
```

Voiceover:

> MnemOS rejects low-conviction noise at ingestion. Garbage does not enter the
> graph and does not wait around to be pruned later.

Caption:

```text
Low-conviction memory rejected before graph write.
```

### 2:35-2:55 — Evaluation Proof

Visual: `docs/REPORT.md`, `docs/LIVE_EVAL_RESULTS.md`, or latest result file.

Voiceover:

> We test this with live agentic scenarios and MnemBench, our companion suite
> for long-running memory behavior: recall, contradiction chains, salience,
> interference, user isolation, and bounded context.

Show headline numbers:

```text
Live agentic benchmark: 86.5% MnemOS vs 64.6% baseline
Project continuity: dominant cross-session advantage
MnemBench contradiction-chain sample: 89.6% probe score
```

For a clean screenshot, generate:

```powershell
python -m eval.mnembench --dry-run --scenario contradiction_chain --judge-report
```

### 2:55-3:15 — Alibaba Cloud Proof + Close

Visual: terminal or ECS console.

Show:

```powershell
pwsh ./scripts/deploy-preflight.ps1
```

If the cloud-proof video is separate, keep this shot short. Show only the final
passing preflight output and the ECS public visualizer URL.

Voiceover:

> MnemOS runs on Alibaba Cloud with Qwen-compatible inference, Docker services,
> OpenClaw MCP integration, and a judge-safe clean memory namespace.

Caption:

```text
Alibaba Cloud + Qwen + OpenClaw + MnemOS
```

## Live Test Results From Local Stack

Verified on 2026-07-05:

- MnemOS API healthy: `prompt_version=v4-dual-path-write`.
- Visualizer harness healthy with `demo-brain`: 62 beliefs, 405 edges.
- OpenClaw gateway healthy after restart.
- OpenClaw MCP probe: `mnemos` exposes 7 tools.
- Cross-session recall succeeded when the prompt explicitly called
  `mnemos__memory_dump`.
- Contradiction event succeeded with exact tool arguments:
  `backend/framework FastAPI -> Hono`.
- Low-conviction memory with `conviction=0.2` was rejected.

## Recording Notes

- Use exact `mnemos__...` tool names in the spoken/demo prompts. Vague prompts
  like "use memory" can let the model answer without calling MCP.
- For contradiction recording, specify exact `entity` and `relation`; otherwise
  the model may store a related but separate belief.
- Use `demo-brain` for the rich visual shot and the judge id for the clean live
  user proof.
- Cut waiting time during model responses. Keep the model's successful final
  sentence visible.
