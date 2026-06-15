"""Tests for storage.db_manager."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from storage.db_manager import (
    get_db_connection,
    get_total_turns,
    initialize_database,
    log_episodic_turn,
)


def test_initialize_database_creates_file(tmp_db_path: Path) -> None:
    initialize_database(tmp_db_path)
    assert tmp_db_path.exists()


def test_initialize_database_creates_tables(initialized_db: Path) -> None:
    conn = get_db_connection(initialized_db)
    try:
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert "episodic_logs" in tables
        assert "semantic_graph" in tables
        assert "user_entities" in tables
    finally:
        conn.close()


def test_initialize_database_idempotent(tmp_db_path: Path) -> None:
    initialize_database(tmp_db_path)
    initialize_database(tmp_db_path)


def test_get_db_connection_wal_mode(initialized_db: Path) -> None:
    conn = get_db_connection(initialized_db)
    try:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"
    finally:
        conn.close()


def test_get_total_turns_empty(initialized_db: Path) -> None:
    assert get_total_turns("new-user", initialized_db) == 1


def test_get_total_turns_with_data(initialized_db: Path) -> None:
    for i in range(5):
        log_episodic_turn("u1", "s1", f"prompt{i}", f"resp{i}", initialized_db)
    assert get_total_turns("u1", initialized_db) == 5


def test_log_episodic_turn_inserts(initialized_db: Path) -> None:
    log_episodic_turn("u1", "s1", "hello", "world", initialized_db)
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute("SELECT * FROM episodic_logs").fetchone()
        assert row["user_prompt"] == "hello"
        assert row["agent_response"] == "world"
    finally:
        conn.close()


def test_log_episodic_turn_multiple_users(initialized_db: Path) -> None:
    log_episodic_turn("a", "s1", "p", "r", initialized_db)
    log_episodic_turn("b", "s1", "p", "r", initialized_db)
    log_episodic_turn("b", "s1", "p2", "r2", initialized_db)
    assert get_total_turns("a", initialized_db) == 1
    assert get_total_turns("b", initialized_db) == 2


def test_semantic_graph_upsert(initialized_db: Path) -> None:
    conn = get_db_connection(initialized_db)
    try:
        conn.execute(
            """
            INSERT INTO semantic_graph (user_id, entity_source, relation, entity_target)
            VALUES ('u', 'framework', 'prefers', 'express')
            """
        )
        conn.execute(
            """
            INSERT INTO semantic_graph (user_id, entity_source, relation, entity_target)
            VALUES ('u', 'framework', 'prefers', 'fastify')
            """
        )
        conn.commit()
        row = conn.execute(
            "SELECT entity_target FROM semantic_graph WHERE user_id='u'"
        ).fetchone()
        assert row["entity_target"] == "fastify"
        count = conn.execute("SELECT COUNT(*) AS c FROM semantic_graph").fetchone()["c"]
        assert count == 1
    finally:
        conn.close()


def test_semantic_graph_partial_index(initialized_db: Path) -> None:
    conn = get_db_connection(initialized_db)
    try:
        conn.execute(
            """
            INSERT INTO semantic_graph (user_id, entity_source, relation, entity_target, node_weight)
            VALUES ('u', 'dead', 'is', 'gone', 0.05)
            """
        )
        conn.commit()
        rows = conn.execute(
            """
            SELECT entity_source FROM semantic_graph
            WHERE user_id='u' AND node_weight > 0.1
            """
        ).fetchall()
        assert len(rows) == 0
    finally:
        conn.close()


def test_upsert_user_entities_coerces_non_string(initialized_db: Path) -> None:
    from storage.db_manager import get_user_entity_dict, upsert_user_entities

    upsert_user_entities("u", [42, "prisma"], db_path=initialized_db)
    entities = get_user_entity_dict("u", initialized_db)
    assert "42" in entities
    assert "prisma" in entities


def test_backfill_user_entities_from_graph(initialized_db: Path) -> None:
    from storage.db_manager import get_user_entity_dict

    conn = get_db_connection(initialized_db)
    conn.execute(
        """
        INSERT INTO semantic_graph (
            user_id, category, entity_source, relation, entity_target
        ) VALUES (?, ?, ?, ?, ?)
        """,
        ("legacy-user", "preference", "backend", "uses", "prisma"),
    )
    conn.commit()
    conn.close()

    initialize_database(initialized_db)
    entities = get_user_entity_dict("legacy-user", initialized_db)
    assert "prisma" in entities
    assert "backend" in entities
