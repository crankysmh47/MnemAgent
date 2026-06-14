"""MnemBench report generator — Markdown reports with ASCII trajectory charts.

Produces:
  - Markdown report with per-scenario tables and trajectory charts
  - JSON results file for programmatic access
  - Comparison mode: side-by-side with baseline
  - Executive summary with overall scores
"""

from __future__ import annotations

import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from eval.mnembench.runner import MnemBenchComparison, MnemBenchReport, MnemBenchScenarioRun


# ==============================================================================
# ASCII chart utilities
# ==============================================================================


def _ascii_bar(score: float, max_width: int = 30) -> str:
    """Render a horizontal ASCII bar proportional to score (0.0-1.0)."""
    filled = max(0, min(max_width, round(score * max_width)))
    return "█" * filled + "░" * (max_width - filled)


def _ascii_trajectory(
    with_scores: list[float],
    without_scores: list[float],
    width: int = 40,
    height: int = 8,
) -> list[str]:
    """Render a simple ASCII line chart comparing two score trajectories.

    Args:
        with_scores: Probe scores for with-memory.
        without_scores: Probe scores for without-memory.
        width: Character width of the chart.
        height: Character height of the chart.

    Returns:
        List of strings forming the ASCII chart.
    """
    if not with_scores and not without_scores:
        return ["(no data)"]

    all_scores = with_scores + without_scores
    if not all_scores:
        return ["(no data)"]

    min_score = min(all_scores)
    max_score = max(all_scores)
    score_range = max(max_score - min_score, 0.001)

    def _val_to_row(val: float) -> int:
        return height - 1 - round((val - min_score) / score_range * (height - 1))

    n_points = max(len(with_scores), len(without_scores))
    grid: list[list[str]] = [[" "] * width for _ in range(height)]

    # Draw axes
    for row in range(height):
        grid[row][0] = "|"
    for col in range(width):
        grid[height - 1][col] = "-" if col > 0 else "+"

    def _plot_series(scores: list[float], marker: str) -> None:
        if len(scores) < 2:
            return
        for i in range(len(scores) - 1):
            x1 = max(1, round(i / (n_points - 1) * (width - 1))) if n_points > 1 else 1
            x2 = max(1, round((i + 1) / (n_points - 1) * (width - 1))) if n_points > 1 else 1
            y1 = _val_to_row(scores[i])
            y2 = _val_to_row(scores[i + 1])
            # Draw line
            steps = max(abs(x2 - x1), abs(y2 - y1))
            for t in range(steps + 1):
                frac = t / steps if steps > 0 else 0
                x = round(x1 + (x2 - x1) * frac)
                y = round(y1 + (y2 - y1) * frac)
                if 0 <= y < height and 0 <= x < width:
                    if grid[y][x] == " " or grid[y][x] == "|" or grid[y][x] == "-":
                        grid[y][x] = marker

    _plot_series(with_scores, "*")
    _plot_series(without_scores, "o")

    # Add legend
    grid[0][width - 8:width] = list("* = with")
    grid[1][width - 8:width] = list("o = w/o ")

    return ["".join(row) for row in grid]


def _dimension_radar_chart(dimensions: dict[str, float], width: int = 24) -> list[str]:
    """Render a simple ASCII radar/spider chart for dimensions."""
    labels = list(dimensions.keys())
    if not labels:
        return ["(no dimensions)"]

    lines: list[str] = []
    for label in labels:
        val = dimensions.get(label, 0.0)
        bar = _ascii_bar(val, width - len(label) - 2)
        lines.append(f"  {label.ljust(18)} {bar} {val:.2f}")
    return lines


# ==============================================================================
# Report generation
# ==============================================================================


def _build_category_map(scenarios: list) -> dict[str, str]:
    """Build scenario_id -> category mapping."""
    # Import here to avoid circular imports
    from eval.mnembench.scenarios import ALL_MNEMBENCH_SCENARIOS
    return {s.id: s.category for s in ALL_MNEMBENCH_SCENARIOS}


def generate_mnembench_report(
    comparison: MnemBenchComparison | None = None,
    with_report: MnemBenchReport | None = None,
    without_report: MnemBenchReport | None = None,
) -> str:
    """Generate a Markdown report for MnemBench results.

    Args:
        comparison: Optional comparison between with/without memory.
        with_report: Required if comparison not provided.
        without_report: Required if comparison not provided.

    Returns:
        Markdown report string.
    """
    from eval.mnembench.scenarios import ALL_MNEMBENCH_SCENARIOS
    cat_map = _build_category_map(ALL_MNEMBENCH_SCENARIOS)

    if comparison is not None:
        with_report = comparison.with_report
        without_report = comparison.without_report
    else:
        if with_report is None:
            raise ValueError("Must provide either comparison or with_report")

    lines: list[str] = [
        "# MnemBench — Long-Running Memory System Benchmark",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
    ]

    # ── Aggregate comparison table ──
    if comparison is not None:
        agg = comparison.aggregate
        lines.append("| Metric | With Memory | Without Memory | Delta |")
        lines.append("|--------|------------:|---------------:|------:|")
        lines.append(
            f"| **Average Probe Score** | {agg.get('with_avg_score', 0):.1%} "
            f"| {agg.get('without_avg_score', 0):.1%} "
            f"| {agg.get('avg_score_delta', 0):+.1%} |"
        )
        lines.append(
            f"| **Average Composite Score** | {agg.get('with_avg_composite', 0):.3f} "
            f"| {agg.get('without_avg_composite', 0):.3f} "
            f"| {agg.get('avg_composite_delta', 0):+.3f} |"
        )
        lines.append(
            f"| **Pass Rate** | {agg.get('with_pass_rate', 0):.1%} "
            f"| {agg.get('without_pass_rate', 0):.1%} "
            f"| {agg.get('scenarios_improved', 0)}/{agg.get('scenarios_total', 0)} improved |"
        )
    else:
        lines.append(
            f"| Average Probe Score | {with_report.average_score:.1%} |"
        )
        lines.append(
            f"| Pass Rate | {with_report.pass_rate:.1%} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Per-scenario results ──
    lines.append("## Per-Scenario Results")
    lines.append("")

    if comparison is not None:
        without_by_id = {r.scenario_id: r for r in without_report.runs}
        lines.append("| Scenario | Category | With Memory | Without Memory | Delta | Pass |")
        lines.append("|----------|----------|------------:|---------------:|------:|:----:|")
        for with_run in with_report.runs:
            without_run = without_by_id.get(with_run.scenario_id)
            wo_score = without_run.average_probe_score if without_run else 0.0
            delta = with_run.average_probe_score - wo_score
            cat = cat_map.get(with_run.scenario_id, "?").title()
            passed = "Yes" if with_run.score_summary.get("pass", False) else "No"
            lines.append(
                f"| {with_run.scenario_id} | {cat} "
                f"| {with_run.average_probe_score:.1%} "
                f"| {wo_score:.1%} "
                f"| {delta:+.1%} "
                f"| {passed} |"
            )
    else:
        lines.append("| Scenario | Category | Score | Pass |")
        lines.append("|----------|----------|------:|:----:|")
        for run in with_report.runs:
            cat = cat_map.get(run.scenario_id, "?").title()
            passed = "Yes" if run.score_summary.get("pass", False) else "No"
            lines.append(
                f"| {run.scenario_id} | {cat} "
                f"| {run.average_probe_score:.1%} "
                f"| {passed} |"
            )

    lines.append("")
    lines.append("---")
    lines.append("")

    # ── Score trajectories (ASCII charts) ──
    lines.append("## Score Trajectories")
    lines.append("")
    lines.append(
        "The charts below show probe-by-probe scores. "
        "A rising trajectory indicates the memory layer compounding advantage "
        "across steps."
    )
    lines.append("")

    if comparison is not None:
        # Side-by-side trajectories
        for with_run in with_report.runs:
            without_run = without_by_id.get(with_run.scenario_id)
            wo_probes = without_run.score_summary.get("probe_results", []) if without_run else []
            w_probes = with_run.score_summary.get("probe_results", [])

            with_scores = [p["score"] for p in w_probes]
            without_scores = [p["score"] for p in wo_probes]

            if not with_scores:
                continue

            lines.append(f"### `{with_run.scenario_id}`")
            lines.append("")

            # Probe detail table
            lines.append("| Probe | Label | With Memory | Without Memory | Delta |")
            lines.append("|-------|-------|------------:|---------------:|------:|")
            max_len = max(len(with_scores), len(without_scores))
            for i in range(max_len):
                w_score = with_scores[i] if i < len(with_scores) else 0.0
                wo_score = without_scores[i] if i < len(without_scores) else 0.0
                label = w_probes[i].get("label", f"step-{i + 1}") if i < len(w_probes) else f"step-{i + 1}"
                delta = w_score - wo_score
                lines.append(
                    f"| {i + 1} | {label} | {w_score:.1%} | {wo_score:.1%} | {delta:+.1%} |"
                )
            lines.append("")

            # ASCII trajectory chart
            lines.append("```")
            for chart_line in _ascii_trajectory(with_scores, without_scores):
                lines.append(chart_line)
            lines.append("```")
            lines.append("")

            # Dimensions
            dims = with_run.dimensions or {}
            if dims:
                lines.append("**Dimension scores:**")
                lines.append("```")
                for chart_line in _dimension_radar_chart(dims):
                    lines.append(chart_line)
                lines.append("```")
                lines.append("")

            # Comparison dimensions deltas
            if comparison and with_run.scenario_id in comparison.comparisons:
                comp = comparison.comparisons[with_run.scenario_id]
                deltas = comp.get("dimension_deltas", {})
                if deltas:
                    lines.append("**Dimension deltas (with - without):**")
                    lines.append("")
                    lines.append("| Dimension | Delta |")
                    lines.append("|-----------|------:|")
                    for dim, delta in sorted(deltas.items(), key=lambda x: abs(x[1]), reverse=True):
                        lines.append(f"| {dim} | {delta:+.3f} |")
                    lines.append("")

            lines.append("---")
            lines.append("")
    else:
        # Single mode trajectories
        for run in with_report.runs:
            probes = run.score_summary.get("probe_results", [])
            scores = [p["score"] for p in probes]
            if not scores:
                continue

            lines.append(f"### `{run.scenario_id}`")
            lines.append("")
            lines.append("| Probe | Label | Score |")
            lines.append("|-------|-------|------:|")
            for i, probe in enumerate(probes):
                lines.append(
                    f"| {i + 1} | {probe.get('label', f'step-{i + 1}')} "
                    f"| {probe['score']:.1%} |"
                )
            lines.append("")

            dims = run.dimensions or {}
            if dims:
                lines.append("**Dimension scores:**")
                lines.append("```")
                for chart_line in _dimension_radar_chart(dims):
                    lines.append(chart_line)
                lines.append("```")
                lines.append("")

            lines.append("---")
            lines.append("")

    # ── Dimension summary (aggregate) ──
    if comparison is not None:
        agg = comparison.aggregate
        dim_deltas = agg.get("avg_dimension_deltas", {})
    else:
        dim_deltas = {}

    if dim_deltas:
        lines.append("## Aggregate Dimension Deltas")
        lines.append("")
        lines.append("| Dimension | Avg Delta |")
        lines.append("|-----------|----------:|")
        for dim, delta in sorted(dim_deltas.items(), key=lambda x: abs(x[1]), reverse=True):
            lines.append(f"| {dim} | {delta:+.3f} |")
        lines.append("")
        lines.append("---")
        lines.append("")

    # ── Interpretation ──
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- **Probe Score**: Proportion of keyword expectations met in the agent's response.")
    lines.append("- **Composite Score**: Weighted combination of probe score, salience F1, contradiction resolution, interference prevention, and recall precision.")
    lines.append("- **Score Trajectory**: `*` = with memory, `o` = without memory. Rising trajectory = compounding memory advantage.")
    lines.append("- **Dimensions**: Multi-aspect evaluation including recall precision, salience F1, contradiction resolution, interference rate, and latency.")
    lines.append("- **Dimension Delta**: Positive values mean the memory system outperformed the baseline on that dimension.")
    lines.append("- **Dry-run mode**: Uses pre-recorded fixture responses. Useful for testing the benchmark harness without API calls.")

    return "\n".join(lines)


# ==============================================================================
# JSON export
# ==============================================================================


def export_json(
    comparison: MnemBenchComparison | None = None,
    with_report: MnemBenchReport | None = None,
    output_path: str | Path | None = None,
) -> dict:
    """Export results as a JSON-serializable dict.

    Args:
        comparison: Optional comparison results.
        with_report: Required if comparison not provided.
        output_path: Optional file path to write JSON.

    Returns:
        Dict with all results.
    """
    if comparison is not None:
        with_report = comparison.with_report
    if with_report is None:
        raise ValueError("Must provide either comparison or with_report")

    data: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": with_report.mode,
        "summary": {
            "average_score": with_report.average_score,
            "average_composite": with_report.average_composite,
            "pass_rate": with_report.pass_rate,
            "num_runs": len(with_report.runs),
        },
        "scenarios": [],
    }

    for run in with_report.runs:
        scenario_data = {
            "scenario_id": run.scenario_id,
            "mode": run.mode,
            "average_probe_score": run.average_probe_score,
            "composite_score": run.composite_score,
            "dimensions": run.dimensions,
            "probe_results": run.score_summary.get("probe_results", []),
            "pass": run.score_summary.get("pass", False),
        }
        data["scenarios"].append(scenario_data)

    if comparison is not None:
        data["comparison"] = {
            "aggregate": comparison.aggregate,
            "per_scenario": comparison.comparisons,
        }
        data["without_summary"] = {
            "average_score": comparison.without_report.average_score,
            "average_composite": comparison.without_report.average_composite,
            "pass_rate": comparison.without_report.pass_rate,
        }

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")

    return data


# ==============================================================================
# Report writer (convenience)
# ==============================================================================


def write_report(
    comparison: MnemBenchComparison | None = None,
    with_report: MnemBenchReport | None = None,
    without_report: MnemBenchReport | None = None,
    output_dir: str | Path = "eval/results",
    prefix: str = "mnembench",
) -> dict[str, Path]:
    """Write Markdown and JSON reports to disk.

    Args:
        comparison: Optional comparison results.
        with_report: Required if comparison not provided.
        without_report: Required if comparison not provided.
        output_dir: Directory to write reports to.
        prefix: Filename prefix.

    Returns:
        Dict with "markdown" and "json" paths.
    """
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    md = generate_mnembench_report(comparison, with_report, without_report)
    md_path = out_dir / f"{prefix}_report_{timestamp}.md"
    md_path.write_text(md, encoding="utf-8")

    json_data = export_json(comparison, with_report)
    json_path = out_dir / f"{prefix}_results_{timestamp}.json"
    json_path.write_text(json.dumps(json_data, indent=2, default=str), encoding="utf-8")

    return {"markdown": md_path, "json": json_path}
