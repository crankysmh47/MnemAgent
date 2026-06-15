"""SQLite connection factory with WAL mode, sqlite-vec extension loading, and schema init."""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

VEC_AVAILABLE: bool = False
_db_lock = threading.Lock()


def get_db_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Open a SQLite connection with WAL mode and row factory enabled.

    Args:
        db_path: Optional override path for the database file.

    Returns:
        An open sqlite3.Connection.
    """
    path = db_path or settings.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    _load_vec_extension(conn)
    return conn


def _load_vec_extension(conn: sqlite3.Connection) -> bool:
    """
    Attempt to load the sqlite-vec extension.

    Args:
        conn: Active SQLite connection.

    Returns:
        True if vec0 is available, False otherwise.
    """
    global VEC_AVAILABLE
    try:
        import sqlite_vec

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        VEC_AVAILABLE = True
        logger.info("sqlite-vec extension loaded successfully")
        return True
    except (ImportError, sqlite3.OperationalError, OSError) as exc:
        logger.warning("sqlite-vec unavailable: %s. Falling back to keyword retrieval.", exc)
        VEC_AVAILABLE = False
        return False


def _backfill_user_entities(conn: sqlite3.Connection) -> None:
    """Seed user_entities from existing beliefs (idempotent, runs each init)."""
    try:
        conn.execute(
            """
            INSERT OR IGNORE INTO user_entities (user_id, entity_name, source)
            SELECT DISTINCT user_id, LOWER(TRIM(entity_source)), 'backfill'
            FROM semantic_graph
            WHERE LENGTH(TRIM(entity_source)) >= 2
            UNION
            SELECT DISTINCT user_id, LOWER(TRIM(entity_target)), 'backfill'
            FROM semantic_graph
            WHERE LENGTH(TRIM(entity_target)) >= 2
            """
        )
    except sqlite3.Error as exc:
        logger.warning("User entity backfill skipped: %s", exc)


def initialize_database(db_path: Path | None = None) -> None:
    """
    Initialize schema and optional vector table.

    Args:
        db_path: Optional override path for the database file.
    """
    global VEC_AVAILABLE
    path = db_path or settings.DB_PATH
    with _db_lock:
        conn = get_db_connection(path)
        try:
            schema_path = Path(__file__).parent / "schema.sql"
            conn.executescript(schema_path.read_text(encoding="utf-8"))
            _load_vec_extension(conn)
            if VEC_AVAILABLE:
                conn.execute(
                    f"""
                    CREATE VIRTUAL TABLE IF NOT EXISTS vec_memory USING vec0(
                        id INTEGER PRIMARY KEY,
                        embedding float[{settings.EMBEDDING_DIM}]
                    )
                    """
                )
            _backfill_user_entities(conn)
            conn.commit()
            logger.info("Database initialized at %s", path)
        finally:
            conn.close()


def get_total_turns(user_id: str, db_path: Path | None = None) -> int:
    """
    Return episodic turn count for a user (minimum 1 for UCB math).

    Args:
        user_id: User identifier.
        db_path: Optional database path override.

    Returns:
        Turn count, at least 1.
    """
    conn = get_db_connection(db_path)
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM episodic_logs WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        count = int(row["cnt"]) if row else 0
        return max(1, count)
    finally:
        conn.close()


def log_episodic_turn(
    user_id: str,
    session_id: str,
    user_prompt: str,
    agent_response: str,
    db_path: Path | None = None,
) -> None:
    """
    Persist one episodic conversation turn.

    Args:
        user_id: User identifier.
        session_id: Session identifier.
        user_prompt: User message text.
        agent_response: Agent response text.
        db_path: Optional database path override.
    """
    try:
        conn = get_db_connection(db_path)
        try:
            conn.execute(
                """
                INSERT INTO episodic_logs (user_id, session_id, user_prompt, agent_response)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, session_id, user_prompt, agent_response),
            )
            conn.commit()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        logger.error("Failed to log episodic turn: %s", exc)


def upsert_vec_embedding(
    metadata_id: int,
    embedding: list[float],
    db_path: Path | None = None,
) -> None:
    """
    Store or replace a vector embedding for a semantic_graph row.

    Args:
        metadata_id: semantic_graph.id
        embedding: Embedding vector matching EMBEDDING_DIM.
        db_path: Optional database path override.
    """
    if not VEC_AVAILABLE:
        return
    try:
        import sqlite_vec

        conn = get_db_connection(db_path)
        try:
            conn.execute("DELETE FROM vec_memory WHERE id = ?", (metadata_id,))
            conn.execute(
                "INSERT INTO vec_memory (id, embedding) VALUES (?, ?)",
                (metadata_id, sqlite_vec.serialize_float32(embedding)),
            )
            conn.commit()
        finally:
            conn.close()
    except (ImportError, sqlite3.Error) as exc:
        logger.warning("Failed to upsert vector embedding for id=%s: %s", metadata_id, exc)


def upsert_user_entities(
    user_id: str,
    entity_names: list[str],
    source: str = "memory_update",
    db_path: Path | None = None,
) -> int:
    """
    Add entity names to the user's dynamic entity dictionary.

    Args:
        user_id: User identifier.
        entity_names: List of entity name strings to upsert.
        source: Origin label (memory_update, manual, seed).
        db_path: Optional database path override.

    Returns:
        Number of new entities added (duplicates ignored).
    """
    if not entity_names:
        return 0
    conn = get_db_connection(db_path)
    added = 0
    try:
        for name in entity_names:
            clean = str(name).strip().lower()
            if len(clean) < 2:
                continue
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO user_entities (user_id, entity_name, source)
                VALUES (?, ?, ?)
                """,
                (user_id, clean, source),
            )
            added += cursor.rowcount
        conn.commit()
        if added:
            logger.debug("Added %d new entities to user=%s dictionary", added, user_id)
    except sqlite3.Error as exc:
        logger.warning("Failed to upsert user entities: %s", exc)
    finally:
        conn.close()
    return added


def get_user_entity_dict(
    user_id: str,
    db_path: Path | None = None,
) -> set[str]:
    """
    Return the set of dynamically-learned entity names for a user.

    Args:
        user_id: User identifier.
        db_path: Optional database path override.

    Returns:
        Set of lowercased entity name strings.
    """
    conn = get_db_connection(db_path)
    try:
        rows = conn.execute(
            "SELECT entity_name FROM user_entities WHERE user_id = ?",
            (user_id,),
        ).fetchall()
        return {row["entity_name"] for row in rows}
    except sqlite3.Error as exc:
        logger.warning("Failed to fetch user entity dict: %s", exc)
        return set()
    finally:
        conn.close()


def delete_vec_embedding(metadata_id: int, db_path: Path | None = None) -> None:
    """
    Remove a vector embedding when a belief is pruned.

    Args:
        metadata_id: semantic_graph.id
        db_path: Optional database path override.
    """
    if not VEC_AVAILABLE:
        return
    try:
        conn = get_db_connection(db_path)
        try:
            conn.execute("DELETE FROM vec_memory WHERE id = ?", (metadata_id,))
            conn.commit()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        logger.warning("Failed to delete vector embedding for id=%s: %s", metadata_id, exc)
