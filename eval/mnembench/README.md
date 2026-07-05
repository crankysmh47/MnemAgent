# MnemBench

Benchmark the memory capabilities of LLM-powered agents — 10 scenarios that test how well a system remembers, forgets, and connects facts across sessions.

## What is MnemBench?

MnemBench is a standalone benchmark suite for evaluating memory-augmented language model agents. It runs long, multi-step scenarios against any OpenAI-compatible API and measures how well the system handles:

- **Recall** across many sessions (10 facts, 10 sessions, one unified probe)
- **Contradiction resolution** through chains of updates (A→B→C→D)
- **Salience gating** — storing definitive facts while rejecting hedged statements
- **Interference prevention** — preventing stale facts from leaking after updates
- **Dormant resurrection** — surfacing facts after long distraction (UCB exploration)
- **Overload resistance** — keeping high-conviction facts under memory pressure
- **Multi-hop association** — traversing knowledge graph edges (A→B→C→D)
- **Temporal decay** — oldest facts lose confidence, recent ones persist
- **Context window efficiency** — injected memory stays O(1) as the graph grows
- **Cross-user isolation** — User A's facts don't leak into User B's probes

It's designed to work with **any memory system** that exposes an OpenAI-compatible chat endpoint. If you can POST to `/chat` and optionally store facts via `/api/memory/store`, you can benchmark it.

## Why MnemBench?

Existing memory benchmarks tend to be narrow. They test one thing (a single recall probe) and they don't simulate the kind of long-running, multi-turn workflows that real agents deal with. MnemBench takes the opposite approach: each scenario is a mini-workflow that chains multiple teach/probe/contradict steps together, the way a real agent would accumulate and update knowledge over time.

**What makes it different:**

- **10 scenarios, not 1**. Each targets a different failure mode for memory systems.
- **Multi-dimensional scoring**. You get separate scores for recall, contradiction handling, salience, interference, and latency — not just one number.
- **Works with any API**. Standard OpenAI chat format. No SDK lock-in.
- **Dry-run mode**. Test the harness before you point it at a server. Useful for CI/CD.
- **Comparison mode**. Run with-memory and without-memory side by side to isolate the memory layer's contribution.

If your system talks to an LLM with a memory layer bolted on, MnemBench will tell you where the weak spots are.

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Scenarios](#scenarios)
- [CLI Reference](#cli-reference)
- [Output](#output)
- [Scoring Dimensions](#scoring-dimensions)
- [Adding Scenarios](#adding-scenarios)
- [License](#license)

## Installation

This package lives inside the `eval/` directory of the MnemAgent project. There's nothing extra to install:

```bash
# From the project root
cd eval/mnembench
```

The package depends on `httpx` for API calls. If you're running outside the project's virtualenv:

```bash
pip install httpx
```

Python 3.10+ required.

## Quick Start

### List available scenarios:

```bash
python -m eval.mnembench --list
```

You'll see output like:

```
ID                             Name                               Category        Steps
------------------------------ ---------------------------------- --------------- -----
ten_session_recall             Ten-Session Recall                 recall          11
contradiction_chain            Contradiction Chain                contradiction   8
salience_gate                  Salience Gate                      salience        13
interference_gauntlet          Interference Gauntlet              interference    13
dormant_resurrection           Dormant Resurrection               forgetting      18
overload_resistance            Overload Resistance                salience        31
multi_hop_association          Multi-Hop Association              context         6
temporal_decay                 Temporal Decay                     forgetting      9
context_window_efficiency      Context Window Efficiency          context         52
cross_user_isolation           Cross-User Isolation               context         10
```

### Run in dry-run mode (no API calls):

```bash
python -m eval.mnembench --dry-run
```

This uses pre-recorded fixture responses so you can see the output format without spinning up a server.

### Run against a memory-enabled server:

```bash
python -m eval.mnembench \
  --server http://localhost:8000 \
  --baseline http://localhost:8002
```

### Generate a judge-facing summary:

```bash
python -m eval.mnembench \
  --server http://localhost:8000 \
  --baseline http://localhost:8002 \
  --judge-report
```

### Run one scenario with repeats:

```bash
python -m eval.mnembench \
  --server http://localhost:8000 \
  --scenario ten_session_recall \
  --repeat 3
```

### Run with-memory only (skip baseline):

```bash
python -m eval.mnembench \
  --server http://localhost:8000 \
  --no-baseline
```

## Scenarios

Each scenario is a sequence of teach, probe, contradict, and distract steps. Here's what they test:

| Scenario | What it Tests | Steps | Key Metric |
|----------|---------------|-------|------------|
| `ten_session_recall` | Recall 10 facts taught across 10 separate sessions | 11 | Recall precision |
| `contradiction_chain` | Resolve 3 sequential contradictions (A→B→C→D) | 8 | Contradiction score |
| `salience_gate` | Store 5 definite facts, reject 5 hedged ones | 13 | Salience F1 |
| `interference_gauntlet` | Teach 5 facts, update all 5, verify no leakage | 13 | Interference rate |
| `dormant_resurrection` | Teach 1 fact, 15 distractor turns, then probe | 18 | Recall precision |
| `overload_resistance` | 30 rapid-fire facts, probe high-conviction survival | 31 | Salience F1 |
| `multi_hop_association` | Chain A→B→C→D, probe A→D | 6 | Recall precision |
| `temporal_decay` | Staggered timestamps, older facts should decay | 9 | Interference rate |
| `context_window_efficiency` | 50 facts taught, measure injected context size | 52 | Latency / token count |
| `cross_user_isolation` | Separate facts for User A and B, no cross-leakage | 10 | Recall precision |

### Scenario Categories

- **recall**: Pure cross-session recall. Teach across sessions, probe for all facts.
- **contradiction**: Fact updates. Old values must not survive.
- **salience**: Hedged vs definitive statements. Memory precision under noise.
- **interference**: Proactive and retroactive interference. 5 simultaneous updates.
- **forgetting**: Temporal decay and dormant fact resurrection under distraction.
- **context**: Associative hops, context efficiency, and user isolation.

### Detailed Breakdown

**ten_session_recall** — Teaches one infrastructure fact per session (Docker, Kubernetes, Go, gRPC, etc.) across 10 sessions. Session 11 asks "Describe our full infrastructure stack." A perfect score requires recalling all 10 facts.

**contradiction_chain** — Three sequential migrations: Express→Fastify→Koa→Hono. After the final probe, the system must know "Hono" and not mention Express, Fastify, or Koa.

**salience_gate** — Interleaves 5 hedged statements ("maybe we could try Vue") with 5 definitive statements ("we always use TypeScript"). Probes verify that definitive facts are stored and hedged ones are rejected.

**interference_gauntlet** — Five parallel facts (OS version, Python version, database, hosting, framework) taught, then all five updated. Probes check that old values (Ubuntu 20.04, Python 3.9, PostgreSQL 12, Heroku, Flask) are absent.

**dormant_resurrection** — Teaches "I prefer dark mode" then runs 15 completely unrelated questions (math, geography, coding concepts). The final probe asks about IDE theme setup. A system with UCB exploration should surface the dormant preference.

**overload_resistance** — 30 facts in rapid succession. Only 3 have high conviction (Python, Jira, agile). Probes check that high-conviction facts survive the noise.

**multi_hop_association** — Teaches a 4-hop chain: Alice→frontend team→React→Tailwind→custom design system. Probe asks "What design system does Alice's team use?" — requires traversing 3-4 graph edges.

**temporal_decay** — Teaches 3 "old" facts and 4 "recent" facts with staggered timestamps. Old facts (Phoenix, Mike, CircleCI) should be forgotten; recent ones (Aether, Priya, GitHub Actions, December 15) should be remembered.

**context_window_efficiency** — 50 low-value facts, then one relevant probe. Measures the size of the injected memory context. A good memory system injects only relevant facts (O(1)) rather than everything (O(n)).

**cross_user_isolation** — Teaches 4 facts for Alice and 4 for Bob in alternating sessions. Probes Alice with "What is my name and stack?" — must not mention Bob's facts (Bob, Go, dog, Rover).

## CLI Reference

```
python -m eval.mnembench [options]
```

### Main Options

| Option | Default | Description |
|--------|---------|-------------|
| `--server`, `-s` | `http://localhost:8000` | Memory-enabled server URL |
| `--baseline` | `http://localhost:8002` | Baseline (no memory) server URL |
| `--scenario`, `-s` | `["all"]` | Scenario(s) to run. Use `--list` to see IDs |
| `--output-dir`, `-o` | `eval/results` | Where to write reports |
| `--repeat`, `-r` | `1` | Repeat each scenario N times for statistical significance |

### Mode Flags

| Flag | Description |
|------|-------------|
| `--dry-run`, `-n` | Use pre-recorded fixture responses. No API calls. |
| `--no-baseline` | Skip baseline comparison. Run with-memory only. |
| `--no-seed-memory` | Don't auto-seed facts via `/api/memory/store`. |
| `--judge-report` | Also write a compact Track 1 judge-facing Markdown summary. |
| `--list` | Print available scenarios and exit. |
| `--no-progress` | Suppress per-scenario progress output. |
| `--version` | Print version and exit. |

### Examples

```bash
# Full comparison run
python -m eval.mnembench \
  --server http://localhost:8000 \
  --baseline http://localhost:8002 \
  --repeat 5

# Single scenario, 3 repeats, no baseline
python -m eval.mnembench \
  --server http://localhost:8000 \
  --scenario contradiction_chain \
  --repeat 3 \
  --no-baseline

# Dry run with specific scenarios
python -m eval.mnembench \
  --dry-run \
  --scenario ten_session_recall salience_gate

# Just the JSON results, custom output dir
python -m eval.mnembench \
  --server http://localhost:8000 \
  --no-baseline \
  --output-dir ./benchmark_results

# Quick sanity check — single repeat, one scenario
python -m eval.mnembench \
  --server http://localhost:8000 \
  --scenario cross_user_isolation
```

## Output

Results go to `eval/results/` (or your `--output-dir`). Two files per run:

### Markdown Report (`mnembench_report_<timestamp>.md`)

The Markdown report includes:

- **Executive summary** — aggregate scores, pass rates, comparison deltas
- **Per-scenario tables** — probe-by-probe scores with labels
- **ASCII trajectory charts** — visual comparison of with-memory vs without-memory scores across probe steps

Here's what a trajectory chart looks like:

```
|---------------
|*  *    *
| *  *  * o  o
|  o  o  o  o
+----------------
* = with memory
o = without memory
```

Rising `*` line = memory advantage compounding. Flat or falling = memory isn't helping.

- **Dimension radar** — ASCII bar chart of per-scenario dimension scores
- **Dimension deltas** — for comparison mode, shows which dimensions improved

### JSON Results (`mnembench_results_<timestamp>.json`)

For programmatic access. Structure:

```json
{
  "generated_at": "2026-06-14T12:00:00Z",
  "mode": "with_memory",
  "summary": {
    "average_score": 0.85,
    "average_composite": 0.78,
    "pass_rate": 0.9,
    "num_runs": 10
  },
  "scenarios": [
    {
      "scenario_id": "ten_session_recall",
      "mode": "with_memory",
      "average_probe_score": 0.9,
      "composite_score": 0.85,
      "dimensions": {
        "recall_precision": 0.9,
        "contradiction_score": 1.0,
        "salience_f1": 0.8,
        "interference_rate": 0.95,
        "latency_ms": 850.0
      },
      "probe_results": [
        {
          "step_index": 11,
          "label": "probe-all-10",
          "score": 0.9,
          "details": [...],
          "pass": true,
          "latency_ms": 850.0
        }
      ],
      "pass": true
    }
  ],
  "comparison": {
    "aggregate": { ... },
    "per_scenario": { ... }
  }
}
```

## Scoring Dimensions

Each scenario is scored across five dimensions:

| Dimension | Range | What it Measures |
|-----------|-------|------------------|
| `recall_precision` | 0.0–1.0 | Fraction of expected keywords found in probe responses |
| `contradiction_score` | 0.0–1.0 | Old values absent AND new values present after updates |
| `salience_f1` | 0.0–1.0 | F1 of stored vs rejected facts in memory dumps |
| `interference_rate` | 0.0–1.0 | 1.0 = no stale facts leaked. Lower = more interference. |
| `latency_ms` | ms | Average response time for probe steps |

The **composite score** is a weighted combination:

```
composite = 0.4 * avg_probe_score
           + 0.2 * salience_f1
           + 0.2 * contradiction_score
           + 0.1 * interference_rate
           + 0.1 * recall_precision
```

This means probe accuracy matters most, but the memory quality dimensions (salience, contradiction handling) together contribute as much weight.

## Architecture

MnemBench has four layers:

```
┌─────────────┐
│   CLI       │  cli.py — argparse entry point
├─────────────┤
│  Runner     │  runner.py — orchestrates API calls, collects responses
├─────────────┤
│ Scenarios   │  scenarios.py — 10 scenario definitions
│             │  fixtures.py — dry-run fixture responses
├─────────────┤
│ Scoring     │  scoring.py — multi-dimensional scoring
│             │  report.py — Markdown + JSON output
└─────────────┘
```

The runner sends requests to any HTTP server that speaks this protocol:

```
POST /chat
{
  "user_id": "string",
  "session_id": "string",
  "message": "string"
}
→ { "response": "string" }
```

For memory seeding (when `--seed-memory` is enabled and mode is `with_memory`):

```
POST /api/memory/store
{
  "user_id": "string",
  "entity": "string",
  "relation": "string",
  "value": "string",
  "category": "string",
  "conviction": 1.0
}
```

Both endpoints are optional — you can run without seeding and just rely on the LLM extracting facts from conversation history.

### How the Runner Works

1. For each scenario, the runner creates a unique user_id (so parallel runs don't collide).
2. Steps are executed sequentially in order.
3. For teach steps with a `memory_seed`: pre-stores the fact via `/api/memory/store` (skipped if `--no-seed-memory`).
4. For probe/contradict steps: sends the user message, collects the response and latency, then fetches a memory dump via `/memory`.
5. After all steps, scoring functions evaluate each probe's response against its expectations.
6. Reports are written to disk as Markdown and JSON.

## Adding Scenarios

Scenarios are defined as `MnemBenchScenario` objects with a list of `MnemBenchStep` objects. Here's the structure:

```python
from eval.mnembench.scenarios import MnemBenchScenario, MnemBenchStep, MemorySeed, _seed, _exp

my_scenario = MnemBenchScenario(
    id="my_custom_test",
    name="My Custom Test",
    description="Tests something specific about the memory system.",
    category="recall",
    steps=[
        MnemBenchStep(1, "s1", "teach",
            "We use Python for everything.",
            memory_seed=_seed("language", "uses", "Python")),
        MnemBenchStep(2, "s2", "probe",
            "What language do we use?",
            [
                _exp("keyword_present", "Python", "Should recall Python"),
            ],
            label="probe-1"),
    ],
)
```

Then register it in the `ALL_MNEMBENCH_SCENARIOS` list at the bottom of `scenarios.py`:

```python
ALL_MNEMBENCH_SCENARIOS: list[MnemBenchScenario] = [
    # ... existing scenarios ...
    my_scenario,
]
```

### Step Phases

| Phase | Purpose | Seeds Memory | Triggers Scoring |
|-------|---------|--------------|------------------|
| `teach` | Teaches a fact | If `memory_seed` is set | No |
| `probe` | Asks a question with expectations | No | Yes, if expectations exist |
| `contradict` | Updates a previously taught fact | If `memory_seed` is set | Yes, if expectations exist |
| `distract` | Unrelated turn (fills context window) | No | No |
| `measure` | Special measurement step (context size) | No | No |

### Adding Dry-Run Fixtures

If you add a scenario, add fixture responses in `fixtures.py` for dry-run mode:

```python
FIXTURE_RESPONSES["my_custom_test"] = {
    "with_memory": {
        2: "We use Python for everything, as per your stated preference.",
    },
    "without_memory": {
        2: "I don't know your language preference. Could you tell me?",
    },
}

FIXTURE_MEMORY_DUMPS["my_custom_test"] = "language → uses → Python"
```

Without fixtures, the dry-run will fall back to generic responses ("Acknowledged." for with_memory, "Could you provide more details?" for without_memory).

### Expectation Types

| Check Type | Value Format | Description |
|------------|-------------|-------------|
| `keyword_present` | `"Python"` | Keyword must appear in response |
| `keyword_absent` | `"Express"` | Keyword must NOT appear in response |
| `contradiction_resolved` | `"old\|new"` | Old value absent, new value present |
| `no_question_asked` | `""` | Agent must not ask a clarifying question |
| `relevance` | `"topic1,topic2"` | Proportion of topics covered in response |
| `memory_state` | `"contain\|not_contain"` | Memory dump contains/avoids terms |
| `salience_f1` | `"stored1,stored2\|rejected1"` | F1 of what's stored vs rejected in memory |

## License

MIT - see [LICENSE](../../LICENSE) for details.

This benchmark is designed to be open-source from day one. Use it, fork it, run it against your own memory system. If you find a failure mode we haven't covered, open an issue or send a PR.
