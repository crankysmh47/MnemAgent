"""MnemOS — FastAPI application with memory-augmented chat endpoint."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from config import settings
from llm.qwen_client import (
    call_qwen_api,
    extract_facts_from_conversation,
    extract_memory_updates,
    strip_memory_tags,
)
from memory.waking import PROMPT_VERSION
from log_setup import setup_logging
from memory.api_data import (
    get_events_since,
    get_graph_data,
    get_metrics_data,
    search_memories,
)
from memory.user_bindings import bind_user, list_bindings_for_user
from memory.dreaming import (
    consolidate_and_prune_memory,
    evaluate_memory_utility_feedback,
    refresh_belief_vitality,
)
from memory.mcp_commands import execute_memory_dump_tool, execute_memory_stats_tool
from memory.response_grounding import ground_response_with_injection, record_hedged_teach_rejections
from memory.waking import build_optimized_qwen_payload
from storage.db_manager import get_total_turns, initialize_database, log_episodic_turn

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    """Incoming chat request from OpenClaw gateway."""

    user_id: str
    session_id: str
    message: str


class ChatResponse(BaseModel):
    """Chat response returned to the client."""

    response: str
    user_id: str
    session_id: str


class MemoryStoreRequest(BaseModel):
    """Direct memory store request for MCP adapter."""

    user_id: str
    entity: str
    relation: str
    value: str
    category: str = "preference"
    conviction: float = Field(default=1.0, ge=0.0, le=1.0)


class MemoryBatchStoreRequest(BaseModel):
    """Batch memory store for multiple facts."""

    user_id: str
    facts: list[MemoryStoreRequest]
    skip_maintenance: bool = False
    refresh_vitality: bool = False


class UserBindRequest(BaseModel):
    """Bind channel sender to canonical user_id."""

    channel: str
    sender_id: str
    display_name: str | None = None


async def _run_dreaming_phase(
    user_id: str,
    session_id: str,
    user_prompt: str,
    clean_response: str,
    injected_ids: list[int],
    memory_dicts: list[dict] | dict | None,
) -> None:
    """
    Run feedback, consolidation, episodic logging, and optional cloud sync.

    Blocking DB functions are dispatched to the default thread pool executor.
    Supports multiple memory dicts (multi-fact extraction) or a single dict.
    """
    try:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            evaluate_memory_utility_feedback,
            user_id,
            clean_response,
            injected_ids,
        )
        if memory_dicts is not None:
            # Normalize to list
            items = (
                memory_dicts if isinstance(memory_dicts, list)
                else [memory_dicts]
            )
            for memory_dict in items:
                if memory_dict is not None:
                    await loop.run_in_executor(
                        None,
                        consolidate_and_prune_memory,
                        user_id,
                        memory_dict,
                    )
        elif settings.ENABLE_DREAMING_EXTRACTION:
            fallback_facts = await extract_facts_from_conversation(
                user_prompt,
                clean_response,
            )
            for fact in fallback_facts:
                conviction = float(fact.get("conviction", 0.5))
                if conviction >= settings.EXTRACTION_MIN_CONVICTION:
                    await loop.run_in_executor(
                        None,
                        consolidate_and_prune_memory,
                        user_id,
                        fact,
                    )
        await loop.run_in_executor(
            None,
            log_episodic_turn,
            user_id,
            session_id,
            user_prompt,
            clean_response,
        )
        total_turns = await loop.run_in_executor(None, get_total_turns, user_id)
        if total_turns % 50 == 0:
            try:
                from storage.cloud_sync import sync_to_cloud
                await loop.run_in_executor(None, sync_to_cloud)
            except ImportError:
                logger.debug("Cloud sync skipped — OSS dependencies not installed")
    except Exception as exc:
        logger.error("Dreaming phase failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    setup_logging(settings.LOG_LEVEL)
    initialize_database()
    logger.info("MnemOS booted successfully.")
    yield
    logger.info("MnemOS shutting down.")


app = FastAPI(title="MnemOS Memory Server", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "mnemos",
        "prompt_version": PROMPT_VERSION,
    }


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Handle chat messages and MCP memory commands.

    Args:
        request: Chat request with user_id, session_id, and message.

    Returns:
        ChatResponse with clean assistant text.
    """
    message = request.message.strip()
    if message == "/memory":
        dump = execute_memory_dump_tool(request.user_id)
        return ChatResponse(
            response=dump,
            user_id=request.user_id,
            session_id=request.session_id,
        )
    if message == "/memory --mode stats":
        total_turns = get_total_turns(request.user_id)
        stats = execute_memory_stats_tool(request.user_id, total_turns)
        return ChatResponse(
            response=stats,
            user_id=request.user_id,
            session_id=request.session_id,
        )

    total_turns = get_total_turns(request.user_id)
    record_hedged_teach_rejections(request.user_id, request.message)
    result = await build_optimized_qwen_payload(
        request.user_id,
        request.session_id,
        request.message,
        total_turns,
    )
    raw_response = await call_qwen_api(result["payload"])
    clean_response = strip_memory_tags(raw_response)
    clean_response = ground_response_with_injection(
        clean_response,
        request.message,
        result.get("injected_values", []),
        result.get("suppressed"),
        result.get("rejected"),
    )
    memory_dicts = extract_memory_updates(raw_response)

    asyncio.create_task(
        _run_dreaming_phase(
            request.user_id,
            request.session_id,
            request.message,
            clean_response,
            result["injected_ids"],
            memory_dicts if memory_dicts else None,
        )
    )

    return ChatResponse(
        response=clean_response,
        user_id=request.user_id,
        session_id=request.session_id,
    )


@app.get("/api/graph/{user_id}")
async def api_graph(user_id: str) -> dict:
    """Return belief graph data for the memory visualizer."""
    return get_graph_data(user_id)


@app.get("/api/events/{user_id}")
async def api_events(
    user_id: str,
    since: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
) -> dict:
    """Return memory lifecycle events since an optional timestamp."""
    return {"events": get_events_since(user_id, since=since, limit=limit)}


@app.get("/api/metrics/{user_id}")
async def api_metrics(user_id: str) -> dict:
    """Return aggregate metrics and UCB timeline data."""
    return get_metrics_data(user_id)


@app.get("/api/memory/search/{user_id}")
async def api_memory_search(
    user_id: str,
    query: str = Query(..., min_length=1),
    top_k: int = Query(default=5, ge=1, le=20),
    category: str | None = Query(default=None),
    min_confidence: float | None = Query(default=None, ge=0.0, le=1.0),
) -> dict:
    """Search persistent memory for MCP memory_search."""
    return {
        "results": search_memories(
            user_id,
            query,
            top_k=top_k,
            category=category,
            min_confidence=min_confidence,
        )
    }


@app.get("/api/memory/dump/{user_id}")
async def api_memory_dump(
    user_id: str,
    format: str = Query(default="markdown", pattern="^(text|markdown|json)$"),
) -> dict:
    """Return memory dump in agent-friendly format."""
    dump = execute_memory_dump_tool(user_id)
    if format == "json":
        return {"user_id": user_id, "format": "json", "beliefs": dump}
    if format == "text":
        return {"user_id": user_id, "format": "text", "response": dump.replace("|", " ").replace("---", "")}
    return {"user_id": user_id, "format": "markdown", "response": dump}


@app.get("/api/memory/stats/{user_id}")
async def api_memory_stats(
    user_id: str,
    format: str = Query(default="markdown", pattern="^(text|markdown|json)$"),
) -> dict:
    """Return UCB stats in agent-friendly format."""
    total_turns = get_total_turns(user_id)
    stats = execute_memory_stats_tool(user_id, total_turns)
    if format == "json":
        return {"user_id": user_id, "format": "json", "stats": stats}
    if format == "text":
        return {"user_id": user_id, "format": "text", "response": stats.replace("|", " ")}
    return {"user_id": user_id, "format": "markdown", "response": stats}


@app.post("/api/user/bind")
async def api_user_bind(request: UserBindRequest) -> dict:
    """Bind channel sender to canonical MnemOS user_id."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        None,
        bind_user,
        request.channel,
        request.sender_id,
        request.display_name,
    )


@app.get("/api/user/bindings/{user_id}")
async def api_user_bindings(user_id: str) -> dict:
    """List channel bindings for a canonical user_id."""
    loop = asyncio.get_running_loop()
    bindings = await loop.run_in_executor(None, list_bindings_for_user, user_id)
    return {"user_id": user_id, "bindings": bindings}


@app.post("/api/memory/store")
async def api_memory_store(request: MemoryStoreRequest) -> dict:
    """Store a fact via salience auction (MCP memory_store)."""
    memory_dict = {
        "entity": request.entity,
        "relation": request.relation,
        "value": request.value,
        "category": request.category,
        "conviction": request.conviction,
    }
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None,
        consolidate_and_prune_memory,
        request.user_id,
        memory_dict,
    )
    return {
        "status": "ok",
        "stored": True,
        "entity": request.entity,
        "relation": request.relation,
        "value": request.value,
    }


@app.post("/api/memory/store/batch")
async def api_memory_store_batch(request: MemoryBatchStoreRequest) -> dict:
    """Store multiple facts in one request."""
    loop = asyncio.get_running_loop()
    stored: list[dict] = []
    skip_maintenance = request.skip_maintenance or request.refresh_vitality
    for fact in request.facts:
        memory_dict = {
            "entity": fact.entity,
            "relation": fact.relation,
            "value": fact.value,
            "category": fact.category,
            "conviction": fact.conviction,
        }

        def _store_one(uid: str = request.user_id, payload: dict = memory_dict) -> None:
            consolidate_and_prune_memory(uid, payload, run_maintenance=not skip_maintenance)

        await loop.run_in_executor(None, _store_one)
        stored.append(
            {"entity": fact.entity, "relation": fact.relation, "value": fact.value}
        )

    refreshed = 0
    if request.refresh_vitality:
        refreshed = await loop.run_in_executor(
            None, refresh_belief_vitality, request.user_id
        )

    return {
        "status": "ok",
        "stored_count": len(stored),
        "facts": stored,
        "vitality_refreshed": refreshed,
    }
