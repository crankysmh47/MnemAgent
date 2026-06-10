"""Generate Markdown comparison reports for benchmark runs."""

from __future__ import annotations

from datetime import datetime, timezone

from eval.benchmark_runner import BenchmarkReport


def generate_comparison_report(
    with_memory: BenchmarkReport,
    without_memory: BenchmarkReport,
) -> str:
    """
    Build a side-by-side Markdown report.

    Args:
        with_memory: MnemOS benchmark report.
        without_memory: Baseline report.

    Returns:
        Markdown report string.
    """
    lines = [
        "# MnemOS Benchmark Comparison Report",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Overall Scores",
        "",
        f"| Mode | Average Score |",
        f"| --- | ---: |",
        f"| MnemOS (with memory) | **{with_memory.average_score:.1%}** |",
        f"| Baseline (without memory) | **{without_memory.average_score:.1%}** |",
        "",
        f"**Improvement:** {(with_memory.average_score - without_memory.average_score):.1%}",
        "",
        "## Per-Scenario Results",
        "",
        "| Scenario | MnemOS | Baseline | Delta |",
        "| --- | ---: | ---: | ---: |",
    ]

    without_map = {result.scenario_id: result for result in without_memory.results}
    for result in with_memory.results:
        base = without_map.get(result.scenario_id)
        base_score = base.score if base else 0.0
        delta = result.score - base_score
        lines.append(
            f"| {result.scenario_id} | {result.score:.0%} | {base_score:.0%} | {delta:+.0%} |"
        )

    lines.append("")
    lines.append("## Example Responses")
    lines.append("")
    for result in with_memory.results[:3]:
        base = without_map.get(result.scenario_id)
        lines.append(f"### {result.scenario_id}")
        lines.append(f"**MnemOS:** {result.responses[-1][:200] if result.responses else 'n/a'}")
        if base and base.responses:
            lines.append(f"**Baseline:** {base.responses[-1][:200]}")
        lines.append("")

    return "\n".join(lines)
