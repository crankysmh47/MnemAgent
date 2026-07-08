"""CLI entry point for MnemAgent evaluation benchmark."""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from eval.benchmark_runner import BenchmarkRunner
from eval.report_generator import generate_comparison_report


async def _run(mode: str, server_url: str, output_dir: Path, dry_run: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_suffix = "" if dry_run else timestamp

    with_report = None
    without_report = None

    if mode in ("with_memory", "both"):
        runner = BenchmarkRunner(
            server_url, "with_memory", dry_run=dry_run, run_suffix=run_suffix
        )
        with_report = await runner.run_all_scenarios()
        print(f"MnemAgent average score: {with_report.average_score:.1%}")

    if mode in ("without_memory", "both"):
        baseline_url = server_url if mode == "without_memory" else "http://localhost:8002"
        runner = BenchmarkRunner(
            baseline_url, "without_memory", dry_run=dry_run, run_suffix=run_suffix
        )
        without_report = await runner.run_all_scenarios()
        print(f"Baseline average score: {without_report.average_score:.1%}")

    if mode == "both" and with_report and without_report:
        report = generate_comparison_report(with_report, without_report)
        out_path = output_dir / f"benchmark_report_{timestamp}.md"
        out_path.write_text(report, encoding="utf-8")
        print(f"Report written to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run MnemAgent evaluation benchmark")
    parser.add_argument(
        "--mode",
        choices=["with_memory", "without_memory", "both"],
        default="both",
    )
    parser.add_argument("--server-url", default="http://localhost:8000")
    parser.add_argument("--output-dir", default="eval/results")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use fixture responses — no API key or running server required",
    )
    args = parser.parse_args()
    asyncio.run(_run(args.mode, args.server_url, Path(args.output_dir), args.dry_run))


if __name__ == "__main__":
    main()
