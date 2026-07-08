# Alibaba Cloud Deployment Proof

This document is the judge-facing proof plan for the Qwen Global AI Hackathon
submission. It defines what to record, what to screenshot, and which code files
prove Alibaba Cloud usage.

## What The Submission Needs

The submission should include two proof artifacts:

1. A short recording showing the backend running on Alibaba Cloud.
2. A repository link showing Alibaba Cloud service/API usage in code.

For this project, the cloud proof is:

- MnemOS running on an Alibaba Cloud ECS instance.
- Docker Compose showing the MnemOS services healthy on ECS.
- ECS metadata showing the instance is really Alibaba Cloud infrastructure.
- Public ECS IP serving the visualizer and health endpoints.
- Optional OSS snapshot code path for Alibaba Cloud Object Storage backup.

## Code Proof

Use this file as the required repository link that demonstrates Alibaba Cloud
service usage:

```text
mcp-memory-server/src/storage/cloud_sync.py
```

That code uses Alibaba Cloud OSS through `oss2` and uploads SQLite snapshots to:

```text
agent_runtime/backups/memory_state_<timestamp>.db
```

MnemOS keeps the live memory graph in SQLite for simple single-instance ECS
deployment, then snapshots the database to OSS for recovery and cloud-service
proof.

## Recording Checklist

Record a separate 30-60 second cloud proof video. This is not the 3-minute
product demo. It should be simple and hard to dispute.

### 1. Show ECS Console

Open Alibaba Cloud Console and show:

- Elastic Compute Service instance list.
- Instance region.
- Running status.
- Public IP.
- Instance ID.

Do not show AccessKey secrets, `.env`, billing pages, or private keys.

### 2. SSH Into The ECS Instance

In the terminal on the ECS instance, run:

```bash
cd ~/MnemAgent
hostname
curl -s http://100.100.100.200/latest/meta-data/instance-id
curl -s http://100.100.100.200/latest/meta-data/region-id
```

Expected evidence:

- `instance-id` returns an Alibaba ECS instance id.
- `region-id` returns the Alibaba Cloud region, such as `ap-southeast-1`.

If metadata access is unavailable on the image, show the ECS console instance
details instead and continue with the Docker/health checks.

### 3. Show Containers Running

Run:

```bash
docker compose ps
```

Expected services:

```text
mnemos-memory       healthy
mnemos-mcp          healthy
openclaw-harness    healthy
```

Then show recent logs:

```bash
docker compose logs --tail=30 mnemos-memory
docker compose logs --tail=20 openclaw-harness
```

Useful things to capture:

- Uvicorn/FastAPI startup.
- Health checks.
- Any memory store or graph API calls during the demo.
- No startup errors.

### 4. Show Public Health Endpoints

Replace `<ecs-ip>` with the ECS public IP:

```bash
curl http://<ecs-ip>:3000/health
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8001/health
```

The public proof should expose the visualizer/harness on `:3000`. The internal
API and MCP ports can remain localhost-only for safer deployment.

Expected examples:

```json
{"status":"ok","service":"mnemos","prompt_version":"v4-dual-path-write"}
{"status":"ok"}
```

### 5. Run Judge Preflight

Run:

```bash
pwsh ./scripts/reset-cloud-memory.ps1
pwsh ./scripts/deploy-preflight.ps1 \
  -MnemosUrl http://127.0.0.1:8000 \
  -HarnessUrl http://<ecs-ip>:3000
```

Capture the output showing:

- MnemOS API is healthy.
- Visualizer harness is healthy.
- Judge user id is isolated.
- Judge namespace starts empty.
- Demo graph is populated.
- OpenClaw sees 7 MnemOS MCP tools.

This is the cleanest proof that judges will not inherit stale test memories.

### 6. Show Browser Proof

Open:

```text
http://<ecs-ip>:3000?user=demo-brain
http://<ecs-ip>:3000?user=<judge-user-id>
```

Show:

- `demo-brain` has a rich graph for the visual demo.
- `<judge-user-id>` starts empty or only contains memories created during the
  judge recording.

## Optional OSS Proof

If OSS credentials are configured, record one of these:

### Console Proof

Open Alibaba Cloud OSS Console and show:

- Bucket name.
- Region.
- Private ACL.
- Object prefix:

```text
agent_runtime/backups/
```

### Terminal Proof

If `ossutil` is installed:

```bash
ossutil ls oss://<bucket-name>/agent_runtime/backups/
```

Or show container logs after a successful snapshot:

```bash
docker compose logs mnemos-memory | grep OSS
```

Expected log line:

```text
Uploaded database snapshot to OSS: agent_runtime/backups/memory_state_<timestamp>.db
```

OSS is optional for the live product path. ECS deployment is the main proof;
OSS is additional evidence that the project integrates Alibaba Cloud services.

## 3-Minute Product Demo Flow

Use `docs/SUBMISSION_VIDEO_PLAN.md` for the product demo. Keep the cloud proof
video separate unless the submission form only allows one link.

Recommended final package:

- 3-minute demo video: product value, memory behavior, visualizer, benchmarks.
- 30-60 second cloud proof video: ECS console, SSH, Docker health, public URL.
- Repository link: this repo.
- Code proof link: `mcp-memory-server/src/storage/cloud_sync.py`.
- Architecture diagram: README Mermaid diagram or `docs/ARCHITECTURE.md`.

## What Not To Show

Do not show:

- API keys.
- `.env` contents.
- Alibaba AccessKey secrets.
- SSH private keys.
- Billing/payment pages.
- Judge credentials.

If a command risks printing secrets, do not run it during recording.
