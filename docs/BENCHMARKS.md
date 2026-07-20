# Benchmark evidence

MnemAgent keeps benchmark claims deliberately separate by suite, model, and execution mode. Fixture dry runs validate the harness; they are not presented as model-quality results.

## Headline: live Postgres-backed MnemBench v2 smoke run

The latest stable 13-scenario smoke record was run on July 8, 2026 against the production Postgres/pgvector path and a no-memory baseline.

| Metric | MnemAgent | Stateless baseline | Difference |
| --- | ---: | ---: | ---: |
| Average probe score | 66.7% | 23.7% | +43.0 points |
| Average composite | 0.622 | 0.399 | +0.223 |
| Pass rate | 76.9% | 38.5% | +38.4 points |
| Scenarios improved | 8 of 13 | — | — |

The strongest categories were cross-session recall, overload resistance, dormant retrieval, user continuity, poison resistance, learning, and prospective memory. The stable record did not preserve a trustworthy model identifier, so this run is not labelled as Qwen evidence.

The detailed record is [docs/evidence/MNEMBENCH_V2_RESULTS.md](evidence/MNEMBENCH_V2_RESULTS.md).

## Live Qwen result: project continuity

On June 13, 2026, OpenClaw and MnemAgent were exercised with `qwen-plus` through Alibaba Cloud DashScope in Singapore. The multi-step suite scored **79.2% vs 64.6%** overall, but the gain was not uniform:

| Scenario | MnemAgent | Baseline | Difference |
| --- | ---: | ---: | ---: |
| Compound stack | 100.0% | 100.0% | 0.0 |
| Contradiction arc | 75.0% final probes | 75.0% | 0.0 |
| Salience noise | 75.0% | 75.0% | 0.0 |
| Project continuity | 91.7% | 8.3% | +83.4 points |

Project continuity drives the aggregate advantage. That is the most defensible result because it spans fresh sessions and uses arbitrary project details the stateless model cannot infer. The same evaluation also recorded a slight overall loss on a 25-scenario single-turn suite, while MnemAgent led on contradiction and forgetting. Those limitations matter: MnemAgent's value is persistent experience, not making every isolated answer better.

The full live Qwen record and exact OpenClaw store/recall evidence are in [docs/evidence/QWEN_OPENCLAW_LIVE.md](evidence/QWEN_OPENCLAW_LIVE.md).

## Provider portability check

A separate July 9 live DeepSeek V4 Flash v2 smoke run produced:

| Metric | MnemAgent | Stateless baseline | Difference |
| --- | ---: | ---: | ---: |
| Average probe score | 66.7% | 27.6% | +39.1 points |
| Average composite | 0.622 | 0.414 | +0.208 |
| Pass rate | 76.9% | 46.2% | +30.7 points |

This supports a narrower claim: the memory advantage survives a provider change. It is not used as Qwen Cloud evidence.

## MnemBench v1 and v2 are not the same repository

- **MnemBench v1:** the original compact public benchmark at [crankysmh47/MnemBench](https://github.com/crankysmh47/MnemBench).
- **MnemBench v2:** the expanded evaluation code currently under this repository's [`eval/`](../eval/) directory. It is not a separate public repository.

MnemBench is optional. A user may ignore the suite entirely and run OpenClaw with the MnemAgent MCP servers as its memory layer.

## Reproduce

Start MnemAgent on `:8000` and the stateless baseline on `:8002`, configure the same model for both arms, then run:

```bash
python -m eval.run_benchmark --mode both --server-url http://localhost:8000
```

For the historical multi-step suite:

```bash
python -m eval.run_agentic_benchmark \
  --mode both \
  --mnemos-url http://localhost:8000 \
  --baseline-url http://localhost:8002
```

Use `--dry-run` only to validate scoring and report generation. A submission result should record the timestamp, suite/profile, exact model and endpoint region, storage backend, seed method, probe score, composite score, pass rate, and raw report hash.

## Limits

- Provider behavior and latency vary across runs.
- The July 8 stable summary lacks a preserved model identifier.
- Direct memory seeding isolates retrieval quality but does not measure model extraction reliability.
- Keyword probes are imperfect proxies for response quality.
- Aggregate gains can hide scenario ties or regressions; scenario tables are therefore retained.
- Machine-local raw outputs are ignored because they may contain transient identifiers and large provider traces. Stable evidence records are committed instead.
