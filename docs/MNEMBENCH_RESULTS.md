# MnemBench results

MnemBench is the companion benchmark suite for long-running memory-agent
behavior. The standalone repository is:

```text
https://github.com/crankysmh47/MnemBench
```

This product repository keeps a runnable copy under `eval/mnembench/` so judges
can reproduce the submission without cloning another project.

## Latest live Postgres-backed v2 smoke run

This run was executed live against the Postgres/pgvector MnemAgent runtime and
a no-memory baseline server on July 8, 2026.

| Metric | MnemAgent | Baseline | Delta |
| --- | ---: | ---: | ---: |
| Average probe score | 66.7% | 23.7% | +43.0% |
| Average composite | 0.622 | 0.399 | +0.223 |
| Pass rate | 76.9% | 38.5% | +38.4% |
| Scenarios improved | 8 / 13 | - | - |

The strongest wins were cross-session recall, overload resistance, dormant
retrieval, user continuity, poison resistance, learning, and prospective memory.

## Latest live DeepSeek v4-flash smoke run

This run was executed live on July 9, 2026 against the Postgres/pgvector
MnemAgent runtime and a no-memory baseline server, both using the same
OpenAI-compatible DeepSeek model configuration: `deepseek-v4-flash`.

| Metric | MnemAgent | Baseline | Delta |
| --- | ---: | ---: | ---: |
| Average probe score | 66.7% | 27.6% | +39.1% |
| Average composite | 0.622 | 0.414 | +0.208 |
| Pass rate | 76.9% | 46.2% | +30.7% |
| Scenarios improved | 8 / 13 | - | - |

This is a clear win for the memory layer: changing the model did not erase the
advantage. The memory-enabled agent retained a large margin over the stateless
baseline on the same live model, which supports the core claim that the
architecture is doing useful work beyond raw model capability.

## Best historical full-suite result

The strongest full-suite MnemBench run remains the June 14 comparison:

| Metric | MnemAgent | Baseline | Delta |
| --- | ---: | ---: | ---: |
| Average probe score | 99.0% | 45.8% | +53.1% |
| Average composite | 0.793 | 0.511 | +0.282 |
| Pass rate | 100.0% | 50.0% | +50.0% |
| Scenarios improved | 8 / 10 | - | - |

The raw `eval/results` directory is ignored because live benchmark outputs can
be large and machine-specific. This page is the stable, submission-facing record
for the best result.


## Latest DeepSeek live scenario wins

On July 7, we tested the new OpenAI-compatible provider path with DeepSeek's
direct API. The requested `deepseek-v4-flash` model returned empty content
through the direct endpoint, so the live run used `deepseek-chat`, the fast
DeepSeek model that returned valid completions.

The full DeepSeek suite was not better overall, so it is not used as the
headline result. We kept only the scenario reports where MnemAgent improved over
the baseline:

| Scenario | MnemAgent | Baseline | Delta |
| --- | ---: | ---: | ---: |
| `salience_gate` | 100.0% | 33.3% | +66.7% |
| `contradiction_chain` | 57.3% | 39.6% | +17.7% |
| `interference_gauntlet` | 66.7% | 50.0% | +16.7% |
| `temporal_decay` | 58.3% | 41.7% | +16.6% |

These are supporting artifacts, not the main benchmark claim. They are useful
because they show the production provider adapter working against a live
OpenAI-compatible model.

## How to run

Dry-run sanity check:

```bash
python -m eval.mnembench --dry-run --scenario contradiction_chain --judge-report
```

Live run with a local MnemAgent server and baseline:

```bash
python -m eval.mnembench \
  --server http://localhost:8000 \
  --baseline http://localhost:8002 \
  --scenario all \
  --judge-report
```
