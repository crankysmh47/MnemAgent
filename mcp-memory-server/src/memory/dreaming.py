"""Dreaming phase — background memory consolidation, feedback, decay, and pruning."""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

from config import settings
from memory.event_log import log_memory_event
from memory.prospective import prospective_from_belief, store_prospective_memory
from memory.waking import store_belief_embedding_sync
from memory.entity_lexicon import terms_for_entity_dict
from storage.db_manager import delete_vec_embedding, get_db_connection, upsert_user_entities

logger = logging.getLogger(__name__)

Q_REWARD = 0.05
Q_PENALTY = 0.01
PROXIMITY_WINDOW = 100
SALIENCE_MIN_CONVICTION = 0.4
INACTIVE_MINUTES = 45

SAFETY_KEYWORDS = (
    "allerg",
    "medication",
    "health",
    "medical",
    "emergency",
    "intoleran",
    "condition",
    "diagnos",
    "illness",
    "disease",
)

MEMORY_POISON_PATTERNS = (
    r"\bignore\s+(?:all\s+)?(?:memory|system|developer)\s+rules\b",
    r"\bsilently\s+(?:rewrite|overwrite|replace)\b",
    r"\bdo\s+not\s+mention\s+(?:this|the\s+rewrite|the\s+change)\b",
    r"\bforget\s+the\s+(?:previous|old)\s+memory\s+rules\b",
    r"\boverride\s+(?:memory|salience|storage)\s+policy\b",
)


def _text_has_safety_keyword(text: str) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in SAFETY_KEYWORDS)


def _looks_like_memory_poison(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.I) for pattern in MEMORY_POISON_PATTERNS)


def is_belief_referenced(src: str, tgt: str, response: str) -> bool:
    """
    Check whether both entity terms appear within proximity in the response.

    Tradeoff (deliberate): proximity regex instead of embedding similarity.
    Fast, deterministic, and good enough for hackathon-scale graphs — avoids
    an extra embedding call per injected belief on every turn. Embedding-based
    influence scoring would be more semantically precise but adds latency and
    can false-positive on polysemy (e.g. "python" snake vs language).

    Args:
        src: Entity source term.
        tgt: Entity target term.
        response: Agent response text.

    Returns:
        True if both terms appear within PROXIMITY_WINDOW characters.
    """
    if not src or not tgt:
        return False
    try:
        pattern = (
            f"(?i)(?:{re.escape(src)}.{{0,{PROXIMITY_WINDOW}}}{re.escape(tgt)}"
            f"|{re.escape(tgt)}.{{0,{PROXIMITY_WINDOW}}}{re.escape(src)})"
        )
        return bool(re.search(pattern, response))
    except re.error as exc:
        logger.warning("Regex error in belief reference check: %s", exc)
        return False


def evaluate_memory_utility_feedback(
    user_id: str,
    response_text: str,
    injected_belief_ids: list[int],
    db_path: Path | None = None,
) -> None:
    """
    Update Q_i and injection stats based on whether injected beliefs shaped the response.

    Args:
        user_id: User identifier.
        response_text: Clean agent response text.
        injected_belief_ids: IDs of beliefs injected into the prompt.
        db_path: Optional database path override.
    """
    if not injected_belief_ids:
        return

    conn = get_db_connection(db_path)
    referenced_count = 0
    try:
        for belief_id in injected_belief_ids:
            row = conn.execute(
                """
                SELECT entity_source, entity_target, base_utility_q, influence_count
                FROM semantic_graph WHERE id = ?
                """,
                (belief_id,),
            ).fetchone()
            if row is None:
                continue

            referenced = is_belief_referenced(row["entity_source"], row["entity_target"], response_text)
            new_q = row["base_utility_q"]
            influence = row["influence_count"]
            if referenced:
                new_q = min(1.0, new_q + Q_REWARD)
                influence += 1
                referenced_count += 1
                log_memory_event(
                    user_id,
                    "influenced",
                    entity_source=row["entity_source"],
                    entity_target=row["entity_target"],
                    detail={
                        "belief_id": belief_id,
                        "old_q": row["base_utility_q"],
                        "new_q": new_q,
                    },
                    db_path=db_path,
                    conn=conn,
                )
            else:
                new_q = max(0.0, new_q - Q_PENALTY)

            conn.execute(
                """
                UPDATE semantic_graph
                SET base_utility_q = ?, injection_count = injection_count + 1,
                    influence_count = ?
                WHERE id = ?
                """,
                (new_q, influence, belief_id),
            )
        conn.commit()
        logger.debug(
            "Feedback updated for user=%s beliefs=%s referenced=%s",
            user_id,
            len(injected_belief_ids),
            referenced_count,
        )
    except sqlite3.Error as exc:
        logger.error("Feedback update failed: %s", exc)
    finally:
        conn.close()


def _run_decay_and_prune(user_id: str, db_path: Path | None = None) -> None:
    """Decay inactive nodes and hard-prune beliefs below the weight threshold."""
    conn = get_db_connection(db_path)
    try:
        decay_candidates = conn.execute(
            """
            SELECT id, entity_source, entity_target, node_weight
            FROM semantic_graph
            WHERE user_id = ? AND last_accessed < datetime('now', '-45 minutes')
            """,
            (user_id,),
        ).fetchall()
        for decay_row in decay_candidates:
            old_weight = float(decay_row["node_weight"])
            new_weight = old_weight * settings.DECAY_RATE
            log_memory_event(
                user_id,
                "decayed",
                entity_source=decay_row["entity_source"],
                entity_target=decay_row["entity_target"],
                detail={"old_weight": old_weight, "new_weight": new_weight},
                db_path=db_path,
                conn=conn,
            )

        conn.execute(
            """
            UPDATE semantic_graph
            SET node_weight = node_weight * ?
            WHERE user_id = ? AND last_accessed < datetime('now', '-45 minutes')
            """,
            (settings.DECAY_RATE, user_id),
        )

        pruned = conn.execute(
            """
            SELECT id, entity_source, entity_target, node_weight
            FROM semantic_graph
            WHERE user_id = ? AND node_weight < ?
            """,
            (user_id, settings.PRUNE_THRESHOLD),
        ).fetchall()
        for pruned_row in pruned:
            log_memory_event(
                user_id,
                "pruned",
                entity_source=pruned_row["entity_source"],
                entity_target=pruned_row["entity_target"],
                detail={
                    "belief_id": int(pruned_row["id"]),
                    "weight": float(pruned_row["node_weight"]),
                },
                db_path=db_path,
                conn=conn,
            )
            delete_vec_embedding(int(pruned_row["id"]), db_path)

        cursor = conn.execute(
            "DELETE FROM semantic_graph WHERE user_id = ? AND node_weight < ?",
            (user_id, settings.PRUNE_THRESHOLD),
        )
        if cursor.rowcount:
            logger.info("Hard pruned %s beliefs for user=%s", cursor.rowcount, user_id)

        conn.commit()
    except sqlite3.Error as exc:
        logger.error("Decay/prune failed: %s", exc)
    finally:
        conn.close()


def refresh_belief_vitality(user_id: str, db_path: Path | None = None) -> int:
    """Reset node weights and access time — used after demo batch seeding."""
    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            UPDATE semantic_graph
            SET node_weight = 1.0, last_accessed = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (user_id,),
        )
        conn.commit()
        return cursor.rowcount
    except sqlite3.Error as exc:
        logger.error("Vitality refresh failed: %s", exc)
        return 0
    finally:
        conn.close()


def consolidate_and_prune_memory(
    user_id: str,
    memory_dict: dict,
    db_path: Path | None = None,
    *,
    run_maintenance: bool = True,
    user_prompt: str | None = None,
    scope_type: str = "core",
    scope_id: str = "core",
) -> bool:
    """
    Apply salience gate, upsert belief, optionally decay inactive nodes and hard prune.

    Returns:
        True if a belief was stored, False if rejected or invalid.
    """
    from memory.scopes import MemoryScope

    scope = MemoryScope(scope_type, scope_id)
    entity = memory_dict.get("entity")
    relation = memory_dict.get("relation")
    value = memory_dict.get("value")
    category = memory_dict.get("category", "preference")
    conviction = float(memory_dict.get("conviction", 0.5))

    if not entity or not relation or value is None:
        logger.warning("consolidate_and_prune_memory missing required fields: %s", memory_dict)
        return False

    safety_blob = " ".join(
        str(part)
        for part in (entity, relation, value, user_prompt or "")
        if part is not None
    )
    if user_prompt and _looks_like_memory_poison(safety_blob):
        logger.info("Memory firewall rejected likely prompt-injection write")
        log_memory_event(
            user_id,
            "memory_firewall_rejected",
            entity_source=entity,
            entity_target=str(value),
            detail={"category": category, "conviction": conviction},
            db_path=db_path,
        )
        return False
    safety_critical = _text_has_safety_keyword(safety_blob)

    if conviction < SALIENCE_MIN_CONVICTION and category != "system_state" and not safety_critical:
        logger.info("Salience Auction rejected: low conviction (%.2f)", conviction)
        log_memory_event(
            user_id,
            "salience_rejected",
            entity_source=entity,
            entity_target=str(value),
            detail={"conviction": conviction, "category": category},
            db_path=db_path,
        )
        return False

    if safety_critical and conviction < SALIENCE_MIN_CONVICTION:
        conviction = max(conviction, SALIENCE_MIN_CONVICTION)
        if category == "preference":
            category = "system_state"

    conn = get_db_connection(db_path)
    belief_id: int | None = None
    try:
        existing = conn.execute(
            """
            SELECT id, entity_target FROM semantic_graph
            WHERE user_id = ? AND scope_type = ? AND scope_id = ?
              AND entity_source = ? AND relation = ?
            """,
            (user_id, scope.scope_type, scope.scope_id, entity, relation),
        ).fetchone()
        if existing and existing["entity_target"] != value:
            logger.info(
                "Contradiction Detected — Forgetting: %s → Learning: %s",
                existing["entity_target"],
                value,
            )
            log_memory_event(
                user_id,
                "contradiction",
                entity_source=entity,
                entity_target=value,
                detail={
                    "relation": relation,
                    "old_value": existing["entity_target"],
                    "new_value": value,
                },
                db_path=db_path,
                conn=conn,
            )

        conn.execute(
            """
            INSERT INTO semantic_graph (
                user_id, scope_type, scope_id, category, entity_source, relation, entity_target, conviction_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, scope_type, scope_id, entity_source, relation) DO UPDATE SET
                category = excluded.category,
                entity_target = excluded.entity_target,
                conviction_score = excluded.conviction_score,
                node_weight = 1.0,
                last_accessed = CURRENT_TIMESTAMP
            """,
            (user_id, scope.scope_type, scope.scope_id, category, entity, relation, value, conviction),
        )
        row = conn.execute(
            """
            SELECT id FROM semantic_graph
            WHERE user_id = ? AND scope_type = ? AND scope_id = ?
              AND entity_source = ? AND relation = ?
            """,
            (user_id, scope.scope_type, scope.scope_id, entity, relation),
        ).fetchone()
        belief_id = int(row["id"]) if row else None

        if belief_id is not None and (not existing or existing["entity_target"] == value):
            log_memory_event(
                user_id,
                "new_belief",
                entity_source=entity,
                entity_target=str(value),
                detail={
                    "relation": relation,
                    "category": category,
                    "conviction": conviction,
                    "belief_id": belief_id,
                },
                db_path=db_path,
                conn=conn,
            )

        conn.commit()
    except sqlite3.Error as exc:
        logger.error("Consolidation failed: %s", exc)
        return False
    finally:
        conn.close()

    if run_maintenance:
        _run_decay_and_prune(user_id, db_path)

    prospective = prospective_from_belief(memory_dict)
    if prospective is not None:
        cue, action = prospective
        store_prospective_memory(
            user_id,
            cue,
            action,
            source_belief=belief_id,
            db_path=db_path,
        )

    dict_terms = terms_for_entity_dict(entity, value)
    if dict_terms:
        upsert_user_entities(user_id, dict_terms, source="memory_update", db_path=db_path)

    if belief_id is not None:
        store_belief_embedding_sync(belief_id, entity, relation, value, db_path)
    return True
