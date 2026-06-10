"""Tests for memory.mcp_commands."""

from __future__ import annotations

from pathlib import Path

from memory.mcp_commands import execute_memory_dump_tool, execute_memory_stats_tool
from storage.db_manager import get_db_connection


def _insert_belief(
    db_path: Path,
    source: str,
    target: str,
    weight: float,
    category: str = "preference",
    q: float = 0.8,
    n_i: int = 0,
    inf: int = 0,
) -> None:
    conn = get_db_connection(db_path)
    conn.execute(
        """
        INSERT INTO semantic_graph (
            user_id, category, entity_source, relation, entity_target,
            node_weight, base_utility_q, injection_count, influence_count
        ) VALUES ('u', ?, ?, 'prefers', ?, ?, ?, ?, ?)
        """,
        (category, source, target, weight, q, n_i, inf),
    )
    conn.commit()
    conn.close()


def test_memory_dump_empty(initialized_db: Path) -> None:
    result = execute_memory_dump_tool("u", initialized_db)
    assert "No memories" in result


def test_memory_dump_with_beliefs(initialized_db: Path) -> None:
    _insert_belief(initialized_db, "a", "x", 0.9)
    _insert_belief(initialized_db, "b", "y", 0.9)
    _insert_belief(initialized_db, "c", "z", 0.9)
    result = execute_memory_dump_tool("u", initialized_db)
    assert result.count("|") >= 3


def test_memory_dump_confidence_labels(initialized_db: Path) -> None:
    _insert_belief(initialized_db, "high", "x", 0.9)
    _insert_belief(initialized_db, "med", "y", 0.6)
    _insert_belief(initialized_db, "low", "z", 0.3)
    result = execute_memory_dump_tool("u", initialized_db)
    assert "High Confidence" in result
    assert "Confident" in result
    assert "Fading Memory" in result


def test_memory_stats_empty(initialized_db: Path) -> None:
    assert "No memories" in execute_memory_stats_tool("u", 1, initialized_db)


def test_memory_stats_with_beliefs(initialized_db: Path) -> None:
    _insert_belief(initialized_db, "framework", "express", 0.9)
    result = execute_memory_stats_tool("u", 5, initialized_db)
    assert "Q_i" in result
    assert "UCB Score" in result


def test_memory_stats_truncation(initialized_db: Path) -> None:
    long_name = "a" * 20
    _insert_belief(initialized_db, long_name, "value", 0.9)
    result = execute_memory_stats_tool("u", 5, initialized_db)
    assert ".." in result


def test_memory_stats_ucb_calculation(initialized_db: Path) -> None:
    _insert_belief(initialized_db, "fw", "express", 0.9, q=0.5, n_i=3)
    result = execute_memory_stats_tool("u", 10, initialized_db)
    assert "0.50" in result


def test_memory_stats_category_tags(initialized_db: Path) -> None:
    _insert_belief(initialized_db, "a", "x", 0.9, category="preference")
    _insert_belief(initialized_db, "b", "y", 0.9, category="system_state")
    _insert_belief(initialized_db, "c", "z", 0.9, category="persona")
    result = execute_memory_stats_tool("u", 5, initialized_db)
    assert "PREF" in result
    assert "SYST" in result
    assert "PERS" in result


def test_memory_stats_inf_percentage(initialized_db: Path) -> None:
    _insert_belief(initialized_db, "fw", "express", 0.9, n_i=10, inf=7)
    result = execute_memory_stats_tool("u", 10, initialized_db)
    assert "70%" in result


def test_mcp_commands_dump_excludes_pruned(initialized_db: Path) -> None:
    _insert_belief(initialized_db, "dead", "gone", 0.05)
    result = execute_memory_dump_tool("u", initialized_db)
    assert "dead" not in result
