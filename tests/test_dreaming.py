"""Tests for memory.dreaming."""

from __future__ import annotations

from pathlib import Path

import pytest

from memory.dreaming import (
    consolidate_and_prune_memory,
    evaluate_memory_utility_feedback,
    is_belief_referenced,
)
from storage.db_manager import get_db_connection


def test_is_belief_referenced_nearby() -> None:
    assert is_belief_referenced("express", "backend", "We use express for our backend API")


def test_is_belief_referenced_far_apart() -> None:
    text = "express " + ("x" * 200) + " backend"
    assert not is_belief_referenced("express", "backend", text)


def test_is_belief_referenced_reversed_order() -> None:
    assert is_belief_referenced("python", "language", "language of choice is python")


def test_is_belief_referenced_case_insensitive() -> None:
    assert is_belief_referenced("Python", "language", "python is my language")


def test_is_belief_referenced_not_present() -> None:
    assert not is_belief_referenced("react", "vue", "nothing here")


def test_is_belief_referenced_empty_strings() -> None:
    assert not is_belief_referenced("", "x", "text")


def _insert_belief(db_path: Path, q: float = 0.5) -> int:
    conn = get_db_connection(db_path)
    try:
        cur = conn.execute(
            """
            INSERT INTO semantic_graph (
                user_id, entity_source, relation, entity_target, base_utility_q
            ) VALUES ('u', 'express', 'prefers', 'backend', ?)
            """,
            (q,),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def test_feedback_rewards_referenced_belief(initialized_db: Path) -> None:
    belief_id = _insert_belief(initialized_db, 0.5)
    evaluate_memory_utility_feedback(
        "u", "We chose express for the backend stack", [belief_id], initialized_db
    )
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute("SELECT base_utility_q FROM semantic_graph WHERE id=?", (belief_id,)).fetchone()
        assert row["base_utility_q"] == pytest.approx(0.55)
    finally:
        conn.close()


def test_feedback_penalizes_unreferenced_belief(initialized_db: Path) -> None:
    belief_id = _insert_belief(initialized_db, 0.5)
    evaluate_memory_utility_feedback("u", "unrelated text", [belief_id], initialized_db)
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute("SELECT base_utility_q FROM semantic_graph WHERE id=?", (belief_id,)).fetchone()
        assert row["base_utility_q"] == pytest.approx(0.49)
    finally:
        conn.close()


def test_feedback_always_increments_injection_count(initialized_db: Path) -> None:
    belief_id = _insert_belief(initialized_db)
    evaluate_memory_utility_feedback("u", "text", [belief_id], initialized_db)
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute(
            "SELECT injection_count FROM semantic_graph WHERE id=?", (belief_id,)
        ).fetchone()
        assert row["injection_count"] == 1
    finally:
        conn.close()


def test_feedback_handles_deleted_belief(initialized_db: Path) -> None:
    evaluate_memory_utility_feedback("u", "text", [9999], initialized_db)


def test_feedback_empty_ids() -> None:
    evaluate_memory_utility_feedback("u", "text", [])


def test_feedback_q_capped_at_1(initialized_db: Path) -> None:
    belief_id = _insert_belief(initialized_db, 0.98)
    evaluate_memory_utility_feedback(
        "u", "express backend", [belief_id], initialized_db
    )
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute("SELECT base_utility_q FROM semantic_graph WHERE id=?", (belief_id,)).fetchone()
        assert row["base_utility_q"] == 1.0
    finally:
        conn.close()


def test_feedback_q_floored_at_0(initialized_db: Path) -> None:
    belief_id = _insert_belief(initialized_db, 0.005)
    evaluate_memory_utility_feedback("u", "unrelated", [belief_id], initialized_db)
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute("SELECT base_utility_q FROM semantic_graph WHERE id=?", (belief_id,)).fetchone()
        assert row["base_utility_q"] == 0.0
    finally:
        conn.close()


def test_consolidate_stores_new_belief(initialized_db: Path) -> None:
    consolidate_and_prune_memory(
        "u",
        {
            "entity": "framework",
            "relation": "prefers",
            "value": "fastify",
            "category": "preference",
            "conviction": 0.9,
        },
        initialized_db,
    )
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute(
            "SELECT entity_target FROM semantic_graph WHERE entity_source='framework'"
        ).fetchone()
        assert row["entity_target"] == "fastify"
    finally:
        conn.close()


def test_consolidate_salience_rejects_low_conviction(initialized_db: Path) -> None:
    consolidate_and_prune_memory(
        "u",
        {
            "entity": "tailwind",
            "relation": "prefers",
            "value": "maybe",
            "category": "preference",
            "conviction": 0.2,
        },
        initialized_db,
    )
    conn = get_db_connection(initialized_db)
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM semantic_graph").fetchone()["c"]
        assert count == 0
    finally:
        conn.close()


def test_consolidate_safety_keyword_overrides_low_conviction(initialized_db: Path) -> None:
    consolidate_and_prune_memory(
        "u",
        {
            "entity": "user",
            "relation": "has_allergy",
            "value": "peanuts",
            "category": "preference",
            "conviction": 0.2,
        },
        initialized_db,
        user_prompt="I have a severe peanut allergy.",
    )
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute(
            "SELECT entity_target FROM semantic_graph WHERE entity_source='user'"
        ).fetchone()
        assert row is not None
        assert row["entity_target"] == "peanuts"
    finally:
        conn.close()


def test_consolidate_salience_allows_system_state_low_conviction(initialized_db: Path) -> None:
    consolidate_and_prune_memory(
        "u",
        {
            "entity": "deadline",
            "relation": "is",
            "value": "march-15",
            "category": "system_state",
            "conviction": 0.2,
        },
        initialized_db,
    )
    conn = get_db_connection(initialized_db)
    try:
        count = conn.execute("SELECT COUNT(*) AS c FROM semantic_graph").fetchone()["c"]
        assert count == 1
    finally:
        conn.close()


def test_consolidate_contradiction_replaces(initialized_db: Path) -> None:
    consolidate_and_prune_memory(
        "u",
        {"entity": "fw", "relation": "prefers", "value": "express", "conviction": 1.0},
        initialized_db,
    )
    consolidate_and_prune_memory(
        "u",
        {"entity": "fw", "relation": "prefers", "value": "fastify", "conviction": 1.0},
        initialized_db,
    )
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute("SELECT entity_target FROM semantic_graph").fetchone()
        assert row["entity_target"] == "fastify"
        count = conn.execute("SELECT COUNT(*) AS c FROM semantic_graph").fetchone()["c"]
        assert count == 1
    finally:
        conn.close()


def test_consolidate_prune_removes_low_weight(initialized_db: Path) -> None:
    conn = get_db_connection(initialized_db)
    conn.execute(
        """
        INSERT INTO semantic_graph (user_id, entity_source, relation, entity_target, node_weight)
        VALUES ('u', 'dead', 'is', 'gone', 0.05)
        """
    )
    conn.commit()
    conn.close()
    consolidate_and_prune_memory(
        "u",
        {"entity": "live", "relation": "is", "value": "ok", "conviction": 1.0},
        initialized_db,
    )
    conn = get_db_connection(initialized_db)
    try:
        rows = conn.execute("SELECT entity_source FROM semantic_graph").fetchall()
        sources = {row["entity_source"] for row in rows}
        assert "dead" not in sources
    finally:
        conn.close()


def test_consolidate_decay_reduces_weight(initialized_db: Path) -> None:
    conn = get_db_connection(initialized_db)
    conn.execute(
        """
        INSERT INTO semantic_graph (
            user_id, entity_source, relation, entity_target, node_weight, last_accessed
        ) VALUES ('u', 'old', 'is', 'stale', 1.0, '2020-01-01 00:00:00')
        """
    )
    conn.commit()
    conn.close()
    consolidate_and_prune_memory(
        "u",
        {"entity": "new", "relation": "is", "value": "fresh", "conviction": 1.0},
        initialized_db,
    )
    conn = get_db_connection(initialized_db)
    try:
        row = conn.execute(
            "SELECT node_weight FROM semantic_graph WHERE entity_source='old'"
        ).fetchone()
        assert float(row["node_weight"]) < 1.0
    finally:
        conn.close()


def test_dreaming_consolidate_missing_keys(initialized_db: Path) -> None:
    consolidate_and_prune_memory("u", {"relation": "x"}, initialized_db)
