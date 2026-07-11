# Alibaba Cloud Proof

Use this document as the judge-facing proof checklist.

## Required Proof Artifacts

1. A short recording showing the backend running on Alibaba Cloud ECS.
2. A repository link showing Alibaba Cloud service/API usage.

## Code Proof Link

Use:

```text
mcp-memory-server/src/storage/cloud_sync.py
```

That file uses Alibaba Cloud OSS via `oss2`. In Postgres runtime mode it runs
`pg_dump` against `DATABASE_URL`, then uploads a compressed dump to:

```text
agent_runtime/backups/mnemagent_pg_<timestamp>.dump
```

## Recording Checklist

Show these in one 30-60 second proof video:

1. Alibaba Cloud ECS console with region, instance id, running status, and public IP.
2. SSH terminal on the ECS instance.
3. `docker compose ps` showing `postgres`, `mnemos-memory`, `mnemos-mcp`, and `openclaw-harness` healthy.
4. `curl http://127.0.0.1:8000/health`.
5. Browser opening the visualizer from the ECS public IP.
6. Optional: OSS bucket path containing a `mnemagent_pg_*.dump` snapshot.

## Security Note

Before recording or judging, run:

```powershell
pwsh ./scripts/reset-cloud-memory.ps1
```

This keeps the visual demo namespace (`demo-brain`) but removes non-demo test
users from Postgres so judges begin with a clean memory namespace.
