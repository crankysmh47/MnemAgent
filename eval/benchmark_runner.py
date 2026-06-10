"""Benchmark orchestrator for MnemOS vs baseline comparison."""

from __future__ import annotations

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
    """Run benchmark scenarios against MnemOS or baseline server."""

    def __init__(self, base_url: str, mode: str, dry_run: bool = False) -> None:
        self.base_url = base_url.rstrip("/")
        self.mode = mode
        self.dry_run = dry_run

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

        async with httpx.AsyncClient(timeout=60.0) as client:
            response_idx = 0
            for session in scenario.conversations:
                for turn in session.turns:
                    payload = {
                        "user_id": f"bench_{scenario.id}",
                        "session_id": session.session_id,
                        "message": turn.user_message,
                    }
                    resp = await client.post(f"{self.base_url}/chat", json=payload)
                    responses.append(resp.json().get("response", ""))
                    response_idx += 1
                mem = await client.post(
                    f"{self.base_url}/chat",
                    json={
                        "user_id": f"bench_{scenario.id}",
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
