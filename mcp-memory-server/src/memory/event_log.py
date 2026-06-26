"""Persist memory lifecycle events for the visualizer and activity feed."""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

from storage.db_manager import get_db_connection, run_write_with_retry

logger = logging.getLogger(__name__)


def log_memory_event(
    user_id: str,
    event_type: str,
    entity_source: str | None = None,
    entity_target: str | None = None,
    detail: dict[str, Any] | None = None,
    db_path: Path | None = None,
    *,
    conn: sqlite3.Connection | None = None,
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
        conn: Optional existing connection to reuse (avoids SQLite lock contention).
    """
    try:
        if conn is not None:
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
        else:
            def _write() -> None:
                c = get_db_connection(db_path)
                try:
                    c.execute(
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
                    c.commit()
                finally:
                    c.close()

            run_write_with_retry(_write)
    except sqlite3.Error as exc:
        logger.error("Failed to log memory event %s: %s", event_type, exc)
