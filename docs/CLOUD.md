# MnemOS — Cloud Deployment Guide

Deploy MnemOS (memory layer + visualizer + MCP tools) to cloud infrastructure. Target platform: **Alibaba Cloud ECS** with optional **OSS backup**.

---

## Architecture (cloud)

```
┌─────────────────────────────────────────────────────┐
│  ECS Instance (2 vCPU / 4 GiB minimum)              │
│                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ mnemos-  │  │ mnemos-  │  │ openclaw-        │  │
│  │ memory   │  │ mcp      │  │ harness          │  │
│  │ :8000    │  │ :8001    │  │ :3000            │  │
│  │ FastAPI  │◄─┤ Node MCP │  │ Express + D3.js  │  │
│  └────┬─────┘  └──────────┘  └──────────────────┘  │
│       │                                              │
│       ▼                                              │
│  ┌──────────┐                                       │
│  │ SQLite   │  Docker volume (mnemos-data)          │
│  │ + vec    │                                       │
│  └────┬─────┘                                       │
│       │  every 50 turns (optional)                   │
│       ▼                                              │
└───────┬─────────────────────────────────────────────┘
        │
   ┌────▼────┐
   │ OSS     │  agent_runtime/backups/memory_state_*.db
   │ Bucket  │
   └─────────┘
```

---

## Quick deploy (ECS)

### 1. Provision an ECS instance

| Setting | Value |
|---------|-------|
| OS | Ubuntu 22.04 or Debian 12 |
| vCPU | 2 minimum (4 recommended — embeddings are CPU-bound) |
| Memory | 4 GiB minimum |
| Disk | 20 GiB system + 20 GiB data |
| Network | Public IP + security group |

**Security group inbound rules:**

| Port | Protocol | Source | Purpose |
|------|----------|--------|---------|
| 22 | TCP | Your IP | SSH |
| 3000 | TCP | 0.0.0.0/0 (or restrict) | Memory visualizer |
| 8000 | TCP | 127.0.0.1 only | MnemOS API (internal) |
| 8001 | TCP | 127.0.0.1 only | MCP server (internal) |

> **Important:** Ports 8000 and 8001 carry unauthenticated API traffic. Bind them to
> `127.0.0.1` via the docker-compose `ports` directive or a reverse proxy. Only the
> visualizer on port 3000 should be publicly reachable (or use nginx/CADDY for TLS).

### 2. Install prerequisites

```bash
# Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
newgrp docker

# Docker Compose (if not included)
sudo apt install -y docker-compose-plugin
```

### 3. Deploy the stack

```bash
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent

# Set up environment
cp config/env.template .env
# Edit .env — add your DashScope API key
nano .env

# Start services
docker compose up -d --build

# Verify
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:3000/health
```

### 4. Verify services

```bash
docker compose ps            # all 3 services healthy
curl http://localhost:3000    # visualizer loads
docker compose logs -f        # check for errors
```

---

## Container registry push (ACR or Docker Hub)

### Push to Alibaba Cloud ACR

```bash
# Login to ACR
docker login --username=<your-alibaba-cloud-account> registry.cn-singapore.aliyuncs.com

# Tag images
docker tag mnemagent-mnemos-memory registry.cn-singapore.aliyuncs.com/mnemos/memory:latest
docker tag mnemagent-mnemos-mcp    registry.cn-singapore.aliyuncs.com/mnemos/mcp:latest
docker tag mnemagent-openclaw-harness registry.cn-singapore.aliyuncs.com/mnemos/harness:latest

# Push
docker push registry.cn-singapore.aliyuncs.com/mnemos/memory:latest
docker push registry.cn-singapore.aliyuncs.com/mnemos/mcp:latest
docker push registry.cn-singapore.aliyuncs.com/mnemos/harness:latest
```

### Push to Docker Hub

```bash
docker login
docker tag mnemagent-mnemos-memory crankysmh47/mnemos-memory:latest
docker tag mnemagent-mnemos-mcp    crankysmh47/mnemos-mcp:latest
docker tag mnemagent-openclaw-harness crankysmh47/mnemos-harness:latest
docker push crankysmh47/mnemos-memory:latest
docker push crankysmh47/mnemos-mcp:latest
docker push crankysmh47/mnemos-harness:latest
```

### Use registry images in docker-compose

Create `docker-compose.deploy.yml`:

```yaml
services:
  mnemos-memory:
    image: registry.cn-singapore.aliyuncs.com/mnemos/memory:latest
    # ... (rest same as docker-compose.yml, remove build: section)

  mnemos-mcp:
    image: registry.cn-singapore.aliyuncs.com/mnemos/mcp:latest
    # ...

  openclaw-harness:
    image: registry.cn-singapore.aliyuncs.com/mnemos/harness:latest
    # ...
```

---

## OSS backup configuration

MnemOS automatically snapshots `memory_state.db` to Alibaba Cloud OSS every 50 turns
when valid credentials are provided.

### 1. Create an OSS bucket

```
Console → Object Storage Service → Create Bucket
  Bucket name: mnemos-backups
  Region:      Asia Pacific SE 1 (Singapore) — same region as ECS
  ACL:         Private
```

### 2. Create an AccessKey

```
Console → RAM → Users → Create User
  Enable: Open API Access
  Attach: AlibabaCloudOSSFullAccess
```

### 3. Set environment variables

In `.env` on the ECS instance:

```bash
ALIBABA_CLOUD_ACCESS_KEY_ID=LTAI5t...       # your real key
ALIBABA_CLOUD_ACCESS_KEY_SECRET=...          # your real secret
ALIBABA_CLOUD_OSS_BUCKET=mnemos-backups
ALIBABA_CLOUD_OSS_ENDPOINT=https://oss-ap-southeast-1.aliyuncs.com
```

Then restart:

```bash
docker compose up -d --force-recreate mnemos-memory
```

### Verification

Check container logs after 50 chat turns:

```bash
docker compose logs mnemos-memory | grep "OSS"
# → Uploaded database snapshot to OSS: agent_runtime/backups/memory_state_20260628T120000Z.db
```

---

## Environment variable reference

All variables are read from `.env` at container start. Required variables are **bold**.

| Variable | Default | Description |
|----------|---------|-------------|
| **`QWEN_API_KEY`** | (required) | DashScope API key |
| `QWEN_MODEL` | `qwen-flash` | Model ID for chat/completions |
| `QWEN_BASE_URL` | `https://dashscope.aliyuncs.com/compatible-mode/v1` | API base URL |
| `HOST` | `0.0.0.0` | uvicorn bind address |
| `PORT` | `8000` | MnemOS API port |
| `LOG_LEVEL` | `INFO` | Python log level |
| `DB_PATH` | `./data/memory_state.db` | SQLite database path |
| `ENABLE_DREAMING_EXTRACTION` | `true` | Server-side fact extraction |
| `AWAIT_DREAMING` | `true` | Wait for memory write before reply |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Sentence transformer model |
| `EMBEDDING_DIM` | `384` | Embedding vector dimension |
| `UCB_EXPLORATION_C` | `0.3` | UCB exploration constant |
| `RWR_ALPHA` | `0.85` | Random walk restart probability |
| `DECAY_RATE` | `0.85` | Synaptic decay multiplier |
| `PRUNE_THRESHOLD` | `0.1` | Minimum node weight before pruning |
| `MAX_INJECTED_FACTS` | `6` | Max facts injected per turn |
| `ALIBABA_CLOUD_ACCESS_KEY_ID` | (placeholder) | OSS access key for cloud sync |
| `ALIBABA_CLOUD_ACCESS_KEY_SECRET` | (placeholder) | OSS secret for cloud sync |
| `ALIBABA_CLOUD_OSS_BUCKET` | `mnemos-backups` | OSS bucket name |
| `ALIBABA_CLOUD_OSS_ENDPOINT` | `https://oss-ap-southeast-1.aliyuncs.com` | OSS endpoint |

---

## Monitoring

### Health endpoints

```bash
# All three services expose /health:
curl http://<ecs-ip>:8000/health   # MnemOS API
curl http://<ecs-ip>:8001/health   # MCP server
curl http://<ecs-ip>:3000/health   # Visualizer harness
```

### Container health

```bash
docker compose ps                    # status + health
docker stats                         # CPU/memory
docker compose logs --tail=50 mnemos-memory
```

### Memory layer health

The visualizer (`:3000`) shows live metrics:
- Belief count, edge count, sessions
- UCB timeline (Chart.js)
- Injection count by category
- Live event feed (store, decay, prune, contradiction, inject)

### Log persistence

```bash
# Docker json-file logging by default. For production:
# Add to docker-compose.yml:
services:
  mnemos-memory:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Scaling notes

The current architecture is single-instance because SQLite has a single-writer constraint.
For multi-instance deployments:

1. **Read replicas**: Mount the SQLite DB on a shared volume (NAS/OSS) and use read-only replicas for the visualizer and search endpoints
2. **DB migration**: Replace SQLite with PostgreSQL + pgvector for multi-writer support (the `storage/db_manager.py` interface is isolated and swappable)
3. **Stateless MCP**: The MCP server is stateless — scale horizontally behind a load balancer
4. **Embedding offload**: Switch `EMBEDDING_MODEL=text-embedding-v3` to use Qwen cloud embeddings instead of local `all-MiniLM-L6-v2`

---

## Disaster recovery

1. **OSS snapshots** (every 50 turns): `agent_runtime/backups/memory_state_<timestamp>.db`
2. **Docker volume backup**:
   ```bash
   docker run --rm -v mnemagent_mnemos-data:/data -v $(pwd):/backup alpine \
     cp /data/memory_state.db /backup/memory_state_$(date +%Y%m%d).db
   ```
3. **Restore from OSS**:
   ```bash
   # Download latest snapshot from OSS console or ossutil
   ossutil cp oss://mnemos-backups/agent_runtime/backups/memory_state_20260628T120000Z.db ./restore.db
   # Stop stack, replace volume, restart
   docker compose stop mnemos-memory
   docker run --rm -v mnemagent_mnemos-data:/data alpine sh -c "rm -f /data/memory_state.db*"
   docker cp restore.db <container>:/app/data/memory_state.db
   docker compose start mnemos-memory
   ```

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| Container exits on start | `docker compose logs mnemos-memory` — likely missing `.env` or invalid `QWEN_API_KEY` |
| Health check fails (180s timeout) | Embedding model download on first start (~90 MB). Wait longer, or check network. |
| "Out of memory" | Increase ECS memory to 4 GiB+. Sentence-transformers loads ~500 MB. |
| OSS sync not running | Verify `ALIBABA_CLOUD_ACCESS_KEY_ID` is not the placeholder (`xxxxxxxxxxxx`). |
| Port already in use | Check for conflicting services on 3000/8000/8001. |
| Slow first request | Normal — embedding warmup runs on container start (awaited, max 45s). |
