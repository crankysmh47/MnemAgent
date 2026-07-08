"""Eval v2 runner — tests unguessable fact recall across sessions.

.. deprecated::
    Use ``python -m eval.run_benchmark`` as the single supported entry point.
"""

from __future__ import annotations

import argparse
import asyncio
import uuid
from dataclasses import dataclass, field
from pathlib import Path

import httpx

from eval.agentic_scenarios_v2 import AGENTIC_SCENARIOS_V2, AgenticScenario
from eval.agentic_scoring import score_agentic_scenario


@dataclass
class EvalV2Report:
    mode: str
    scenario_results: list[dict] = field(default_factory=list)

    @property
    def avg_score(self) -> float:
        if not self.scenario_results:
            return 0.0
        return sum(r["score"] for r in self.scenario_results) / len(self.scenario_results)


async def run_scenario(
    scenario: AgenticScenario,
    base_url: str,
    mode: str,
    seed_memory: bool = True,
) -> dict:
    """Run one scenario and return scored result."""
    uid = f"evalv2_{scenario.id}_{uuid.uuid4().hex[:6]}"
    responses: dict[int, str] = {}
    memory_dumps: dict[int, str] = {}

    async with httpx.AsyncClient(timeout=120.0) as client:
        for step in scenario.steps:
            # Seed memory for teach steps (only in with_memory mode)
            if seed_memory and mode == "with_memory" and step.memory_seed is not None:
                await client.post(
                    f"{base_url}/api/memory/store",
                    json={
                        "user_id": uid,
                        "entity": step.memory_seed.entity,
                        "relation": step.memory_seed.relation,
                        "value": step.memory_seed.value,
                        "category": step.memory_seed.category,
                        "conviction": step.memory_seed.conviction,
                    },
                )
                await asyncio.sleep(0.5)

            # Send the message
            resp = await client.post(
                f"{base_url}/chat",
                json={
                    "user_id": uid,
                    "session_id": step.session_id,
                    "message": step.user_message,
                },
            )
            responses[step.step_index] = resp.json().get("response", "")

            # Wait for dreaming phase to complete
            await asyncio.sleep(1.5)

            # Collect memory dump for probe/contradict steps
            if step.phase in ("probe", "contradict") and step.expectations:
                await asyncio.sleep(0.5)
                mem = await client.post(
                    f"{base_url}/chat",
                    json={
                        "user_id": uid,
                        "session_id": step.session_id,
                        "message": "/memory",
                    },
                )
                memory_dumps[step.step_index] = mem.json().get("response", "")

    score_data = score_agentic_scenario(scenario, responses, memory_dumps)
    return {
        "scenario_id": scenario.id,
        "scenario_name": scenario.name,
        "score": score_data.get("average_probe_score", 0),
        "probe_details": score_data.get("probe_results", []),
        "mode": mode,
    }


async def run_all(
    mode: str,
    base_url: str,
    scenarios: list[AgenticScenario] | None = None,
    seed_memory: bool = True,
) -> EvalV2Report:
    """Run all eval v2 scenarios."""
    report = EvalV2Report(mode=mode)
    for scenario in scenarios or AGENTIC_SCENARIOS_V2:
        result = await run_scenario(scenario, base_url, mode, seed_memory)
        report.scenario_results.append(result)
        probes = [p for p in result["probe_details"] if p.get("score", 0) > 0]
        print(f"  {scenario.id}: {result['score']:.0%} ({len(probes)}/{len(result['probe_details'])} probes passed)")
    print(f"  AVG: {report.avg_score:.0%}")
    return report


def main() -> None:
    import warnings

    warnings.warn(
        "eval.run_eval_v2 is deprecated; use python -m eval.run_benchmark instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    parser = argparse.ArgumentParser(description="Eval v2 — unguessable memory recall")
    parser.add_argument("--mode", choices=["with_memory", "without_memory", "both"], default="both")
    parser.add_argument("--mnemos-url", default="http://localhost:8000")
    parser.add_argument("--baseline-url", default="http://localhost:8002")
    parser.add_argument("--output-dir", default="eval/results")
    args = parser.parse_args()

    async def _run() -> None:
        if args.mode in ("with_memory", "both"):
            print("=== MnemAgent (with memory) ===")
            with_report = await run_all("with_memory", args.mnemos_url)
            print(f"  OVERALL: {with_report.avg_score:.1%}")

        if args.mode in ("without_memory", "both"):
            baseline_url = args.baseline_url
            print("=== Baseline (no memory) ===")
            without_report = await run_all(
                "without_memory", baseline_url, seed_memory=False
            )
            print(f"  OVERALL: {without_report.avg_score:.1%}")

        if args.mode == "both":
            delta = with_report.avg_score - without_report.avg_score
            print(f"\n  MEMORY ADVANTAGE: {delta:+.1%}")

    asyncio.run(_run())


if __name__ == "__main__":
    main()
