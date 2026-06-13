"""Qwen Cloud API client with dual-output response parsing."""

from __future__ import annotations

import asyncio
import json
import logging
import re

import aiohttp

from config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = aiohttp.ClientTimeout(total=30)
_MAX_RETRIES = 3
_FALLBACK_RESPONSE = "I'm having trouble connecting right now. Please try again."
_MEMORY_TAG_PATTERN = re.compile(r"<memory_update>.*?</memory_update>", re.DOTALL)
_MEMORY_EXTRACT_PATTERN = re.compile(r"<memory_update>(.*?)</memory_update>", re.DOTALL)
_BARE_MEMORY_JSON_PATTERN = re.compile(
    r"\{\s*\"entity\"\s*:\s*\"[^\"]*\"\s*,\s*\"relation\"\s*:\s*\"[^\"]*\""
    r"\s*,\s*\"value\"\s*:\s*\"[^\"]*\""
    r"(?:\s*,\s*\"category\"\s*:\s*\"[^\"]*\")?"
    r"(?:\s*,\s*\"conviction\"\s*:\s*[\d.]+)?\s*\}",
    re.DOTALL,
)
# Secondary extraction: markdown code blocks (```json ... ``` or ``` ... ```)
_CODE_BLOCK_PATTERN = re.compile(
    r"```(?:json)?\s*\n?(\{[^`]*\"entity\"[^`]*\"relation\"[^`]*\"value\"[^`]*\})\s*\n?```",
    re.DOTALL | re.IGNORECASE,
)


class QwenAPIError(Exception):
    """Raised when the Qwen API returns a non-recoverable error."""


async def call_qwen_api(payload: dict) -> str:
    """
    Call the Qwen chat completions API with retry on rate limits.

    Args:
        payload: Request body including model and messages.

    Returns:
        Raw assistant message content, or a safe fallback string on failure.
    """
    url = f"{settings.QWEN_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.QWEN_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(_MAX_RETRIES):
        try:
            async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
                async with session.post(url, json=payload, headers=headers) as resp:
                    if resp.status == 429:
                        logger.warning("Qwen rate limit (429), attempt %s", attempt + 1)
                        await asyncio.sleep(2**attempt)
                        continue
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error("Qwen API error %s: %s", resp.status, body[:500])
                        raise QwenAPIError(f"HTTP {resp.status}")
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]
        except asyncio.TimeoutError:
            logger.error("Qwen API timeout")
            return _FALLBACK_RESPONSE
        except aiohttp.ClientError as exc:
            logger.error("Qwen API client error: %s", exc)
            return _FALLBACK_RESPONSE
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            logger.error("Unexpected Qwen response shape: %s", exc)
            return _FALLBACK_RESPONSE
        except QwenAPIError:
            return _FALLBACK_RESPONSE

    logger.error("Qwen API rate limit retries exhausted")
    return _FALLBACK_RESPONSE


def _parse_memory_dict(raw_json: str) -> dict | None:
    """Validate and return a memory dict from JSON text."""
    try:
        parsed = json.loads(raw_json.strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    if parsed.get("skip"):
        return None
    required = ("entity", "relation", "value")
    if not all(key in parsed for key in required):
        return None
    return parsed


async def extract_facts_from_conversation(
    user_message: str,
    agent_response: str,
) -> list[dict]:
    """
    Background extraction pass when dual-output CoT failed to emit memory tags.

    Uses a focused extraction prompt (typically qwen-turbo or EXTRACTION_MODEL).
    """
    model = settings.EXTRACTION_MODEL or settings.QWEN_MODEL
    prompt = f"""User said: "{user_message}"
Agent said: "{agent_response}"

Extract persistent facts the USER stated (not the agent). Return a JSON array only.
Each element: {{"entity":"...","relation":"...","value":"...","category":"preference|persona|system_state","conviction":0.0-1.0}}
Rules:
- Only user-stated facts
- conviction 1.0 = definitive, 0.5 = likely, 0.2 = hedged
- Return [] if nothing extractable
- Return ONLY the JSON array, no markdown"""
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 400,
    }
    raw = await call_qwen_api(payload)
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.info("Dreaming extraction pass returned non-JSON")
        return []
    if not isinstance(data, list):
        return []
    facts: list[dict] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if item.get("skip"):
            continue
        entity = item.get("entity")
        relation = item.get("relation")
        value = item.get("value")
        if entity and relation and value is not None:
            facts.append(item)
    if facts:
        logger.info("Dreaming extraction pass recovered %s fact(s)", len(facts))
    return facts


def extract_memory_update(response: str) -> dict | None:
    """
    Parse a <memory_update> JSON block from the model response.

    Extraction order (first match wins):
    1. ``<memory_update>...</memory_update>`` XML tags.
    2. Markdown code block containing memory JSON (```json ... ```).
    3. Bare JSON object with entity/relation/value keys (no tags).

    Handles multiple JSON objects on separate lines (JSONL) inside the tags —
    only the first valid object is returned for single-fact consolidation.
    Use ``extract_memory_updates`` for multi-fact extraction.

    Args:
        response: Raw model output.

    Returns:
        Parsed memory dict or None if missing/invalid.
    """
    # 1. XML tags
    match = _MEMORY_EXTRACT_PATTERN.search(response)
    if match:
        inner = match.group(1).strip()
        if inner:
            parsed = _parse_memory_dict(inner)
            if parsed is not None:
                return parsed
            logger.warning("Malformed memory_update JSON: %s", inner[:200])

    # 2. Markdown code block
    code_match = _CODE_BLOCK_PATTERN.search(response)
    if code_match:
        parsed = _parse_memory_dict(code_match.group(1))
        if parsed is not None:
            logger.info("Memory JSON extracted from markdown code block")
            return parsed

    # 3. Bare JSON
    bare = _BARE_MEMORY_JSON_PATTERN.search(response)
    if bare:
        parsed = _parse_memory_dict(bare.group(0))
        if parsed is not None:
            logger.warning(
                "Bare memory JSON without <memory_update> tags — parsed for consolidation"
            )
            return parsed
        logger.warning("Malformed bare memory JSON: %s", bare.group(0)[:200])
    return None


def extract_memory_updates(response: str) -> list[dict]:
    """
    Extract ALL memory updates from a response (multi-fact extraction).

    Handles JSONL (one JSON object per line) inside <memory_update> tags.
    Falls back to single-object extraction if JSONL parsing yields nothing.

    Args:
        response: Raw model output.

    Returns:
        List of parsed memory dicts (may be empty).
    """
    facts: list[dict] = []

    # Try XML tags first
    match = _MEMORY_EXTRACT_PATTERN.search(response)
    if match:
        inner = match.group(1).strip()
        if inner:
            # Try each line as a separate JSON object (JSONL format)
            for line in inner.split("\n"):
                line = line.strip()
                if not line or line.startswith("//"):
                    continue
                parsed = _parse_memory_dict(line)
                if parsed is not None:
                    facts.append(parsed)
            if facts:
                return facts
            # Fallback: try entire block as single JSON
            parsed = _parse_memory_dict(inner)
            if parsed is not None:
                facts.append(parsed)
                return facts

    # Fallback to single-object extraction
    single = extract_memory_update(response)
    if single is not None:
        facts.append(single)

    return facts


def strip_memory_tags(response: str) -> str:
    """
    Remove <memory_update> blocks, code blocks, and bare memory JSON from the
    model response so the user sees a clean reply.

    Args:
        response: Raw model output.

    Returns:
        Clean user-facing text.
    """
    cleaned = _MEMORY_TAG_PATTERN.sub("", response)
    cleaned = _CODE_BLOCK_PATTERN.sub("", cleaned)
    cleaned = _BARE_MEMORY_JSON_PATTERN.sub("", cleaned)
    return cleaned.strip()
