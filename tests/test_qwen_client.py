"""Tests for llm.qwen_client."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from llm.qwen_client import (
    call_qwen_api,
    extract_memory_update,
    strip_memory_tags,
)


def test_extract_memory_update_valid() -> None:
    raw = (
        '<memory_update>{"entity":"x","relation":"prefers","value":"y",'
        '"category":"preference","conviction":1.0}</memory_update> OK'
    )
    result = extract_memory_update(raw)
    assert result is not None
    assert result["entity"] == "x"
    assert result["value"] == "y"


def test_extract_memory_update_no_tags() -> None:
    assert extract_memory_update("plain text") is None


def test_extract_memory_update_malformed_json() -> None:
    assert extract_memory_update("<memory_update>{bad</memory_update>") is None


def test_extract_memory_update_missing_keys() -> None:
    raw = '<memory_update>{"entity":"x"}</memory_update>'
    assert extract_memory_update(raw) is None


def test_extract_memory_update_with_surrounding_text() -> None:
    raw = 'prefix <memory_update>{"entity":"a","relation":"b","value":"c"}</memory_update> suffix'
    result = extract_memory_update(raw)
    assert result["value"] == "c"


def test_strip_memory_tags_removes_block() -> None:
    raw = '<memory_update>{"entity":"a","relation":"b","value":"c"}</memory_update> Hello'
    assert strip_memory_tags(raw) == "Hello"


def test_strip_memory_tags_no_tags() -> None:
    assert strip_memory_tags("unchanged") == "unchanged"


def test_strip_memory_tags_multiline() -> None:
    raw = "<memory_update>\n{\"entity\":\"a\",\"relation\":\"b\",\"value\":\"c\"}\n</memory_update>\nHi"
    assert strip_memory_tags(raw) == "Hi"


@pytest.mark.asyncio
async def test_call_qwen_api_success() -> None:
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={"choices": [{"message": {"content": "hello world"}}]}
    )
    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("llm.qwen_client.aiohttp.ClientSession", return_value=mock_session):
        result = await call_qwen_api({"model": "qwen-plus", "messages": []})
    assert result == "hello world"


@pytest.mark.asyncio
async def test_call_qwen_api_timeout() -> None:
    with patch(
        "llm.qwen_client.aiohttp.ClientSession",
        side_effect=aiohttp.ClientError("timeout"),
    ):
        result = await call_qwen_api({"model": "qwen-plus", "messages": []})
    assert "trouble connecting" in result


@pytest.mark.asyncio
async def test_call_qwen_api_rate_limit_then_success() -> None:
    resp429 = AsyncMock()
    resp429.status = 429
    resp200 = AsyncMock()
    resp200.status = 200
    resp200.json = AsyncMock(return_value={"choices": [{"message": {"content": "ok"}}]})

    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(
        side_effect=[resp429, resp200]
    )
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("llm.qwen_client.aiohttp.ClientSession", return_value=mock_session):
        with patch("llm.qwen_client.asyncio.sleep", new=AsyncMock()):
            result = await call_qwen_api({"model": "qwen-plus", "messages": []})
    assert result == "ok"


@pytest.mark.asyncio
async def test_call_qwen_api_rate_limit_exhausted() -> None:
    resp429 = AsyncMock()
    resp429.status = 429
    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=resp429)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("llm.qwen_client.aiohttp.ClientSession", return_value=mock_session):
        with patch("llm.qwen_client.asyncio.sleep", new=AsyncMock()):
            result = await call_qwen_api({"model": "qwen-plus", "messages": []})
    assert "trouble connecting" in result
