# MnemBench

MnemBench tests whether an agent's memory changes what it can do later. It is the evaluation layer of MnemAgent, separate from the memory server itself.

## What MnemBench proves

A memory system is useful only when it can recover the right information in a later turn, keep unrelated scopes apart, replace facts that have changed, and let stale information lose influence. A fluent answer is not enough evidence. MnemBench turns those behaviors into repeatable scenarios with a stateless comparison arm.

The benchmark answers a different question from the other project surfaces:

| Surface | Question |
| --- | --- |
| MnemAgent | Can an agent store, retrieve, revise, and forget experience? |
| MnemTree | What does the agent currently remember, and how is it connected? |
| MnemBench | Does that memory improve behavior in later sessions? |
| MnemCode | Can recalled experience guide a real, bounded agent task? |

MnemBench and MnemCode are optional. MnemAgent can be used directly as an MCP memory layer for OpenClaw without either one.

## How it evolved

MnemBench v1 began as a compact, portable benchmark in its own public repository. It established the basic comparison: give one agent persistent memory, leave the other stateless, then test what each can recover.

Building MnemAgent exposed harder cases that simple recall does not cover. Memories can belong to a person or a repository. New evidence can correct an old belief. Frequently used facts should remain easy to retrieve, while stale or low-value facts should fade. Large archives also force the retriever to choose what fits inside a bounded prompt.

MnemBench v2 grew around those cases. It lives beside the memory engine so its scenarios can exercise the same storage, scoping, retrieval, lifecycle, and Postgres/pgvector paths used by the product. The expanded suite adds multi-step and cross-session tasks rather than replacing the small public benchmark's role.

## Version boundary

- **MnemBench v1** is the public [`crankysmh47/MnemBench`](https://github.com/crankysmh47/MnemBench) repository. It remains the portable benchmark and hosts the public issue used by the MnemCode judge flow.
- **MnemBench v2** is the expanded suite under this repository's [`eval/`](../eval/) directory. It can be found at the repo, [`crankysmh47/MnemBench-v2`](https://github.com/crankysmh47/MnemBench-v2).

Keeping that boundary explicit matters. Results from one version should not be presented as results from the other, and a dry-run fixture should never be presented as a live model run.

## What v2 evaluates

The v2 scenarios cover the parts of memory that become visible over time:

- recall after a new session starts;
- continuity across user and project scopes;
- retrieval when relevant facts are surrounded by noise;
- correction and contradiction handling;
- resistance to poisoned or irrelevant memories;
- reinforcement, dormant retrieval, and prospective memory;
- forgetting and lifecycle behavior;
- bounded recall when the archive is larger than the available context.

Each run records probe accuracy and a composite result. Submission-facing runs compare MnemAgent with a stateless baseline using the same provider wherever the saved evidence permits that claim.

## How the four surfaces fit together

MnemBench supplies measurement, while MnemTree supplies inspection. A failed benchmark probe can be investigated in the tree: was the memory absent, scoped incorrectly, superseded, or simply not retrieved?

MnemCode takes the next step. Its prepared issue depends on a repository rule: every MnemBench metric is oriented so `1.0` means best behavior. A judge teaches that rule in one conversation, starts a fresh coding session, and watches OpenClaw retrieve it before producing a test, a bounded patch, and a reviewable diff. The public [issue #1](https://github.com/crankysmh47/MnemBench/issues/1) and [draft PR #2](https://github.com/crankysmh47/MnemBench/pull/2) preserve that acceptance run.

## Evidence and reproduction

The canonical measurements, provider labels, commands, and limitations are in [Benchmark evidence](BENCHMARKS.md). The stable v2 record is in [MnemBench v2 results](evidence/MNEMBENCH_V2_RESULTS.md), and the separate Alibaba Qwen/OpenClaw run is in [Qwen live evidence](evidence/QWEN_OPENCLAW_LIVE.md).

With MnemAgent on port `8000` and the stateless baseline on port `8002`, run both arms with:

```bash
python -m eval.run_benchmark --mode both --server-url http://localhost:8000
```

The historical multi-step suite uses:

```bash
python -m eval.run_agentic_benchmark \
  --mode both \
  --mnemos-url http://localhost:8000 \
  --baseline-url http://localhost:8002
```

`--dry-run` checks the harness and scoring code. It does not measure model quality.

## Current limitations

The saved runs do not support one universal improvement claim. Project continuity produced the largest gain in the live Qwen comparison, while several scenarios tied and some single-turn cases regressed. The stable July 8 Postgres smoke record did not preserve a trustworthy model identifier, so it is storage-path evidence rather than model-specific evidence. Direct memory seeding isolates retrieval quality but does not measure extraction quality.

These constraints are why the repository keeps scenario tables and provider labels instead of publishing only an aggregate score.

## Direction after the hackathon

The next packaging step is to move the expanded suite into a standalone, versioned MnemBench release with immutable run manifests and easier adapters for other memory systems. Until that happens, `eval/` is the source of truth for v2 and the public repository remains v1.
