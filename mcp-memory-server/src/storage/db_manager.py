"""Database connection factory for Postgres runtime and isolated SQLite tests."""

from __future__ import annotations

import logging
import re
import sqlite3
import threading
import time
from pathlib import Path

from config import settings
from memory.entity_lexicon import normalize_entity_dict_term

logger = logging.getLogger(__name__)

VEC_AVAILABLE: bool = False
_db_lock = threading.Lock()


def _pg_error_types() -> tuple[type[Exception], ...]:
    try:
        import psycopg

        return (psycopg.Error,)
    except ImportError:
        return ()


def db_error_types() -> tuple[type[Exception], ...]:
    """Exception classes raised by the active database backend."""

    return (sqlite3.Error, *_pg_error_types())


def is_postgres_backend() -> bool:
    """Return True when STORAGE_BACKEND requests PostgreSQL."""

    return settings.STORAGE_BACKEND.strip().lower() in {"postgres", "postgresql", "pg"}


class _PostgresConnection:
    """Small compatibility wrapper for the sqlite-style storage call sites."""

    def __init__(self, database_url: str):
        import psycopg
        from pgvector.psycopg import register_vector
        from psycopg.rows import dict_row

        self._conn = psycopg.connect(database_url, row_factory=dict_row)
        register_vector(self._conn)

    def execute(self, sql: str, params: tuple | list | None = None):
        return self._conn.execute(_translate_sqlite_sql(sql), params or ())

    def executescript(self, sql: str) -> None:
        with self._conn.cursor() as cursor:
            cursor.execute(sql)

    def commit(self) -> None:
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


def _translate_sqlite_sql(sql: str) -> str:
    """Translate the small SQLite dialect subset used by MnemAgent to Postgres."""

    translated = sql
    translated = translated.replace(
        "datetime('now', '-45 minutes')",
        "CURRENT_TIMESTAMP - INTERVAL '45 minutes'",
    )
    translated = translated.replace("MIN(1.0, node_weight + 0.05)", "LEAST(1.0, node_weight + 0.05)")
    translated = translated.replace("INSERT OR IGNORE INTO", "INSERT INTO")
    translated = translated.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "BIGSERIAL PRIMARY KEY")
    translated = translated.replace("DATETIME DEFAULT CURRENT_TIMESTAMP", "TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP")
    translated = translated.replace("DATETIME", "TIMESTAMPTZ")
    if "INSERT INTO user_entities" in translated and "ON CONFLICT" not in translated:
        translated = translated.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    if "INSERT INTO prospective_memories" in translated and "ON CONFLICT" not in translated:
        translated = translated.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    translated = re.sub(r"\?", "%s", translated)
    return translated


def get_db_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """
    Open a database connection.

    Postgres is the production/runtime backend. Passing ``db_path`` forces the
    lightweight SQLite test backend so existing unit tests can stay fast and
    hermetic.

    Args:
        db_path: Optional override path for the database file.

    Returns:
        An open sqlite3.Connection.
    """
    if is_postgres_backend() and db_path is None:
        if not settings.DATABASE_URL:
            raise RuntimeError("STORAGE_BACKEND=postgres requires DATABASE_URL")
        return _PostgresConnection(settings.DATABASE_URL)  # type: ignore[return-value]

    path = db_path or settings.DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    _load_vec_extension(conn)
    return conn


def run_write_with_retry(
    write_fn,
    *,
    retries: int = 3,
    base_delay_s: float = 0.05,
) -> None:
    """Run a DB write callback, retrying on transient SQLite lock errors."""
    for attempt in range(retries):
        try:
            write_fn()
            return
        except db_error_types() as exc:
            if "locked" not in str(exc).lower() or attempt >= retries - 1:
                raise
            time.sleep(base_delay_s * (2**attempt))


def _load_vec_extension(conn: sqlite3.Connection) -> bool:
    """
    Attempt to load the sqlite-vec extension.

    Args:
        conn: Active SQLite connection.

    Returns:
        True if vec0 is available, False otherwise.
    """
    global VEC_AVAILABLE
    if is_postgres_backend():
        VEC_AVAILABLE = True
        return True
    try:
        import sqlite_vec

        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        if not VEC_AVAILABLE:
            logger.info("sqlite-vec extension loaded successfully")
        VEC_AVAILABLE = True
        return True
    except (ImportError, sqlite3.OperationalError, OSError) as exc:
        logger.warning("sqlite-vec unavailable: %s. Falling back to keyword retrieval.", exc)
        VEC_AVAILABLE = False
        return False


def _backfill_user_entities(conn: sqlite3.Connection) -> None:
    """Seed user_entities from existing beliefs (idempotent, runs each init)."""
    try:
        rows = conn.execute(
            """
            SELECT DISTINCT user_id, LOWER(TRIM(entity_source)) AS term
            FROM semantic_graph
            WHERE LENGTH(TRIM(entity_source)) >= 2
            UNION
            SELECT DISTINCT user_id, LOWER(TRIM(entity_target)) AS term
            FROM semantic_graph
            WHERE LENGTH(TRIM(entity_target)) >= 2
            """
        ).fetchall()
        for row in rows:
            term = normalize_entity_dict_term(row["term"])
            if not term:
                continue
            conn.execute(
                """
                INSERT OR IGNORE INTO user_entities (user_id, entity_name, source)
                VALUES (?, ?, 'backfill')
                """,
                (row["user_id"], term),
            )
    except db_error_types() as exc:
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
        if is_postgres_backend() and db_path is None:
            conn = get_db_connection(None)
            try:
                schema_path = Path(__file__).parent / "schema.postgres.sql"
                conn.executescript(schema_path.read_text(encoding="utf-8"))
                _backfill_user_entities(conn)  # type: ignore[arg-type]
                conn.commit()
                logger.info("Postgres database initialized")
            finally:
                conn.close()
            VEC_AVAILABLE = True
            return

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
        def _write() -> None:
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

        run_write_with_retry(_write)
    except db_error_types() as exc:
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
    if is_postgres_backend() and db_path is None:
        conn = get_db_connection(db_path)
        try:
            conn.execute("DELETE FROM vec_memory WHERE id = ?", (metadata_id,))
            conn.execute(
                "INSERT INTO vec_memory (id, embedding) VALUES (?, ?)",
                (metadata_id, embedding),
            )
            conn.commit()
        finally:
            conn.close()
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
    except (ImportError, *db_error_types()) as exc:
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
            clean = normalize_entity_dict_term(name)
            if not clean:
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
    except db_error_types() as exc:
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
    except db_error_types() as exc:
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
    except db_error_types() as exc:
        logger.warning("Failed to delete vector embedding for id=%s: %s", metadata_id, exc)
