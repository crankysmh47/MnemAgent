"""Automated scoring functions for benchmark scenarios.

Includes both baseline keyword-based scoring and enhanced hackathon-relevant
scoring functions for evaluating memory systems on:
  - Context efficiency (use injected info, penalize bloat)
  - Cross-session recall (facts taught in session 1 recalled in session N)
  - Proactive interference prevention (prefer current facts over stale ones)
  - Salience precision (F1-style memory precision)
  - Forgetting accuracy (old facts decayed, important ones persist)
  - Composite checks (run multiple sub-checks and average them)
"""

from __future__ import annotations

import json
from collections import defaultdict

from eval.scenarios import Expectation, Scenario


# ---------------------------------------------------------------------------
# Baseline scoring functions (unchanged, fully backward-compatible)
# ---------------------------------------------------------------------------


def score_keyword_present(response: str, keyword: str) -> float:
    """Return 1.0 if keyword appears in response (case-insensitive)."""
    return 1.0 if keyword.lower() in response.lower() else 0.0


def score_keyword_absent(response: str, keyword: str) -> float:
    """Return 1.0 if keyword does NOT appear in response."""
    return 1.0 if keyword.lower() not in response.lower() else 0.0


def score_response_relevance(response: str, expected_topics: list[str]) -> float:
    """Return proportion of expected topics mentioned."""
    if not expected_topics:
        return 1.0
    hits = sum(1 for topic in expected_topics if topic.lower() in response.lower())
    return hits / len(expected_topics)


def score_response_conciseness(response: str, max_words: int) -> float:
    """Return 1.0 if response is under max_words."""
    words = len(response.split())
    if words <= max_words:
        return 1.0
    return max(0.0, 1.0 - (words - max_words) / max_words)


def score_no_question_asked(response: str) -> float:
    """Return 1.0 if agent does not ask clarifying questions."""
    prompts = ("what do you", "which ", "could you tell me", "can you clarify")
    lowered = response.lower()
    return 0.0 if any(p in lowered for p in prompts) else 1.0


def score_contradiction_resolved(response: str, old_value: str, new_value: str) -> float:
    """Score whether contradiction resolution prefers the new value."""
    has_new = new_value.lower() in response.lower()
    has_old = old_value.lower() in response.lower()
    if has_new and not has_old:
        return 1.0
    if has_new and has_old:
        return 0.5
    return 0.0


def score_memory_state(
    memory_dump: str,
    should_contain: list[str],
    should_not_contain: list[str],
) -> float:
    """Score memory dump against expected contents."""
    score_parts: list[float] = []
    for item in should_contain:
        score_parts.append(1.0 if item.lower() in memory_dump.lower() else 0.0)
    for item in should_not_contain:
        score_parts.append(1.0 if item.lower() not in memory_dump.lower() else 0.0)
    if not score_parts:
        return 1.0
    return sum(score_parts) / len(score_parts)


# ---------------------------------------------------------------------------
# Enhanced hackathon-relevant scoring functions
# ---------------------------------------------------------------------------


def score_context_efficiency(
    response: str,
    injected_count: int,
    used_count: int,
) -> float:
    """Measure how efficiently injected context was used, penalizing bloat.

    The core metric is the ratio of used context items to injected items.
    A bloat penalty is applied when the response is excessively verbose
    relative to the number of injected items.

    Args:
        response: The assistant's response string.
        injected_count: Number of context items injected into the prompt.
        used_count: Number of those injected items actually referenced in the response.

    Returns:
        Score in [0.0, 1.0]; higher is better.
    """
    if injected_count <= 0:
        return 1.0

    usage_ratio = used_count / injected_count
    word_count = len(response.split())

    expected_word_count = max(10, injected_count * 30)
    if word_count > expected_word_count:
        bloat_ratio = (word_count - expected_word_count) / expected_word_count
        bloat_penalty = max(0.0, 1.0 - bloat_ratio * 0.5)
        return min(1.0, usage_ratio * bloat_penalty)

    return min(1.0, usage_ratio)


def score_cross_session_recall(
    responses_by_session: dict[str, list[str]],
    expected_facts: dict[str, list[str]],
) -> float:
    """Check if facts taught in earlier sessions are recalled in later sessions.

    For each target session listed in *expected_facts*, the function checks
    whether each fact string appears in any response from that session.

    Args:
        responses_by_session: Mapping of session_id -> list of assistant
            response strings for that session.
        expected_facts: Mapping of target_session_id -> list of fact strings
            that should appear in that session's responses.

    Returns:
        Proportion of expected facts found across the target sessions.
    """
    if not expected_facts:
        return 1.0

    scores: list[float] = []
    for target_session, facts in expected_facts.items():
        session_responses = responses_by_session.get(target_session, [])
        combined = " ".join(session_responses).lower()
        for fact in facts:
            scores.append(1.0 if fact.lower() in combined else 0.0)

    return sum(scores) / len(scores) if scores else 0.0


def score_proactive_interference_prevention(
    response: str,
    stale_fact: str,
    current_fact: str,
) -> float:
    """Score interference prevention when a preference has been superseded.

    Cases:
        - 1.0 : Only the current fact is mentioned (ideal).
        - 0.5 : Both facts are mentioned (partial interference).
        - 0.5 : Neither fact is mentioned (equivocal / avoided the issue).
        - 0.0 : Only the stale fact is mentioned (active interference failure).

    Args:
        response: The assistant's response.
        stale_fact: Fact that should have been superseded.
        current_fact: The correct, current fact.

    Returns:
        Score in [0.0, 1.0].
    """
    has_stale = stale_fact.lower() in response.lower()
    has_current = current_fact.lower() in response.lower()

    if has_current and not has_stale:
        return 1.0
    if has_current and has_stale:
        return 0.5
    if not has_current and has_stale:
        return 0.0
    return 0.5  # neither mentioned — inconclusive


def score_salience_precision(
    memory_dump: str,
    should_contain: list[str],
    should_not_contain: list[str],
) -> float:
    """F1-like score for memory precision.

    Penalises both missing information (false negatives) and hallucinated
    information (false positives) using an F1 formulation:

        precision = TP / (TP + FP)
        recall    = TP / (TP + FN)
        F1        = 2 * P * R / (P + R)

    where:
        TP = should_contain items present in memory dump
        FP = should_not_contain items present in memory dump
        FN = should_contain items absent from memory dump

    Args:
        memory_dump: Snapshot of the agent's memory.
        should_contain: Items that should be present.
        should_not_contain: Items that should be absent.

    Returns:
        F1 score in [0.0, 1.0].
    """
    if not should_contain and not should_not_contain:
        return 1.0

    dump_lower = memory_dump.lower()
    tp = sum(1 for item in should_contain if item.lower() in dump_lower)
    fn = sum(1 for item in should_contain if item.lower() not in dump_lower)
    fp = sum(1 for item in should_not_contain if item.lower() in dump_lower)
    # tn = sum(1 for item in should_not_contain if item.lower() not in dump_lower)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0

    if precision + recall == 0.0:
        return 0.0
    return 2.0 * precision * recall / (precision + recall)


def score_forgetting_accuracy(
    memory_dump: str,
    should_be_forgotten: list[str],
    should_be_remembered: list[str],
) -> float:
    """Verify that old facts have decayed while important ones persist.

    Balanced accuracy: equally weights forgetting (removing stale items)
    and remembering (keeping important items).

    Args:
        memory_dump: Snapshot of agent memory.
        should_be_forgotten: Items that should have been forgotten / removed.
        should_be_remembered: Items that should persist in memory.

    Returns:
        Balanced accuracy score in [0.0, 1.0].
    """
    if not should_be_forgotten and not should_be_remembered:
        return 1.0

    dump_lower = memory_dump.lower()
    forgetting_scores = [
        1.0 if item.lower() not in dump_lower else 0.0
        for item in should_be_forgotten
    ]
    remembering_scores = [
        1.0 if item.lower() in dump_lower else 0.0
        for item in should_be_remembered
    ]

    all_scores = forgetting_scores + remembering_scores
    return sum(all_scores) / len(all_scores)


# ---------------------------------------------------------------------------
# Composite scoring
# ---------------------------------------------------------------------------


def score_composite(
    response: str,
    memory_dump: str,
    sub_checks: list[dict],
    responses_by_session: dict[str, list[str]] | None = None,
) -> float:
    """Run multiple sub-checks and return their average score.

    Each sub-check dict must have at least ``type`` and ``value`` keys.

    Args:
        response: The assistant's final response.
        memory_dump: Snapshot of agent memory.
        sub_checks: List of dicts with ``type`` and ``value`` keys.
        responses_by_session: Optional per-session responses for
            cross-session recall checks.

    Returns:
        Average of all sub-check scores.
    """
    if not sub_checks:
        return 1.0

    scores: list[float] = []
    for check in sub_checks:
        check_type = check.get("type", "")
        check_value = check.get("value", "")
        score = _score_single_check(
            check_type, check_value, response, memory_dump, responses_by_session,
        )
        scores.append(score)

    return sum(scores) / len(scores)


# ---------------------------------------------------------------------------
# Internal dispatch — maps check_type string to scoring function
# ---------------------------------------------------------------------------


def _score_single_check(
    check_type: str,
    check_value: str,
    response: str,
    memory_dump: str,
    responses_by_session: dict[str, list[str]] | None = None,
) -> float:
    """Score a single expectation check by dispatching to the appropriate function.

    This is the single point of dispatch for all check types (both baseline
    and enhanced). It replaces the legacy ``_score_expectation`` for new code.
    """
    # --- Baseline check types ---
    if check_type == "keyword_present":
        return score_keyword_present(response, check_value)
    if check_type == "keyword_absent":
        return score_keyword_absent(response, check_value)
    if check_type == "no_question_asked":
        return score_no_question_asked(response)
    if check_type == "memory_state":
        parts = check_value.split("|")
        contain = [parts[0]] if parts else []
        not_contain = [parts[1]] if len(parts) > 1 else []
        return score_memory_state(memory_dump, contain, not_contain)
    if check_type == "contradiction_resolved":
        old_val, new_val = check_value.split("|", 1)
        return score_contradiction_resolved(response, old_val, new_val)
    if check_type == "relevance":
        topics = [part.strip() for part in check_value.split(",")]
        return score_response_relevance(response, topics)
    if check_type == "conciseness":
        return score_response_conciseness(response, int(check_value))

    # --- Enhanced check types ---
    if check_type == "context_efficiency":
        parts = check_value.split("|")
        injected = int(parts[0]) if parts else 0
        used = int(parts[1]) if len(parts) > 1 else 0
        return score_context_efficiency(response, injected, used)

    if check_type == "proactive_interference":
        stale, current = check_value.split("|", 1)
        return score_proactive_interference_prevention(response, stale, current)

    if check_type == "salience_precision":
        parts = check_value.split("|", 1)
        contain_part = parts[0].strip() if parts else ""
        not_contain_part = parts[1].strip() if len(parts) > 1 else ""
        should_contain = (
            [item.strip() for item in contain_part.split(",")] if contain_part else []
        )
        should_not_contain = (
            [item.strip() for item in not_contain_part.split(",")]
            if not_contain_part
            else []
        )
        return score_salience_precision(memory_dump, should_contain, should_not_contain)

    if check_type == "forgetting_accuracy":
        parts = check_value.split("|", 1)
        forget_part = parts[0].strip() if parts else ""
        remember_part = parts[1].strip() if len(parts) > 1 else ""
        should_forget = (
            [item.strip() for item in forget_part.split(",")] if forget_part else []
        )
        should_remember = (
            [item.strip() for item in remember_part.split(",")] if remember_part else []
        )
        return score_forgetting_accuracy(memory_dump, should_forget, should_remember)

    if check_type == "cross_session_recall":
        try:
            expected_facts = json.loads(check_value)
        except (json.JSONDecodeError, ValueError):
            return 0.0
        return score_cross_session_recall(responses_by_session or {}, expected_facts)

    if check_type == "composite":
        try:
            sub_checks = (
                json.loads(check_value) if isinstance(check_value, str) else check_value
            )
        except (json.JSONDecodeError, ValueError):
            return 0.0
        return score_composite(response, memory_dump, sub_checks, responses_by_session)

    # Unknown check type
    return 0.0


# ---------------------------------------------------------------------------
# Backward-compatibility wrapper
# ---------------------------------------------------------------------------


def _score_expectation(
    expectation: Expectation,
    response: str,
    memory_dump: str,
) -> float:
    """Legacy dispatcher — delegates to ``_score_single_check``.

    Retained for external callers that imported the private function before
    the refactor. New code should call ``_score_single_check`` directly or
    rely on ``compute_scenario_score``.
    """
    return _score_single_check(
        expectation.check_type,
        expectation.check_value,
        response,
        memory_dump,
        responses_by_session=None,
    )


# ---------------------------------------------------------------------------
# Scenario-level orchestrator
# ---------------------------------------------------------------------------


def compute_scenario_score(
    scenario: Scenario,
    responses: list[str],
    memory_dumps: list[str] | None = None,
) -> dict:
    """
    Compute aggregate score for one scenario.

    Builds per-session response groupings from the flat *responses* list
    (by aligning with the scenario's conversation structure) so that
    cross-session recall checks can be evaluated.

    Args:
        scenario: Scenario definition.
        responses: Collected assistant responses (last response used for
            keyword / relevance / conciseness checks).
        memory_dumps: Optional memory dump strings (last one used for
            memory-state checks).

    Returns:
        Score dict with scenario_id, score, details, pass.
    """
    memory_dumps = memory_dumps or []
    final_response = responses[-1] if responses else ""
    memory_dump = memory_dumps[-1] if memory_dumps else ""

    # Align flat responses list with sessions
    responses_by_session: dict[str, list[str]] = {}
    resp_idx = 0
    for session in scenario.conversations:
        session_responses: list[str] = []
        for _ in session.turns:
            if resp_idx < len(responses):
                session_responses.append(responses[resp_idx])
                resp_idx += 1
        responses_by_session[session.session_id] = session_responses

    details: list[dict] = []

    for expectation in scenario.expected_outcomes:
        score = _score_single_check(
            expectation.check_type,
            expectation.check_value,
            final_response,
            memory_dump,
            responses_by_session,
        )
        details.append(
            {
                "check_type": expectation.check_type,
                "description": expectation.description,
                "score": score,
            }
        )

    avg = sum(item["score"] for item in details) / len(details) if details else 0.0
    return {
        "scenario_id": scenario.id,
        "score": avg,
        "details": details,
        "pass": avg >= 0.5,
    }
