from typing import Literal

from pydantic import BaseModel


class CardOut(BaseModel):
    id: int
    title: str
    details: str
    position: int


class ColumnOut(BaseModel):
    id: int
    title: str
    position: int
    cards: list[CardOut]


class BoardOut(BaseModel):
    id: int
    name: str
    columns: list[ColumnOut]


class RenameColumnRequest(BaseModel):
    title: str


class CreateCardRequest(BaseModel):
    column_id: int
    title: str
    details: str = ""


class UpdateCardRequest(BaseModel):
    title: str | None = None
    details: str | None = None


class MoveCardRequest(BaseModel):
    column_id: int
    position: int


# --- AI structured output models ---


class CreateCardOp(BaseModel):
    action: Literal["create_card"]
    column_id: int
    title: str
    details: str = ""


class UpdateCardOp(BaseModel):
    action: Literal["update_card"]
    card_id: int
    title: str | None = None
    details: str | None = None


class MoveCardOp(BaseModel):
    action: Literal["move_card"]
    card_id: int
    target_column_id: int
    position: int = 0


class DeleteCardOp(BaseModel):
    action: Literal["delete_card"]
    card_id: int


class AIResponse(BaseModel):
    message: str
    board_updates: list[CreateCardOp | UpdateCardOp | MoveCardOp | DeleteCardOp] = []


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    message: str
    board_updates: list[CreateCardOp | UpdateCardOp | MoveCardOp | DeleteCardOp] = []
    board: BoardOut
