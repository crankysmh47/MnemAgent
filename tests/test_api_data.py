"""Tests for visualizer API data helpers."""

from __future__ import annotations

from memory.api_data import _build_graph_edges, get_events_since, get_graph_data, get_metrics_data, search_memories
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


def test_graph_edges_sparse_not_clique(initialized_db) -> None:
    facts = [
        ("phoenix", "lead", "Sarah", "persona"),
        ("phoenix", "deadline", "March_15", "system_state"),
        ("phoenix", "auth", "Auth0", "system_state"),
        ("backend", "language", "Python", "system_state"),
        ("language", "prefers", "Python", "preference"),
    ]
    for entity, relation, value, category in facts:
        consolidate_and_prune_memory(
            "u1",
            {
                "entity": entity,
                "relation": relation,
                "value": value,
                "category": category,
                "conviction": 0.9,
            },
            initialized_db,
        )

    graph = get_graph_data("u1", initialized_db)
    beliefs = graph["beliefs"]
    edges = graph["edges"]
    max_clique = len(beliefs) * (len(beliefs) - 1) // 2
    assert len(edges) < max_clique
    assert any(e.get("kind") == "cluster" for e in edges)
    assert len(edges) >= len(beliefs) - 1


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


def test_search_memories_tokenizes_natural_compound_queries(initialized_db) -> None:
    facts = [
        ("backend_language", "prefers", "Python", "preference"),
        ("frontend_framework", "uses", "React", "system_state"),
        ("project_codename", "is", "Atlas", "system_state"),
    ]
    for entity, relation, value, category in facts:
        consolidate_and_prune_memory(
            "u1",
            {
                "entity": entity,
                "relation": relation,
                "value": value,
                "category": category,
                "conviction": 1.0,
            },
            initialized_db,
        )

    results = search_memories(
        "u1",
        "what do I use for Python React backend work on Atlas",
        top_k=5,
        db_path=initialized_db,
    )
    pairs = {(r["entity_source"], r["entity_target"]) for r in results}
    assert ("backend_language", "Python") in pairs
    assert ("frontend_framework", "React") in pairs
    assert ("project_codename", "Atlas") in pairs


def test_search_memories_compound_queries_preserve_category_filter(initialized_db) -> None:
    consolidate_and_prune_memory(
        "u1",
        {
            "entity": "backend_language",
            "relation": "prefers",
            "value": "Python",
            "category": "preference",
            "conviction": 1.0,
        },
        initialized_db,
    )
    consolidate_and_prune_memory(
        "u1",
        {
            "entity": "backend_runtime",
            "relation": "uses",
            "value": "Python",
            "category": "system_state",
            "conviction": 1.0,
        },
        initialized_db,
    )

    results = search_memories(
        "u1",
        "backend python",
        top_k=5,
        category="system_state",
        db_path=initialized_db,
    )
    assert results
    assert {r["category"] for r in results} == {"system_state"}
