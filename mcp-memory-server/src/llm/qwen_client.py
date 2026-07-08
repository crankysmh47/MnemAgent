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
QWEN_FALLBACK_RESPONSE = "I'm having trouble connecting right now. Please try again."
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
_CODE_BLOCK_FALLBACK = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```",
    re.DOTALL | re.IGNORECASE,
)
_EMPTY_REPLY_FALLBACK = "I need a moment — could you repeat that?"


class QwenAPIError(Exception):
    """Raised when the Qwen API returns a non-recoverable error."""


def _join_url(base_url: str, path: str) -> str:
    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def _chat_model(payload: dict) -> str:
    return str(payload.get("model") or settings.LLM_MODEL or settings.QWEN_MODEL)


def _openai_base_url() -> str:
    return settings.LLM_BASE_URL or settings.QWEN_BASE_URL


def _openai_api_key() -> str:
    return settings.LLM_API_KEY or settings.QWEN_API_KEY


def _anthropic_api_key() -> str:
    return settings.ANTHROPIC_API_KEY or settings.LLM_API_KEY


def _anthropic_payload(payload: dict) -> dict:
    messages = payload.get("messages") or []
    system_parts: list[str] = []
    anthropic_messages: list[dict[str, str]] = []

    for msg in messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            system_parts.append(str(content))
        elif role in ("user", "assistant"):
            anthropic_messages.append({"role": role, "content": str(content)})

    body: dict = {
        "model": _chat_model(payload),
        "messages": anthropic_messages,
        "max_tokens": int(payload.get("max_tokens") or settings.CHAT_MAX_TOKENS),
    }
    if system_parts:
        body["system"] = "\n\n".join(system_parts)
    if "temperature" in payload:
        body["temperature"] = payload["temperature"]
    return body


def _parse_openai_response(data: dict) -> str:
    return data["choices"][0]["message"]["content"]


def _parse_anthropic_response(data: dict) -> str:
    content = data.get("content", [])
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text_parts.append(str(block.get("text", "")))
        return "\n".join(part for part in text_parts if part)
    raise KeyError("content")


async def call_qwen_api(payload: dict) -> str:
    """
    Call the configured LLM chat API with retry on rate limits.

    Supported providers:
    - ``openai_compatible`` / ``qwen``: POST ``/chat/completions``.
    - ``anthropic``: POST ``/v1/messages``.

    Args:
        payload: Request body including model and messages.

    Returns:
        Raw assistant message content, or a safe fallback string on failure.
    """
    provider = settings.LLM_PROVIDER.strip().lower()
    if provider in ("anthropic", "claude"):
        url = _join_url(settings.ANTHROPIC_BASE_URL, "/v1/messages")
        request_payload = _anthropic_payload(payload)
        headers = {
            "x-api-key": _anthropic_api_key(),
            "anthropic-version": settings.ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }
        parse_response = _parse_anthropic_response
    else:
        url = _join_url(_openai_base_url(), "/chat/completions")
        request_payload = {**payload, "model": _chat_model(payload)}
        headers = {
            "Authorization": f"Bearer {_openai_api_key()}",
            "Content-Type": "application/json",
        }
        parse_response = _parse_openai_response

    for attempt in range(_MAX_RETRIES):
        try:
            async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
                async with session.post(url, json=request_payload, headers=headers) as resp:
                    if resp.status == 429:
                        logger.warning("LLM rate limit (429), attempt %s", attempt + 1)
                        await asyncio.sleep(2**attempt)
                        continue
                    if resp.status != 200:
                        body = await resp.text()
                        logger.error("LLM API error %s: %s", resp.status, body[:500])
                        raise QwenAPIError(f"HTTP {resp.status}")
                    data = await resp.json()
                    return parse_response(data)
        except asyncio.TimeoutError:
            logger.error("LLM API timeout")
            return QWEN_FALLBACK_RESPONSE
        except aiohttp.ClientError as exc:
            logger.error("LLM API client error: %s", exc)
            return QWEN_FALLBACK_RESPONSE
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            logger.error("Unexpected LLM response shape: %s", exc)
            return QWEN_FALLBACK_RESPONSE
        except QwenAPIError:
            return QWEN_FALLBACK_RESPONSE

    logger.error("LLM API rate limit retries exhausted")
    return QWEN_FALLBACK_RESPONSE


def is_qwen_fallback_response(response: str) -> bool:
    """Return True when chat generation fell back because the model was unavailable."""
    return response.strip() == QWEN_FALLBACK_RESPONSE


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


def _strip_json_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _parse_fact_array(raw: str) -> list[dict]:
    """Parse a JSON array of memory fact dicts from model output."""
    try:
        data = json.loads(_strip_json_fence(raw))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    facts: list[dict] = []
    for item in data:
        if not isinstance(item, dict) or item.get("skip"):
            continue
        entity = item.get("entity")
        relation = item.get("relation")
        value = item.get("value")
        if entity and relation and value is not None:
            facts.append(item)
    return facts


def extract_facts_deterministically(user_message: str) -> list[dict]:
    """
    Lightweight local extractor for explicit teach statements.

    This is only a resilience path for model/API outages. It intentionally
    handles clear patterns rather than trying to infer fuzzy memories.
    """
    facts: list[dict] = []
    seen: set[tuple[str, str, str]] = set()

    def add(entity: str, relation: str, value: str, category: str, conviction: float = 0.9) -> None:
        entity = re.sub(r"\s+", "_", entity.strip().lower())
        entity = re.sub(r"^(?:my|our|the)_", "", entity)
        entity = re.sub(r"^preferred_", "", entity)
        value = value.strip().strip("'\"` ")
        value = re.sub(r"\s+$", "", value)
        if not entity or not value or len(entity) > 64 or len(value) > 80:
            return
        key = (entity, relation, value.lower())
        if key in seen:
            return
        seen.add(key)
        facts.append(
            {
                "entity": entity,
                "relation": relation,
                "value": value,
                "category": category,
                "conviction": conviction,
            }
        )

    clause_text = re.sub(r"\bremember this for future chats?:?", "", user_message, flags=re.I)
    clause_text = re.sub(r"\band\s+(my|our)\b", r"\1", clause_text, flags=re.I)
    clauses = re.split(r"[,.;]\s*", clause_text)
    for clause in clauses:
        clause = clause.strip()
        if not clause:
            continue

        mine = re.search(
            r"\b(?:my|our)\s+(preferred\s+)?([a-zA-Z0-9 _-]{2,48}?)\s+(?:is|are|=)\s+(.+)$",
            clause,
            flags=re.I,
        )
        if mine:
            preferred, entity, value = mine.groups()
            category = "preference" if preferred else "system_state"
            add(entity, "prefers" if preferred else "is", value, category, 1.0)
            continue

        prefer = re.search(r"\bI\s+prefer\s+(.+?)\s+for\s+([a-zA-Z0-9 _-]{2,48})$", clause, flags=re.I)
        if prefer:
            value, entity = prefer.groups()
            add(entity, "prefers", value, "preference", 1.0)
            continue

        uses = re.search(
            r"\b(?:I|we)\s+(?:use|am using|are using)\s+(.+?)\s+for\s+([a-zA-Z0-9 _-]{2,48})$",
            clause,
            flags=re.I,
        )
        if uses:
            value, entity = uses.groups()
            add(entity, "uses", value, "system_state", 0.9)

    return facts


async def extract_facts_from_user_message(user_message: str, user_id: str) -> list[dict]:
    """
    Server-side fact extractor — reads the user message directly.

    Does not depend on the primary model's <memory_update> compliance.
    Uses EXTRACTION_MODEL (typically qwen-turbo) at temperature 0.
    """
    _ = user_id  # reserved for per-user extraction tuning
    prompt = f"""Extract persistent facts from this user message.
Return a JSON array only. No other text.

User message: "{user_message}"

Rules:
- Only extract facts the user is explicitly stating about themselves,
  their preferences, or their project
- conviction: 1.0 = definitive, 0.7 = clear, 0.4 = probable, 0.2 = hedged
- category: preference | persona | system_state
- Return [] if nothing extractable
- Return ONLY the JSON array

Example output:
[{{"entity":"editor","relation":"uses","value":"vs code",
  "category":"preference","conviction":0.9}}]"""
    payload = {
        "model": settings.EXTRACTION_MODEL or settings.LLM_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 300,
    }
    raw = await call_qwen_api(payload)
    facts = _parse_fact_array(raw)
    if facts:
        logger.info("Server-side user extraction recovered %s fact(s)", len(facts))
        return facts
    local_facts = extract_facts_deterministically(user_message)
    if local_facts:
        logger.info("Local deterministic extraction recovered %s fact(s)", len(local_facts))
    return local_facts


async def extract_facts_from_conversation(
    user_message: str,
    agent_response: str,
) -> list[dict]:
    """
    Background extraction pass when dual-output CoT failed to emit memory tags.

    Uses a focused extraction prompt (typically qwen-turbo or EXTRACTION_MODEL).
    """
    model = settings.EXTRACTION_MODEL or settings.LLM_MODEL
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
    facts = _parse_fact_array(raw)
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

    # 2. Markdown code block (strict entity/relation/value shape)
    code_match = _CODE_BLOCK_PATTERN.search(response)
    if code_match:
        parsed = _parse_memory_dict(code_match.group(1))
        if parsed is not None:
            logger.info("Memory JSON extracted from markdown code block")
            return parsed

    # 2b. Looser markdown JSON fallback
    for loose_match in _CODE_BLOCK_FALLBACK.finditer(response):
        parsed = _parse_memory_dict(loose_match.group(1))
        if parsed is not None:
            logger.info("Memory JSON extracted from loose markdown code block")
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


def response_has_memory_block(response: str) -> bool:
    """True when the model emitted a memory_update block (including explicit skip)."""
    if _MEMORY_EXTRACT_PATTERN.search(response):
        return True
    if _CODE_BLOCK_PATTERN.search(response) or _CODE_BLOCK_FALLBACK.search(response):
        return True
    if _BARE_MEMORY_JSON_PATTERN.search(response):
        return True
    return False


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
    cleaned = _CODE_BLOCK_FALLBACK.sub("", cleaned)
    cleaned = _BARE_MEMORY_JSON_PATTERN.sub("", cleaned)
    cleaned = cleaned.strip()
    if cleaned:
        return cleaned
    logger.warning("strip_memory_tags yielded empty string; response may be truncated")
    return _EMPTY_REPLY_FALLBACK
