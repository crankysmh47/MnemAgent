"""Scoring and trajectory metrics for multi-step agentic benchmarks."""

from __future__ import annotations

from eval.agentic_scenarios import AgenticScenario, AgenticStep
from eval.scenarios import Expectation
from eval.scoring import (
    score_contradiction_resolved,
    score_keyword_absent,
    score_keyword_present,
    score_memory_state,
    score_no_question_asked,
    score_response_relevance,
)


def expected_memory_terms(step: AgenticStep) -> list[str]:
    """Keywords that should appear in memory after successful teach + retrieval."""
    terms: list[str] = []
    for expectation in step.expectations:
        if expectation.check_type == "keyword_present":
            terms.append(expectation.check_value)
        elif expectation.check_type == "relevance":
            terms.extend(part.strip() for part in expectation.check_value.split(","))
    return terms


def score_probe_memory_coverage(step: AgenticStep, memory_dump: str) -> float:
    """Fraction of expected probe keywords visible in /memory dump."""
    terms = expected_memory_terms(step)
    if not terms or not memory_dump:
        return 0.0
    hits = sum(1 for term in terms if term.lower() in memory_dump.lower())
    return hits / len(terms)


def score_scenario_memory_progress(
    scenario: AgenticScenario,
    through_step_index: int,
    memory_dump: str,
) -> float:
    """
    Fraction of all scenario facts accumulated in memory by this step.

    Grows across interleaved teach/probe steps (e.g. 1/4 → 4/4); baseline stays 0.
    """
    all_seeds = [s.memory_seed for s in scenario.steps if s.memory_seed]
    seeds_so_far = [
        s.memory_seed
        for s in scenario.steps
        if s.step_index <= through_step_index and s.memory_seed
    ]
    if not all_seeds or not seeds_so_far or not memory_dump:
        return 0.0
    hits = sum(
        1
        for seed in seeds_so_far
        if seed and seed.value.lower() in memory_dump.lower()
    )
    return hits / len(all_seeds)


def score_probe_step(
    step: AgenticStep,
    response: str,
    memory_dump: str = "",
    scenario: AgenticScenario | None = None,
) -> dict:
    """
    Score one probe step against its expectations.

    Args:
        step: Agentic probe step with expectations.
        response: Assistant response for this step.
        memory_dump: Optional memory dump after the step.

    Returns:
        Dict with step_index, label, score, details, pass.
    """
    details: list[dict] = []
    for expectation in step.expectations:
        score = _score_expectation(expectation, response, memory_dump)
        details.append(
            {
                "check_type": expectation.check_type,
                "description": expectation.description,
                "score": score,
            }
        )
    avg = sum(d["score"] for d in details) / len(details) if details else 0.0
    memory_coverage = score_probe_memory_coverage(step, memory_dump)
    memory_progress = (
        score_scenario_memory_progress(scenario, step.step_index, memory_dump)
        if scenario
        else memory_coverage
    )
    composite = round(0.5 * avg + 0.5 * memory_progress, 3) if memory_dump else avg
    return {
        "step_index": step.step_index,
        "label": step.label or f"step-{step.step_index}",
        "phase": step.phase,
        "score": avg,
        "memory_coverage": memory_coverage,
        "memory_progress": memory_progress,
        "composite_score": composite,
        "details": details,
        "pass": avg >= 0.5,
    }


def _score_expectation(expectation: Expectation, response: str, memory_dump: str) -> float:
    check = expectation.check_type
    value = expectation.check_value
    if check == "keyword_present":
        return score_keyword_present(response, value)
    if check == "keyword_absent":
        return score_keyword_absent(response, value)
    if check == "no_question_asked":
        return score_no_question_asked(response)
    if check == "memory_state":
        parts = value.split("|")
        contain = [parts[0]] if parts else []
        not_contain = [parts[1]] if len(parts) > 1 else []
        return score_memory_state(memory_dump, contain, not_contain)
    if check == "contradiction_resolved":
        old_val, new_val = value.split("|", 1)
        return score_contradiction_resolved(response, old_val, new_val)
    if check == "relevance":
        topics = [part.strip() for part in value.split(",")]
        return score_response_relevance(response, topics)
    return 0.0


def probe_difficulty_weights(probe_steps: list[AgenticStep]) -> list[float]:
    """Weight each probe by number of expectations (compound probes weigh more)."""
    weights: list[float] = []
    for step in probe_steps:
        n = len(step.expectations) or 1
        weights.append(float(n))
    return weights


def compute_memory_advantage_trajectory(
    with_probe_scores: list[float],
    without_probe_scores: list[float],
    probe_weights: list[float] | None = None,
) -> dict:
    """
    Compute how much the memory layer advantage grows across probe steps.

    Args:
        with_probe_scores: Per-probe scores for MnemOS (0–1).
        without_probe_scores: Per-probe scores for baseline (0–1).

    Returns:
        Trajectory metrics including advantage deltas and slope.
    """
    n = min(len(with_probe_scores), len(without_probe_scores))
    with_scores = with_probe_scores[:n]
    without_scores = without_probe_scores[:n]
    advantages = [round(w - b, 3) for w, b in zip(with_scores, without_scores)]

    cumulative = round(sum(advantages), 3)
    final_gap = advantages[-1] if advantages else 0.0
    initial_gap = advantages[0] if advantages else 0.0
    growth = round(final_gap - initial_gap, 3)

    # Linear slope: average increase in advantage per probe step
    slope = 0.0
    if len(advantages) > 1:
        slope = round((advantages[-1] - advantages[0]) / (len(advantages) - 1), 3)

    monotonic_steps = 0
    for i in range(1, len(advantages)):
        if advantages[i] >= advantages[i - 1]:
            monotonic_steps += 1
    monotonic_ratio = monotonic_steps / max(1, len(advantages) - 1)

    weights = (probe_weights or [1.0] * n)[:n]
    if len(weights) < n:
        weights.extend([1.0] * (n - len(weights)))
    weight_sum = sum(weights) or 1.0
    weighted_cumulative = round(
        sum(a * w for a, w in zip(advantages, weights)) / weight_sum, 3
    )
    weighted_growth = 0.0
    if len(advantages) > 1:
        w_first, w_last = weights[0], weights[-1]
        weighted_growth = round(
            (advantages[-1] * w_last - advantages[0] * w_first) / max(w_first, w_last), 3
        )

    return {
        "probe_count": n,
        "probe_weights": weights,
        "with_scores": with_scores,
        "without_scores": without_scores,
        "advantage_deltas": advantages,
        "cumulative_advantage": cumulative,
        "weighted_cumulative_advantage": weighted_cumulative,
        "initial_gap": initial_gap,
        "final_gap": final_gap,
        "advantage_growth": growth,
        "weighted_advantage_growth": weighted_growth,
        "advantage_slope": slope,
        "monotonic_ratio": round(monotonic_ratio, 3),
        "memory_wins_all_probes": all(a > 0 for a in advantages),
        "memory_wins_final_probe": final_gap > 0,
    }


def score_agentic_scenario(
    scenario: AgenticScenario,
    step_responses: dict[int, str],
    memory_dumps: dict[int, str] | None = None,
) -> dict:
    """
    Score all probe steps in a scenario.

    Args:
        scenario: Full agentic scenario definition.
        step_responses: Map step_index → assistant response.
        memory_dumps: Optional map step_index → memory dump.

    Returns:
        Scenario score summary with per-probe breakdown.
    """
    memory_dumps = memory_dumps or {}
    probe_results: list[dict] = []
    for step in scenario.probe_steps:
        response = step_responses.get(step.step_index, "")
        dump = memory_dumps.get(step.step_index, "")
        probe_results.append(score_probe_step(step, response, dump, scenario=scenario))

    probe_scores = [r["score"] for r in probe_results]
    memory_scores = [r.get("memory_progress", r["memory_coverage"]) for r in probe_results]
    composite_scores = [r["composite_score"] for r in probe_results]
    weights = probe_difficulty_weights(scenario.probe_steps)
    avg = sum(probe_scores) / len(probe_scores) if probe_scores else 0.0
    weighted_avg = 0.0
    if probe_scores and weights:
        w_sum = sum(weights)
        weighted_avg = sum(s * w for s, w in zip(probe_scores, weights)) / w_sum
    mem_avg = sum(memory_scores) / len(memory_scores) if memory_scores else 0.0
    composite_avg = sum(composite_scores) / len(composite_scores) if composite_scores else 0.0
    return {
        "scenario_id": scenario.id,
        "scenario_name": scenario.name,
        "category": scenario.category,
        "probe_results": probe_results,
        "average_probe_score": avg,
        "average_memory_coverage": mem_avg,
        "average_composite_score": composite_avg,
        "weighted_probe_score": weighted_avg,
        "pass": avg >= 0.5,
    }
