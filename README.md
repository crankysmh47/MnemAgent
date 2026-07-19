# MnemAgent

> A persistent memory control plane for agents that learns what matters, replaces what changed, forgets what no longer helps, and shows its work.

[![Track](https://img.shields.io/badge/Qwen%20Global%20AI%20Hackathon-Track%201%3A%20MemoryAgent-6f7f52)](https://qwencloud-hackathon.devpost.com/)
[![Live](https://img.shields.io/badge/live-Alibaba%20Cloud%20ECS-b36b3c)](https://47-237-140-12.sslip.io/?user=demo-brain)
[![License: MIT](https://img.shields.io/badge/license-MIT-596b45)](LICENSE)

<p align="center">
  <img src="docs/assets/logo.jpg" alt="MnemAgent logo" width="150">
</p>

Agents do not become dependable by remembering everything. They become dependable by remembering the right things: a user's stable preferences, a project's conventions, the correction that replaced an old belief, and the unfinished intention that matters now. MnemAgent gives OpenClaw that selective, inspectable memory layer.

![Populated MnemTree and MnemCode judge workbench](docs/assets/visualizer.png)

## Submission links

| Start here | Link |
| --- | --- |
| Live deployment | [Open the populated MnemTree](https://47-237-140-12.sslip.io/?user=demo-brain) |
| Judge walkthrough | [Test the complete flow in about five minutes](docs/JUDGE_GUIDE.md) |
| Architecture | [Diagram and engineering design](docs/ARCHITECTURE.md) |
| Alibaba proof | [Running ECS evidence and Qwen Cloud code links](docs/CLOUD_PROOF.md) |
| Benchmarks | [Live results, reproduction, and limitations](docs/BENCHMARKS.md) |
| Agentic proof | [MnemCode and the validated WebPort PR](docs/MNEMCODE_DEMO.md) |
| Open source | [MIT license](LICENSE) |

**Submission track:** Track 1 — MemoryAgent.

## Judge it in five minutes

1. Open the live URL. It lands on `demo-brain`, a populated, read-only archive—no setup or model spend required.
2. Search for `backend framework`, select a leaf, and inspect the relationship chain in the Memory Lens.
3. Enter the private judge code supplied in Devpost. This creates a random namespace valid for seven days, with 30 chat turns, five coding runs, and five draft-PR approvals.
4. Teach a repository convention. Ask for it again: the second message runs in a fresh OpenClaw session, but the answer and growing tree retain the memory.
5. Start the prepared WebPort task. Watch the agent inspect issue #14, retrieve scoped memory, edit bounded files, run fixed tests, and stop for review.
6. Inspect the exact diff and test output. Only an explicit checkbox and approval can open a draft pull request.

The public tree and [validated draft PR #15](https://github.com/crankysmh47/WebPort/pull/15) remain available if the sponsored model allowance or spot instance is interrupted.

## One system, three kinds of proof

### MnemTree — see what the agent remembers

The visualizer turns memory into an inspectable living archive. Search scales beyond the first graph page; focused memories can be fetched outside the initial result; archives above 120 memories switch to hybrid rendering, and those above 500 become summary-first. The API never sends more than 150 individual memories and 120 ambient relationships in one graph response.

### MnemBench — measure whether memory helps

MnemBench exercises cross-session recall, contradiction handling, interference, prospective memory, overload resistance, learning, decay, and pruning. The current v2 suite lives under `eval/`; the original public v1 benchmark remains a [separate repository](https://github.com/crankysmh47/MnemBench).

The conservative July 8 Postgres-backed v2 smoke run scored **66.7% vs 23.7%** average probe accuracy and **76.9% vs 38.5%** pass rate against the same stateless baseline. A separate live Qwen run's clearest result was project continuity: **91.7% vs 8.3%**. That scenario drives most of the aggregate gain; tied and weaker scenarios are documented rather than hidden. See [benchmark evidence](docs/BENCHMARKS.md).

### MnemCode — watch memory change an agent's work

MnemCode is the bounded coding demonstration built on OpenClaw. In the acceptance run, the agent used repository-scoped memory while fixing [WebPort issue #14](https://github.com/crankysmh47/WebPort/issues/14), added a regression test first, passed the focused and full unit commands, and prepared [draft PR #15](https://github.com/crankysmh47/WebPort/pull/15). The runner has no network, receives no GitHub token, and cannot publish without human approval.

MnemCode is a proof surface, not a requirement. You can discard both MnemCode and MnemBench, attach the MnemAgent MCP servers to an ordinary OpenClaw deployment, and keep OpenClaw's wider integrations and tool ecosystem. Broader one-click repository packs are in progress; the current WebPort path is intentionally narrow and working.

## Architecture

![MnemAgent architecture](docs/assets/architecture.png)

The normal Qwen path uses Alibaba Cloud Model Studio's OpenAI-compatible endpoint. The public sponsored judge path currently uses DeepSeek V4 Flash so judges can test without supplying a key; the two evidence paths are labelled separately throughout the repository.

MnemAgent processes each turn in two phases:

1. **Waking:** vector and keyword retrieval, UCB exploration, scoped associative hops, and at most six beliefs injected into the model context.
2. **Dreaming:** structured fact extraction from the same response, salience gating, scoped contradiction replacement, utility feedback, decay, pruning, and lifecycle events.

Core memories (`core/core`) and repository memories (`repository/owner/repo`) cannot overwrite one another. Retrieval reserves up to four repository memories plus two core memories, keeping prompt overhead constant as the archive grows.

## Track 1 fit

| Requirement | MnemAgent mechanism |
| --- | --- |
| Persistent, cross-session memory | Postgres semantic graph, episodic log, OpenClaw MCP tools, and stable user namespaces |
| Accumulated experience | Every successful turn can consolidate durable beliefs and update their learned utility |
| User preferences | Core and repository scopes separate global preferences from project-specific rules |
| Efficient storage | A salience gate rejects low-conviction noise before it reaches the graph |
| Limited-context recall | Hybrid retrieval and UCB exploration inject no more than six beliefs |
| Timely forgetting | Inactive memories decay; nodes below the prune threshold are deleted |
| Correcting stale facts | Scoped uniqueness replaces only the conflicting belief and records the lifecycle event |
| Better decisions | MnemCode makes retrieved guidance visible beside the actual code diff and tests |

## Cloud deployment

The live submission runs on one Alibaba Cloud ECS pay-as-you-go spot instance in Singapore. Caddy is the only public service. OpenClaw, the MCP server, memory API, workspace broker, runner control plane, and Postgres/pgvector stay behind the Docker network or loopback boundary.

- Public URL: [https://47-237-140-12.sslip.io/](https://47-237-140-12.sslip.io/)
- Workbench screenshot and live checks: [docs/CLOUD_PROOF.md](docs/CLOUD_PROOF.md)
- Qwen Cloud code proof: [mcp-memory-server/src/config.py](mcp-memory-server/src/config.py)
- Reproduction: [docs/DEPLOY_ALIBABA.md](docs/DEPLOY_ALIBABA.md)

## Run locally

Requirements: Docker Engine/Desktop with Compose v2, Git, and roughly 8 GB of free memory.

```bash
git clone https://github.com/crankysmh47/MnemAgent.git
cd MnemAgent
git switch MnemCode
cp config/env.template .env
# Add a supported model key to .env.
docker compose --profile judge-build build workspace-runner
export JUDGE_GITHUB_TOKEN="$(gh auth token)"  # optional MnemCode publication
docker compose up -d --build
```

Open `http://localhost:3000/?user=demo-brain`. Local judge access defaults to `mnemcode-local-judge`; cloud mode refuses to start with placeholder or missing secrets.

Run the verification suites:

```bash
python -m pytest -q
npm test --prefix openclaw-harness
npm test --prefix workspace-broker
npm test --prefix workspace-runner
node openclaw-harness/scripts/check-visualizer.mjs
```

## Security boundary

- Signed HttpOnly judge cookie, same-origin CSRF, IP lockout, and seven-day durable quota state
- OpenClaw deny policy for host shell, filesystem, browser, and generic web tools
- HMAC-authenticated broker requests with nonce and timestamp replay protection
- Five-file/500-line patch bounds and fixed argv test commands
- Non-root, read-only, no-network runner with dropped capabilities and resource limits
- Five-minute approval token bound to the exact diff and PR metadata
- Fine-grained GitHub token held only by the private broker

See [docs/SECURITY.md](docs/SECURITY.md) for the full threat model.

## What comes next

The next product step is to make MnemCode's safety model available to more repositories through pre-reviewed task packs and configurable test policies. Other natural extensions include more MCP tool packs, managed Postgres/RDS, organization-scoped memory, and learned retention policies. The core memory MCP remains usable today without those additions.

## License

MnemAgent is open source under the [MIT License](LICENSE).
