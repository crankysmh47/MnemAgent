# MnemAgent Setup Guide

Set up MnemOS (persistent memory layer) with OpenClaw (AI agent gateway) in one command.

## Table of Contents

- [Prerequisites](#prerequisites)
- [One-Command Setup](#one-command-setup)
- [What Gets Installed](#what-gets-installed)
- [Manual Setup (Step by Step)](#manual-setup-step-by-step)
- [Daily Startup](#daily-startup)
- [Verifying Everything Works](#verifying-everything-works)
- [Switching Models](#switching-models)
- [Troubleshooting](#troubleshooting)
- [Architecture Reference](#architecture-reference)

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| **Docker** | Engine 24+ or Docker Desktop | `docker info` |
| **Node.js** | 20+ | `node --version` |
| **npm** | 9+ | `npm --version` |
| **Python** | 3.11+ | `python3 --version` or `python --version` |
| **Git** | Any recent | `git --version` |

### Platform Notes

- **Linux** (Ubuntu/Debian): Install Docker with `sudo apt install docker.io`. Ensure your user is in the `docker` group: `sudo usermod -aG docker $USER && newgrp docker`.
- **macOS**: Install [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac/). Node.js via `brew install node`. Python via `brew install python@3.11`.
- **Windows**: Use [WSL 2](https://learn.microsoft.com/en-us/windows/wsl/install) with Ubuntu. Install Docker Desktop with WSL 2 backend. Run all commands inside the WSL terminal.

### Quick Install (Linux / macOS)

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker

# Node.js + npm
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Python 3.11+
sudo apt install -y python3 python3-pip python3-venv

# Verify
docker info --format '{{.ServerVersion}}'
node --version
python3 --version
```

---

## One-Command Setup

```bash
git clone <repo-url>
cd MnemAgent
bash scripts/setup.sh
```

**What this does in one shot:**

1. Checks prerequisites (Docker, Node.js, npm, Python 3.11+)
2. Creates `.env` from `config/env.template` (edit your API key in `.env`)
3. Creates a Python virtual environment and installs dependencies
4. Builds and starts Docker containers (MnemOS memory + MCP + web harness)
5. Waits for health on ports 8000 and 8001 (with countdown)
6. Installs OpenClaw globally via npm
7. Runs `openclaw onboard` with your credentials
8. Registers the MnemOS MCP toolset (7 tools via stdio transport)
9. Copies workspace files to `~/.openclaw/workspace/`
10. Starts the OpenClaw gateway
12. Verifies MCP probe returns 7 tools
13. Prints a success banner with quick-start commands

**First run takes 2-5 minutes** (Docker image builds). Subsequent runs are seconds.

---

## What Gets Installed

| Component | Where | Purpose |
|-----------|-------|---------|
| Docker containers | Local ports 8000, 8001, 3000 | MnemOS memory + MCP + web UI |
| `.venv/` | Repo root | Python dependencies (FastAPI, sentence-transformers, etc.) |
| `openclaw` (npm global) | System PATH | AI agent gateway (CLI + daemon) |
| `~/.openclaw/` | User home | OpenClaw config, workspace, MCP registrations |
| `mcp-server/node_modules/` | `mcp-server/` | MCP SDK + Express server |

---

## Manual Setup (Step by Step)

If the one-command script fails or you prefer manual control, follow these steps:

### 1. Environment

```bash
cp config/env.template .env
# Edit .env — set QWEN_API_KEY to your DashScope API key
# Get a key at: https://dashscope.aliyuncs.com
```

### 2. Python Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Docker Services

```bash
docker compose up -d --build
```

Wait for both to return `{"status":"ok"}`:

```bash
curl http://localhost:8000/health
curl http://localhost:8001/health
```

### 4. Install OpenClaw

```bash
npm install -g openclaw@latest
```

### 5. Onboard OpenClaw

```bash
# Source your .env values
source .env

openclaw onboard \
  --non-interactive \
  --accept-risk \
  --flow quickstart \
  --auth-choice custom-api-key \
  --custom-api-key "$QWEN_API_KEY" \
  --custom-base-url "$QWEN_BASE_URL" \
  --custom-model-id "$QWEN_MODEL" \
  --custom-compatibility openai \
  --custom-provider-id dashscope \
  --skip-channels \
  --skip-skills \
  --skip-search \
  --skip-hooks \
  --install-daemon \
  --gateway-bind loopback \
  --gateway-port 18789
```

### 6. Register MnemOS MCP

```bash
# Install MCP server dependencies
cd mcp-server && npm install && cd ..

# Register via stdio — try mcp set first (current OpenClaw), fall back to mcp add
openclaw mcp unset mnemos 2>/dev/null || true
MCP_PATH="$(pwd)/mcp-server/src/index.js"
if ! openclaw mcp set mnemos \
  "{\"command\":\"node\",\"args\":[\"$MCP_PATH\",\"--transport\",\"stdio\"],\"env\":{\"MNEMOS_URL\":\"http://localhost:8000\"}}" 2>/dev/null; then
  # Older OpenClaw versions use mcp add
  openclaw mcp add mnemos \
    --command node \
    --arg "$MCP_PATH" \
    --arg "--transport" \
    --arg "stdio" \
    --env "MNEMOS_URL=http://localhost:8000" \
    --timeout 120 \
    --connect-timeout 30
fi
```

> **IMPORTANT**: If this step fails silently, the agent will have NO memory tools.
> It will fall back to OpenClaw's broken built-in memory and may give confidently
> wrong answers (including leaking demo data). Always verify with `openclaw mcp probe mnemos`
> and ensure it shows 7 tools.

### 7. Copy Workspace Files

```bash
mkdir -p ~/.openclaw/workspace/skills/mnemos-memory
cp -r config/workspace/* ~/.openclaw/workspace/
```

### 8. Start Gateway

```bash
openclaw gateway restart --force
sleep 5
openclaw gateway health
```

### 9. Verify

```bash
openclaw mcp list
openclaw mcp probe mnemos    # Should show 7 tools
```

---

## Daily Startup

After initial setup, start your daily session with:

```bash
bash scripts/dev.sh
```

This starts Docker services and the OpenClaw gateway in one command.

Or manually:

```bash
docker compose up -d
openclaw gateway restart --force
# Wait 5s, then verify
openclaw gateway health
openclaw mcp probe mnemos
```

---

## Verifying Everything Works

### Check Docker services

```bash
curl -s http://localhost:8000/health | python3 -m json.tool
curl -s http://localhost:8001/health | python3 -m json.tool
```

Expected response:
```json
{"status": "ok", ...}
```

### Check OpenClaw gateway

```bash
openclaw gateway health
```

Expected: no errors, shows gateway is running.

### Check MCP tools

```bash
openclaw mcp list
openclaw mcp probe mnemos
```

Expected: `mnemos` server listed with **7 tools**:
- `memory_store`, `memory_search`, `memory_dump`, `memory_stats`
- `memory_chat`, `memory_bind_user`, `memory_resolve_user`

### Send a test message

```bash
openclaw agent --agent main --message "Hello! Remember that I like Python."
```

### Check the visualizer

Open http://localhost:3000/visualizer in your browser to see the memory graph.

### Run the test suite

```bash
# Unit tests (143 passing)
pytest tests/ -v

# Integration tests
bash scripts/integration-test.ps1   # Windows
pwsh scripts/integration-test.ps1   # Linux/macOS with PowerShell
```

---

## Switching Models

### Via OpenClaw config

```bash
# Use cheapest model
openclaw config set agents.defaults.model.primary "dashscope/qwen-flash"

# Use best quality
openclaw config set agents.defaults.model.primary "dashscope/qwen-max"
```

### Via .env file

Edit `.env` and change `QWEN_MODEL`:

```
# Cheapest, daily use
QWEN_MODEL=qwen-flash

# Balanced
QWEN_MODEL=qwen-plus

# Best quality (demos, eval)
QWEN_MODEL=qwen-max
```

Then re-onboard if needed, or just update the gateway config:

```bash
openclaw config set agents.defaults.model.primary "dashscope/$QWEN_MODEL"
openclaw gateway restart --force
```

---

## Troubleshooting

### Docker issues

| Symptom | Fix |
|---------|-----|
| `docker info` fails | Start Docker Desktop or Docker Engine |
| Port 8000 in use | `lsof -ti:8000 \| xargs kill` or change port in `.env` |
| Container exits immediately | `docker compose logs mnemos-memory` to see errors |
| Image build fails | Check Docker disk space: `docker system df` |
| `curl: (56) Recv failure` | Container still starting — wait longer |

### OpenClaw issues

| Symptom | Fix |
|---------|-----|
| `openclaw: command not found` | Run `npm install -g openclaw@latest` and restart terminal |
| `openclaw onboard` fails | Check your `QWEN_API_KEY` in `.env` is valid |
| Gateway won't start | `openclaw gateway restart --force` |
| Gateway "auth required" | `openclaw config set gateway.auth.mode none` |
| `openclaw mcp probe mnemos` fails | Is the gateway running? Check `openclaw gateway health` |

### MCP issues

| Symptom | Fix |
|---------|-----|
| `mnemos` not in MCP list | Re-run MCP registration step |
| Probe shows 0 tools | `openclaw mcp unset mnemos` then re-register |
| "Connection timeout" | Is MnemOS Docker running? `curl http://localhost:8000/health` |
| Node errors in MCP | `cd mcp-server && npm install` |
| **"index metadata is missing"** or **"memory search is paused"** | Your MCP tools are NOT registered. The agent has fallen back to OpenClaw's broken built-in memory. Run `openclaw mcp list` — if `mnemos` is missing, re-register: `openclaw mcp set mnemos '{"command":"node","args":["<path-to-mcp-server>/src/index.js","--transport","stdio"],"env":{"MNEMOS_URL":"http://localhost:8000"}}'` |
| **Agent gives wrong facts (e.g. "FAST student")** | This is demo data from `USER.md` leaking because memory search failed. Fix the MCP registration first (above). The fixed USER.md is now a template that won't be treated as real data. |

### Python issues

| Symptom | Fix |
|---------|-----|
| `python3: command not found` | `sudo apt install python3` (Linux) or `brew install python@3.11` (macOS) |
| `.venv` activation fails | Delete `.venv/` and re-run setup |
| `pip install` SSL errors | Check your VPN/network — try `pip install --trusted-host pypi.org --trusted-host pypi.python.org` |

### Environment issues

| Symptom | Fix |
|---------|-----|
| "QWEN_API_KEY missing" | Edit `.env` and add your key |
| `.env` not being read | Make sure `.env` is in the repo root (same level as `docker-compose.yml`) |

### Port conflicts

If ports 8000, 8001, or 3000 are already in use on your machine:

1. Edit `docker-compose.yml` to change the host ports (e.g., `"8000:8000"` to `"8005:8000"`)
2. Update `.env` with the new ports
3. Re-run setup

---

## Architecture Reference

```
You (CLI / Dashboard)
       │
       ▼
OpenClaw Gateway (:18789)     ←──  openclaw agent / dashboard
       │
       ├── Agent runtime + mnemos MCP tools
       │       │
       │       ▼  (stdio transport)
       │  mcp-server/src/index.js
       │       │  (node process spawned by OpenClaw)
       │       ▼
       │  MnemOS Memory API (:8000)  ←── FastAPI + SQLite + sqlite-vec
       │       │
       │       ├── Waking Phase  (sync — embed, UCB retrieve, respond)
       │       └── Dreaming Phase (async — salience auction, decay, prune)
       │
       └── Web Harness (:3000)     ←── Real-time memory visualizer
                │
                └── MnemOS MCP HTTP (:8001)   ←── Docker container
```

### Data Flow

1. **User message** arrives via OpenClaw CLI or web dashboard
2. **Agent** calls `memory_search(user_id, query)` via MCP stdio
3. **mcp-server** forwards to MnemOS API (`POST /api/memory/search`)
4. **MnemOS** performs UCB retrieval + RWR associative hops
5. **Agent** receives results, builds prompt, sends to LLM
6. **LLM response** is returned to user; facts are extracted and stored in background

### Port Map

| Port | Service | Purpose |
|------|---------|---------|
| 8000 | MnemOS Memory API | FastAPI backend (health at `/health`) |
| 8001 | MCP Server (HTTP) | Docker container for web harness |
| 3000 | Web Harness | Visualizer + dashboard UI |
| 18789 | OpenClaw Gateway | Agent gateway + MCP proxy |

---

## Reference

- [ARCHITECTURE.md](ARCHITECTURE.md) — Full system design
- [README.md](../README.md) — Project overview, benchmarks, tests
- `config/env.template` — All configuration options
- `config/openclaw/` — OpenClaw model bundles, MCP registrations
- `config/workspace/` — Agent instruction files (AGENTS.md, SOUL.md, TOOLS.md)
