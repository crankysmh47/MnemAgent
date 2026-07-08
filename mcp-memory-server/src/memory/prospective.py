"""Cue-triggered prospective memory.

Prospective memory is not a timer. It is an intention that should fire when the
user brings up a matching cue: "when I ask about deployment, remind me to check
the OSS snapshot." This keeps overhead low and avoids scheduler complexity.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from pathlib import Path

from memory.event_log import log_memory_event
from storage.db_manager import get_db_connection

logger = logging.getLogger(__name__)

_WHEN_ENTITY = re.compile(r"^when_(?:asked_)?about_(?P<cue>.+)$", re.I)


def _clean_phrase(value: object) -> str:
    text = str(value or "").strip().strip("'\"`")
    text = text.replace("_", " ")
    return re.sub(r"\s+", " ", text).strip()


def prospective_from_belief(memory_dict: dict) -> tuple[str, str] | None:
    """Return (cue, action) when a memory dict encodes a prospective reminder."""

    relation = str(memory_dict.get("relation") or "").strip().lower()
    if relation not in {"remind", "reminds", "remind_me"}:
        return None

    entity = str(memory_dict.get("entity") or "").strip()
    value = _clean_phrase(memory_dict.get("value"))
    match = _WHEN_ENTITY.match(entity)
    if not match or not value:
        return None
    cue = _clean_phrase(match.group("cue"))
    if len(cue) < 2:
        return None
    return cue, value


def store_prospective_memory(
    user_id: str,
    cue: str,
    action: str,
    *,
    source_belief: int | None = None,
    db_path: Path | None = None,
) -> bool:
    """Persist a cue-triggered intention."""

    conn = get_db_connection(db_path)
    try:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO prospective_memories
                (user_id, cue, action, source_belief)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, cue.lower(), action, source_belief),
        )
        if cursor.rowcount:
            log_memory_event(
                user_id,
                "prospective_stored",
                entity_source=cue,
                entity_target=action,
                detail={"source_belief": source_belief},
                db_path=db_path,
                conn=conn,
            )
        conn.commit()
        return bool(cursor.rowcount)
    except sqlite3.Error as exc:
        logger.warning("Failed to store prospective memory: %s", exc)
        return False
    finally:
        conn.close()


def fetch_due_prospective_memories(
    user_id: str,
    user_input: str,
    *,
    limit: int = 3,
    db_path: Path | None = None,
) -> list[dict]:
    """Return prospective memories whose cue appears in the current prompt."""

    lowered = user_input.lower()
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT id, cue, action, fired_count
            FROM prospective_memories
            WHERE user_id = ?
            ORDER BY fired_count ASC, created_at ASC
            """,
            (user_id,),
        ).fetchall()
        due = []
        for row in rows:
            cue = str(row["cue"])
            if cue and cue in lowered:
                due.append(
                    {
                        "id": int(row["id"]),
                        "cue": cue,
                        "action": row["action"],
                        "fired_count": int(row["fired_count"]),
                    }
                )
            if len(due) >= limit:
                break
        if due:
            ids = [item["id"] for item in due]
            placeholders = ",".join("?" for _ in ids)
            conn.execute(
                f"""
                UPDATE prospective_memories
                SET fired_count = fired_count + 1,
                    last_fired_at = CURRENT_TIMESTAMP
                WHERE id IN ({placeholders})
                """,
                ids,
            )
            for item in due:
                log_memory_event(
                    user_id,
                    "prospective_fired",
                    entity_source=item["cue"],
                    entity_target=item["action"],
                    detail={"prospective_id": item["id"]},
                    db_path=db_path,
                    conn=conn,
                )
            conn.commit()
        return due
    except sqlite3.Error as exc:
        logger.warning("Failed to fetch prospective memories: %s", exc)
        return []
    finally:
        conn.close()
