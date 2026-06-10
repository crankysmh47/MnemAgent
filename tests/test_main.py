"""Tests for main FastAPI application."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

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


@pytest.mark.asyncio
async def test_health_check(test_client: AsyncClient) -> None:
    resp = await test_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "mnemos"


@pytest.mark.asyncio
async def test_chat_memory_command(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/chat",
        json={"user_id": "u1", "session_id": "s1", "message": "/memory"},
    )
    assert resp.status_code == 200
    assert "No memories" in resp.json()["response"]


@pytest.mark.asyncio
async def test_chat_memory_stats_command(test_client: AsyncClient) -> None:
    resp = await test_client.post(
        "/chat",
        json={"user_id": "u1", "session_id": "s1", "message": "/memory --mode stats"},
    )
    assert resp.status_code == 200
    assert "No memories" in resp.json()["response"]


@pytest.mark.asyncio
async def test_chat_normal_message(test_client: AsyncClient) -> None:
    with patch("main.call_qwen_api", new=AsyncMock(return_value="Hello there")):
        with patch(
            "main.build_optimized_qwen_payload",
            new=AsyncMock(return_value={"payload": {}, "injected_ids": []}),
        ):
            resp = await test_client.post(
                "/chat",
                json={"user_id": "u1", "session_id": "s1", "message": "hi"},
            )
    assert resp.status_code == 200
    assert resp.json()["response"] == "Hello there"


@pytest.mark.asyncio
async def test_chat_with_memory_update(test_client: AsyncClient) -> None:
    raw = (
        '<memory_update>{"entity":"fw","relation":"prefers","value":"express",'
        '"category":"preference","conviction":1.0}</memory_update> Noted!'
    )
    with patch("main.call_qwen_api", new=AsyncMock(return_value=raw)):
        with patch(
            "main.build_optimized_qwen_payload",
            new=AsyncMock(return_value={"payload": {}, "injected_ids": []}),
        ):
            resp = await test_client.post(
                "/chat",
                json={"user_id": "u1", "session_id": "s1", "message": "use express"},
            )
    assert "<memory_update>" not in resp.json()["response"]
    assert "Noted!" in resp.json()["response"]


@pytest.mark.asyncio
async def test_chat_request_validation(test_client: AsyncClient) -> None:
    resp = await test_client.post("/chat", json={"user_id": "u1"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_chat_qwen_failure_graceful(test_client: AsyncClient) -> None:
    with patch(
        "main.call_qwen_api",
        new=AsyncMock(return_value="I'm having trouble connecting right now. Please try again."),
    ):
        with patch(
            "main.build_optimized_qwen_payload",
            new=AsyncMock(return_value={"payload": {}, "injected_ids": []}),
        ):
            resp = await test_client.post(
                "/chat",
                json={"user_id": "u1", "session_id": "s1", "message": "hi"},
            )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_main_background_task_error_doesnt_crash(test_client: AsyncClient) -> None:
    with patch("main._run_dreaming_phase", side_effect=Exception("boom")):
        with patch("main.call_qwen_api", new=AsyncMock(return_value="ok")):
            with patch(
                "main.build_optimized_qwen_payload",
                new=AsyncMock(return_value={"payload": {}, "injected_ids": []}),
            ):
                resp = await test_client.post(
                    "/chat",
                    json={"user_id": "u1", "session_id": "s1", "message": "hi"},
                )
    assert resp.status_code == 200
