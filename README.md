# MnemOS — Memory That Earns Its Place

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-128%20passing-brightgreen.svg)](tests/)

**Persistent memory layer for AI agents** — selective ingestion via salience auction, UCB-based retrieval, closed-loop feedback, and mathematical forgetting. Built for the **Qwen Global AI Hackathon, Track 1: MemoryAgent**.

> Standard RAG agents suffer from proactive interference (stale facts drown out current ones) and naive storage (garbage accumulates). MnemOS rejects garbage at ingestion and forces stale facts out mathematically. The retrieval system learns which memories are actually useful.

## Quick Start

```powershell
# 1. Clone and configure
git clone <repo-url>
cd MnemAgent
cp .env.example .env   # add your QWEN_API_KEY (free OpenRouter key works)

# 2. Launch everything (Docker + OpenClaw + MCP)
.\scripts\launch.ps1

# 3. Use it
openclaw dashboard                           # web UI
openclaw agent --agent main --message "Remember I prefer Python for APIs"
openclaw tui                                 # terminal chat
```

After setup: open http://localhost:3000 to watch your memory graph form in real time.

## Architecture

```
WhatsApp / Telegram / Discord / WebChat
                    │
                    ▼
           OpenClaw Gateway (:18789)
         agent + mnemos MCP (7 tools)
                    │
                    ▼
          MnemOS MCP Server (:8001)
              (stdio / HTTP)
                    │
                    ▼
          MnemOS Memory Backend (:8000)
        ┌───────┼───────────────┐
        ▼                       ▼
    Waking Phase           Dreaming Phase
  (sync, hot path)      (async, background)
  • Embed query          • Salience auction
  • UCB retrieval        • Contradiction resolution
  • RWR associative hops • Utility feedback (Q_i)
  • Build Qwen payload   • Synaptic decay + prune
        │                       │
        └───────────┬───────────┘
                    ▼
              SQLite + sqlite-vec
          (single-file memory state)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full system design.

## The Four Pillars

### 1. Salience Auction — Ingestion Gate

Facts are scored on novelty, utility, and conviction BEFORE storage. Only high-conviction or system-critical facts enter the graph. Everything else is logged and discarded.

```
Store if: conviction ≥ 0.4  OR  category == 'system_state'
Reject otherwise
```

### 2. Dual-Output Chain-of-Thought

Qwen emits `<memory_update>` XML before its response. The interceptor strips the tags and passes extracted facts to background consolidation. **Zero additional LLM calls.**

### 3. UCB Retrieval — Multi-Armed Bandit

`Score_i = Q_i + c × √(ln(T) / (N_i + 1))`

Dormant memories are mathematically forced to resurface. The retrieval system learns which memories are useful through closed-loop feedback.

### 4. Synaptic Downscaling — Mathematical Forgetting

Nodes inactive > 45 minutes decay × 0.85. Below 0.1 weight: hard prune. The graph stays small, current, and relevant forever.

## Service Map

| Service | Port | Purpose |
|---------|------|---------|
| MnemOS API | 8000 | Memory backend (FastAPI) |
| MCP Server | 8001 | MCP tools for OpenClaw |
| Visualizer | 3000 | Real-time memory graph UI |

## MCP Tools (7)

| Tool | What it does |
|------|-------------|
| `memory_store` | Salience-gated fact ingestion |
| `memory_search` | Keyword + UCB retrieval |
| `memory_dump` | Full brain state (`/memory`) |
| `memory_stats` | UCB optimization table |
| `memory_chat` | Memory-augmented chat route |
| `memory_bind_user` | Bind channel sender → user_id |
| `memory_resolve_user` | Resolve/create user binding |

## Evaluation Benchmarks

25 scenarios across 5 categories comparing MnemOS vs vanilla LLM baseline:

| Category | Scenarios | What it measures |
|----------|-----------|------------------|
| Recall | 5 | Cross-session preference memory |
| Contradiction | 5 | Updating facts without retaining stale ones |
| Interference | 5 | Proactive interference prevention |
| Forgetting | 5 | Salience precision + temporal decay |
| Context | 5 | Associative recall + context efficiency |

```bash
# Dry-run (offline, instant)
python -m eval.run_benchmark --dry-run --mode both

# Multi-step agentic benchmark (trajectory metrics)
python -m eval.run_agentic_benchmark --dry-run --mode both

# Live (requires API key)
python -m eval.run_benchmark --mode both
```

Key metrics tracked: **context efficiency**, **forgetting accuracy**, **recall precision**, **interference prevention rate**, and **memory advantage trajectory** across probe difficulty levels.

## Tests

```bash
pytest tests/ -v                          # 128 unit + integration tests
.\scripts\integration-test.ps1            # 10 API/MCP/harness checks
.\scripts\submission-test.ps1             # Full submission verification
```

## Project Status

| Item | Status |
|------|--------|
| Core memory layer (4 pillars) | ✅ Complete |
| MCP server (7 tools) | ✅ Complete |
| OpenClaw gateway integration | ✅ Complete |
| Docker deployment | ✅ Complete |
| Memory visualizer | ✅ Complete |
| 25-scenario eval suite | ✅ Complete |
| Agentic benchmark (trajectory metrics) | ✅ Complete |
| Alibaba Cloud ECS + OSS | ⬜ Deferred (Plan B: local + ngrok) |
| Demo video | ⬜ Pending |

## Alibaba Cloud Integration

OSS backup sync: [`mcp-memory-server/src/storage/cloud_sync.py`](mcp-memory-server/src/storage/cloud_sync.py) — uploads memory state snapshots to Alibaba Cloud OSS every 50 conversational turns.

## Known Limitations

- Influence detection uses proximity regex (not embedding similarity) — pragmatic, fast, and surprisingly accurate
- OpenClaw CLI must be installed separately for multi-channel messaging
- Channel E2E tests require your own bot tokens
- No auth on `/chat` endpoint — intended for demo/hackathon use

## License

MIT — MnemOS Team, 2025

---

*Built for the Qwen Global AI Hackathon — Track 1: MemoryAgent*
