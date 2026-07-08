# MnemAgent Architecture

> Memory that earns its place. — Qwen Global AI Hackathon, Track 1: MemoryAgent

## The Core Problem

Standard RAG-based memory agents have two fatal flaws:

1. **Proactive Interference** — stale facts sit alongside current ones in the same flat store and get injected indiscriminately. The agent confidently recalls outdated information.
2. **Naive Storage** — everything gets stored, garbage included, and pruning happens after the fact. The graph bloats with low-conviction throwaway remarks.

MnemAgent solves both at the architectural level, not as patches.

## The Two-Phase Engine

```
                    ┌─────────────────────────────┐
  User Message ───▶ │      WAKING PHASE            │
                    │  (synchronous, hot path)      │
                    │  • Embed query                │
                    │  • UCB-scored retrieval        │
                    │  • RWR associative hops        │
                    │  • Assemble Qwen payload       │
                    │  • Return response to user     │
                    └─────────────┬───────────────┘
                                  │ response returned
                                  ▼
                    ┌─────────────────────────────┐
                    │      DREAMING PHASE           │
                    │  (asynchronous, background)   │
                    │  • Extract <memory_update>    │
                    │  • Salience auction gate      │
                    │  • Contradiction resolution   │
                    │  • Utility feedback (Q_i)     │
                    │  • Synaptic decay             │
                    │  • Hard prune dead nodes      │
                    │  • Cloud sync (every 50 turns)│
                    └─────────────────────────────┘
```

## The Four Pillars

### Pillar 1 — Salience Auction (Ingestion Gate)

Before any fact is written to the semantic graph, it is scored on three axes:

| Axis | What it measures | How |
|------|-----------------|-----|
| **Novelty** | Does this extend or contradict existing knowledge? | Query semantic_graph for existing (user_id, entity, relation) triple |
| **Utility** | Would knowing this change future responses? | Category: system_state > preference > persona |
| **Conviction** | Was this stated with certainty or casually? | Extracted from Qwen's `<memory_update>` JSON (0.0–1.0) |

**Storage rule:** `Store if: conviction >= 0.4 OR category == 'system_state'`

What gets rejected: "Maybe we'll try Tailwind sometime" (conviction ~0.2), "I'm thinking perhaps TypeScript?" (~0.15), "Let's try Vue eventually" (~0.25).

### Pillar 2 — Dual-Output Chain-of-Thought Extraction

The system prompt forces Qwen to emit structured `<memory_update>` XML before its conversational response:

```xml
<memory_update>{"entity":"backend_framework","relation":"prefers","value":"express","category":"system_state","conviction":0.95}</memory_update>
Understood. We'll use Express for the backend.
```

The interceptor strips the XML block before the user sees it, then passes the extracted JSON to the Dreaming phase asynchronously. **Zero additional LLM calls** — both the response and the extracted facts come from a single API call.

### Pillar 3 — UCB Retrieval (Upper Confidence Bound)

Memory retrieval is treated as a Multi-Armed Bandit problem:

```
Score_i = Q_i + c × √(ln(T) / (N_i + 1))
```

| Variable | Meaning |
|----------|---------|
| Q_i | base_utility_q — learned usefulness from feedback loop |
| T | total episodic turns for this user (always ≥ 1) |
| N_i | injection_count — how many times this belief has been retrieved |
| c | 0.3 — exploration constant |

This guarantees exploration: given enough turns, every non-pruned memory will eventually be retrieved. The math forces dormant memories to surface regardless of semantic similarity to the current query.

**Retrieval pipeline:** Embed → KNN top 20 → UCB score → take top 4 → RWR associative hop → cap at 6 total facts.

### Pillar 4 — Closed-Loop Feedback

After Qwen responds, the system checks whether each injected memory actually influenced the response using proximity regex (both entity terms within 100 characters of each other):

```
If belief shaped the response:  Q_i = min(1.0, Q_i + 0.05), influence_count++
If belief was injected but ignored: Q_i = max(0.0, Q_i - 0.01)
Always: injection_count++
```

The asymmetry (+0.05 reward vs -0.01 penalty) prevents the system from penalizing exploratory UCB retrievals too aggressively.

## The Memory Stores

| Tier | Store | Scope | Purpose |
|------|-------|-------|---------|
| 1 | Working Memory | In-process, last 3 turns | Short-term conversational context |
| 2 | Episodic Memory | episodic_logs table, session-scoped | Source material for consolidation, UCB T calculation |
| 3 | Semantic Memory | semantic_graph table, global per user | Long-term beliefs — what gets injected into prompts |
| 4 | Vector Index | vec_memory virtual table (sqlite-vec) | SIMD-accelerated KNN semantic search |
| 5 | Event Log | memory_events table | Lifecycle events for the visualizer |

## The Forgetting System

**Synaptic Downscaling:** Every dreaming cycle, nodes inactive > 45 minutes are decayed × 0.85. After ~8 hours of inactivity, a node crosses the prune threshold.

**Hard Pruning:** `DELETE FROM semantic_graph WHERE node_weight < 0.1` — irreversible. Prevents infinite graph bloat.

## Contradiction Resolution

The `UNIQUE(user_id, entity_source, relation) ON CONFLICT REPLACE` constraint handles atomic overwrites. When a new fact conflicts with an existing one, the database replaces the old row in a single SQL operation. No race conditions possible.

## Data Flow (Turn by Turn)

```
User sends message
  → main.py ChatRequest
  → /memory command? → execute command, return
  → get_total_turns(user_id) → T (≥1)
  → build_optimized_qwen_payload()
    → get_embedding(user_input) → float[384]
    → KNN on vec_memory → top 20 candidates
    → UCB score each → sort → top 4
    → RWR/single-entity hop → 1-2 more
    → Deduplicate → max 6 facts
    → UPDATE last_accessed, boost node_weight
    → Fetch last 3 episodic turns
    → Assemble system prompt + messages array
  → call_qwen_api(payload)
  → strip_memory_tags(raw) → clean_response to user
  → asyncio.create_task(_run_dreaming_phase(...))
    → evaluate_memory_utility_feedback()
    → consolidate_and_prune_memory() [if memory_dict]
    → log_episodic_turn()
    → cloud_sync.sync_to_cloud() [every 50 turns]
```

## Key Design Decisions

- **SQLite, not a vector database** — zero infrastructure, single-file state, WAL mode for concurrent reads
- **T is per-user, not global** — prevents new users from inheriting inflated UCB exploration from power users
- **Asymmetric feedback** — rewards (+0.05) > penalties (-0.01) so exploration isn't punished
- **Proximity regex, not substring** — "Python" in snake context doesn't credit programming preference
- **Max 6 injected facts** — O(1) token overhead regardless of graph size
- **Reject at ingestion, not decay later** — garbage never touches the graph

## System Prompt Template

The agent receives memory context injected into a structured system prompt:

```
[MEMORY CONTEXT — Retrieved from long-term storage]
- backend_framework prefers express (Q: 0.95, confidence: HIGH)
- code_style prefers minimal-comments (Q: 0.72, confidence: CONFIDENT)
- deadline is march-15 (Q: 0.60, confidence: FADING)
```

And is instructed to output new persistent facts inside `<memory_update>` tags with conviction scoring before its visible response.

## API Surface

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Service health |
| `/chat` | POST | Memory-augmented chat |
| `/api/memory/store` | POST | Direct fact storage (salience-gated) |
| `/api/memory/search/{uid}` | GET | Search beliefs by keyword |
| `/api/memory/dump/{uid}` | GET | Full brain state |
| `/api/memory/stats/{uid}` | GET | UCB optimization table |
| `/api/graph/{uid}` | GET | Visualizer graph data (beliefs + edges) |
| `/api/events/{uid}` | GET | Lifecycle event stream |
| `/api/metrics/{uid}` | GET | Aggregate metrics + UCB timeline |
| `/api/user/bind` | POST | Channel → user_id binding |
## Cue-Triggered Prospective Memory

MnemAgent supports a small form of human-like prospective memory: intentions that fire when a cue appears, not after a wall-clock timer expires.

Example:

```text
When I ask about deployment, remind me to check the OSS snapshot.
```

The deterministic extractor stores:

```json
{"entity":"when_asked_about_deployment","relation":"remind","value":"check the OSS snapshot","category":"system_state","conviction":1.0}
```

During the waking phase, MnemAgent scans the user's current prompt for due cues and injects a separate prospective reminder block:

```text
[DUE PROSPECTIVE REMINDERS]
- When the user asks about deployment: remind them to check the OSS snapshot
```

This avoids timed reminders. OpenClaw does not need to track wall-clock time, there is no scheduler overhead, and the feature still tests a memory capability most agent benchmarks ignore: remembering to do the right thing when the relevant context returns.

## Cloud Multi-User Posture

Local development keeps SQLite because it is cheap and deterministic. Alibaba Cloud deployments can use the bundled Postgres/pgvector schema through the `postgres` compose profile or Alibaba RDS.

Security controls for cloud mode:

- optional `MNEMAGENT_API_TOKEN` bearer auth on chat, memory, graph, metrics, and binding endpoints;
- token forwarding from the OpenClaw MCP server and visualizer harness;
- Postgres schema with row-level security policies keyed by `mnemagent.user_id`;
- prompt-injection memory firewall that rejects extracted writes from obvious memory-rule override attempts.
