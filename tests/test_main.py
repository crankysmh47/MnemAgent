"""Tests for main FastAPI application."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


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
    dump = await test_client.post(
        "/chat",
        json={"user_id": "u1", "session_id": "s1", "message": "/memory"},
    )
    assert "express" in dump.json()["response"].lower()


@pytest.mark.asyncio
async def test_chat_with_memory_update_skips_secondary_extraction(test_client: AsyncClient) -> None:
    raw = (
        '<memory_update>{"entity":"project","relation":"codename","value":"HelioForge",'
        '"category":"system_state","conviction":1.0}</memory_update> Noted!'
    )
    with patch("main.call_qwen_api", new=AsyncMock(return_value=raw)):
        with patch(
            "main.extract_facts_from_user_message",
            new=AsyncMock(
                return_value=[
                    {
                        "entity": "hackathon_project_codename",
                        "relation": "is",
                        "value": "HelioForge",
                        "category": "system_state",
                        "conviction": 1.0,
                    }
                ]
            ),
        ) as secondary:
            resp = await test_client.post(
                "/chat",
                json={
                    "user_id": "dedupe-test",
                    "session_id": "s1",
                    "message": "My hackathon project codename is HelioForge.",
                },
            )
    assert resp.status_code == 200
    secondary.assert_not_awaited()

    dump = await test_client.get("/api/memory/dump/dedupe-test")
    response = dump.json()["response"]
    assert response.count("HelioForge") == 1


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
async def test_chat_qwen_failure_still_stores_clear_teach_message(test_client: AsyncClient) -> None:
    with patch(
        "main.call_qwen_api",
        new=AsyncMock(return_value="I'm having trouble connecting right now. Please try again."),
    ):
        with patch(
            "main.build_optimized_qwen_payload",
            new=AsyncMock(
                return_value={
                    "payload": {},
                    "injected_ids": [],
                    "injected_values": [],
                }
            ),
        ):
            resp = await test_client.post(
                "/chat",
                json={
                    "user_id": "fallback-teach",
                    "session_id": "s1",
                    "message": (
                        "Remember this: my project codename is HelioForge, "
                        "and my preferred backend language is Python."
                    ),
                },
            )
    assert resp.status_code == 200
    assert "Saved to memory" in resp.json()["response"]

    dump = await test_client.get("/api/memory/dump/fallback-teach")
    assert "HelioForge" in dump.json()["response"]
    assert "Python" in dump.json()["response"]


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
