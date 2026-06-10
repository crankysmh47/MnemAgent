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
    required = ("entity", "relation", "value")
    if not all(key in parsed for key in required):
        return None
    return parsed


def extract_memory_update(response: str) -> dict | None:
    """
    Parse a <memory_update> JSON block from the model response.

    Falls back to bare JSON objects when the model omits XML tags.

    Args:
        response: Raw model output.

    Returns:
        Parsed memory dict or None if missing/invalid.
    """
    match = _MEMORY_EXTRACT_PATTERN.search(response)
    if match:
        parsed = _parse_memory_dict(match.group(1))
        if parsed is None:
            logger.warning("Malformed memory_update JSON: %s", match.group(1)[:200])
        return parsed

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


def strip_memory_tags(response: str) -> str:
    """
    Remove <memory_update> blocks and bare memory JSON from the model response.

    Args:
        response: Raw model output.

    Returns:
        Clean user-facing text.
    """
    cleaned = _MEMORY_TAG_PATTERN.sub("", response)
    cleaned = _BARE_MEMORY_JSON_PATTERN.sub("", cleaned)
    return cleaned.strip()
