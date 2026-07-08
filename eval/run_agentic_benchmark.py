"""CLI for multi-step agentic memory advantage benchmark.

.. deprecated::
    Use ``python -m eval.run_benchmark`` as the single supported entry point.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from eval.agentic_report import generate_agentic_report
from eval.agentic_runner import AgenticBenchmarkRunner, build_comparison


async def _run(
    mode: str,
    mnemos_url: str,
    baseline_url: str,
    output_dir: Path,
    dry_run: bool,
    scenario_id: str | None,
    seed_memory: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with_report = None
    without_report = None

    from eval.agentic_scenarios import AGENTIC_SCENARIOS

    scenarios = AGENTIC_SCENARIOS
    if scenario_id:
        scenarios = [s for s in AGENTIC_SCENARIOS if s.id == scenario_id]
        if not scenarios:
            raise SystemExit(f"Unknown scenario: {scenario_id}")

    if mode in ("with_memory", "both"):
        runner = AgenticBenchmarkRunner(
            mnemos_url, "with_memory", dry_run=dry_run, seed_memory=seed_memory
        )
        with_report = await runner.run_all(scenarios)
        print(f"MnemAgent avg probe score: {with_report.average_probe_score:.1%}")

    if mode in ("without_memory", "both"):
        runner = AgenticBenchmarkRunner(
            baseline_url, "without_memory", dry_run=dry_run, seed_memory=False
        )
        without_report = await runner.run_all(scenarios)
        print(f"Baseline avg probe score: {without_report.average_probe_score:.1%}")

    if mode == "both" and with_report and without_report:
        comparison = build_comparison(with_report, without_report)
        agg = comparison.aggregate
        print(
            f"Behavior advantage growth: {agg.get('avg_advantage_growth', 0):+.3f} | "
            f"Memory layer growth: {agg.get('avg_memory_layer_growth', 0):+.3f} | "
            f"Composite growth: {agg.get('avg_composite_growth', 0):+.3f}"
        )
        print(
            f"  {agg.get('scenarios_where_advantage_grows', 0)}/{agg.get('total_scenarios', 0)} behavioral grew, "
            f"{agg.get('scenarios_memory_wins_final', 0)} win final behavioral probe"
        )
        report = generate_agentic_report(comparison)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        out_path = output_dir / f"agentic_benchmark_{timestamp}.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"Report written to {out_path}")


def main() -> None:
    import warnings

    warnings.warn(
        "eval.run_agentic_benchmark is deprecated; use python -m eval.run_benchmark instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    parser = argparse.ArgumentParser(
        description="Run multi-step agentic memory advantage benchmark"
    )
    parser.add_argument(
        "--mode",
        choices=["with_memory", "without_memory", "both"],
        default="both",
    )
    parser.add_argument("--mnemos-url", default="http://localhost:8000")
    parser.add_argument(
        "--baseline-url",
        default="http://localhost:8002",
        help="Baseline server URL (no memory). Default :8002 to avoid MCP adapter on :8001",
    )
    parser.add_argument("--output-dir", default="eval/results")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use fixtures — shows growing memory advantage without API calls",
    )
    parser.add_argument(
        "--scenario",
        default=None,
        help="Run a single scenario id (e.g. compound_stack)",
    )
    parser.add_argument(
        "--no-seed-memory",
        action="store_true",
        help="Do not pre-store teach facts via API (tests LLM memory_update tags)",
    )
    args = parser.parse_args()
    asyncio.run(
        _run(
            args.mode,
            args.mnemos_url,
            args.baseline_url,
            Path(args.output_dir),
            args.dry_run,
            args.scenario,
            seed_memory=not args.no_seed_memory,
        )
    )


if __name__ == "__main__":
    main()
