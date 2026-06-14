# MnemOS — Memory That Earns Its Place

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-136%20passing-brightgreen.svg)](tests/)

**Persistent memory layer for AI agents** — selective ingestion via salience auction, UCB-based retrieval, closed-loop feedback, and mathematical forgetting. Built for the **Qwen Global AI Hackathon, Track 1: MemoryAgent**.

> Standard RAG agents suffer from proactive interference (stale facts drown out current ones) and naive storage (garbage accumulates). MnemOS rejects garbage at ingestion and forces stale facts out mathematically. The retrieval system learns which memories are actually useful.

---

## Quick Start — One Command

```bash
git clone <repo-url>
cd MnemAgent
bash scripts/setup.sh
```

That's it. The script checks prerequisites, starts Docker containers, installs OpenClaw, registers the MnemOS MCP toolset (7 tools), and prints quick-start commands.

After setup completes:
```bash
openclaw dashboard                           # web UI
openclaw agent --agent main --message "Remember I prefer Python for APIs"
openclaw tui                                 # terminal chat
openclaw mcp probe mnemos                    # verify MCP tools
```

Open http://localhost:3000?user=demo-brain to watch the pre-seeded memory graph (61 beliefs, golden synapses).

**Daily startup** (after first setup):
```bash
bash scripts/dev.sh
```

> **Windows users**: Run the above commands from WSL (Ubuntu), or use `.\scripts\launch.ps1` in PowerShell.

---

## Setup Guides

- [docs/SETUP.md](docs/SETUP.md) — Detailed setup guide with prerequisites, troubleshooting, and model switching
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Full system design

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

## The Four Pillars

### 1. Salience Auction — Ingestion Gate

Facts are scored on novelty, utility, and conviction BEFORE storage. Only high-conviction or system-critical facts enter the graph. Everything else is logged and discarded.

```
Store if: conviction >= 0.4  OR  category == 'system_state'
Reject otherwise
```

### 2. Dual-Output Chain-of-Thought

Qwen emits `<memory_update>` XML before its response. The interceptor strips the tags and passes extracted facts to background consolidation. **Zero additional LLM calls.**

### 3. UCB Retrieval — Multi-Armed Bandit

`Score_i = Q_i + c x sqrt(ln(T) / (N_i + 1))`

Dormant memories are mathematically forced to resurface. The retrieval system learns which memories are useful through closed-loop feedback.

### 4. Synaptic Downscaling — Mathematical Forgetting

Nodes inactive > 45 minutes decay x 0.85. Below 0.1 weight: hard prune. The graph stays small, current, and relevant forever.

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
| `memory_bind_user` | Bind channel sender to user_id |
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

```bash
# MnemBench — long-running memory benchmark (10 scenarios)
python -m eval.mnembench --dry-run --mode both

# Multi-step agentic benchmark (trajectory metrics)
python -m eval.run_agentic_benchmark --dry-run --mode both

# Live (requires API key)
python -m eval.run_benchmark --mode both
```

Key metrics tracked: **context efficiency**, **forgetting accuracy**, **recall precision**, **interference prevention rate**, and **memory advantage trajectory** across probe difficulty levels.

## Tests

```bash
pytest tests/ -v                          # 136 unit + integration tests
pwsh scripts/integration-test.ps1         # 10 API/MCP/harness checks
pwsh scripts/submission-test.ps1          # Full submission verification
```

## Project Status

| Item | Status |
|------|--------|
| Core memory layer (4 pillars) | Complete |
| MCP server (7 tools) | Complete |
| OpenClaw integration (`scripts/setup.sh`) | Complete |
| Docker deployment (3 services) | Complete |
| Brain-theme visualizer (61 demo memories) | Complete |
| 25-scenario single-turn eval | Complete |
| 4-scenario agentic eval (86.5% vs 64.6%) | Complete |
| MnemBench (10 scenarios, 171+ steps) | Complete |
| REPORT.md + ARCHITECTURE.md + SETUP.md | Complete |
| 136 tests, 81% coverage | Complete |
| One-command setup | `bash scripts/setup.sh` |
| Default model | qwen-turbo (quota-friendly) |

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
