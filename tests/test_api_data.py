"""Tests for visualizer API data helpers."""

from __future__ import annotations

from memory.api_data import get_events_since, get_graph_data, get_metrics_data, search_memories
from memory.dreaming import consolidate_and_prune_memory
from memory.event_log import log_memory_event
def test_memory_events_table_exists(initialized_db) -> None:
    log_memory_event("u1", "new_belief", "backend", "express", {"conviction": 1.0}, initialized_db)
    events = get_events_since("u1", db_path=initialized_db)
    assert len(events) == 1
    assert events[0]["event_type"] == "new_belief"


def test_graph_api_shape(initialized_db) -> None:
    consolidate_and_prune_memory(
        "u1",
        {
            "entity": "backend",
            "relation": "prefers",
            "value": "express",
            "category": "preference",
            "conviction": 0.95,
        },
        initialized_db,
    )
    graph = get_graph_data("u1", initialized_db)
    assert "beliefs" in graph
    assert "edges" in graph
    assert graph["total_turns"] >= 1
    assert len(graph["beliefs"]) >= 1


def test_metrics_api(initialized_db) -> None:
    metrics = get_metrics_data("u1", initialized_db)
    assert "total_beliefs" in metrics
    assert "ucb_timeline" in metrics


def test_search_memories(initialized_db) -> None:
    consolidate_and_prune_memory(
        "u1",
        {
            "entity": "language",
            "relation": "prefers",
            "value": "python",
            "category": "preference",
            "conviction": 1.0,
        },
        initialized_db,
    )
    results = search_memories("u1", "python", top_k=5, db_path=initialized_db)
    assert len(results) >= 1
