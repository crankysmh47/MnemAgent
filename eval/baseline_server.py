"""Baseline FastAPI server — vanilla Qwen without MnemAgent memory layer."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import BaseModel

from config import settings
from llm.qwen_client import call_qwen_api
from log_setup import setup_logging

logger = logging.getLogger(__name__)


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str


class ChatResponse(BaseModel):
    response: str
    user_id: str
    session_id: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging(settings.LOG_LEVEL)
    logger.info("Baseline server (no memory) started.")
    yield


app = FastAPI(title="MnemAgent Baseline", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "baseline"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if request.message.strip() == "/memory":
        return ChatResponse(
            response="Memory not available (baseline mode).",
            user_id=request.user_id,
            session_id=request.session_id,
        )
    if request.message.strip() == "/memory --mode stats":
        return ChatResponse(
            response="Memory stats not available (baseline mode).",
            user_id=request.user_id,
            session_id=request.session_id,
        )

    payload = {
        "model": settings.QWEN_MODEL,
        "messages": [{"role": "user", "content": request.message}],
        "temperature": 0.2,
        "max_tokens": 1000,
    }
    response = await call_qwen_api(payload)
    return ChatResponse(
        response=response,
        user_id=request.user_id,
        session_id=request.session_id,
    )
