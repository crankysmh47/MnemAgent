"""Markdown report generator for agentic memory advantage benchmark."""

from __future__ import annotations

from eval.agentic_runner import AgenticComparisonReport


def generate_agentic_report(comparison: AgenticComparisonReport) -> str:
    """
    Build a markdown report showing growing memory advantage over probe steps.

    Args:
        comparison: Side-by-side agentic benchmark comparison.

    Returns:
        Markdown report string.
    """
    agg = comparison.aggregate
    lines = [
        "# MnemAgent Agentic Memory Advantage Benchmark",
        "",
        "Multi-step scenarios where probe difficulty increases; memory layer advantage should grow.",
        "",
        "## Aggregate Results",
        "",
        f"| Metric | MnemAgent | Baseline |",
        f"|--------|--------|----------|",
        f"| Avg probe score | {agg.get('mnemos_avg_probe_score', 0):.1%} | {agg.get('baseline_avg_probe_score', 0):.1%} |",
        f"| Avg cumulative advantage | {agg.get('avg_cumulative_advantage', 0):+.3f} | — |",
        f"| Weighted cumulative advantage | {agg.get('avg_weighted_cumulative_advantage', 0):+.3f} | — |",
        f"| Avg advantage growth (last−first probe) | {agg.get('avg_advantage_growth', 0):+.3f} | — |",
        f"| Weighted advantage growth | {agg.get('avg_weighted_advantage_growth', 0):+.3f} | — |",
        f"| Avg advantage slope per probe | {agg.get('avg_advantage_slope', 0):+.3f} | — |",
        f"| Scenarios with growing advantage | {agg.get('scenarios_where_advantage_grows', 0)}/{agg.get('total_scenarios', 0)} | — |",
        f"| Scenarios winning final probe | {agg.get('scenarios_memory_wins_final', 0)}/{agg.get('total_scenarios', 0)} | — |",
        f"| Memory layer advantage growth | {agg.get('avg_memory_layer_growth', 0):+.3f} | 0 |",
        f"| Composite advantage growth | {agg.get('avg_composite_growth', 0):+.3f} | — |",
        "",
        "## Per-Scenario Trajectories",
        "",
    ]

    for scenario_id, traj in comparison.trajectories.items():
        lines.append(f"### `{scenario_id}`")
        lines.append("")
        weights = traj.get("probe_weights", [1.0] * len(traj["with_scores"]))
        lines.append("| Probe | Weight | MnemAgent | Baseline | Advantage Δ |")
        lines.append("|-------|--------|--------|----------|-------------|")
        for i, (w, b, a, wt) in enumerate(
            zip(
                traj["with_scores"],
                traj["without_scores"],
                traj["advantage_deltas"],
                weights,
            ),
            start=1,
        ):
            lines.append(f"| {i} | {wt:.0f} | {w:.0%} | {b:.0%} | {a:+.2f} |")
        lines.append("")
        mem = traj.get("memory_layer", {})
        comp = traj.get("composite", {})
        lines.append(
            f"- Behavioral — cumulative: **{traj['cumulative_advantage']:+.3f}** | "
            f"growth: **{traj['advantage_growth']:+.3f}** | slope: **{traj['advantage_slope']:+.3f}**"
        )
        if mem:
            lines.append(
                f"- Memory layer — cumulative: **{mem.get('cumulative_advantage', 0):+.3f}** | "
                f"growth: **{mem.get('advantage_growth', 0):+.3f}** "
                f"(baseline always 0%)"
            )
        if comp:
            lines.append(
                f"- Composite (50% behavior + 50% memory dump) — growth: **{comp.get('advantage_growth', 0):+.3f}**"
            )
        lines.append("")

    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "- **Advantage Δ** = MnemAgent probe score − baseline probe score (higher = memory helped)."
    )
    lines.append(
        "- **Growing advantage** on compound probes shows the memory layer compounding over agentic steps."
    )
    lines.append(
        "- Baseline has no cross-session memory; gap should widen as more facts are taught."
    )
    lines.append(
        "- **Probe weight** = number of facts required (compound probes count more)."
    )
    lines.append(
        "- Live runs seed teach-step facts via `/api/memory/store` unless `--no-seed-memory`."
    )
    lines.append(
        "- **Memory layer** scores `/memory` dump coverage; **behavioral** scores assistant text."
    )
    return "\n".join(lines)
