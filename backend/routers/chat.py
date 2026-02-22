import sqlite3
import time
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth import get_current_user
from ai import chat_with_board, simple_chat
from database import get_conn
from models import ChatRequest, ChatResponse
from routers.board import _load_board, apply_board_updates

router = APIRouter(prefix="/api/chat", tags=["chat"])

RATE_LIMIT_MAX = 10
RATE_LIMIT_WINDOW = 60

_request_log: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(username: str) -> None:
    now = time.monotonic()
    timestamps = _request_log[username]
    _request_log[username] = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(_request_log[username]) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Try again shortly.",
        )
    _request_log[username].append(now)


class ChatTestResponse(BaseModel):
    response: str


@router.post("/test", response_model=ChatTestResponse)
def chat_test(username: str = Depends(get_current_user)):
    _check_rate_limit(username)
    result = simple_chat("What is 2+2? Reply with just the number.")
    return ChatTestResponse(response=result)


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, conn: sqlite3.Connection = Depends(get_conn), username: str = Depends(get_current_user)):
    _check_rate_limit(username)
    board = _load_board(conn, username)
    history = [{"role": m.role, "content": m.content} for m in body.history]
    ai_response = chat_with_board(board, body.message, history)

    if ai_response.board_updates:
        apply_board_updates(conn, ai_response, username)

    updated_board = _load_board(conn, username)
    return ChatResponse(
        message=ai_response.message,
        board_updates=ai_response.board_updates,
        board=updated_board,
    )
