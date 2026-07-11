# MnemBench Spin-Out Plan (Completed)

The split described here is complete. The original compact suite lives at
`https://github.com/crankysmh47/MnemBench`; the research-scale v2 suite lives at
`https://github.com/crankysmh47/MnemBench-v2`.

MnemBench is now separated into two public repositories: the original compact
suite and the research-scale v2 suite.

## Why Split It

The MnemAgent repository should stay focused on the submitted product:

- OpenClaw agent integration;
- Qwen-compatible memory-augmented chat;
- salience-gated storage;
- UCB retrieval;
- contradiction handling;
- memory visualizer;
- Alibaba Cloud deployment.

MnemBench has a different audience: engineers who want to evaluate any
long-running memory system. External benchmark comparisons, methodology notes,
and broader research positioning belong there instead of inside this product
repo.

## Proposed Repository

Repositories:

```text
https://github.com/crankysmh47/MnemBench
https://github.com/crankysmh47/MnemBench-v2
```

Tagline:

```text
Long-running benchmark for agent memory systems.
```

Minimum contents:

- `README.md` with quick start and scenario table.
- `mnembench/` installable Python package.
- `examples/` with a sample OpenAI-compatible `/chat` adapter.
- `reports/` with example Markdown and JSON outputs.
- `LICENSE` matching the project license.
- `pyproject.toml` for installable CLI packaging.

## Public Narrative

MnemBench tests product-level memory behavior:

- cross-session recall;
- contradiction chains;
- salience gating;
- interference prevention;
- dormant memory retrieval;
- context-window efficiency;
- cross-user isolation.

Its core claim is practical rather than academic: a memory layer should be
judged by whether an agent becomes more useful over time without leaking stale,
irrelevant, or cross-user facts.

## MnemAgent Repo Narrative

Keep this repository's evaluation language narrow:

- "MnemBench companion scenarios"
- "live agentic benchmark"
- "baseline without persistent memory"
- "Track 1 requirements"

Avoid external benchmark comparisons in the MnemAgent repo. Those comparisons can
be added to the standalone MnemBench repository where they are contextually
useful and less distracting.

## Completed Spin-Out Checklist

1. MnemBench v1 is published at `https://github.com/crankysmh47/MnemBench`.
2. MnemBench v2 is published at `https://github.com/crankysmh47/MnemBench-v2`.
3. The v2 package exposes `mnembench --suite v2 --profile ...`.
4. The standalone repository includes an OpenAI-compatible adapter example.
5. MnemAgent keeps only links and submission-facing result summaries.
