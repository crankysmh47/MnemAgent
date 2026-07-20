# Live Qwen + OpenClaw evidence

**Date:** June 13, 2026  
**Model:** `qwen-plus`  
**Provider:** Alibaba Cloud DashScope, Singapore  
**Mode:** live API calls, not dry-run fixtures

## MCP store and cross-session recall

OpenClaw used the seven registered MnemAgent MCP tools. One session stored two explicit beliefs for `demo-qwen`:

```text
user -> affiliation -> FAST student
user -> backend_preference -> Python for backend APIs
```

A different OpenClaw session called `memory_search` and `memory_dump` for the same exact user ID and recovered both beliefs with high confidence. This is direct MCP evidence: the result came from the memory tools rather than the model's natural-language claim that it remembered.

## Multi-step agentic comparison

| Scenario | Capability | MnemAgent | Baseline | Difference |
| --- | --- | ---: | ---: | ---: |
| Compound stack | Accumulated project preferences | 100.0% | 100.0% | 0.0 |
| Contradiction arc | Newer facts replace stale ones | 75.0% final probes | 75.0% | 0.0 |
| Salience noise | Reject low-conviction statements | 75.0% | 75.0% | 0.0 |
| Project continuity | Cross-session project context | 91.7% | 8.3% | +83.4 points |
| **Average** |  | **79.2%** | **64.6%** | **+14.6 points** |

Project continuity spans eight steps across fresh sessions and teaches arbitrary project details the model cannot guess. It is the strongest evidence for the Track 1 value proposition. It also drives nearly all of the aggregate gain, which is why the tied scenarios remain visible here.

## Counter-evidence retained

The same evaluation period's 25-scenario single-turn suite scored MnemAgent at 43.7% and the baseline at 45.0%. MnemAgent led in contradiction handling (+15 points) and forgetting (+6.7 points), while the baseline led recall, interference, and context categories.

This does not invalidate the cross-session result. It narrows the claim: MnemAgent is designed to preserve and correct experience across sessions, not to guarantee that every isolated response beats a capable stateless model.

## Extraction limitation

Structured `<memory_update>` extraction depends on the configured model following the output contract. The implementation accepts XML blocks, JSON lines, code blocks, bare JSON, and multiple facts, but extraction quality can still vary by model. Direct-seed benchmark modes isolate retrieval from this separate concern and are labelled accordingly.
