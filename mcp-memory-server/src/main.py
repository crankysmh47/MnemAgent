"""MnemOS — FastAPI application with memory-augmented chat endpoint."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from config import settings
from llm.qwen_client import call_qwen_api, extract_memory_update, strip_memory_tags
from log_setup import setup_logging
from memory.dreaming import consolidate_and_prune_memory, evaluate_memory_utility_feedback
from memory.mcp_commands import execute_memory_dump_tool, execute_memory_stats_tool
from memory.waking import build_optimized_qwen_payload
from storage import cloud_sync
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


async def _run_dreaming_phase(
    user_id: str,
    session_id: str,
    user_prompt: str,
    clean_response: str,
    injected_ids: list[int],
    memory_dict: dict | None,
) -> None:
    """
    Run feedback, consolidation, episodic logging, and optional cloud sync.

    Blocking DB functions are dispatched to the default thread pool executor.
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
        if memory_dict is not None:
            await loop.run_in_executor(
                None,
                consolidate_and_prune_memory,
                user_id,
                memory_dict,
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
            await loop.run_in_executor(None, cloud_sync.sync_to_cloud)
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


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "mnemos"}


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
    result = await build_optimized_qwen_payload(
        request.user_id,
        request.session_id,
        request.message,
        total_turns,
    )
    raw_response = await call_qwen_api(result["payload"])
    clean_response = strip_memory_tags(raw_response)
    memory_dict = extract_memory_update(raw_response)

    asyncio.create_task(
        _run_dreaming_phase(
            request.user_id,
            request.session_id,
            request.message,
            clean_response,
            result["injected_ids"],
            memory_dict,
        )
    )

    return ChatResponse(
        response=clean_response,
        user_id=request.user_id,
        session_id=request.session_id,
    )
