# MnemOS — Memory That Earns Its Place

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-150%20passing-brightgreen.svg)](tests/)
[![Track](https://img.shields.io/badge/hackathon-MemoryAgent-gold.svg)](#track-1-memoryagent)

**Persistent memory for AI agents** — salience-gated ingestion, UCB retrieval, closed-loop feedback, and mathematical forgetting. Built for the **Qwen Global AI Hackathon — Track 1: MemoryAgent**.

> RAG-style memory stores everything and retrieves by similarity. MnemOS **rejects garbage at ingestion**, **learns which memories help** through feedback, and **forgets stale facts** on a schedule. One SQLite brain per deployment; multiple agents share it via `user_id`.

**Repository:** https://github.com/crankysmh47/MnemAgent

---

## Quick start

**Prerequisites:** Docker, Node 18+, Python 3.11+ (WSL on Windows recommended).

```bash
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
cp config/env.template .env   # add QWEN_API_KEY
bash scripts/setup.sh
```

Daily startup after first run:

```bash
bash scripts/dev.sh
```

| What | Command / URL |
|------|----------------|
| Memory visualizer | http://localhost:3000?user=demo-brain |
| MnemOS API health | http://localhost:8000/health |
| MCP server health | http://localhost:8001/health |
| OpenClaw dashboard | `openclaw dashboard` |
| Verify MCP tools | `openclaw mcp probe mnemos` |
| Terminal proof | `pwsh scripts/prove-memory.ps1` |

**Windows:** use WSL for `setup.sh` / `dev.sh`, or `.\scripts\launch.ps1` in PowerShell.

Copy `config/env.template` → `.env`. OpenRouter free models work out of the box; [DashScope Qwen](https://dashscope.aliyun.com/) is recommended for demos and eval.

---

## What happens on each turn

```
User message
    │
    ▼
┌─ WAKING (sync) ─────────────────────────────────────┐
│  Retrieve beliefs (vector KNN or keyword + UCB)       │
│  Inject top facts into Qwen system prompt             │
│  Call Qwen → user sees reply (memory tags stripped)   │
└───────────────────────────┬───────────────────────────┘
                            ▼
┌─ DREAMING (async) ────────────────────────────────────┐
│  Utility feedback on injected beliefs (Q_i)           │
│  Parse <memory_update> → salience gate → store/prune  │
│  Enrich per-user entity dictionary                    │
│  Decay inactive nodes · episodic log · OSS backup     │
└───────────────────────────────────────────────────────┘
```

**Store rule:** `conviction ≥ 0.4` OR `category == system_state`.  
**Retrieval:** `Score = Q_i + c × √(ln(T) / (N_i + 1))` — explores dormant memories over time.

---

## Architecture

```
WhatsApp / Telegram / Discord / WebChat
              │
              ▼
     OpenClaw Gateway (:18789)
       agent + mnemos MCP (7 tools)
              │
              ▼
     MCP Server (:8001)  ──HTTP──►  MnemOS API (:8000)
              │                         │
              │              ┌──────────┴──────────┐
              │              ▼                     ▼
              │         Waking phase         Dreaming phase
              │              │                     │
              │              └──────────┬──────────┘
              │                         ▼
              │              SQLite + sqlite-vec
              │                         │
              ▼                         ▼
     Visualizer (:3000)          Alibaba OSS (optional backup)
```

Full design: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## Repository layout

```
MnemAgent/
├── mcp-memory-server/   Python FastAPI — memory engine (port 8000)
├── mcp-server/          Node MCP adapter — 7 tools for OpenClaw (8001)
├── openclaw-harness/    D3 visualizer + API proxy (3000)
├── config/workspace/    OpenClaw agent rules (AGENTS.md, skills)
├── scripts/             setup.sh, dev.sh, prove-memory.ps1
├── eval/                Benchmarks (MnemOS vs baseline)
├── tests/               pytest suite
├── docs/                SETUP, ARCHITECTURE, eval results
└── REPORT.md            Hackathon evaluation summary
```

---

## Services

| Service | Port | Role |
|---------|------|------|
| `mnemos-memory` | 8000 | Beliefs, chat, retrieval, dreaming |
| `mnemos-mcp` | 8001 | MCP tool surface for agents |
| `openclaw-harness` | 3000 | Live brain graph + event stream |

```bash
docker compose up -d --build
```

---

## MCP tools

| Tool | Purpose |
|------|---------|
| `memory_resolve_user` | Bind channel sender → canonical `user_id` |
| `memory_bind_user` | Explicit user binding |
| `memory_store` | Salience-gated fact ingestion |
| `memory_search` | Keyword search over beliefs |
| `memory_dump` | Full brain state (`/memory`) |
| `memory_stats` | UCB optimization table |
| `memory_chat` | Full memory-augmented chat route |

Agent instructions live in [config/workspace/AGENTS.md](config/workspace/AGENTS.md).

**Shared memory across agents:** point every agent at the same `MNEMOS_URL` and resolve the same `user_id` — one semantic graph, multiple channels.

---

## Configuration modes

| Mode | LLM | Memory DB | Embeddings |
|------|-----|-----------|------------|
| **Local dev** | OpenRouter free (default in `env.template`) | SQLite in Docker volume | Local `all-MiniLM-L6-v2` |
| **Demo / eval** | DashScope Qwen (`QWEN_BASE_URL` + API key) | Same | Same |
| **Cloud backup** | — | OSS snapshot every 50 turns | — |

OSS sync: [mcp-memory-server/src/storage/cloud_sync.py](mcp-memory-server/src/storage/cloud_sync.py) — uploads `memory_state.db` to Alibaba Cloud OSS (optional; requires OSS credentials in `.env`).

---

## Evaluation

**Entry point:** `python -m eval.run_benchmark` (25 scenarios, MnemOS vs baseline).

```bash
# Offline dry-run (instant)
python -m eval.run_benchmark --dry-run --mode both

# Live (MnemOS :8000 + API key)
python -m eval.run_benchmark --mode both

# Optional long-running stress benchmark
python -m eval.mnembench --dry-run --mode both
```

Deprecated: `eval.run_agentic_benchmark`, `eval.run_eval_v2` — use `run_benchmark` instead.

See [REPORT.md](REPORT.md) and [docs/LIVE_EVAL_RESULTS.md](docs/LIVE_EVAL_RESULTS.md) for scores. Headline agentic result: **86.5% vs 64.6%** baseline (+21.9 pp); project continuity **79% vs 8%**.

---

## Tests

```bash
pytest tests/ -v
pwsh scripts/integration-test.ps1
pwsh scripts/submission-test.ps1
node openclaw-harness/scripts/check-visualizer.mjs
```

---

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/SETUP.md](docs/SETUP.md) | Prerequisites, models, channels, troubleshooting |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Waking/dreaming, schema, data flow |
| [REPORT.md](REPORT.md) | Benchmark results and design rationale |

---

## Track 1: MemoryAgent

MnemOS targets **efficient storage and retrieval**, **timely forgetting**, and **critical recall within limited context**:

- **Salience auction** — low-conviction noise never enters the graph
- **UCB retrieval** — useful memories rise; dormant ones resurface mathematically
- **Contradiction resolution** — atomic overwrite on conflicting facts
- **Synaptic decay** — inactive nodes decay; dead nodes are pruned
- **Per-user entity dictionary** — keyword retrieval learns from stored facts

---

## Known limitations

- Influence detection uses proximity regex (fast, not embedding-based)
- `/chat` has no auth — demo/hackathon use only
- OSS backup is snapshot-based, not live multi-region sync
- OpenClaw CLI is separate for multi-channel messaging

---

## License

MIT — see [LICENSE](LICENSE). Copyright (c) 2025 MnemOS Team.

---

*Qwen Global AI Hackathon — Track 1: MemoryAgent*
