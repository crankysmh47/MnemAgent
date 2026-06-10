"""Automated scoring functions for benchmark scenarios."""

from __future__ import annotations

from eval.scenarios import Expectation, Scenario


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


def compute_scenario_score(
    scenario: Scenario,
    responses: list[str],
    memory_dumps: list[str] | None = None,
) -> dict:
    """
    Compute aggregate score for one scenario.

    Args:
        scenario: Scenario definition.
        responses: Collected assistant responses (last response used for scoring).
        memory_dumps: Optional memory dump strings.

    Returns:
        Score dict with scenario_id, score, details, pass.
    """
    memory_dumps = memory_dumps or []
    final_response = responses[-1] if responses else ""
    memory_dump = memory_dumps[-1] if memory_dumps else ""
    details: list[dict] = []

    for expectation in scenario.expected_outcomes:
        score = _score_expectation(expectation, final_response, memory_dump)
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


def _score_expectation(
    expectation: Expectation,
    response: str,
    memory_dump: str,
) -> float:
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
    if check == "conciseness":
        return score_response_conciseness(response, int(value))
    return 0.0
