"""MnemBench — long-running agentic memory system benchmark.

A standalone, open-source benchmark suite for evaluating memory-augmented
language model agents. Supports any OpenAI-compatible API and any memory
system (MnemOS, LoCoMo, MemGPT, etc.).

Provides 10 scenarios spanning:
  - Cross-session recall at scale
  - Multi-hop contradiction resolution
  - Salience gating (hedged vs definitive)
  - Interference (proactive and retroactive)
  - Dormant memory resurrection (UCB exploration)
  - Overload resistance
  - Multi-hop association (RWR)
  - Temporal decay
  - Context window efficiency
  - Cross-user isolation
"""

from __future__ import annotations

from eval.mnembench.scenarios import ALL_MNEMBENCH_SCENARIOS, MnemBenchScenario
from eval.mnembench.runner import MnemBenchRunner
from eval.mnembench.scoring import score_mnembench_scenario
from eval.mnembench.cli import main

__version__ = "1.0.0"
__all__ = [
    "ALL_MNEMBENCH_SCENARIOS",
    "MnemBenchScenario",
    "MnemBenchRunner",
    "score_mnembench_scenario",
    "main",
]
