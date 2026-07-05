"""MnemBench CLI — command-line interface for running the benchmark suite.

Usage:
    python -m eval.mnembench --server http://localhost:8000 --baseline http://localhost:8002 --scenario all
    python -m eval.mnembench --server http://localhost:8000 --scenario ten_session_recall --repeat 3
    python -m eval.mnembench --dry-run  # offline fixture mode
    python -m eval.mnembench --list     # list available scenarios
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

from eval.mnembench.report import write_report
from eval.mnembench.runner import MnemBenchComparison, MnemBenchReport, MnemBenchRunner


def _list_scenarios() -> None:
    """Print available scenarios in a formatted table."""
    from eval.mnembench.scenarios import ALL_MNEMBENCH_SCENARIOS

    print(f"{'ID':<30} {'Name':<35} {'Category':<15} Steps")
    print(f"{'-' * 30} {'-' * 35} {'-' * 15} {'-' * 5}")
    for scenario in ALL_MNEMBENCH_SCENARIOS:
        num_steps = len(scenario.steps)
        print(f"{scenario.id:<30} {scenario.name:<35} {scenario.category:<15} {num_steps}")


async def _run(
    server: str,
    baseline: str,
    output_dir: Path,
    scenarios_filter: list[str] | None,
    dry_run: bool,
    seed_memory: bool,
    repeat: int,
    no_baseline: bool,
    progress: bool,
    judge_report: bool,
) -> None:
    """Execute the benchmark."""
    from eval.mnembench.scenarios import ALL_MNEMBENCH_SCENARIOS

    # Filter scenarios
    scenarios = ALL_MNEMBENCH_SCENARIOS
    if scenarios_filter and "all" not in scenarios_filter:
        filtered = []
        for sid in scenarios_filter:
            matches = [s for s in scenarios if s.id == sid]
            if not matches:
                raise SystemExit(f"Unknown scenario: {sid}")
            filtered.extend(matches)
        scenarios = filtered

    def make_callback(mode: str):
        async def cb(sid: str, rep: int, total: int) -> None:
            if progress:
                print(f"  [{mode}] {sid} — run {rep}/{total}")
        return cb

    # Run with memory
    with_report: MnemBenchReport | None = None
    without_report: MnemBenchReport | None = None

    print(f"\nRunning MnemBench on {len(scenarios)} scenario(s)...\n")

    runner_server = MnemBenchRunner(server, "with_memory", dry_run=dry_run, seed_memory=seed_memory, repeat=repeat)
    print(f"[with_memory] Server: {server}")
    with_report = await runner_server.run_all(scenarios, progress_callback=make_callback("with_memory"))
    print(f"  Average probe score: {with_report.average_score:.1%}")
    print(f"  Average composite:   {with_report.average_composite:.3f}")
    print(f"  Pass rate:           {with_report.pass_rate:.1%}")

    if not no_baseline and baseline:
        runner_baseline = MnemBenchRunner(
            baseline, "without_memory", dry_run=dry_run, seed_memory=False, repeat=repeat
        )
        print(f"\n[without_memory] Baseline: {baseline}")
        without_report = await runner_baseline.run_all(scenarios, progress_callback=make_callback("without_memory"))
        print(f"  Average probe score: {without_report.average_score:.1%}")
        print(f"  Average composite:   {without_report.average_composite:.3f}")
        print(f"  Pass rate:           {without_report.pass_rate:.1%}")

    # Write reports
    if without_report and with_report:
        comparison = MnemBenchComparison(
            with_report=with_report,
            without_report=without_report,
        ).build()
        paths = write_report(
            comparison=comparison,
            with_report=with_report,
            without_report=without_report,
            output_dir=output_dir,
            judge_report=judge_report,
        )
        agg = comparison.aggregate
        print(f"\nComparison summary:")
        print(f"  Score delta:       {agg.get('avg_score_delta', 0):+.1%}")
        print(f"  Composite delta:   {agg.get('avg_composite_delta', 0):+.3f}")
        print(f"  Scenarios improved: {agg.get('scenarios_improved', 0)}/{agg.get('scenarios_total', 0)}")
    else:
        paths = write_report(
            with_report=with_report,
            output_dir=output_dir,
            judge_report=judge_report,
        )

    print(f"\nReports written:")
    print(f"  Markdown: {paths['markdown']}")
    print(f"  JSON:     {paths['json']}")
    if "judge_markdown" in paths:
        print(f"  Judge:    {paths['judge_markdown']}")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="MnemBench — long-running agentic memory system benchmark",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python -m eval.mnembench --server http://localhost:8000 --baseline http://localhost:8002\n"
            "  python -m eval.mnembench --server http://localhost:8000 --scenario ten_session_recall --repeat 3\n"
            "  python -m eval.mnembench --dry-run\n"
            "  python -m eval.mnembench --list\n"
        ),
    )

    # Main options
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Memory-enabled server URL (default: http://localhost:8000)",
    )
    parser.add_argument(
        "--baseline",
        default="http://localhost:8002",
        help="Baseline server URL (no memory). Default :8002",
    )
    parser.add_argument(
        "--scenario",
        "-s",
        nargs="+",
        default=["all"],
        help="Scenario(s) to run (default: all). Use --list to see available IDs.",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        default="eval/results",
        help="Output directory for reports (default: eval/results)",
    )
    parser.add_argument(
        "--repeat",
        "-r",
        type=int,
        default=1,
        help="Number of times to repeat each scenario (default: 1)",
    )

    # Mode flags
    parser.add_argument(
        "--dry-run",
        "-n",
        action="store_true",
        help="Use pre-recorded fixture responses (no API calls)",
    )
    parser.add_argument(
        "--no-baseline",
        action="store_true",
        help="Skip baseline comparison (run with-memory only)",
    )
    parser.add_argument(
        "--no-seed-memory",
        action="store_true",
        help="Disable automatic memory seeding via /api/memory/store",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available scenarios and exit",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Suppress progress output",
    )
    parser.add_argument(
        "--judge-report",
        action="store_true",
        help="Also write a compact Track 1 judge-facing Markdown summary",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print version and exit",
    )

    args = parser.parse_args()

    if args.version:
        from eval.mnembench import __version__
        print(f"MnemBench v{__version__}")
        sys.exit(0)

    if args.list:
        _list_scenarios()
        sys.exit(0)

    asyncio.run(
        _run(
            server=args.server,
            baseline=args.baseline,
            output_dir=Path(args.output_dir),
            scenarios_filter=args.scenario,
            dry_run=args.dry_run,
            seed_memory=not args.no_seed_memory,
            repeat=args.repeat,
            no_baseline=args.no_baseline,
            progress=not args.no_progress,
            judge_report=args.judge_report,
        )
    )


if __name__ == "__main__":
    main()
