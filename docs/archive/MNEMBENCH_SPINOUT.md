# MnemBench Spin-Out Plan

MnemBench should be positioned as a separate public repository after the MnemAgent
submission package is stable.

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

Name:

```text
mnembench
```

Tagline:

```text
Long-running benchmark for agent memory systems.
```

Minimum contents:

- `README.md` with quick start and scenario table.
- `mnembench/` Python package copied from `eval/mnembench`.
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

## Spin-Out Checklist

1. Copy `eval/mnembench` into a new repository as the package root.
2. Convert imports from `eval.mnembench` to `mnembench`.
3. Add `pyproject.toml` with a `mnembench` console script.
4. Add one adapter example for MnemAgent and one generic OpenAI-compatible server.
5. Move external benchmark comparison notes into the new README.
6. Publish MnemBench separately after the MnemAgent hackathon submission is final.
7. In MnemAgent, keep only a short link: "Benchmarked with MnemBench."
