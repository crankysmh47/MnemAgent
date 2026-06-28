"""Tests for user bind and enhanced memory API endpoints."""

from __future__ import annotations

from httpx import AsyncClient


async def test_user_bind_endpoint(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/user/bind",
        json={"channel": "telegram", "sender_id": "999", "display_name": "Test"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "user_id" in data
    assert data["channel"] == "telegram"


async def test_user_bind_endpoint_can_attach_existing_user_id(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/user/bind",
        json={
            "channel": "discord",
            "sender_id": "tester-1",
            "display_name": "Tester",
            "user_id": "review-shared-user",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["user_id"] == "review-shared-user"

    bindings = await test_client.get("/api/user/bindings/review-shared-user")
    assert bindings.status_code == 200
    assert bindings.json()["bindings"][0]["channel"] == "discord"


async def test_memory_dump_endpoint(test_client: AsyncClient) -> None:
    store = await test_client.post(
        "/api/memory/store",
        json={
            "user_id": "dump-test",
            "entity": "lang",
            "relation": "prefers",
            "value": "Rust",
            "conviction": 1.0,
        },
    )
    assert store.status_code == 200
    dump = await test_client.get("/api/memory/dump/dump-test?format=markdown")
    assert dump.status_code == 200
    assert "Rust" in dump.json()["response"]


async def test_memory_store_batch(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/api/memory/store/batch",
        json={
            "user_id": "batch-test",
            "facts": [
                {
                    "user_id": "batch-test",
                    "entity": "db",
                    "relation": "prefers",
                    "value": "PostgreSQL",
                },
                {
                    "user_id": "batch-test",
                    "entity": "api",
                    "relation": "prefers",
                    "value": "FastAPI",
                },
            ],
        },
    )
    assert resp.status_code == 200
    assert resp.json()["stored_count"] == 2


async def test_memory_search_with_category(test_client: AsyncClient) -> None:
    await test_client.post(
        "/api/memory/store",
        json={
            "user_id": "search-cat",
            "entity": "style",
            "relation": "prefers",
            "value": "Tailwind",
            "category": "preference",
            "conviction": 1.0,
        },
    )
    resp = await test_client.get(
        "/api/memory/search/search-cat?query=Tailwind&category=preference"
    )
    assert resp.status_code == 200
    assert len(resp.json()["results"]) >= 1
