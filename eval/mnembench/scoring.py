"""Multi-dimensional scoring for MnemBench scenarios.

Scoring dimensions per scenario:
  - recall_precision: keyword matching on expected facts
  - contradiction_score: old value absent, new value present
  - salience_f1: precision+recall of stored vs rejected facts
  - interference_rate: stale facts not mentioned
  - latency_ms: response time impact
  - token_efficiency: tokens consumed per probe

Each scoring function returns a float in [0.0, 1.0] where 1.0 is perfect.
"""

from __future__ import annotations

import statistics

from eval.mnembench.scenarios import MnemBenchScenario, MnemBenchStep
from eval.scoring import (
    score_keyword_present,
    score_keyword_absent,
    score_contradiction_resolved,
    score_no_question_asked,
    score_response_relevance,
)


# ==============================================================================
# Per-expectation scoring dispatcher
# ==============================================================================


def _score_check(
    check_type: str,
    check_value: str,
    response: str,
    memory_dump: str = "",
) -> float:
    """Score a single expectation check, dispatching to the right function.

    Supports all check types from eval.scoring plus MnemBench-specific types.
    """
    if check_type == "keyword_present":
        return score_keyword_present(response, check_value)
    if check_type == "keyword_absent":
        return score_keyword_absent(response, check_value)
    if check_type == "contradiction_resolved":
        parts = check_value.split("|", 1)
        return score_contradiction_resolved(response, parts[0], parts[1])
    if check_type == "no_question_asked":
        return score_no_question_asked(response)
    if check_type == "relevance":
        topics = [t.strip() for t in check_value.split(",")]
        return score_response_relevance(response, topics)
    # Memory state checks
    if check_type == "memory_state":
        parts = check_value.split("|")
        contain = [parts[0]] if parts else []
        not_contain = [parts[1]] if len(parts) > 1 else []
        return _score_memory_state(memory_dump, contain, not_contain)
    # MnemBench-specific: salience F1
    if check_type == "salience_f1":
        parts = check_value.split("|", 1)
        stored = parts[0].strip().split(",") if parts[0] else []
        rejected = parts[1].strip().split(",") if len(parts) > 1 else []
        return score_salience_f1(memory_dump, stored, rejected)
    return 0.0


def _score_memory_state(
    memory_dump: str,
    should_contain: list[str],
    should_not_contain: list[str],
) -> float:
    """Score memory dump against expected contents."""
    scores: list[float] = []
    for item in should_contain:
        scores.append(1.0 if item.lower() in memory_dump.lower() else 0.0)
    for item in should_not_contain:
        scores.append(1.0 if item.lower() not in memory_dump.lower() else 0.0)
    if not scores:
        return 1.0
    return sum(scores) / len(scores)


# ==============================================================================
# Salience F1 scoring
# ==============================================================================


def score_salience_f1(
    memory_dump: str,
    should_be_stored: list[str],
    should_be_rejected: list[str],
) -> float:
    """F1 score for memory salience gating.

    Measures precision and recall of what the memory system stores vs rejects.

    Args:
        memory_dump: Snapshot of agent's current memory.
        should_be_stored: Facts that should appear in memory.
        should_be_rejected: Facts that should NOT appear in memory.

    Returns:
        F1 score in [0.0, 1.0].
    """
    if not should_be_stored and not should_be_rejected:
        return 1.0

    dump_lower = memory_dump.lower()
    tp = sum(1 for item in should_be_stored if item.lower() in dump_lower)
    fn = sum(1 for item in should_be_stored if item.lower() not in dump_lower)
    fp = sum(1 for item in should_be_rejected if item.lower() in dump_lower)

    precision = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if tp > 0 else 0.0)
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


# ==============================================================================
# Per-step scoring
# ==============================================================================


def score_probe_step(
    step: MnemBenchStep,
    response: str,
    memory_dump: str = "",
    latency_ms: float = 0.0,
) -> dict:
    """Score one probe step against its expectations.

    Args:
        step: MnemBench probe step with expectations.
        response: Assistant response for this step.
        memory_dump: Optional snapshot of agent memory.
        latency_ms: Response time in milliseconds.

    Returns:
        Dict with step_index, label, score, details, and pass status.
    """
    details: list[dict] = []
    for check_type, check_value, description in step.expectations:
        score = _score_check(check_type, check_value, response, memory_dump)
        details.append({
            "check_type": check_type,
            "description": description,
            "score": score,
        })

    avg = sum(d["score"] for d in details) / len(details) if details else 0.0

    return {
        "step_index": step.step_index,
        "label": step.label or f"step-{step.step_index}",
        "phase": step.phase,
        "score": avg,
        "details": details,
        "pass": avg >= 0.5,
        "latency_ms": latency_ms,
    }


# ==============================================================================
# Multi-dimensional scoring
# ==============================================================================


def compute_dimension_scores(
    scenario: MnemBenchScenario,
    step_responses: dict[int, str],
    memory_dumps: dict[int, str] | None = None,
    latencies: dict[int, float] | None = None,
) -> dict:
    """Compute all scoring dimensions for a scenario.

    Dimensions:
      - recall_precision: keyword hits across all probe steps
      - contradiction_score: old-safe, new-present across contradict steps
      - salience_f1: F1 of stored vs rejected facts in memory
      - interference_rate: avoidance of stale facts
      - latency_ms: average response time
      - token_efficiency: estimated token cost (requires metadata)

    Args:
        scenario: The scenario definition.
        step_responses: Map of step_index -> response text.
        memory_dumps: Optional map of step_index -> memory dump text.
        latencies: Optional map of step_index -> latency in ms.

    Returns:
        Dict of scoring dimension -> value.
    """
    memory_dumps = memory_dumps or {}
    latencies = latencies or {}

    recall_scores: list[float] = []
    contradiction_scores: list[float] = []
    interference_scores: list[float] = []
    all_latencies: list[float] = []
    stored_terms: list[str] = []
    rejected_terms: list[str] = []

    for step in scenario.steps:
        response = step_responses.get(step.step_index, "")
        dump = memory_dumps.get(step.step_index, "")
        lat = latencies.get(step.step_index, 0.0)

        if step.phase in ("probe", "contradict") and step.expectations:
            for check_type, check_value, description in step.expectations:
                check_score = _score_check(check_type, check_value, response, dump)

                if check_type == "keyword_present":
                    recall_scores.append(check_score)
                elif check_type == "contradiction_resolved":
                    contradiction_scores.append(check_score)
                elif check_type == "keyword_absent":
                    interference_scores.append(1.0 - check_score)

        if lat > 0:
            all_latencies.append(lat)

        # Collect memory dump terms for salience F1 analysis
        if step.memory_seed is not None and dump:
            stored_terms.append(step.memory_seed.value)
        if step.phase == "teach" and not step.memory_seed and dump:
            # Hedged statements that should NOT appear in memory
            rejected_terms.append(step.user_message)

    # Build dimension scores
    recall_precision = statistics.mean(recall_scores) if recall_scores else 0.0
    contradiction_score = (
        1.0 - statistics.mean(contradiction_scores) if contradiction_scores
        else 0.0
    )
    # Invert: we want 0 interference
    interference_rate = (
        1.0 - (statistics.mean(interference_scores) if interference_scores else 0.0)
    )
    latency_ms = statistics.mean(all_latencies) if all_latencies else 0.0

    # Salience F1 — use the last memory dump
    last_dump = ""
    if memory_dumps:
        last_idx = max(memory_dumps.keys(), default=None)
        if last_idx is not None:
            last_dump = memory_dumps[last_idx]
    salience = score_salience_f1(last_dump, stored_terms, rejected_terms)

    return {
        "recall_precision": round(recall_precision, 3),
        "contradiction_score": round(contradiction_score, 3),
        "salience_f1": round(salience, 3),
        "interference_rate": round(interference_rate, 3),
        "latency_ms": round(latency_ms, 1),
    }


# ==============================================================================
# Scenario-level scoring (unified entry point)
# ==============================================================================


def score_mnembench_scenario(
    scenario: MnemBenchScenario,
    step_responses: dict[int, str],
    memory_dumps: dict[int, str] | None = None,
    latencies: dict[int, float] | None = None,
) -> dict:
    """Score a complete MnemBench scenario with per-probe breakdown.

    Args:
        scenario: Scenario definition.
        step_responses: Map step_index -> response.
        memory_dumps: Optional map step_index -> memory dump.
        latencies: Optional map step_index -> latency in ms.

    Returns:
        Score dict with per-probe results, dimension scores, and aggregate.
    """
    memory_dumps = memory_dumps or {}
    latencies = latencies or {}

    # Per-probe scoring
    probe_results: list[dict] = []
    for step in scenario.probe_steps:
        response = step_responses.get(step.step_index, "")
        dump = memory_dumps.get(step.step_index, "")
        lat = latencies.get(step.step_index, 0.0)
        probe_results.append(score_probe_step(step, response, dump, lat))

    # Compute dimension scores
    dimensions = compute_dimension_scores(
        scenario, step_responses, memory_dumps, latencies
    )

    # Aggregate scores
    probe_scores = [p["score"] for p in probe_results]

    # Average probe score — simple mean
    score_avg = (
        statistics.mean(probe_scores) if probe_scores else 0.0
    )

    # Weighted by number of expectations per probe
    weights: list[int] = []
    for step in scenario.probe_steps:
        weights.append(len(step.expectations) or 1)
    weighted_avg = 0.0
    if probe_scores and weights:
        w_sum = sum(weights)
        weighted_avg = (
            sum(s * w for s, w in zip(probe_scores, weights)) / w_sum
        )

    # Composite: average of probe score and salience / recall dimensions
    composite = round(
        0.4 * score_avg
        + 0.2 * dimensions["salience_f1"]
        + 0.2 * dimensions["contradiction_score"]
        + 0.1 * dimensions["interference_rate"]
        + 0.1 * dimensions["recall_precision"],
        3,
    )

    return {
        "scenario_id": scenario.id,
        "scenario_name": scenario.name,
        "category": scenario.category,
        "probe_results": probe_results,
        "dimensions": dimensions,
        "average_probe_score": round(score_avg, 3),
        "weighted_probe_score": round(weighted_avg, 3),
        "composite_score": composite,
        "pass": score_avg >= 0.5,
    }


# ==============================================================================
# Comparison metrics
# ==============================================================================


def compute_comparison_scores(
    with_scores: dict,
    without_scores: dict,
) -> dict:
    """Compare with-memory vs without-memory scenario results.

    Args:
        with_scores: Scoring result for with-memory run.
        without_scores: Scoring result for without-memory run.

    Returns:
        Comparison dict with deltas and advantage metrics.
    """
    w_dims = with_scores.get("dimensions", {})
    wo_dims = without_scores.get("dimensions", {})

    deltas = {}
    for key in set(list(w_dims.keys()) + list(wo_dims.keys())):
        w_val = w_dims.get(key, 0.0)
        wo_val = wo_dims.get(key, 0.0)
        if isinstance(w_val, (int, float)) and isinstance(wo_val, (int, float)):
            deltas[key] = round(w_val - wo_val, 3)

    w_probe_scores = [
        p["score"] for p in with_scores.get("probe_results", [])
    ]
    wo_probe_scores = [
        p["score"] for p in without_scores.get("probe_results", [])
    ]

    # Compute advantage per probe
    min_len = min(len(w_probe_scores), len(wo_probe_scores))
    advantages = [
        round(w_probe_scores[i] - wo_probe_scores[i], 3)
        for i in range(min_len)
    ]

    return {
        "dimension_deltas": deltas,
        "probe_advantages": advantages,
        "score_delta": round(
            with_scores.get("average_probe_score", 0)
            - without_scores.get("average_probe_score", 0),
            3,
        ),
        "composite_delta": round(
            with_scores.get("composite_score", 0)
            - without_scores.get("composite_score", 0),
            3,
        ),
        "memory_advantage": sum(advantages) / len(advantages) if advantages else 0.0,
    }
