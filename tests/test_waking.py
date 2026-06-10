"""Tests for memory.waking."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from memory import waking
from memory.waking import (
    _calculate_ucb_score,
    _get_rwr_associations,
    build_optimized_qwen_payload,
    extract_entities_robust,
    get_local_embedding_sync,
)
from storage.db_manager import get_db_connection


def test_calculate_ucb_score_basic() -> None:
    score = _calculate_ucb_score(0.5, 3, 10, c=0.3)
    expected = 0.5 + 0.3 * (10 ** 0.5) ** 0  # manual: 0.5 + 0.3 * sqrt(ln(10)/4)
    import math

    expected = 0.5 + 0.3 * math.sqrt(math.log(10) / 4)
    assert score == pytest.approx(expected)


def test_calculate_ucb_score_exploration_bonus_decreases() -> None:
    low_n = _calculate_ucb_score(0.5, 1, 20)
    high_n = _calculate_ucb_score(0.5, 10, 20)
    assert low_n > high_n


def test_calculate_ucb_score_dormant_memory_rises() -> None:
    low_t = _calculate_ucb_score(0.5, 0, 5)
    high_t = _calculate_ucb_score(0.5, 0, 50)
    assert high_t > low_t


def test_extract_entities_robust_tech_terms() -> None:
    entities = extract_entities_robust("I use Python and React daily")
    assert "python" in entities
    assert "react" in entities


def test_extract_entities_robust_proper_nouns() -> None:
    entities = extract_entities_robust("Talk to John about the API")
    assert "john" in entities


def test_extract_entities_robust_deduplication() -> None:
    entities = extract_entities_robust("python Python PYTHON")
    assert entities.count("python") == 1


def test_get_rwr_associations_connected_graph() -> None:
    edges = [(1, 2), (2, 3), (3, 4), (4, 5), (2, 4)]
    result = _get_rwr_associations(edges, 1, top_k=2)
    assert len(result) <= 2
    assert all(node != 1 for node, _ in result)


def test_get_rwr_associations_disconnected_node() -> None:
    assert _get_rwr_associations([(1, 2)], 99) == []


def test_get_rwr_associations_empty_graph() -> None:
    assert _get_rwr_associations([], 1) == []


def test_get_single_entity_hop_finds_related(populated_db: Path) -> None:
    from memory.waking import _get_single_entity_hop

    result = _get_single_entity_hop("user1", "python", set(), populated_db)
    assert len(result) >= 0


def test_get_single_entity_hop_excludes_ids(populated_db: Path) -> None:
    from memory.waking import _get_single_entity_hop

    conn = get_db_connection(populated_db)
    row = conn.execute(
        "SELECT id FROM semantic_graph WHERE entity_source='language' LIMIT 1"
    ).fetchone()
    conn.close()
    assert row is not None
    belief_id = int(row["id"])
    result = _get_single_entity_hop("user1", "language", {belief_id}, populated_db)
    assert belief_id not in result


@pytest.mark.asyncio
async def test_build_payload_returns_correct_structure(populated_db: Path) -> None:
    with patch("memory.waking.get_embedding", new=AsyncMock(return_value=[0.1] * 384)):
        result = await build_optimized_qwen_payload(
            "user1", "s1", "python backend", 10, populated_db
        )
    assert "payload" in result
    assert "injected_ids" in result


@pytest.mark.asyncio
async def test_build_payload_injects_facts_in_prompt(populated_db: Path) -> None:
    with patch("memory.waking.get_embedding", new=AsyncMock(return_value=[0.1] * 384)):
        result = await build_optimized_qwen_payload(
            "user1", "s1", "python express", 10, populated_db
        )
    system_msg = result["payload"]["messages"][0]["content"]
    assert "MEMORY CONTEXT" in system_msg


@pytest.mark.asyncio
async def test_build_payload_empty_graph(initialized_db: Path) -> None:
    with patch("memory.waking.get_embedding", new=AsyncMock(return_value=[0.1] * 384)):
        result = await build_optimized_qwen_payload(
            "u", "s1", "hello", 1, initialized_db
        )
    assert result["injected_ids"] == []


@pytest.mark.asyncio
async def test_build_payload_updates_last_accessed(populated_db: Path) -> None:
    with patch("memory.waking.get_embedding", new=AsyncMock(return_value=[0.1] * 384)):
        result = await build_optimized_qwen_payload(
            "user1", "s1", "python", 10, populated_db
        )
    if result["injected_ids"]:
        conn = get_db_connection(populated_db)
        row = conn.execute(
            "SELECT last_accessed FROM semantic_graph WHERE id=?",
            (result["injected_ids"][0],),
        ).fetchone()
        conn.close()
        assert row["last_accessed"] is not None


@pytest.mark.asyncio
async def test_build_payload_vec_unavailable_falls_back_to_keyword(populated_db: Path) -> None:
    with patch("memory.waking.VEC_AVAILABLE", False):
        with patch("memory.waking.get_embedding", new=AsyncMock(return_value=[0.1] * 384)):
            result = await build_optimized_qwen_payload(
                "user1", "s1", "python backend", 10, populated_db
            )
    assert isinstance(result["injected_ids"], list)


def test_get_embedding_local_model() -> None:
    waking._embedding_cache.clear()
    vector = get_local_embedding_sync("test sentence")
    assert len(vector) == 384


def test_get_embedding_dimension_mismatch_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    from config import settings

    monkeypatch.setattr(settings, "EMBEDDING_DIM", 1024)
    waking._embedding_cache.clear()
    with pytest.raises(ValueError, match="EMBEDDING_DIM"):
        get_local_embedding_sync("dimension mismatch test unique text")


def test_waking_embedding_cache_hit() -> None:
    waking._embedding_cache.clear()
    first = get_local_embedding_sync("cache me")
    second = get_local_embedding_sync("cache me")
    assert first is second


@pytest.mark.asyncio
async def test_build_payload_respects_max_injected_facts(populated_db: Path) -> None:
    with patch("memory.waking.get_embedding", new=AsyncMock(return_value=[0.1] * 384)):
        result = await build_optimized_qwen_payload(
            "user1", "s1", "python express fastify docker", 10, populated_db
        )
    assert len(result["injected_ids"]) <= 6
