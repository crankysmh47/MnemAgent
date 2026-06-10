"""Tests for agentic multi-step memory advantage benchmark."""

from __future__ import annotations

import asyncio

from eval.agentic_runner import AgenticBenchmarkRunner, build_comparison
from eval.agentic_scenarios import AGENTIC_SCENARIOS
from eval.agentic_scoring import (
    compute_memory_advantage_trajectory,
    probe_difficulty_weights,
    score_agentic_scenario,
    score_probe_memory_coverage,
)
from eval.agentic_fixtures import get_fixture_response


def test_agentic_scenarios_defined() -> None:
    assert len(AGENTIC_SCENARIOS) == 4
    for scenario in AGENTIC_SCENARIOS:
        assert len(scenario.probe_steps) >= 2
    teach_seeds = [
        s.memory_seed
        for sc in AGENTIC_SCENARIOS
        for s in sc.steps
        if s.phase in ("teach", "contradict") and s.memory_seed
    ]
    assert len(teach_seeds) >= 10


def test_memory_coverage_from_dump() -> None:
    from eval.agentic_scoring import score_scenario_memory_progress

    scenario = AGENTIC_SCENARIOS[0]
    step = scenario.probe_steps[-1]
    dump = "backend_language prefers Python | PostgreSQL | FastAPI | AWS deployment"
    assert score_probe_memory_coverage(step, dump) == 1.0
    assert score_probe_memory_coverage(step, "") == 0.0
    assert score_scenario_memory_progress(scenario, 2, "Python backend") == 0.25
    assert score_scenario_memory_progress(scenario, step.step_index, dump) == 1.0


def test_weighted_trajectory_prefers_harder_probes() -> None:
    with_scores = [1.0, 1.0, 1.0]
    without_scores = [0.5, 0.25, 0.0]
    unweighted = compute_memory_advantage_trajectory(with_scores, without_scores)
    weighted = compute_memory_advantage_trajectory(
        with_scores, without_scores, probe_weights=[1.0, 2.0, 4.0]
    )
    assert weighted["weighted_cumulative_advantage"] > unweighted["cumulative_advantage"] / 3
    weights = probe_difficulty_weights(AGENTIC_SCENARIOS[0].probe_steps)
    assert weights == [1.0, 2.0, 2.0, 4.0]


def test_advantage_trajectory_grows_in_fixtures() -> None:
    scenario = AGENTIC_SCENARIOS[0]
    with_responses = {
        s.step_index: get_fixture_response(scenario.id, s.step_index, "with_memory")
        for s in scenario.steps
    }
    without_responses = {
        s.step_index: get_fixture_response(scenario.id, s.step_index, "without_memory")
        for s in scenario.steps
    }
    with_score = score_agentic_scenario(scenario, with_responses)
    without_score = score_agentic_scenario(scenario, without_responses)
    with_probes = [p["score"] for p in with_score["probe_results"]]
    without_probes = [p["score"] for p in without_score["probe_results"]]
    traj = compute_memory_advantage_trajectory(with_probes, without_probes)
    assert traj["advantage_growth"] > 0
    assert traj["final_gap"] > traj["initial_gap"]


async def _dry_run_comparison() -> None:
    with_runner = AgenticBenchmarkRunner("", "with_memory", dry_run=True)
    without_runner = AgenticBenchmarkRunner("", "without_memory", dry_run=True)
    with_report = await with_runner.run_all()
    without_report = await without_runner.run_all()
    comparison = build_comparison(with_report, without_report)
    assert comparison.aggregate["avg_advantage_growth"] > 0
    assert with_report.average_probe_score > without_report.average_probe_score


def test_agentic_dry_run_comparison() -> None:
    asyncio.run(_dry_run_comparison())
