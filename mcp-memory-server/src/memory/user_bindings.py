"""Channel sender to canonical MnemOS user_id bindings."""

from __future__ import annotations

import hashlib
import sqlite3
import uuid
from pathlib import Path

from storage.db_manager import get_db_connection


def _canonical_user_id(channel: str, sender_id: str) -> str:
    """Derive a stable user_id from channel + sender."""
    digest = hashlib.sha256(f"{channel}:{sender_id}".encode()).hexdigest()[:16]
    return f"oc_{channel}_{digest}"


def bind_user(
    channel: str,
    sender_id: str,
    display_name: str | None = None,
    db_path: Path | None = None,
) -> dict:
    """
    Bind a channel sender to a canonical MnemOS user_id.

    Args:
        channel: Channel name (telegram, discord, whatsapp, etc.).
        sender_id: Platform-specific sender identifier.
        display_name: Optional human-readable name.
        db_path: Optional database path override.

    Returns:
        Dict with user_id, channel, sender_id, created (bool).
    """
    user_id = _canonical_user_id(channel, sender_id)
    conn = get_db_connection(db_path)
    try:
        existing = conn.execute(
            """
            SELECT user_id FROM user_bindings
            WHERE channel = ? AND sender_id = ?
            """,
            (channel, sender_id),
        ).fetchone()
        created = existing is None
        conn.execute(
            """
            INSERT INTO user_bindings (user_id, channel, sender_id, display_name)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(channel, sender_id) DO UPDATE SET
                display_name = COALESCE(excluded.display_name, user_bindings.display_name)
            """,
            (user_id, channel, sender_id, display_name),
        )
        conn.commit()
        return {
            "user_id": user_id,
            "channel": channel,
            "sender_id": sender_id,
            "display_name": display_name,
            "created": created,
        }
    finally:
        conn.close()


def resolve_user(
    channel: str,
    sender_id: str,
    display_name: str | None = None,
    db_path: Path | None = None,
) -> str:
    """
    Resolve sender to user_id, creating binding if needed.

    Args:
        channel: Channel name.
        sender_id: Platform sender id.
        display_name: Optional display name for new bindings.
        db_path: Optional database path override.

    Returns:
        Canonical user_id string.
    """
    return bind_user(channel, sender_id, display_name, db_path)["user_id"]


def list_bindings_for_user(user_id: str, db_path: Path | None = None) -> list[dict]:
    """
    List all channel bindings for a canonical user_id.

    Args:
        user_id: Canonical MnemOS user id.
        db_path: Optional database path override.

    Returns:
        List of binding dicts.
    """
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            """
            SELECT channel, sender_id, display_name, created_at
            FROM user_bindings WHERE user_id = ?
            ORDER BY created_at ASC
            """,
            (user_id,),
        ).fetchall()
        return [
            {
                "channel": row["channel"],
                "sender_id": row["sender_id"],
                "display_name": row["display_name"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    except sqlite3.Error:
        return []
