from fastapi import APIRouter, Depends
from pydantic import BaseModel

from auth import get_current_user
from ai import chat_with_board, simple_chat
from models import ChatRequest, ChatResponse
from routers.board import _load_board, apply_board_updates

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatTestResponse(BaseModel):
    response: str


@router.post("/test", response_model=ChatTestResponse)
def chat_test(username: str = Depends(get_current_user)):
    result = simple_chat("What is 2+2? Reply with just the number.")
    return ChatTestResponse(response=result)


@router.post("", response_model=ChatResponse)
def chat(body: ChatRequest, username: str = Depends(get_current_user)):
    board = _load_board(username)
    history = [{"role": m.role, "content": m.content} for m in body.history]
    ai_response = chat_with_board(board, body.message, history)

    if ai_response.board_updates:
        apply_board_updates(ai_response, username)

    updated_board = _load_board(username)
    return ChatResponse(
        message=ai_response.message,
        board_updates=ai_response.board_updates,
        board=updated_board,
    )
