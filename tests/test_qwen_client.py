"""Tests for llm.qwen_client."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

import llm.qwen_client as qwen_client
from llm.qwen_client import (
    call_qwen_api,
    extract_facts_deterministically,
    extract_facts_from_conversation,
    extract_facts_from_user_message,
    extract_memory_update,
    extract_memory_updates,
    response_has_memory_block,
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


def test_extract_facts_deterministically_handles_clear_teach_message() -> None:
    facts = extract_facts_deterministically(
        "Remember this for future chats: my hackathon project codename is HelioForge, "
        "my preferred backend language is Python, and my frontend framework is React."
    )
    triples = {(f["entity"], f["relation"], f["value"]) for f in facts}
    assert ("hackathon_project_codename", "is", "HelioForge") in triples
    assert ("backend_language", "prefers", "Python") in triples
    assert ("frontend_framework", "is", "React") in triples


def test_extract_facts_deterministically_handles_prospective_memory() -> None:
    facts = extract_facts_deterministically(
        "When I ask about deployment, remind me to check the OSS snapshot."
    )
    triples = {(f["entity"], f["relation"], f["value"]) for f in facts}
    assert ("when_asked_about_deployment", "remind", "check the OSS snapshot") in triples


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


def test_strip_memory_tags_bare_json() -> None:
    raw = (
        'Sure! { "entity": "user", "relation": "has interest in", '
        '"value": "hackathons", "category": "persona", "conviction": 0.7 }'
    )
    assert "entity" not in strip_memory_tags(raw)
    assert strip_memory_tags(raw).startswith("Sure!")


def test_extract_memory_update_bare_json() -> None:
    raw = (
        'Hello { "entity": "user", "relation": "prefers", "value": "Python", '
        '"category": "preference", "conviction": 0.9 } world'
    )
    result = extract_memory_update(raw)
    assert result is not None
    assert result["entity"] == "user"
    assert result["value"] == "Python"


def test_extract_memory_update_skip() -> None:
    raw = '<memory_update>{"skip": true}</memory_update> Hello'
    assert extract_memory_update(raw) is None
    assert extract_memory_updates(raw) == []


def test_response_has_memory_block_skip() -> None:
    raw = '<memory_update>{"skip": true}</memory_update> Hello'
    assert response_has_memory_block(raw) is True


def test_response_has_memory_block_absent() -> None:
    assert response_has_memory_block("plain reply") is False


def test_extract_memory_update_markdown_codeblock() -> None:
    raw = """```json
{"entity":"backend","relation":"uses","value":"prisma","category":"system_state","conviction":0.9}
```
Sounds good."""
    result = extract_memory_update(raw)
    assert result is not None
    assert result["value"] == "prisma"


def test_strip_memory_tags_empty_after_strip() -> None:
    raw = '<memory_update>{"skip": true}</memory_update>'
    assert "repeat" in strip_memory_tags(raw).lower()


def test_extract_memory_updates_jsonl() -> None:
    raw = """<memory_update>
{"entity":"a","relation":"r","value":"1","category":"preference","conviction":1.0}
{"entity":"b","relation":"r","value":"2","category":"preference","conviction":1.0}
</memory_update>
Reply here"""
    facts = extract_memory_updates(raw)
    assert len(facts) == 2
    assert facts[0]["entity"] == "a"
    assert facts[1]["entity"] == "b"


@pytest.mark.asyncio
async def test_extract_facts_from_user_message() -> None:
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "choices": [
                {
                    "message": {
                        "content": (
                            '[{"entity":"editor","relation":"uses","value":"vs code",'
                            '"category":"preference","conviction":0.9},'
                            '{"entity":"editor","relation":"theme","value":"gruvbox",'
                            '"category":"preference","conviction":0.9}]'
                        )
                    }
                }
            ]
        }
    )
    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("llm.qwen_client.aiohttp.ClientSession", return_value=mock_session):
        facts = await extract_facts_from_user_message(
            "I use VS Code with Vim keybindings and the Gruvbox theme.",
            "user-1",
        )
    assert len(facts) == 2
    assert facts[0]["value"] == "vs code"
    assert facts[1]["value"] == "gruvbox"


@pytest.mark.asyncio
async def test_extract_facts_from_conversation() -> None:
    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(
        return_value={
            "choices": [
                {
                    "message": {
                        "content": '[{"entity":"theme","relation":"prefers","value":"moonlight-amber","category":"preference","conviction":1.0}]'
                    }
                }
            ]
        }
    )
    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("llm.qwen_client.aiohttp.ClientSession", return_value=mock_session):
        facts = await extract_facts_from_conversation(
            "My theme is moonlight-amber",
            "Got it!",
        )
    assert len(facts) == 1
    assert facts[0]["value"] == "moonlight-amber"


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
async def test_call_qwen_api_openai_compatible_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(qwen_client.settings, "LLM_PROVIDER", "openai_compatible")
    monkeypatch.setattr(qwen_client.settings, "LLM_API_KEY", "sk-test")
    monkeypatch.setattr(qwen_client.settings, "LLM_BASE_URL", "https://openrouter.ai/api/v1/")
    monkeypatch.setattr(qwen_client.settings, "LLM_MODEL", "deepseek/deepseek-chat-v3.1:free")

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"choices": [{"message": {"content": "openai ok"}}]})
    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    with patch("llm.qwen_client.aiohttp.ClientSession", return_value=mock_session):
        result = await call_qwen_api({"messages": [{"role": "user", "content": "hi"}]})

    assert result == "openai ok"
    _, kwargs = mock_session.post.call_args
    assert kwargs["json"]["model"] == "deepseek/deepseek-chat-v3.1:free"
    assert kwargs["headers"]["Authorization"] == "Bearer sk-test"
    assert str(mock_session.post.call_args.args[0]) == "https://openrouter.ai/api/v1/chat/completions"


@pytest.mark.asyncio
async def test_call_qwen_api_anthropic_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(qwen_client.settings, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(qwen_client.settings, "ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setattr(qwen_client.settings, "ANTHROPIC_BASE_URL", "https://api.anthropic.com")
    monkeypatch.setattr(qwen_client.settings, "ANTHROPIC_VERSION", "2023-06-01")
    monkeypatch.setattr(qwen_client.settings, "LLM_MODEL", "claude-sonnet-4-20250514")
    monkeypatch.setattr(qwen_client.settings, "CHAT_MAX_TOKENS", 1234)

    mock_resp = AsyncMock()
    mock_resp.status = 200
    mock_resp.json = AsyncMock(return_value={"content": [{"type": "text", "text": "anthropic ok"}]})
    mock_session = MagicMock()
    mock_session.post.return_value.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_session.post.return_value.__aexit__ = AsyncMock(return_value=None)
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=None)

    payload = {
        "messages": [
            {"role": "system", "content": "System rules"},
            {"role": "user", "content": "hello"},
        ],
        "temperature": 0.2,
    }
    with patch("llm.qwen_client.aiohttp.ClientSession", return_value=mock_session):
        result = await call_qwen_api(payload)

    assert result == "anthropic ok"
    _, kwargs = mock_session.post.call_args
    assert str(mock_session.post.call_args.args[0]) == "https://api.anthropic.com/v1/messages"
    assert kwargs["headers"]["x-api-key"] == "sk-ant-test"
    assert kwargs["headers"]["anthropic-version"] == "2023-06-01"
    assert kwargs["json"]["model"] == "claude-sonnet-4-20250514"
    assert kwargs["json"]["system"] == "System rules"
    assert kwargs["json"]["messages"] == [{"role": "user", "content": "hello"}]
    assert kwargs["json"]["max_tokens"] == 1234


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
