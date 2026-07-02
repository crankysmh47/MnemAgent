# Judge-Safe Deployment Runbook

This project has two memory namespaces:

- `demo-brain` - pre-seeded memories for the visualizer and screenshots.
- `judge-*` - fresh live namespace used by OpenClaw and the judge-facing chat.

The judge namespace must be empty before submission. Do not expose a DB where
OpenClaw points at old test users such as `demo-fast-student`, `default_user`,
`user_123`, or local review markers.

## Final Cloud Reset

Run this after testing and before opening the deployment to judges:

```powershell
cd C:\sem4\MnemAgent
.\scripts\reset-cloud-memory.ps1
```

What it does:

- Preserves `demo-brain`.
- Deletes all non-demo rows from `semantic_graph`, `episodic_logs`,
  `memory_events`, `user_bindings`, `user_entities`, and `vec_memory`.
- Creates a fresh `judge-<random>` user id.
- Writes `MNEMOS_DEFAULT_USER_ID=<judge-id>` to `.env`.
- Updates `%USERPROFILE%\.openclaw\mnemos-user-id.txt`.
- Re-registers the `mnemos` MCP server with OpenClaw when the CLI is present.
- Disables OpenClaw's built-in `memory-core` plugin.
- Restarts Docker services unless `-NoDockerRestart` is passed.

By default the script resets the SQLite DB inside the running
`mnemos-memory` Docker container. Pass `-DbPath <path>` only when preparing an
offline database file.

## Preflight

After reset, run:

```powershell
.\scripts\deploy-preflight.ps1
```

This fails if:

- MnemOS or the harness is unhealthy.
- The judge user id is missing or points at a known demo/test namespace.
- The judge namespace already contains memories.
- The `demo-brain` visualizer graph is not populated.
- OpenClaw does not see exactly 7 MnemOS MCP tools.

## Judge URLs

Use these after preflight passes:

```text
OpenClaw chat:     http://<host>:18789
Demo visualizer:   http://<host>:3000?user=demo-brain
Judge visualizer:  http://<host>:3000?user=<judge-id>
```

The judge visualizer will start empty, then show memories forming as the judge
teaches the agent facts through OpenClaw.

## Important Rule

Never seed `demo-brain` into the same user id used by OpenClaw. The setup and
reset scripts route OpenClaw through `MNEMOS_DEFAULT_USER_ID`, while the seeded
visual graph stays under `demo-brain`.
