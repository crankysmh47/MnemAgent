# MnemAgent

> Persistent, scoped memory for agents: remember what matters, replace what changed, forget what no longer helps, and show the evidence.

[![Track](https://img.shields.io/badge/Qwen%20Global%20AI%20Hackathon-Track%201%3A%20MemoryAgent-6f7f52)](https://qwencloud-hackathon.devpost.com/)
[![Live](https://img.shields.io/badge/live-Alibaba%20Cloud%20ECS-b36b3c)](https://47-237-140-12.sslip.io/?user=demo-brain)
[![License: MIT](https://img.shields.io/badge/license-MIT-596b45)](LICENSE)

<p align="center"><img src="docs/assets/logo.jpg" alt="MnemAgent logo" width="170"></p>

![Populated MnemTree and MnemCode judge workbench](docs/assets/visualizer.png)

## Judge start here

**Submission track:** Track 1 — MemoryAgent

| What judges need | Direct evidence |
| --- | --- |
| Live product | [Open the populated Alibaba Cloud deployment](https://47-237-140-12.sslip.io/?user=demo-brain) |
| Alibaba Cloud proof | [ECS instance, public health, Qwen endpoint code, and topology](docs/CLOUD_PROOF.md) |
| Architecture diagram | [System boundaries, memory lifecycle, and scale design](docs/ARCHITECTURE.md) |
| Exact test path | [Five-minute judge guide](docs/JUDGE_GUIDE.md) |
| Three-minute video | [One-take recording script](docs/DEMO_VIDEO_PRODUCTION_SCRIPT.md) |
| Measured results | [MnemBench evidence and honest limitations](docs/BENCHMARKS.md) |
| Agentic coding proof | [Public issue #1](https://github.com/crankysmh47/MnemBench/issues/1), [agent-created draft PR #2](https://github.com/crankysmh47/MnemBench/pull/2), and [MnemCode design](docs/MNEMCODE_DEMO.md) |
| Source and license | This public repository and the [MIT License](LICENSE) |

The public page opens on `demo-brain`, a populated read-only archive. Judges can understand the memory model before entering the private code from Devpost or spending sponsored model capacity.

## Three-minute product path

1. Search the populated MnemTree for `backend framework`, select a leaf, and inspect its relationship chain.
2. Enter the private judge code from Devpost. The server creates a random namespace with a signed seven-day session.
3. Tell the agent: `For MnemBench, keep every metric oriented so 1.0 means best behavior.`
4. Ask the rule again. The reply comes from a fresh OpenClaw conversation, while MnemAgent retrieves the repository-scoped memory.
5. Start public [MnemBench issue #1](https://github.com/crankysmh47/MnemBench/issues/1). The agent inspects the defect, retrieves the rule, adds a regression test, fixes the inverted contradiction score, and runs two fixed Python commands in a no-network container.
6. Review Activity, Memory, Changes, and test output. A draft pull request can open only after both checks pass and a human explicitly approves the exact diff.

Allowance per judge: 30 chat turns, five coding runs, and five draft-PR approvals. The session lasts seven days; the quota does not refresh with time.

## What the project proves

### MnemTree: inspect memory

The visualizer presents beliefs as a living tree rather than an opaque vector store. Search can retrieve memories outside the initial graph page. Large archives become progressively summarized: above 120 memories the renderer switches to a hybrid view, and above 500 it becomes summary-first. A graph response is capped at 150 memories and 120 ambient relationships.

### MnemBench: measure memory

The original public [MnemBench v1 repository](https://github.com/crankysmh47/MnemBench) provides a portable benchmark and the public coding task. The expanded MnemBench v2 suite lives only in this repository under [`eval/`](eval/); it is not a second public repository.

The conservative July 8 Postgres-backed v2 smoke run scored **66.7% versus 23.7%** average probe accuracy and **76.9% versus 38.5%** pass rate against the same stateless baseline. In a separate live Qwen run, project continuity scored **91.7% versus 8.3%**. Project continuity drives most of that run's aggregate gain; weaker and tied scenarios remain in the evidence. See [BENCHMARKS.md](docs/BENCHMARKS.md).

### MnemCode: use memory

MnemCode gives the agent one deliberately narrow, public coding task. The GitHub token stays in the private broker, never in the browser, model, or runner. The runner has no network and can edit only bounded source and test paths. It executes only:

```text
python -m pytest -q tests/test_scoring.py
python -m pytest -q
```

The current task fixes a real benchmark integrity bug: a correctly resolved contradiction was inverted while aggregating the `contradiction_score`. The memory rule, regression test, source diff, and approval boundary are all visible in one judge workbench.

The July 20 acceptance run used two fresh OpenClaw conversations, recovered the repository rule, added three regression tests, passed both fixed commands, and opened [draft PR #2](https://github.com/crankysmh47/MnemBench/pull/2) only after explicit approval.

MnemCode and MnemBench are proof surfaces, not dependencies. A user can run ordinary OpenClaw with the MnemAgent MCP servers and retain OpenClaw's broader tool ecosystem.

## Architecture

![MnemAgent architecture](docs/assets/architecture.png)

Each turn has two phases:

1. **Waking:** hybrid vector and keyword retrieval, UCB exploration, scoped associative hops, and at most six beliefs injected into context.
2. **Dreaming:** structured fact extraction, salience gating, scoped contradiction replacement, utility feedback, decay, pruning, and lifecycle events.

Core memories use `core/core`. Project memories use `repository/owner/repository`. One scope cannot overwrite another. Retrieval reserves up to four repository memories and two core memories, so prompt overhead stays bounded as storage grows.

The standard Qwen path uses Alibaba Cloud Model Studio's OpenAI-compatible endpoint. The public sponsored judge runtime currently uses DeepSeek V4 Flash so judges need no model key. Those evidence paths are labelled separately; no DeepSeek run is presented as a Qwen result.

## Repository map

| Path | Start here when reviewing |
| --- | --- |
| [`mcp-memory-server/`](mcp-memory-server/) | Memory API, retrieval, consolidation, decay, pruning, and storage |
| [`mcp-server/`](mcp-server/) | MCP interface consumed by OpenClaw |
| [`openclaw-harness/`](openclaw-harness/) | Judge UI, sponsored chat, MnemTree, quotas, and evidence stream |
| [`eval/`](eval/) | Expanded MnemBench v2 scenarios and runners |
| [`workspace-broker/`](workspace-broker/) | GitHub credentials, isolated workspaces, approvals, and PR publication |
| [`workspace-runner/`](workspace-runner/) | Read-only, no-network fixed-command sandbox |
| [`config/openclaw/`](config/openclaw/) | OpenClaw agent contracts and MCP wiring |
| [`docs/evidence/`](docs/evidence/) | Stable benchmark records and submission evidence |
| [`scripts/`](scripts/) | Local demo, cloud deployment, verification, and smoke tests |

## Run locally

Requirements: Docker Desktop or Docker Engine with Compose v2, Git, GitHub CLI, and about 8 GB of free memory.

```powershell
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
git switch MnemCode
Copy-Item config/env.template .env
# Add a supported model key to .env, then authenticate GitHub CLI:
gh auth login
.\scripts\start-demo.ps1
```

`start-demo.ps1` reads the GitHub token from the GitHub CLI keyring for this process. It does not write the token into the repository. Open `http://localhost:3000/?user=demo-brain`.

Local judge access defaults to `mnemcode-local-judge`. Cloud mode refuses placeholder or missing secrets. Judges never need local setup or their own credentials; these commands are for maintainers reproducing the complete stack.

Run every verification suite:

```powershell
python -m pytest -q
npm test --prefix openclaw-harness
npm test --prefix workspace-broker
npm test --prefix workspace-runner
node openclaw-harness/scripts/check-visualizer.mjs
```

## Security boundary

- Signed HttpOnly judge cookie, same-origin CSRF protection, IP lockout, and durable seven-day quota state
- OpenClaw denial of host shell, filesystem, browser, and generic web tools
- HMAC-authenticated broker requests with timestamp and nonce replay protection
- Five-file and 500-line patch limits
- Non-root, read-only, no-network runner with dropped capabilities and resource limits
- Five-minute approval token bound to the exact diff and pull-request metadata
- Repository-limited GitHub token held only by the broker

See [SECURITY.md](docs/SECURITY.md) for the threat model and [docs/README.md](docs/README.md) for the complete documentation index.

## License

MnemAgent is open source under the [MIT License](LICENSE).
