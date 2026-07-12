# MnemAgent

Persistent, scope-aware memory for coding agents. Submitted to the Qwen Global AI Hackathon, Track 1: MemoryAgent.

[![License: MIT](https://img.shields.io/badge/License-MIT-596b45.svg)](LICENSE)

![MnemAgent logo](docs/assets/logo.jpg)

MnemAgent learns preferences and project conventions across sessions, resolves contradictions inside the correct scope, forgets low-value facts, and makes every coding action visible in a living memory tree. MnemCode is the judge-facing coding workflow built on top: an OpenClaw agent chooses a real issue, works in an isolated no-network container, runs fixed tests, and pauses before opening a draft PR.

![Populated MnemTree with the MnemCode judge workbench](docs/assets/visualizer.png)

## Start here

- Judges: [five-minute walkthrough](docs/JUDGE_GUIDE.md)
- System design: [architecture](docs/ARCHITECTURE.md)
- Measured results: [benchmarks](docs/BENCHMARKS.md)
- Alibaba ECS setup: [deployment guide](docs/DEPLOY_ALIBABA.md)
- Threat model: [security](docs/SECURITY.md)
- Coding-agent demo: [MnemCode demo](docs/MNEMCODE_DEMO.md)
- Submission readiness: [checklist](docs/SUBMISSION_CHECKLIST.md)

## Architecture

```mermaid
flowchart LR
  J["Judge browser"] -->|"HTTPS"| C["Caddy on Alibaba ECS"]
  C --> H["MnemTree + MnemCode workbench"]
  H --> A["OpenClaw judge-coder"]
  A --> M["MnemAgent MCP"]
  A --> B["Signed workspace broker"]
  M --> API["FastAPI memory engine"]
  API --> P[("Postgres + pgvector")]
  API --> Q["Qwen / DashScope"]
  B --> R["No-network runner"]
  B --> G["GitHub draft PR API"]
  API -.-> O[("Alibaba OSS backup")]
```

The public browser can read only `demo-brain`. Interactive runs require a signed judge session and CSRF token. OpenClaw cannot use a host shell, browser, or host filesystem. It receives only MnemAgent memory tools and the broker's structured repository tools. The broker owns the GitHub token; the runner never sees it and has no network.

## What the memory system does

MnemAgent splits each turn into two phases:

1. The waking phase retrieves at most six beliefs, ranks them with UCB, and adds a small memory context to the model call.
2. The dreaming phase extracts durable facts from the same response, applies a salience gate, resolves contradictions, updates utility, decays stale memories, and prunes dead nodes.

Coding memories have explicit scope:

- `core/core` holds durable user preferences.
- `repository/owner/repo` holds project conventions and review corrections.
- Repository retrieval returns at most four repository memories plus two core memories.
- A contradiction in one repository cannot overwrite a fact in another repository or core memory.

The graph API renders no more than 150 individual memories and 120 ambient relationships. Larger archives switch to hybrid or summary mode, while search can fetch a focused memory outside the first page.

## Judge flow

1. Open the deployed URL and inspect the populated MnemTree.
2. Enter the private judge access code in the right-hand MnemCode panel.
3. Start a prepared task. The activity feed shows issue inspection, scoped memory retrieval, file reads, patch application, and tests.
4. Give one review correction. The agent stores it as repository memory.
5. Start a fresh session and run the next task. The Memory tab shows that the correction was retrieved before planning.
6. Review the exact diff and test output. Approve only if both are correct.
7. The broker opens a draft PR. It cannot push to `main` or create a ready-for-review PR.

The final repository acceptance run uses `crankysmh47/WebPort`: the agent selected [issue #11](https://github.com/crankysmh47/WebPort/issues/11), retrieved its repository-scoped correction, wrote regression coverage, implemented the bounded fix with `deepseek-v4-flash`, and produced [tested draft PR #13](https://github.com/crankysmh47/WebPort/pull/13).

## Local setup

Requirements: Docker Desktop or Docker Engine with Compose v2, Git, and 8 GB of free memory.

```bash
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
git switch MnemCode
cp config/env.template .env
```

Set the model keys in `.env`, then build and start:

```bash
docker compose --profile judge-build build workspace-runner
docker compose up -d --build
```

Open `http://localhost:3000/?user=demo-brain`. Local judge access defaults to `mnemcode-local-judge`; cloud mode refuses to start with missing judge secrets.

Run the checks:

```bash
python -m pytest -q
npm test --prefix openclaw-harness
npm test --prefix workspace-runner
npm test --prefix workspace-broker
node openclaw-harness/scripts/check-visualizer.mjs
```

## Cloud deployment

MnemAgent is designed for one low-cost Alibaba ECS instance in Hong Kong. Caddy is the only public service. Postgres, the memory API, MCP, and workspace broker stay on the Compose network or loopback.

```bash
cp .env.cloud.example .env.cloud
# Replace every placeholder and use a fine-grained GitHub token for one demo repository.
./scripts/deploy-cloud.sh
./scripts/verify-cloud.sh
```

The required Alibaba proof is in [cloud sync](mcp-memory-server/src/storage/cloud_sync.py) and the [Alibaba deployment script](scripts/deploy-alibaba.sh). See the deployment guide for the exact ECS, security-group, DNS, TLS, OSS, and spot-instance steps.

## Engineering details

- FastAPI, PostgreSQL 16, pgvector, and a disposable SQLite test adapter
- One model call per normal chat turn; memory extraction shares the response
- UCB exploration plus vector/keyword retrieval and associative graph hops
- Salience-gated writes, atomic scoped contradictions, prospective cue memories, decay, and pruning
- OpenClaw with a per-agent deny policy and filtered MCP tools
- HMAC-signed broker requests with replay protection
- Diff-bound approval tokens that expire after five minutes
- Runner limits: no network, read-only root, non-root user, dropped capabilities, 768 MB RAM, 0.75 CPU, 128 PIDs
- Global model budget: $4.25 soft threshold and $4.50 hard stop, followed by replay mode

## API summary

| Route | Purpose |
|---|---|
| `POST /chat` | Memory-augmented agent turn |
| `POST /api/memory/store` | Salience-gated fact storage |
| `GET /api/memory/search/:uid` | Bounded memory search |
| `GET /api/graph/:uid` | Scalable MnemTree payload |
| `GET /api/events/:uid` | Memory lifecycle events |
| `POST /judge/session` | Signed judge access session |
| `POST /api/judge/runs` | Start an observable OpenClaw run |
| `GET /api/judge/runs/:id` | Read run state and ordered evidence |

## Benchmarks

The repository contains the raw run artifacts and the methodology, not hand-entered scores. Start with [docs/BENCHMARKS.md](docs/BENCHMARKS.md). The submission reports whichever verified MnemBench version is more favorable without mixing v1 and v2 datasets.

## License

MIT. See [LICENSE](LICENSE).
