"""Benchmark orchestrator for MnemAgent vs baseline comparison."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field

import httpx

from eval.fixtures import FIXTURE_MEMORY_DUMPS, FIXTURE_RESPONSES
from eval.scenarios import ALL_SCENARIOS, Scenario
from eval.scoring import compute_scenario_score


@dataclass
class ScenarioResult:
    """Result of running one scenario."""

    scenario_id: str
    mode: str
    score: float
    passed: bool
    responses: list[str] = field(default_factory=list)


@dataclass
class BenchmarkReport:
    """Aggregate benchmark report."""

    mode: str
    results: list[ScenarioResult] = field(default_factory=list)

    @property
    def average_score(self) -> float:
        if not self.results:
            return 0.0
        return sum(result.score for result in self.results) / len(self.results)


class BenchmarkRunner:
    """Run benchmark scenarios against MnemAgent or baseline server."""

    def __init__(
        self,
        base_url: str,
        mode: str,
        dry_run: bool = False,
        run_suffix: str = "",
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.mode = mode
        self.dry_run = dry_run
        self.run_suffix = run_suffix.strip("_")

    async def run_scenario(self, scenario: Scenario) -> ScenarioResult:
        """Execute one scenario and score the outcome."""
        responses: list[str] = []
        memory_dumps: list[str] = []
        fixture_mode = "with_memory" if self.mode == "with_memory" else "without_memory"
        fixture_responses = FIXTURE_RESPONSES.get(scenario.id, {}).get(fixture_mode, [])

        if self.dry_run:
            responses = fixture_responses or ["dry-run response"]
            if self.mode == "with_memory":
                dump = FIXTURE_MEMORY_DUMPS.get(scenario.id, "")
                memory_dumps = [dump] if dump else []
            score_data = compute_scenario_score(scenario, responses, memory_dumps)
            return ScenarioResult(
                scenario_id=scenario.id,
                mode=self.mode,
                score=score_data["score"],
                passed=score_data["pass"],
                responses=responses,
            )

        async with httpx.AsyncClient(timeout=600.0) as client:
            response_idx = 0
            user_tag = f"bench_{scenario.id}"
            if self.run_suffix:
                user_tag = f"{user_tag}_{self.run_suffix}"
            for session in scenario.conversations:
                for turn in session.turns:
                    payload = {
                        "user_id": user_tag,
                        "session_id": session.session_id,
                        "message": turn.user_message,
                    }
                    resp = await client.post(f"{self.base_url}/chat", json=payload)
                    if resp.status_code != 200:
                        raise RuntimeError(
                            f"{scenario.id} HTTP {resp.status_code}: {resp.text[:300]}"
                        )
                    if not resp.content:
                        raise RuntimeError(f"{scenario.id} empty response body")
                    responses.append(resp.json().get("response", ""))
                    response_idx += 1
                    if not self.dry_run:
                        await asyncio.sleep(1.5)
                mem = await client.post(
                    f"{self.base_url}/chat",
                    json={
                        "user_id": user_tag,
                        "session_id": session.session_id,
                        "message": "/memory",
                    },
                )
                memory_dumps.append(mem.json().get("response", ""))

        score_data = compute_scenario_score(scenario, responses, memory_dumps)
        return ScenarioResult(
            scenario_id=scenario.id,
            mode=self.mode,
            score=score_data["score"],
            passed=score_data["pass"],
            responses=responses,
        )

    async def run_all_scenarios(self) -> BenchmarkReport:
        """Run all defined scenarios."""
        report = BenchmarkReport(mode=self.mode)
        for scenario in ALL_SCENARIOS:
            report.results.append(await self.run_scenario(scenario))
        return report
