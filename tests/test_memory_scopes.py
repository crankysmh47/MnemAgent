from pathlib import Path

import pytest

from memory.api_data import get_graph_data, retrieve_scoped_beliefs
from memory.scopes import MemoryScope
from storage.db_manager import get_db_connection, initialize_database


def test_memory_scope_defaults_and_validates_repository_ids():
    assert MemoryScope().scope_type == "core"
    assert MemoryScope().scope_id == "core"
    assert MemoryScope("repository", "crankysmh47/MnemBench").scope_id == "crankysmh47/MnemBench"
    with pytest.raises(ValueError):
        MemoryScope("repository", "../secret")


def test_graph_isolates_repository_scopes_and_can_include_core(tmp_path: Path):
    db = tmp_path / "scopes.db"
    initialize_database(db)
    conn = get_db_connection(db)
    rows = [
        ("u", "core", "core", "user", "prefers", "concise"),
        ("u", "repository", "org/a", "tests", "uses", "vitest"),
        ("u", "repository", "org/b", "tests", "uses", "pytest"),
    ]
    conn.executemany("INSERT INTO semantic_graph (user_id, scope_type, scope_id, entity_source, relation, entity_target) VALUES (?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    graph = get_graph_data("u", db, scope_type="repository", scope_id="org/a", include_core=True)
    assert {(b["scope_type"], b["scope_id"]) for b in graph["beliefs"]} == {("core", "core"), ("repository", "org/a")}
    assert all(b["entity_target"] != "pytest" for b in graph["beliefs"])


def test_scoped_retrieval_caps_repository_at_four_and_core_at_two(tmp_path: Path):
    db = tmp_path / "retrieval.db"
    initialize_database(db)
    conn = get_db_connection(db)
    for index in range(7):
        conn.execute("INSERT INTO semantic_graph (user_id, scope_type, scope_id, entity_source, relation, entity_target) VALUES ('u','repository','org/repo',?, 'uses', 'test')", (f"repo-{index}",))
    for index in range(4):
        conn.execute("INSERT INTO semantic_graph (user_id, scope_type, scope_id, entity_source, relation, entity_target) VALUES ('u','core','core',?, 'prefers', 'test')", (f"core-{index}",))
    conn.commit()
    conn.close()
    found = retrieve_scoped_beliefs("u", "org/repo", "test", db_path=db)
    assert len(found) == 6
    assert sum(item["scope_type"] == "repository" for item in found) == 4
    assert sum(item["scope_type"] == "core" for item in found) == 2
