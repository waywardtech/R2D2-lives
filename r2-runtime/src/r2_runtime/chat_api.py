"""Loopback-only FastAPI surface for non-actuating R2 conversation."""

from __future__ import annotations

from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from .conversation import ConversationStore, LocalConversationDispatcher, validate_message
from .chat_migrations import upgrade_chat_database
from .model_conversation import SafeModelConversationDispatcher


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=280)
    session_id: str | None = Field(default=None, pattern=r"^[a-f0-9]{32}$")


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    session_id: str
    turn: int
    binary: str
    translation: str
    mode: str = "local"
    physical_action: bool = False


def _status(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"overall": "unavailable"}
    return value if isinstance(value, dict) else {"overall": "unavailable"}


def create_app() -> FastAPI:
    database = Path(
        os.environ.get("R2_CHAT_DATABASE", "/var/lib/r2-runtime/chat/continuity.sqlite3")
    )
    status_path = Path(
        os.environ.get("R2_STATUS_PATH", "/var/lib/r2-runtime/dashboard/status.json")
    )
    upgrade_chat_database(database)
    store = ConversationStore(database)
    dispatcher: LocalConversationDispatcher | SafeModelConversationDispatcher
    endpoint = os.environ.get("R2_CHAT_MODEL_ENDPOINT")
    model = os.environ.get("R2_CHAT_MODEL")
    credential_path = os.environ.get("R2_CHAT_API_KEY_FILE")
    if any((endpoint, model, credential_path)) and not all((endpoint, model, credential_path)):
        raise RuntimeError("model endpoint, model, and credential file must be configured together")
    if endpoint and model and credential_path:
        dispatcher = SafeModelConversationDispatcher(
            endpoint=endpoint,
            model=model,
            api_key=Path(credential_path).read_text(encoding="utf-8").strip(),
        )
    else:
        dispatcher = LocalConversationDispatcher()

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
        yield
        store.close()

    app = FastAPI(
        title="R2 Conversation",
        version="0.1.0",
        docs_url=None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.conversation_store = store

    @app.get("/health")
    def health() -> dict[str, object]:
        mode = "model-ready" if isinstance(dispatcher, SafeModelConversationDispatcher) else "local"
        return {"status": "ready", "mode": mode, "physical_control": False}

    @app.post("/chat", response_model=ChatResponse)
    def chat(request: ChatRequest) -> ChatResponse:
        try:
            message = validate_message(request.message)
        except ValueError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        session_id = store.ensure_session(request.session_id)
        status = _status(status_path)
        if isinstance(dispatcher, SafeModelConversationDispatcher):
            binary, translation, mode = dispatcher.reply_result(message, session_id, store, status)
        else:
            binary, translation = dispatcher.reply(message, session_id, store, status)
            mode = "local"
        turn = store.record(session_id, message, translation)
        return ChatResponse(
            session_id=session_id,
            turn=turn,
            binary=binary,
            translation=translation,
            mode=mode,
        )

    return app
