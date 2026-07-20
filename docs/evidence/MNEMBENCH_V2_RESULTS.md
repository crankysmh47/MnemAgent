# MnemBench v2 stable results

This is the stable, submission-facing record of the live v2 comparisons used by MnemAgent. MnemBench v2 currently lives under this repository's `eval/` package. It is distinct from the original public [MnemBench v1](https://github.com/crankysmh47/MnemBench) repository.

## July 8, 2026 — Postgres/pgvector smoke profile

| Metric | MnemAgent | Baseline | Delta |
| --- | ---: | ---: | ---: |
| Average probe score | 66.7% | 23.7% | +43.0 points |
| Average composite | 0.622 | 0.399 | +0.223 |
| Pass rate | 76.9% | 38.5% | +38.4 points |
| Scenarios improved | 8 / 13 | — | — |

The run used the production Postgres/pgvector path. Strong categories were cross-session recall, overload resistance, dormant retrieval, user continuity, poison resistance, learning, and prospective memory. The stable report did not retain a trustworthy model identifier, so it must not be cited as model-specific evidence.

## July 9, 2026 — DeepSeek V4 Flash portability run

Both arms used the same official OpenAI-compatible DeepSeek configuration.

| Metric | MnemAgent | Baseline | Delta |
| --- | ---: | ---: | ---: |
| Average probe score | 66.7% | 27.6% | +39.1 points |
| Average composite | 0.622 | 0.414 | +0.208 |
| Pass rate | 76.9% | 46.2% | +30.7 points |
| Scenarios improved | 8 / 13 | — | — |

This is portability evidence, not Qwen Cloud evidence.

## Historical full-suite record

The June 14 ten-scenario record reported 99.0% vs 45.8% probe score and 100% vs 50% pass rate. It is not the headline because the newer 13-scenario smoke profile is broader and more conservative.

## Reproduction contract

Run both arms against the same model/provider and retain:

- UTC timestamp;
- git commit;
- suite and scenario profile;
- exact model and base URL region;
- storage backend;
- direct-seed versus extraction mode;
- JSON/Markdown outputs and hashes.

Dry-run fixtures validate harness behavior only and must be labelled as fixtures.
