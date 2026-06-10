"""Dreaming phase — background memory consolidation, feedback, decay, and pruning."""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

from config import settings
from storage.db_manager import delete_vec_embedding, get_db_connection
from memory.waking import store_belief_embedding_sync

logger = logging.getLogger(__name__)

Q_REWARD = 0.05
Q_PENALTY = 0.01
PROXIMITY_WINDOW = 100
SALIENCE_MIN_CONVICTION = 0.4
INACTIVE_MINUTES = 45


def is_belief_referenced(src: str, tgt: str, response: str) -> bool:
    """
    Check whether both entity terms appear within proximity in the response.

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


def consolidate_and_prune_memory(
    user_id: str,
    memory_dict: dict,
    db_path: Path | None = None,
) -> None:
    """
    Apply salience gate, upsert belief, decay inactive nodes, and hard prune.

    Args:
        user_id: User identifier.
        memory_dict: Parsed memory_update with entity, relation, value, category, conviction.
        db_path: Optional database path override.
    """
    entity = memory_dict.get("entity")
    relation = memory_dict.get("relation")
    value = memory_dict.get("value")
    category = memory_dict.get("category", "preference")
    conviction = float(memory_dict.get("conviction", 0.5))

    if not entity or not relation or value is None:
        logger.warning("consolidate_and_prune_memory missing required fields: %s", memory_dict)
        return

    if conviction < SALIENCE_MIN_CONVICTION and category != "system_state":
        logger.info("Salience Auction rejected: low conviction (%.2f)", conviction)
        return

    conn = get_db_connection(db_path)
    belief_id: int | None = None
    try:
        existing = conn.execute(
            """
            SELECT id, entity_target FROM semantic_graph
            WHERE user_id = ? AND entity_source = ? AND relation = ?
            """,
            (user_id, entity, relation),
        ).fetchone()
        if existing and existing["entity_target"] != value:
            logger.info(
                "Contradiction Detected — Forgetting: %s → Learning: %s",
                existing["entity_target"],
                value,
            )

        conn.execute(
            """
            INSERT INTO semantic_graph (
                user_id, category, entity_source, relation, entity_target, conviction_score
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, entity_source, relation) DO UPDATE SET
                category = excluded.category,
                entity_target = excluded.entity_target,
                conviction_score = excluded.conviction_score,
                node_weight = 1.0,
                last_accessed = CURRENT_TIMESTAMP
            """,
            (user_id, category, entity, relation, value, conviction),
        )
        row = conn.execute(
            """
            SELECT id FROM semantic_graph
            WHERE user_id = ? AND entity_source = ? AND relation = ?
            """,
            (user_id, entity, relation),
        ).fetchone()
        belief_id = int(row["id"]) if row else None

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
            SELECT id FROM semantic_graph
            WHERE user_id = ? AND node_weight < ?
            """,
            (user_id, settings.PRUNE_THRESHOLD),
        ).fetchall()
        for pruned_row in pruned:
            delete_vec_embedding(int(pruned_row["id"]), db_path)

        cursor = conn.execute(
            "DELETE FROM semantic_graph WHERE user_id = ? AND node_weight < ?",
            (user_id, settings.PRUNE_THRESHOLD),
        )
        if cursor.rowcount:
            logger.info("Hard pruned %s beliefs for user=%s", cursor.rowcount, user_id)

        conn.commit()
    except sqlite3.Error as exc:
        logger.error("Consolidation failed: %s", exc)
        return
    finally:
        conn.close()

    if belief_id is not None:
        store_belief_embedding_sync(belief_id, entity, relation, value, db_path)
