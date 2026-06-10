# MnemOS

Persistent memory layer for OpenClaw — selective ingestion, UCB retrieval, closed-loop feedback, and mathematical forgetting (Qwen Global AI Hackathon, Track 1: MemoryAgent).

## Architecture

```
WhatsApp / Telegram / Discord / Slack / WebChat
                    │
                    ▼
           OpenClaw Gateway (:18789)
         (agent + MCP tool discovery)
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
  MnemOS MCP Server        Built-in tools
  (:8001 stdio/http)       (web search, etc.)
        │
        ▼
  MnemOS Memory Backend (:8000)
    ├─ Waking (UCB + RWR)
    ├─ Dreaming (feedback + decay)
    └─ Qwen / OpenAI-compatible LLM
```

Legacy web harness at `:3000` remains for chat UI and memory visualizer during development.

## Four Pillars

1. **Salience Auction** — gates ingestion by conviction and category
2. **UCB Retrieval** — `Score_i = Q_i + c × √(ln(T)/(N_i+1))`
3. **Closed-Loop Feedback** — proximity-based Q_i updates after each response
4. **Synaptic Downscaling** — decay ×0.85 / hard prune below 0.1

## Quick Start

### Docker (recommended)

```bash
git clone <repo>
cd MnemAgent
cp .env.example .env          # add QWEN_API_KEY
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| MnemOS API | http://localhost:8000 |
| MCP Server | http://localhost:8001 |
| Chat UI (legacy) | http://localhost:3000 |
| Visualizer | http://localhost:3000/visualizer |

### Full OpenClaw setup

```powershell
# Windows
.\scripts\setup-openclaw.ps1

# Linux/macOS
chmod +x scripts/setup-openclaw.sh && ./scripts/setup-openclaw.sh
```

Then (full onboard + MCP wiring):

```powershell
.\scripts\onboard-openclaw.ps1
.\scripts\prove-openclaw.ps1
```

Daily usage:

```powershell
openclaw dashboard                    # web UI
openclaw agent --agent main --message "Remember I prefer Python"
openclaw tui                          # terminal chat
```

Architecture:

```
You → OpenClaw Gateway (:18789)
        → Agent (OpenRouter free: openrouter/free + R1/Llama/Qwen fallbacks)
        → mnemos MCP tools (stdio)
        → mcp-server → MnemOS API (:8000) → SQLite memory
```

### Free OpenRouter models

Copy [`openclaw-config/mnemos-free.env.example`](openclaw-config/mnemos-free.env.example) into `.env`.
OpenClaw model routing is in [`openclaw-config/free-models.patch.json`](openclaw-config/free-models.patch.json)
(applied automatically by `onboard-openclaw.ps1`).

| Layer | Primary | Fallbacks |
|-------|---------|-----------|
| MnemOS chat | `deepseek/deepseek-r1-0528:free` | swap in `.env` |
| OpenClaw + MCP | `openrouter/free` | R1, Llama 3.3, Qwen 2.5/3 free |

### Project status

**Done (Parts 0–14 + OpenClaw):** memory layer, MCP server, gateway integration, Docker, evals, web harness.

**Remaining (Parts 15–17):** Alibaba Cloud ECS deploy + OSS proof screenshot, demo video, final README polish.

### Add messaging channels

```powershell
.\scripts\add-telegram.ps1    # fastest — bot token from @BotFather
.\scripts\add-discord.ps1       # Discord bot token
.\scripts\add-whatsapp.ps1      # QR code pairing
```

## MCP Tools

Registered as `mnemos` in OpenClaw (`openclaw mcp set mnemos ...`):

| Tool | Description |
|------|-------------|
| `memory_store` | Salience-gated fact ingestion |
| `memory_search` | Keyword + UCB search over beliefs |
| `memory_dump` | Full brain state (`/memory`) |
| `memory_stats` | UCB optimization table |
| `memory_chat` | Memory-augmented chat route |
| `memory_bind_user` | Bind channel sender → user_id |
| `memory_resolve_user` | Resolve or create user binding |

Config templates: [`openclaw-config/openclaw.json`](openclaw-config/openclaw.json), [`workspace-config/`](workspace-config/)

## Agent Workspace

Copy [`workspace-config/`](workspace-config/) to `~/.openclaw/workspace/`:

- `AGENTS.md` — memory rules and MCP tool usage
- `SOUL.md` — persona
- `TOOLS.md` — MnemOS endpoints
- `skills/mnemos-memory/SKILL.md` — memory workflow skill

## REST API (MnemOS backend)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/chat` | POST | Memory-augmented chat |
| `/api/memory/store` | POST | Store one fact |
| `/api/memory/store/batch` | POST | Store multiple facts |
| `/api/memory/search/{user_id}` | GET | Search beliefs |
| `/api/memory/dump/{user_id}` | GET | Brain state |
| `/api/memory/stats/{user_id}` | GET | UCB stats |
| `/api/user/bind` | POST | Channel → user_id binding |
| `/api/graph/{user_id}` | GET | Visualizer graph data |

## Benchmark

```bash
# Original single-turn benchmark
python -m eval.run_benchmark --dry-run --mode both

# Multi-step agentic memory advantage benchmark
python -m eval.run_agentic_benchmark --dry-run --mode both
python -m eval.run_agentic_benchmark --mode both   # live (needs API key)
```

## Tests

```bash
pytest tests/ -v
.\scripts\integration-test.ps1
.\scripts\smoke_test.ps1
```

## Alibaba Cloud Proof

OSS backup: [`mcp-memory-server/src/storage/cloud_sync.py`](mcp-memory-server/src/storage/cloud_sync.py)

## Known Limitations

- Influence detection uses proximity regex (not embedding similarity)
- OpenClaw CLI must be installed separately for real multi-channel messaging
- Channel E2E tests require your own bot tokens
- No auth on `/chat` — demo only

## License

MIT
