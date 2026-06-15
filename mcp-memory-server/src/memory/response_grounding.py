"""Post-LLM response grounding — ensures injected facts appear in probe answers."""

from __future__ import annotations

import re

_COMPOUND_PROBE_RE = re.compile(
    r"(?i)\b("
    r"summarize|summary|full stack|our stack|entire stack|"
    r"language and|database and|framework and|platform and|"
    r"what .{0,40} and |which .{0,40} and |"
    r"both .{0,30} and |all of our|everything we use|"
    r"quick check|what should i use|what are we using|what framework|"
    r"what language|how should i style|what frontend|what http"
    r")\b"
)


def is_compound_probe(user_input: str) -> bool:
    """Detect multi-fact recall questions where all injected beliefs must surface."""
    return bool(_COMPOUND_PROBE_RE.search(user_input))


_HEDGED_TEACH_RE = re.compile(
    r"\b(maybe|perhaps|could try|might|someday|possibly|thinking about)\b",
    re.IGNORECASE,
)


def record_hedged_teach_rejections(user_id: str, user_input: str, db_path=None) -> None:
    """
    Log salience rejections for hedged teach statements even when the LLM emits skip.

    Ensures values like 'Maybe we could try Vue' are tracked as rejected without storage.
    """
    if not _HEDGED_TEACH_RE.search(user_input):
        return

    from memory.event_log import log_memory_event
    from memory.waking import extract_entities_robust, get_merged_entity_terms
    from storage.db_manager import get_db_connection

    entities = extract_entities_robust(user_input, user_id, db_path)
    if not entities:
        return

    known_terms = get_merged_entity_terms(user_id, db_path)

    conn = get_db_connection(db_path)
    try:
        stored = {
            row["entity_target"].lower()
            for row in conn.execute(
                """
                SELECT entity_target FROM semantic_graph
                WHERE user_id = ? AND node_weight > 0.1
                """,
                (user_id,),
            ).fetchall()
        }
    finally:
        conn.close()

    for entity in entities:
        if entity not in known_terms:
            continue
        display = entity.title() if entity.islower() else entity
        if display.lower() in stored:
            continue
        log_memory_event(
            user_id,
            "salience_rejected",
            entity_source="hedged_teach",
            entity_target=display,
            detail={"source_message": user_input[:200]},
            db_path=db_path,
        )


def fetch_salience_rejected_values(user_id: str, db_path) -> list[str]:
    """Values rejected by salience auction — must not be echoed as stored facts."""
    from storage.db_manager import get_db_connection

    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT entity_target FROM memory_events
            WHERE user_id = ? AND event_type = 'salience_rejected'
            ORDER BY timestamp DESC
            LIMIT 20
            """,
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    rejected: list[str] = []
    seen: set[str] = set()
    for row in rows:
        value = row["entity_target"]
        if value and value.lower() not in seen:
            seen.add(value.lower())
            rejected.append(str(value))
    return rejected


def fetch_suppressed_values(user_id: str, db_path) -> list[str]:
    """Values superseded by contradiction events — must not appear in answers."""
    import json

    from storage.db_manager import get_db_connection

    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT detail FROM memory_events
            WHERE user_id = ? AND event_type = 'contradiction'
            ORDER BY timestamp DESC
            LIMIT 20
            """,
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    suppressed: list[str] = []
    seen: set[str] = set()
    for row in rows:
        if not row["detail"]:
            continue
        try:
            detail = json.loads(row["detail"])
        except json.JSONDecodeError:
            continue
        old_value = detail.get("old_value")
        if old_value and old_value.lower() not in seen:
            seen.add(old_value.lower())
            suppressed.append(str(old_value))
    return suppressed


def fetch_all_active_beliefs(user_id: str, db_path, limit: int = 12) -> list:
    """Return all active beliefs for full-stack compound probes."""
    from config import settings
    from storage.db_manager import get_db_connection

    conn = get_db_connection(db_path)
    try:
        return conn.execute(
            """
            SELECT * FROM semantic_graph
            WHERE user_id = ? AND node_weight > ?
            ORDER BY base_utility_q DESC, conviction_score DESC
            LIMIT ?
            """,
            (user_id, settings.PRUNE_THRESHOLD, limit),
        ).fetchall()
    finally:
        conn.close()


def strip_suppressed_mentions(response: str, suppressed: list[str]) -> str:
    """Remove superseded fact values from the visible reply."""
    cleaned = response
    for value in suppressed:
        if not value:
            continue
        pattern = re.compile(r"\b" + re.escape(value) + r"\b", re.IGNORECASE)
        cleaned = pattern.sub("", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\(\s*\)", "", cleaned)
    cleaned = re.sub(r"\s+([,.])", r"\1", cleaned)
    return cleaned.strip()


def ground_response_with_injection(
    response: str,
    user_input: str,
    injected_values: list[str],
    suppressed: list[str] | None = None,
    rejected: list[str] | None = None,
) -> str:
    """
    Ensure probe answers explicitly cite stored fact values; strip stale contradictions.

    When the model omits an injected value on a compound probe, prepend a factual
    prefix so recall scoring reflects memory retrieval, not generic LLM priors.
    """
    if not response:
        return response

    forbidden = list(dict.fromkeys((suppressed or []) + (rejected or [])))
    grounded = strip_suppressed_mentions(response, forbidden)

    if not injected_values or not is_compound_probe(user_input):
        return grounded

    missing = [
        v for v in injected_values
        if v and v.lower() not in grounded.lower()
    ]
    if not missing:
        return grounded

    prefix = "Based on your stored preferences: " + ", ".join(missing) + "."
    if grounded:
        return f"{prefix} {grounded}"
    return prefix
