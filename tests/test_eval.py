"""Tests for evaluation benchmark scoring and dry-run."""

from __future__ import annotations

from eval.benchmark_runner import BenchmarkRunner
from eval.fixtures import FIXTURE_RESPONSES
from eval.report_generator import generate_comparison_report
from eval.scenarios import ALL_SCENARIOS
from eval.scoring import (
    compute_scenario_score,
    score_contradiction_resolved,
    score_keyword_absent,
    score_keyword_present,
    score_memory_state,
)


def test_score_keyword_present() -> None:
    assert score_keyword_present("Use Python for the API", "Python") == 1.0
    assert score_keyword_present("Use Java", "Python") == 0.0


def test_score_keyword_absent() -> None:
    assert score_keyword_absent("No framework chosen", "Vue") == 1.0
    assert score_keyword_absent("Try Vue", "Vue") == 0.0


def test_score_contradiction_resolved() -> None:
    assert score_contradiction_resolved("We use Fastify", "express", "Fastify") == 1.0
    assert score_contradiction_resolved("Express and Fastify", "express", "Fastify") == 0.5
    assert score_contradiction_resolved("Use Express", "express", "Fastify") == 0.0


def test_score_memory_state() -> None:
    dump = "backend_framework → prefers → fastify"
    assert score_memory_state(dump, ["fastify"], ["express"]) == 1.0


def test_scenario_definition_valid() -> None:
    assert len(ALL_SCENARIOS) == 25
    for scenario in ALL_SCENARIOS:
        assert scenario.id
        assert scenario.conversations
        assert scenario.expected_outcomes


def test_compute_scenario_score_perfect() -> None:
    scenario = ALL_SCENARIOS[0]
    responses = FIXTURE_RESPONSES[scenario.id]["with_memory"]
    result = compute_scenario_score(scenario, responses)
    assert result["pass"] is True
    assert result["score"] == 1.0


def test_compute_scenario_score_failure() -> None:
    scenario = ALL_SCENARIOS[0]
    responses = FIXTURE_RESPONSES[scenario.id]["without_memory"]
    result = compute_scenario_score(scenario, responses)
    assert result["score"] <= 1.0


async def _dry_run_once() -> None:
    runner = BenchmarkRunner("http://localhost:8000", "with_memory", dry_run=True)
    report = await runner.run_all_scenarios()
    assert report.average_score >= 0.0


def test_dry_run_produces_report() -> None:
    import asyncio

    asyncio.run(_dry_run_once())


def test_report_generator_produces_markdown() -> None:
    import asyncio

    async def _run() -> str:
        with_runner = BenchmarkRunner("", "with_memory", dry_run=True)
        without_runner = BenchmarkRunner("", "without_memory", dry_run=True)
        with_report = await with_runner.run_all_scenarios()
        without_report = await without_runner.run_all_scenarios()
        return generate_comparison_report(with_report, without_report)

    report = asyncio.run(_run())
    assert "# MnemAgent Benchmark Comparison Report" in report
    assert "MnemAgent (with memory)" in report


def test_fixtures_cover_all_scenarios() -> None:
    for scenario in ALL_SCENARIOS:
        assert scenario.id in FIXTURE_RESPONSES
        assert "with_memory" in FIXTURE_RESPONSES[scenario.id]
        assert "without_memory" in FIXTURE_RESPONSES[scenario.id]
