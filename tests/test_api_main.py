"""Tests for FastAPI visualizer and memory store endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_api_graph_endpoint(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/graph/test-user")
    assert resp.status_code == 200
    data = resp.json()
    assert "beliefs" in data


async def test_api_events_endpoint(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/events/test-user")
    assert resp.status_code == 200
    assert "events" in resp.json()


async def test_api_metrics_endpoint(test_client: AsyncClient) -> None:
    resp = await test_client.get("/api/metrics/test-user")
    assert resp.status_code == 200
    assert "avg_q_i" in resp.json()


async def test_api_memory_store(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/memory/store",
        json={
            "user_id": "store-user",
            "entity": "framework",
            "relation": "prefers",
            "value": "fastify",
            "category": "preference",
            "conviction": 0.9,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["stored"] is True
    dump = await test_client.post(
        "/chat",
        json={"user_id": "store-user", "session_id": "s1", "message": "/memory"},
    )
    assert "fastify" in dump.json()["response"].lower()


async def test_api_memory_store_rejects_low_conviction(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/memory/store",
        json={
            "user_id": "reject-user",
            "entity": "orm",
            "relation": "maybe",
            "value": "prisma",
            "category": "preference",
            "conviction": 0.1,
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["stored"] is False
    assert body["status"] == "rejected"


async def test_chat_memory_stats_alias(test_client: AsyncClient) -> None:
    await test_client.post(
        "/api/memory/store",
        json={
            "user_id": "stats-user",
            "entity": "lang",
            "relation": "prefers",
            "value": "python",
            "category": "preference",
            "conviction": 0.9,
        },
    )
    resp = await test_client.post(
        "/chat",
        json={"user_id": "stats-user", "session_id": "s1", "message": "/memory stats"},
    )
    assert resp.status_code == 200
    assert "Q_i" in resp.json()["response"] or "Summary" in resp.json()["response"]


async def test_api_user_bind_rejects_blank(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/user/bind",
        json={"channel": " ", "sender_id": "123"},
    )
    assert resp.status_code == 422


async def test_api_memory_dump_json_format(test_client: AsyncClient) -> None:
    await test_client.post(
        "/api/memory/store",
        json={
            "user_id": "json-dump-user",
            "entity": "db",
            "relation": "uses",
            "value": "postgres",
            "category": "system_state",
            "conviction": 0.9,
        },
    )
    resp = await test_client.get("/api/memory/dump/json-dump-user?format=json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["format"] == "json"
    assert isinstance(data["beliefs"], list)
    assert any(b["value"] == "postgres" for b in data["beliefs"])
