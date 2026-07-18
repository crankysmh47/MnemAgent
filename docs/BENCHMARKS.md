# Benchmark evidence

The headline result is the latest documented live Postgres-backed MnemBench v2 smoke run from July 8, 2026. MnemBench v2 is currently an evaluation suite in this repository, not a separate public repository. The original public benchmark is [MnemBench](https://github.com/crankysmh47/MnemBench); the two should not be confused. The detailed stable report is [retained here](archive/MNEMBENCH_RESULTS.md); raw machine-local outputs are not committed.

| Metric | MnemAgent | Stateless baseline | Difference |
| --- | ---: | ---: | ---: |
| Average probe score | 66.7% | 23.7% | +43.0 points |
| Average composite | 0.622 | 0.399 | +0.223 |
| Pass rate | 76.9% | 38.5% | +38.4 points |
| Scenarios improved | 8 of 13 | — | — |

The run used the production Postgres/pgvector path. Its strongest categories were cross-session recall, overload resistance, dormant retrieval, user continuity, poison resistance, learning, and prospective memory.

An earlier 10-scenario full-suite run reported a 99.0% probe score against a 45.8% baseline. It is retained as historical evidence, not the headline, because the newer 13-scenario smoke profile covers more behaviors and is the more conservative claim.

## Limits of the evidence

- Model behavior and provider latency vary between runs.
- Dry-run fixture scores test the harness, not model quality, and are not used above.
- Ignored machine-local `eval/results` files are not a substitute for reproducible commands.
- Before submission, the deployed Alibaba instance should run the documented smoke profile and attach its generated JSON/Markdown report to the release.

## Reproduce

Start MnemAgent and the stateless baseline, then run the v2 evaluation entry point:

```bash
python -m eval.run_eval_v2 --help
```

Use the same provider and model for both arms. Record the exact model, region, scenario profile, timestamp, probe score, composite score, and pass rate in the release notes.
