from __future__ import annotations

import asyncio
import logging
import os
import time
from typing import Annotated, Any

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from agent_fastapi.zep_agent_runner import ZepAgentResult, ZepAgentRunner, zep_agent_runner

_LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=_LOG_FORMAT)
DEFAULT_GRAPH_ID = os.getenv("ZEP_AGENT_DEFAULT_GRAPH_ID", "mirofish_53c089d117c649c7")

app = FastAPI(title="IMP Agent API", version="0.1.0")
logger = logging.getLogger(__name__)
request_logger = logging.getLogger("agent_fastapi.requests")


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    graph_id: str | None = None
    graph_backend: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    task_poll_timeout_sec: float = Field(default=600.0, gt=0)
    task_poll_interval_sec: float = Field(default=5.0, gt=0)


class ChatResponse(BaseModel):
    task_id: str | None
    task_status: str | None
    final_text: str | None


def get_zep_agent_runner() -> ZepAgentRunner:
    return zep_agent_runner


@app.middleware("http")
async def log_request(request: Request, call_next: Any) -> Any:
    client = f"{request.client.host}:{request.client.port}" if request.client else "-"
    path = request.url.path
    if request.url.query:
        path = f"{path}?{request.url.query}"
    request_line = f'"{request.method} {path} HTTP/{request.scope.get("http_version", "1.1")}"'
    started_at = time.perf_counter()
    request_logger.info('%s - request started: %s', client, request_line)

    try:
        response = await call_next(request)
    except Exception:
        request_logger.exception('%s - %s 500 ERROR', client, request_line)
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000
    request_logger.info(
        "%s - %s %s %.1fms",
        client,
        request_line,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    runner: Annotated[ZepAgentRunner, Depends(get_zep_agent_runner)],
) -> ChatResponse:
    metadata = dict(request.metadata)
    metadata["graph_id"] = request.graph_id or metadata.get("graph_id") or DEFAULT_GRAPH_ID
    graph_backend = str(request.graph_backend or metadata.get("graph_backend") or "").strip()
    if graph_backend:
        metadata["graph_backend"] = graph_backend

    try:
        result = await runner.invoke(
            message=request.message,
            metadata=metadata or None,
            task_poll_timeout_sec=request.task_poll_timeout_sec,
            task_poll_interval_sec=request.task_poll_interval_sec,
        )
    except TimeoutError as exc:
        logger.exception("Zep agent chat request timed out")
        raise HTTPException(status_code=504, detail=str(exc)) from exc
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.exception("Zep agent chat request failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _chat_response(result)


def _chat_response(result: ZepAgentResult) -> ChatResponse:
    return ChatResponse(
        task_id=result.task_id,
        task_status=result.task_status,
        final_text=result.final_text,
    )
