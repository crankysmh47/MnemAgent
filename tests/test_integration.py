"""Integration tests for multi-turn memory flows."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from main import app
from storage.db_manager import initialize_database


async def flush_background_tasks() -> None:
    """Let pending asyncio background tasks complete."""
    await asyncio.sleep(0.15)
    tasks = [
        task
        for task in asyncio.all_tasks()
        if task is not asyncio.current_task() and not task.done()
    ]
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


@pytest.fixture
async def fresh_app(tmp_path, monkeypatch):
    db_path = tmp_path / "integration.db"
    monkeypatch.setattr("config.settings.DB_PATH", db_path)
    monkeypatch.setattr("storage.db_manager.settings.DB_PATH", db_path)
    initialize_database(db_path)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.mark.asyncio
async def test_three_session_contradiction_flow(fresh_app: AsyncClient) -> None:
    express_response = (
        '<memory_update>{"entity":"backend_framework","relation":"prefers",'
        '"value":"express","category":"system_state","conviction":1.0}'
        "</memory_update> Got it, Express it is!"
    )
    dark_response = (
        '<memory_update>{"entity":"ide_theme","relation":"prefers",'
        '"value":"dark-mode","category":"preference","conviction":0.9}'
        "</memory_update> Dark mode noted."
    )
    fastify_response = (
        '<memory_update>{"entity":"backend_framework","relation":"prefers",'
        '"value":"fastify","category":"system_state","conviction":1.0}'
        "</memory_update> Switching to Fastify."
    )

    with patch("main.call_qwen_api", new=AsyncMock(side_effect=[express_response, dark_response, fastify_response])):
        r1 = await fresh_app.post(
            "/chat",
            json={
                "user_id": "demo",
                "session_id": "s1",
                "message": "We are using Express for the backend.",
            },
        )
        await flush_background_tasks()
        assert "<memory_update>" not in r1.json()["response"]

        mem1 = await fresh_app.post(
            "/chat",
            json={"user_id": "demo", "session_id": "s1", "message": "/memory"},
        )
        assert "express" in mem1.json()["response"].lower()

        r2 = await fresh_app.post(
            "/chat",
            json={
                "user_id": "demo",
                "session_id": "s1",
                "message": "I prefer dark mode in my IDE.",
            },
        )
        await flush_background_tasks()
        assert r2.status_code == 200

        mem2 = await fresh_app.post(
            "/chat",
            json={"user_id": "demo", "session_id": "s1", "message": "/memory"},
        )
        assert "dark-mode" in mem2.json()["response"].lower()

        r3 = await fresh_app.post(
            "/chat",
            json={
                "user_id": "demo",
                "session_id": "s2",
                "message": "Actually we're switching to Fastify now.",
            },
        )
        await flush_background_tasks()
        assert r3.status_code == 200

        mem3 = await fresh_app.post(
            "/chat",
            json={"user_id": "demo", "session_id": "s2", "message": "/memory"},
        )
        body = mem3.json()["response"].lower()
        assert "fastify" in body
        assert "express" not in body


@pytest.mark.asyncio
async def test_salience_auction_rejects_low_conviction(fresh_app: AsyncClient) -> None:
    tailwind = (
        '<memory_update>{"entity":"css_framework","relation":"prefers",'
        '"value":"tailwind","category":"preference","conviction":0.2}'
        "</memory_update> Maybe later."
    )
    with patch("main.call_qwen_api", new=AsyncMock(return_value=tailwind)):
        await fresh_app.post(
            "/chat",
            json={
                "user_id": "u",
                "session_id": "s1",
                "message": "Maybe we'll try Tailwind at some point.",
            },
        )
    await flush_background_tasks()
    mem = await fresh_app.post(
        "/chat",
        json={"user_id": "u", "session_id": "s1", "message": "/memory"},
    )
    assert "tailwind" not in mem.json()["response"].lower()


@pytest.mark.asyncio
async def test_salience_auction_accepts_system_state(fresh_app: AsyncClient) -> None:
    deadline = (
        '<memory_update>{"entity":"deadline","relation":"is",'
        '"value":"march-15","category":"system_state","conviction":0.3}'
        "</memory_update> Noted."
    )
    with patch("main.call_qwen_api", new=AsyncMock(return_value=deadline)):
        await fresh_app.post(
            "/chat",
            json={"user_id": "u", "session_id": "s1", "message": "The deadline is March 15."},
        )
    await flush_background_tasks()
    mem = await fresh_app.post(
        "/chat",
        json={"user_id": "u", "session_id": "s1", "message": "/memory"},
    )
    assert "march-15" in mem.json()["response"].lower()


@pytest.mark.asyncio
async def test_decay_reduces_stale_beliefs(initialized_db) -> None:
    from memory.dreaming import consolidate_and_prune_memory
    from storage.db_manager import get_db_connection

    conn = get_db_connection(initialized_db)
    conn.execute(
        """
        INSERT INTO semantic_graph (
            user_id, entity_source, relation, entity_target, node_weight, last_accessed
        ) VALUES ('u', 'old_fact', 'is', 'stale', 1.0, '2020-01-01 00:00:00')
        """
    )
    conn.commit()
    conn.close()

    consolidate_and_prune_memory(
        "u",
        {"entity": "new_fact", "relation": "is", "value": "fresh", "conviction": 1.0},
        initialized_db,
    )
    conn = get_db_connection(initialized_db)
    row = conn.execute(
        "SELECT node_weight FROM semantic_graph WHERE entity_source='old_fact'"
    ).fetchone()
    conn.close()
    assert float(row["node_weight"]) < 1.0


@pytest.mark.asyncio
async def test_prune_removes_dead_beliefs(fresh_app: AsyncClient, tmp_path) -> None:
    from storage.db_manager import get_db_connection

    db_path = tmp_path / "integration.db"
    conn = get_db_connection(db_path)
    conn.execute(
        """
        INSERT INTO semantic_graph (
            user_id, entity_source, relation, entity_target, node_weight
        ) VALUES ('u', 'dead', 'is', 'gone', 0.05)
        """
    )
    conn.commit()
    conn.close()

    trigger = (
        '<memory_update>{"entity":"live","relation":"is","value":"ok","conviction":1.0}'
        "</memory_update> ok"
    )
    with patch("main.call_qwen_api", new=AsyncMock(return_value=trigger)):
        await fresh_app.post(
            "/chat",
            json={"user_id": "u", "session_id": "s1", "message": "go"},
        )
    await flush_background_tasks()
    conn = get_db_connection(db_path)
    row = conn.execute(
        "SELECT COUNT(*) AS c FROM semantic_graph WHERE entity_source='dead'"
    ).fetchone()
    conn.close()
    assert row["c"] == 0


def test_ucb_surfaces_dormant_memories(initialized_db) -> None:
    from memory.waking import _calculate_ucb_score

    high_n = _calculate_ucb_score(0.8, 20, 50)
    dormant = _calculate_ucb_score(0.8, 0, 50)
    assert dormant > high_n
