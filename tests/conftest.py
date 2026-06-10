"""Shared pytest fixtures for MnemOS tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from storage.db_manager import initialize_database


@pytest.fixture
async def test_client(tmp_path, monkeypatch):
    db_path = tmp_path / "app_test.db"
    monkeypatch.setattr("config.settings.DB_PATH", db_path)
    monkeypatch.setattr("storage.db_manager.settings.DB_PATH", db_path)
    initialize_database(db_path)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database file path."""
    return tmp_path / "test_memory_state.db"


@pytest.fixture
def initialized_db(tmp_db_path: Path) -> Path:
    """Initialize a fresh database and return its path."""
    initialize_database(tmp_db_path)
    return tmp_db_path


@pytest.fixture
def populated_db(initialized_db: Path) -> Path:
    """Insert sample beliefs for retrieval tests."""
    from storage.db_manager import get_db_connection

    conn = get_db_connection(initialized_db)
    beliefs = [
        ("user1", "preference", "backend_framework", "prefers", "express", 0.9, 2, 1, 0.9),
        ("user1", "preference", "code_style", "prefers", "minimal-comments", 0.7, 1, 0, 0.6),
        ("user1", "system_state", "deadline", "is", "march-15", 0.6, 0, 0, 0.5),
        ("user1", "persona", "user_role", "is", "senior-engineer", 0.8, 0, 0, 0.85),
        ("user1", "preference", "language", "prefers", "python", 0.95, 5, 3, 0.95),
    ]
    for belief in beliefs:
        conn.execute(
            """
            INSERT INTO semantic_graph (
                user_id, category, entity_source, relation, entity_target,
                base_utility_q, injection_count, influence_count, node_weight
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            belief,
        )
    conn.commit()
    conn.close()
    return initialized_db
