"""Persist memory lifecycle events for the visualizer and activity feed."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from storage.db_manager import get_db_connection

logger = logging.getLogger(__name__)


def log_memory_event(
    user_id: str,
    event_type: str,
    entity_source: str | None = None,
    entity_target: str | None = None,
    detail: dict[str, Any] | None = None,
    db_path: Path | None = None,
) -> None:
    """
    Insert one row into memory_events.

    Args:
        user_id: User identifier.
        event_type: Event kind (new_belief, contradiction, injected, etc.).
        entity_source: Optional entity source label.
        entity_target: Optional entity target label.
        detail: Optional JSON-serializable context.
        db_path: Optional database path override.
    """
    try:
        conn = get_db_connection(db_path)
        try:
            conn.execute(
                """
                INSERT INTO memory_events (
                    user_id, event_type, entity_source, entity_target, detail
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    event_type,
                    entity_source,
                    entity_target,
                    json.dumps(detail) if detail else None,
                ),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        logger.error("Failed to log memory event %s: %s", event_type, exc)
