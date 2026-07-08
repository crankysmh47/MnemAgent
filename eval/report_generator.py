"""Generate Markdown comparison reports for benchmark runs.

Produces submission-ready reports for the Alibaba Global Hackathon Track 1
(MemoryAgent) with:
  - Executive summary (aggregate scores, pass rates)
  - Category breakdown with ASCII bar chart
  - Statistical summary (mean, median, std dev, min, max)
  - Hackathon-relevant metrics (Context Efficiency, Forgetting Accuracy,
    Recall Precision, Interference Prevention Rate)
  - Per-scenario result table
  - "Night & Day" section highlighting MnemAgent's largest wins with excerpts
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime, timezone

from eval.benchmark_runner import BenchmarkReport, ScenarioResult
from eval.scenarios import ALL_SCENARIOS


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _build_category_map() -> dict[str, str]:
    """Build a mapping from scenario_id to its category string."""
    return {s.id: s.category for s in ALL_SCENARIOS}


def _category_scores(report: BenchmarkReport) -> dict[str, list[float]]:
    """Group scenario scores by category.

    Returns:
        dict mapping category name -> list of scores for that category.
    """
    cat_map = _build_category_map()
    categories: dict[str, list[float]] = defaultdict(list)
    for result in report.results:
        cat = cat_map.get(result.scenario_id, "unknown")
        categories[cat].append(result.score)
    return dict(categories)


def _ascii_bar(score: float, max_width: int = 30) -> str:
    """Render a horizontal ASCII bar proportional to *score* (0.0 – 1.0).

    Uses block characters: ``█`` for the filled portion and ``░`` for the
    unfilled tail.
    """
    filled = round(score * max_width)
    return "█" * filled + "░" * (max_width - filled)


def _stat_summary(report: BenchmarkReport) -> dict[str, float]:
    """Compute descriptive statistics for a report's scores."""
    scores = [r.score for r in report.results]
    if not scores:
        return {"mean": 0.0, "median": 0.0, "stdev": 0.0, "min": 0.0, "max": 0.0}
    return {
        "mean": statistics.mean(scores),
        "median": statistics.median(scores),
        "stdev": statistics.stdev(scores) if len(scores) > 1 else 0.0,
        "min": min(scores),
        "max": max(scores),
    }


# ---------------------------------------------------------------------------
# Category order and label helpers
# ---------------------------------------------------------------------------

_CATEGORY_ORDER = ("recall", "contradiction", "interference", "forgetting", "context")

_CATEGORY_LABELS: dict[str, str] = {
    "recall": "Recall",
    "contradiction": "Contradiction",
    "interference": "Interference",
    "forgetting": "Forgetting",
    "context": "Context",
}

_HACKATHON_METRICS: list[tuple[str, str, str]] = [
    ("Context Efficiency", "context", "Efficiency of using injected context"),
    ("Forgetting Accuracy", "forgetting", "Accuracy of forgetting outdated info"),
    ("Recall Precision", "recall", "Precision of recalled preferences"),
    ("Interference Prevention Rate", "interference", "Rate of preventing proactive interference"),
]


# ---------------------------------------------------------------------------
# Main report entry point
# ---------------------------------------------------------------------------


def generate_comparison_report(
    with_memory: BenchmarkReport,
    without_memory: BenchmarkReport,
) -> str:
    """
    Build a side-by-side Markdown comparison report.

    Args:
        with_memory: MnemAgent benchmark report.
        without_memory: Baseline (no memory) benchmark report.

    Returns:
        Complete Markdown report string.
    """
    cat_map = _build_category_map()
    without_map = {result.scenario_id: result for result in without_memory.results}
    total = len(with_memory.results)

    # Category breakdowns
    with_cats = _category_scores(with_memory)
    without_cats = _category_scores(without_memory)

    # Pass rates
    with_pass = sum(1 for r in with_memory.results if r.passed)
    without_pass = sum(1 for r in without_memory.results if r.passed)

    # Statistics
    with_stats = _stat_summary(with_memory)
    without_stats = _stat_summary(without_memory)

    improvement = with_memory.average_score - without_memory.average_score

    # ------------------------------------------------------------------
    # Header & Executive Summary
    # ------------------------------------------------------------------
    lines: list[str] = [
        "# MnemAgent Benchmark Comparison Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "**Mode:** MnemAgent (with memory) vs Baseline (without memory)",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        "| Metric | MnemAgent | Baseline | Delta |",
        "| --- | ---: | ---: | ---: |",
        f"| **Average Score** | **{with_memory.average_score:.1%}** | {without_memory.average_score:.1%} | **{improvement:+.1%}** |",
        f"| **Pass Rate** | {with_pass}/{total} | {without_pass}/{total} | **{with_pass - without_pass:+d}** |",
        f"| **Total Scenarios** | {total} | {total} | — |",
        "",
        "---",
        "",
    ]

    # ------------------------------------------------------------------
    # Category Breakdown
    # ------------------------------------------------------------------
    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | MnemAgent | Baseline | Delta | Leader |")
    lines.append("| --- | ---: | ---: | ---: | --- |")

    for cat in _CATEGORY_ORDER:
        w_scores = with_cats.get(cat, [])
        wo_scores = without_cats.get(cat, [])
        w_avg = statistics.mean(w_scores) if w_scores else 0.0
        wo_avg = statistics.mean(wo_scores) if wo_scores else 0.0
        delta = w_avg - wo_avg
        leader = "MnemAgent" if delta > 0 else ("Baseline" if delta < 0 else "Tie")
        label = _CATEGORY_LABELS.get(cat, cat.title())
        count = len(w_scores)
        lines.append(
            f"| {label} ({count} scenarios) | {w_avg:.1%} | {wo_avg:.1%} "
            f"| {delta:+.1%} | {leader} |"
        )

    lines.append("")
    lines.append("### Category Comparison (ASCII Bar Chart)")
    lines.append("")
    lines.append("```")
    for cat in _CATEGORY_ORDER:
        w_scores = with_cats.get(cat, [])
        w_avg = statistics.mean(w_scores) if w_scores else 0.0
        bar = _ascii_bar(w_avg)
        label = _CATEGORY_LABELS.get(cat, cat.title()).ljust(14)
        lines.append(f"  {label} {bar} {w_avg:.1%}")
    lines.append("```")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Statistical Summary
    # ------------------------------------------------------------------
    lines.append("## Statistical Summary")
    lines.append("")
    lines.append("| Statistic | MnemAgent | Baseline |")
    lines.append("| --- | ---: | ---: |")
    rows = [
        ("Mean", "mean"),
        ("Median", "median"),
        ("Std Deviation", "stdev"),
        ("Minimum", "min"),
        ("Maximum", "max"),
    ]
    for label, key in rows:
        lines.append(
            f"| **{label}** | {with_stats[key]:.1%} | {without_stats[key]:.1%} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Hackathon-Relevant Metrics
    # ------------------------------------------------------------------
    lines.append("## Hackathon-Relevant Metrics")
    lines.append("")
    lines.append(
        "These metrics map directly to the judging criteria for the Alibaba "
        "Global Hackathon Track 1 (MemoryAgent):"
    )
    lines.append("")
    lines.append("| Metric | MnemAgent | Baseline | Improvement |")
    lines.append("| --- | ---: | ---: | ---: |")

    for label, cat, _desc in _HACKATHON_METRICS:
        w_scores = with_cats.get(cat, [])
        wo_scores = without_cats.get(cat, [])
        w_avg = statistics.mean(w_scores) if w_scores else 0.0
        wo_avg = statistics.mean(wo_scores) if wo_scores else 0.0
        delta = w_avg - wo_avg
        lines.append(
            f"| **{label}** | {w_avg:.1%} | {wo_avg:.1%} | {delta:+.1%} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Per-Scenario Results
    # ------------------------------------------------------------------
    lines.append("## Per-Scenario Results")
    lines.append("")
    lines.append("| Scenario | Category | MnemAgent | Baseline | Delta |")
    lines.append("| --- | --- | ---: | ---: | ---: |")

    for result in with_memory.results:
        base = without_map.get(result.scenario_id)
        base_score = base.score if base else 0.0
        delta = result.score - base_score
        cat = cat_map.get(result.scenario_id, "?").title()
        lines.append(
            f"| {result.scenario_id} | {cat} | {result.score:.0%} "
            f"| {base_score:.0%} | {delta:+.0%} |"
        )

    lines.append("")
    lines.append("---")
    lines.append("")

    # ------------------------------------------------------------------
    # Night & Day — Top MnemAgent Wins
    # ------------------------------------------------------------------
    scored_deltas: list[tuple[str, float, ScenarioResult, ScenarioResult]] = []
    for result in with_memory.results:
        base = without_map.get(result.scenario_id)
        if base is not None and result.score > base.score:
            scored_deltas.append(
                (result.scenario_id, result.score - base.score, result, base)
            )

    scored_deltas.sort(key=lambda x: x[1], reverse=True)
    top_3 = scored_deltas[:3]

    lines.append("## Night & Day: Top 3 Scenarios Where MnemAgent Excels")
    lines.append("")
    lines.append(
        "The following scenarios show the largest performance gap between "
        "MnemAgent and the baseline, with actual response excerpts."
    )
    lines.append("")

    for rank, (sid, delta, w_result, wo_result) in enumerate(top_3, 1):
        cat = cat_map.get(sid, "?").title()
        w_resp = w_result.responses[-1][:300] if w_result.responses else "n/a"
        wo_resp = wo_result.responses[-1][:300] if wo_result.responses else "n/a"
        lines.extend(
            [
                f"### {rank}. {sid} ({delta:+.0%} improvement)",
                f"**Category:** {cat}",
                "",
                "**MnemAgent response:**",
                f"> {w_resp}",
                "",
                "**Baseline response:**",
                f"> {wo_resp}",
                "",
            ]
        )

    if not top_3:
        lines.append(
            "*No scenarios showed a positive improvement for MnemAgent in this run.*"
        )
        lines.append("")

    # ------------------------------------------------------------------
    # Footer
    # ------------------------------------------------------------------
    lines.append("---")
    lines.append("")
    lines.append(
        "*Report generated by MnemAgent Evaluation Framework "
        "— prepared for Alibaba Global Hackathon Track 1 "
        "(MemoryAgent) submission.*"
    )
    lines.append("")

    return "\n".join(lines)
