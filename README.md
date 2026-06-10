# MnemOS

Persistent memory layer for OpenClaw — selective ingestion, UCB retrieval, closed-loop feedback, and mathematical forgetting (Qwen Global AI Hackathon, Track 1: MemoryAgent).

## Architecture

```
User
  ├─ Chat UI (:3000) ──────────────┐
  ├─ Memory Visualizer (:3000/viz) │
  └─ OpenClaw TUI ──► OpenClaw Gateway
                              │
                              ▼
                    MCP Adapter (:8001)
                              │
                              ▼
                    MnemOS Memory Server (:8000)
                      ├─ Waking (UCB + RWR)
                      ├─ Dreaming (feedback + decay)
                      └─ Qwen / OpenAI-compatible LLM
```

## Four Pillars

1. **Salience Auction** — gates ingestion by conviction and category
2. **UCB Retrieval** — `Score_i = Q_i + c × √(ln(T)/(N_i+1))`
3. **Closed-Loop Feedback** — proximity-based Q_i updates after each response
4. **Synaptic Downscaling** — decay ×0.85 / hard prune below 0.1

## Quick Start

```bash
git clone <repo>
cd MnemAgent
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # add API keys
docker compose up --build
```

| Service | URL |
|---------|-----|
| Chat UI | http://localhost:3000 |
| Memory Visualizer | http://localhost:3000/visualizer |
| MnemOS API | http://localhost:8000 |
| MCP Adapter | http://localhost:8001 |

### OpenClaw TUI (optional)

```bash
# Windows
.\openclaw-harness\setup.ps1

# Linux/Mac
chmod +x openclaw-harness/setup.sh && ./openclaw-harness/setup.sh

openclaw gateway
openclaw tui
```

Use the shared `user_id` from `~/.openclaw/mnemos-user-id.txt` in the chat UI (`localStorage.mnemos_user_id`) so TUI and web share one memory graph.

## OpenClaw Integration

MnemOS registers as OpenClaw's memory backend via the **MCP adapter** (`openclaw-harness/mcp-adapter/`). It exposes:

- `memory_store` — salience-gated fact ingestion
- `memory_search` — keyword retrieval over `semantic_graph`
- `memory_dump` — `/memory` brain state
- `memory_stats` — `/memory --mode stats` UCB table

Config: `openclaw-harness/openclaw-config/mnemos.config.json`

## Alibaba Cloud Proof

OSS backup is implemented in [`mcp-memory-server/src/storage/cloud_sync.py`](mcp-memory-server/src/storage/cloud_sync.py).

## Benchmark

```bash
python -m eval.run_benchmark --dry-run --mode both   # offline
python -m eval.run_benchmark --mode both             # live (server + API key)
```

## Tests

```bash
pytest tests/ -v
```

## Known Limitations

- Influence detection uses proximity regex (not embedding similarity)
- OpenClaw TUI integration requires the OpenClaw CLI installed separately
- UCB timeline in the visualizer approximates historical scores from current state
- No auth on `/chat` — demo only

## License

MIT
