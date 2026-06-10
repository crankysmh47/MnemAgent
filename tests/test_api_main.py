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
