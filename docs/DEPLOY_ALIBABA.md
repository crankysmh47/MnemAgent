# Deploy to Alibaba Cloud

## Target

Use one Alibaba ECS Linux instance with Docker Engine and the Compose plugin. Point `memory.<domain>` at its public IP. The ECS security group should allow 80/443 publicly and SSH only from the operator's IP.

## Deploy

```bash
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
cp .env.cloud.example .env.cloud
```

Replace every example value. Generate secrets with `openssl rand -hex 32`.

```bash
bash scripts/deploy-cloud.sh
bash scripts/verify-cloud.sh
```

The command starts the memory service, MCP service, visualizer, Postgres, and Caddy. MCP binds to `127.0.0.1:8001` on ECS, so OpenClaw can use it from the host terminal without exposing it publicly.

## Submission proof

The runtime Alibaba API integration is [`mcp-memory-server/src/storage/cloud_sync.py`](../mcp-memory-server/src/storage/cloud_sync.py). It creates a database snapshot and uploads it to OSS when the OSS variables are configured. Use an ECS RAM role or a narrowly scoped RAM user; prefer an internal OSS endpoint when ECS and OSS share a region.

Record these items for the submission:

1. The public HTTPS visualizer and protected agent URLs.
2. ECS console or CLI output identifying the running instance and region.
3. The deployed `/health` response without secrets.
4. An OSS object created by the runtime backup path, if OSS is enabled.
5. A direct repository link to `cloud_sync.py`.

## Rollback

Keep the previous image tags and database volume. If verification fails, restore the previous Git tag and run the same deployment script. Database snapshots are additive; a failed backup does not stop memory serving.
