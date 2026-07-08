"""Multi-step agentic benchmark runner — MnemAgent vs baseline with trajectory metrics."""

from __future__ import annotations

import asyncio
import uuid
from dataclasses import dataclass, field

import httpx

from eval.agentic_fixtures import get_fixture_memory_dump, get_fixture_response
from eval.agentic_scenarios import AGENTIC_SCENARIOS, AgenticScenario, MemorySeed
from eval.agentic_scoring import (
    compute_memory_advantage_trajectory,
    probe_difficulty_weights,
    score_agentic_scenario,
)


@dataclass
class AgenticScenarioRun:
    """Result of running one agentic scenario in one mode."""

    scenario_id: str
    mode: str
    step_responses: dict[int, str] = field(default_factory=dict)
    score_summary: dict = field(default_factory=dict)


@dataclass
class AgenticBenchmarkReport:
    """Full agentic benchmark report for one mode."""

    mode: str
    runs: list[AgenticScenarioRun] = field(default_factory=list)

    @property
    def average_probe_score(self) -> float:
        if not self.runs:
            return 0.0
        return sum(r.score_summary.get("average_probe_score", 0) for r in self.runs) / len(self.runs)


@dataclass
class AgenticComparisonReport:
    """Side-by-side comparison with memory advantage trajectories."""

    with_report: AgenticBenchmarkReport
    without_report: AgenticBenchmarkReport
    trajectories: dict[str, dict] = field(default_factory=dict)
    aggregate: dict = field(default_factory=dict)


class AgenticBenchmarkRunner:
    """Execute multi-step scenarios against MnemAgent or baseline."""

    def __init__(
        self,
        base_url: str,
        mode: str,
        dry_run: bool = False,
        seed_memory: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.mode = mode
        self.dry_run = dry_run
        self.seed_memory = seed_memory

    async def _store_memory_seed(
        self,
        client: httpx.AsyncClient,
        user_id: str,
        seed: MemorySeed,
    ) -> None:
        """Persist a teach-step fact via API (bypasses unreliable LLM memory tags)."""
        await client.post(
            f"{self.base_url}/api/memory/store",
            json={
                "user_id": user_id,
                "entity": seed.entity,
                "relation": seed.relation,
                "value": seed.value,
                "category": seed.category,
                "conviction": seed.conviction,
            },
        )

    async def run_scenario(self, scenario: AgenticScenario) -> AgenticScenarioRun:
        """Run all steps in one scenario sequentially."""
        run_suffix = uuid.uuid4().hex[:8] if not self.dry_run else "dry"
        user_id = f"agentic_{scenario.id}_{self.mode}_{run_suffix}"
        step_responses: dict[int, str] = {}
        memory_dumps: dict[int, str] = {}

        if self.dry_run:
            for step in scenario.steps:
                step_responses[step.step_index] = get_fixture_response(
                    scenario.id, step.step_index, self.mode
                )
                if step.phase in ("probe", "contradict"):
                    memory_dumps[step.step_index] = get_fixture_memory_dump(
                        scenario.id, step.step_index
                    )
        else:
            async with httpx.AsyncClient(timeout=120.0) as client:
                for step in scenario.steps:
                    if (
                        self.seed_memory
                        and self.mode == "with_memory"
                        and step.memory_seed is not None
                    ):
                        await self._store_memory_seed(client, user_id, step.memory_seed)
                        await asyncio.sleep(0.5)

                    resp = await client.post(
                        f"{self.base_url}/chat",
                        json={
                            "user_id": user_id,
                            "session_id": step.session_id,
                            "message": step.user_message,
                        },
                    )
                    step_responses[step.step_index] = resp.json().get("response", "")
                    if step.phase in ("teach", "contradict") and step.memory_seed:
                        await asyncio.sleep(1.5)
                    if step.phase in ("probe", "contradict") and step.expectations:
                        await asyncio.sleep(2)
                        mem = await client.post(
                            f"{self.base_url}/chat",
                            json={
                                "user_id": user_id,
                                "session_id": step.session_id,
                                "message": "/memory",
                            },
                        )
                        memory_dumps[step.step_index] = mem.json().get("response", "")

        score_summary = score_agentic_scenario(scenario, step_responses, memory_dumps)
        return AgenticScenarioRun(
            scenario_id=scenario.id,
            mode=self.mode,
            step_responses=step_responses,
            score_summary=score_summary,
        )

    async def run_all(
        self,
        scenarios: list[AgenticScenario] | None = None,
    ) -> AgenticBenchmarkReport:
        """Run agentic scenarios (default: all)."""
        report = AgenticBenchmarkReport(mode=self.mode)
        for scenario in scenarios or AGENTIC_SCENARIOS:
            report.runs.append(await self.run_scenario(scenario))
        return report


def build_comparison(
    with_report: AgenticBenchmarkReport,
    without_report: AgenticBenchmarkReport,
) -> AgenticComparisonReport:
    """
    Pair scenarios and compute memory advantage trajectories.

    Args:
        with_report: MnemAgent run results.
        without_report: Baseline run results.

    Returns:
        Comparison with per-scenario and aggregate trajectory metrics.
    """
    comparison = AgenticComparisonReport(
        with_report=with_report,
        without_report=without_report,
    )
    scenario_by_id = {s.id: s for s in AGENTIC_SCENARIOS}
    without_by_id = {r.scenario_id: r for r in without_report.runs}
    all_cumulative: list[float] = []
    all_weighted_cumulative: list[float] = []
    all_growth: list[float] = []
    all_weighted_growth: list[float] = []
    all_slopes: list[float] = []
    all_memory_growth: list[float] = []
    all_composite_growth: list[float] = []

    for with_run in with_report.runs:
        without_run = without_by_id.get(with_run.scenario_id)
        if without_run is None:
            continue
        scenario = scenario_by_id.get(with_run.scenario_id)
        weights = (
            probe_difficulty_weights(scenario.probe_steps) if scenario else None
        )
        probe_results_with = with_run.score_summary.get("probe_results", [])
        probe_results_without = without_run.score_summary.get("probe_results", [])
        with_probes = [p["score"] for p in probe_results_with]
        without_probes = [p["score"] for p in probe_results_without]
        with_memory_cov = [
            p.get("memory_progress", p.get("memory_coverage", 0.0))
            for p in probe_results_with
        ]
        without_memory_cov = [0.0] * len(with_memory_cov)
        with_composite = [p.get("composite_score", p["score"]) for p in probe_results_with]

        trajectory = compute_memory_advantage_trajectory(
            with_probes, without_probes, probe_weights=weights
        )
        memory_trajectory = compute_memory_advantage_trajectory(
            with_memory_cov, without_memory_cov, probe_weights=weights
        )
        composite_trajectory = compute_memory_advantage_trajectory(
            with_composite, without_probes, probe_weights=weights
        )
        trajectory["memory_layer"] = memory_trajectory
        trajectory["composite"] = composite_trajectory
        comparison.trajectories[with_run.scenario_id] = trajectory
        all_cumulative.append(trajectory["cumulative_advantage"])
        all_weighted_cumulative.append(trajectory["weighted_cumulative_advantage"])
        all_growth.append(trajectory["advantage_growth"])
        all_weighted_growth.append(trajectory["weighted_advantage_growth"])
        all_slopes.append(trajectory["advantage_slope"])
        all_memory_growth.append(memory_trajectory["advantage_growth"])
        all_composite_growth.append(composite_trajectory["advantage_growth"])

    n = len(all_cumulative) or 1
    comparison.aggregate = {
        "mnemos_avg_probe_score": with_report.average_probe_score,
        "baseline_avg_probe_score": without_report.average_probe_score,
        "avg_cumulative_advantage": round(sum(all_cumulative) / n, 3),
        "avg_weighted_cumulative_advantage": round(sum(all_weighted_cumulative) / n, 3),
        "avg_advantage_growth": round(sum(all_growth) / n, 3),
        "avg_weighted_advantage_growth": round(sum(all_weighted_growth) / n, 3),
        "avg_advantage_slope": round(sum(all_slopes) / n, 3),
        "scenarios_where_advantage_grows": sum(1 for g in all_growth if g > 0),
        "scenarios_memory_wins_final": sum(
            1 for t in comparison.trajectories.values() if t.get("memory_wins_final_probe")
        ),
        "avg_memory_layer_growth": round(sum(all_memory_growth) / n, 3),
        "avg_composite_growth": round(sum(all_composite_growth) / n, 3),
        "total_scenarios": len(comparison.trajectories),
    }
    return comparison
