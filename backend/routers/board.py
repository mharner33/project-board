import logging

from fastapi import APIRouter, Depends, HTTPException, status

from auth import get_current_user
from database import get_db, ensure_board_for_user
from models import (
    AIResponse,
    BoardOut,
    CardOut,
    ColumnOut,
    CreateCardRequest,
    MoveCardRequest,
    RenameColumnRequest,
    UpdateCardRequest,
)

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/board", tags=["board"])


def _load_board(username: str) -> BoardOut:
    conn = get_db()
    try:
        board_id = ensure_board_for_user(conn, username)
        board = conn.execute("SELECT id, name FROM boards WHERE id = ?", (board_id,)).fetchone()
        cols = conn.execute(
            "SELECT id, title, position FROM columns WHERE board_id = ? ORDER BY position",
            (board_id,),
        ).fetchall()
        columns = []
        for col in cols:
            cards = conn.execute(
                "SELECT id, title, details, position FROM cards WHERE column_id = ? ORDER BY position",
                (col["id"],),
            ).fetchall()
            columns.append(
                ColumnOut(
                    id=col["id"],
                    title=col["title"],
                    position=col["position"],
                    cards=[CardOut(**dict(c)) for c in cards],
                )
            )
        return BoardOut(id=board["id"], name=board["name"], columns=columns)
    finally:
        conn.close()


def _verify_column_ownership(conn, column_id: int, username: str) -> int:
    """Returns board_id if column belongs to user, else raises 404."""
    row = conn.execute(
        """SELECT b.id AS board_id FROM columns c
           JOIN boards b ON c.board_id = b.id
           JOIN users u ON b.user_id = u.id
           WHERE c.id = ? AND u.username = ?""",
        (column_id, username),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Column not found")
    return row["board_id"]


def _verify_card_ownership(conn, card_id: int, username: str) -> dict:
    """Returns card row if it belongs to user, else raises 404."""
    row = conn.execute(
        """SELECT ca.id, ca.column_id, ca.title, ca.details, ca.position
           FROM cards ca
           JOIN columns c ON ca.column_id = c.id
           JOIN boards b ON c.board_id = b.id
           JOIN users u ON b.user_id = u.id
           WHERE ca.id = ? AND u.username = ?""",
        (card_id, username),
    ).fetchone()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Card not found")
    return dict(row)


def _reindex_column(conn, column_id: int) -> None:
    cards = conn.execute(
        "SELECT id FROM cards WHERE column_id = ? ORDER BY position", (column_id,)
    ).fetchall()
    for i, card in enumerate(cards):
        conn.execute("UPDATE cards SET position = ? WHERE id = ?", (i, card["id"]))


@router.get("", response_model=BoardOut)
def get_board(username: str = Depends(get_current_user)):
    return _load_board(username)


@router.put("/columns/{column_id}", response_model=BoardOut)
def rename_column(
    column_id: int,
    body: RenameColumnRequest,
    username: str = Depends(get_current_user),
):
    conn = get_db()
    try:
        _verify_column_ownership(conn, column_id, username)
        conn.execute("UPDATE columns SET title = ? WHERE id = ?", (body.title, column_id))
        conn.commit()
    finally:
        conn.close()
    return _load_board(username)


@router.post("/cards", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
def create_card(
    body: CreateCardRequest,
    username: str = Depends(get_current_user),
):
    conn = get_db()
    try:
        _verify_column_ownership(conn, body.column_id, username)
        max_pos = conn.execute(
            "SELECT COALESCE(MAX(position), -1) AS mp FROM cards WHERE column_id = ?",
            (body.column_id,),
        ).fetchone()["mp"]
        conn.execute(
            "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
            (body.column_id, body.title, body.details, max_pos + 1),
        )
        conn.commit()
    finally:
        conn.close()
    return _load_board(username)


@router.put("/cards/{card_id}", response_model=BoardOut)
def update_card(
    card_id: int,
    body: UpdateCardRequest,
    username: str = Depends(get_current_user),
):
    conn = get_db()
    try:
        card = _verify_card_ownership(conn, card_id, username)
        title = body.title if body.title is not None else card["title"]
        details = body.details if body.details is not None else card["details"]
        conn.execute(
            "UPDATE cards SET title = ?, details = ? WHERE id = ?",
            (title, details, card_id),
        )
        conn.commit()
    finally:
        conn.close()
    return _load_board(username)


@router.delete("/cards/{card_id}", response_model=BoardOut)
def delete_card(
    card_id: int,
    username: str = Depends(get_current_user),
):
    conn = get_db()
    try:
        card = _verify_card_ownership(conn, card_id, username)
        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        _reindex_column(conn, card["column_id"])
        conn.commit()
    finally:
        conn.close()
    return _load_board(username)


@router.put("/cards/{card_id}/move", response_model=BoardOut)
def move_card(
    card_id: int,
    body: MoveCardRequest,
    username: str = Depends(get_current_user),
):
    conn = get_db()
    try:
        card = _verify_card_ownership(conn, card_id, username)
        _verify_column_ownership(conn, body.column_id, username)
        old_column_id = card["column_id"]

        # Remove from old position
        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        _reindex_column(conn, old_column_id)

        # Shift cards at target to make room
        conn.execute(
            "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
            (body.column_id, body.position),
        )
        conn.execute(
            "INSERT INTO cards (id, column_id, title, details, position) VALUES (?, ?, ?, ?, ?)",
            (card_id, body.column_id, card["title"], card["details"], body.position),
        )
        _reindex_column(conn, body.column_id)
        conn.commit()
    finally:
        conn.close()
    return _load_board(username)


def apply_board_updates(ai_response: AIResponse, username: str) -> None:
    conn = get_db()
    try:
        board_id = ensure_board_for_user(conn, username)
        for op in ai_response.board_updates:
            try:
                if op.action == "create_card":
                    col = conn.execute(
                        "SELECT c.id FROM columns c JOIN boards b ON c.board_id = b.id "
                        "JOIN users u ON b.user_id = u.id WHERE c.id = ? AND u.username = ?",
                        (op.column_id, username),
                    ).fetchone()
                    if not col:
                        log.warning("AI create_card: column %d not found", op.column_id)
                        continue
                    max_pos = conn.execute(
                        "SELECT COALESCE(MAX(position), -1) AS mp FROM cards WHERE column_id = ?",
                        (op.column_id,),
                    ).fetchone()["mp"]
                    conn.execute(
                        "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
                        (op.column_id, op.title, op.details, max_pos + 1),
                    )

                elif op.action == "update_card":
                    card = conn.execute(
                        "SELECT ca.id, ca.title, ca.details FROM cards ca "
                        "JOIN columns c ON ca.column_id = c.id "
                        "JOIN boards b ON c.board_id = b.id "
                        "JOIN users u ON b.user_id = u.id "
                        "WHERE ca.id = ? AND u.username = ?",
                        (op.card_id, username),
                    ).fetchone()
                    if not card:
                        log.warning("AI update_card: card %d not found", op.card_id)
                        continue
                    title = op.title if op.title is not None else card["title"]
                    details = op.details if op.details is not None else card["details"]
                    conn.execute(
                        "UPDATE cards SET title = ?, details = ? WHERE id = ?",
                        (title, details, op.card_id),
                    )

                elif op.action == "move_card":
                    card = conn.execute(
                        "SELECT ca.id, ca.column_id, ca.title, ca.details FROM cards ca "
                        "JOIN columns c ON ca.column_id = c.id "
                        "JOIN boards b ON c.board_id = b.id "
                        "JOIN users u ON b.user_id = u.id "
                        "WHERE ca.id = ? AND u.username = ?",
                        (op.card_id, username),
                    ).fetchone()
                    if not card:
                        log.warning("AI move_card: card %d not found", op.card_id)
                        continue
                    old_col_id = card["column_id"]
                    conn.execute("DELETE FROM cards WHERE id = ?", (op.card_id,))
                    _reindex_column(conn, old_col_id)
                    conn.execute(
                        "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
                        (op.target_column_id, op.position),
                    )
                    conn.execute(
                        "INSERT INTO cards (id, column_id, title, details, position) VALUES (?, ?, ?, ?, ?)",
                        (op.card_id, op.target_column_id, card["title"], card["details"], op.position),
                    )
                    _reindex_column(conn, op.target_column_id)

                elif op.action == "delete_card":
                    card = conn.execute(
                        "SELECT ca.id, ca.column_id FROM cards ca "
                        "JOIN columns c ON ca.column_id = c.id "
                        "JOIN boards b ON c.board_id = b.id "
                        "JOIN users u ON b.user_id = u.id "
                        "WHERE ca.id = ? AND u.username = ?",
                        (op.card_id, username),
                    ).fetchone()
                    if not card:
                        log.warning("AI delete_card: card %d not found", op.card_id)
                        continue
                    conn.execute("DELETE FROM cards WHERE id = ?", (op.card_id,))
                    _reindex_column(conn, card["column_id"])

            except Exception:
                log.exception("Failed to apply AI board update: %s", op)
                continue

        conn.commit()
    finally:
        conn.close()
