import json
from unittest.mock import MagicMock, patch

from models import AIResponse


def test_chat_test_endpoint(client, auth_header):
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "4"

    with patch("ai.get_ai_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        resp = client.post("/api/chat/test", headers=auth_header)

    assert resp.status_code == 200
    assert resp.json()["response"] == "4"


def test_chat_test_requires_auth(client):
    resp = client.post("/api/chat/test")
    assert resp.status_code == 401


def _mock_ai_response(ai_response: AIResponse):
    """Create a mock that makes chat_with_board return the given AIResponse."""
    return patch("routers.chat.chat_with_board", return_value=ai_response)


def test_chat_simple_message(client, auth_header):
    ai_resp = AIResponse(message="Hello! Your board looks great.", board_updates=[])

    with _mock_ai_response(ai_resp):
        resp = client.post(
            "/api/chat",
            json={"message": "Hi there", "history": []},
            headers=auth_header,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Hello! Your board looks great."
    assert data["board_updates"] == []
    assert len(data["board"]["columns"]) == 5


def test_chat_creates_card(client, auth_header):
    # Get column ID first
    board = client.get("/api/board", headers=auth_header).json()
    col_id = board["columns"][0]["id"]
    original_count = len(board["columns"][0]["cards"])

    ai_resp = AIResponse(
        message="Done! I added the card.",
        board_updates=[
            {"action": "create_card", "column_id": col_id, "title": "AI card", "details": "Created by AI"},
        ],
    )

    with _mock_ai_response(ai_resp):
        resp = client.post(
            "/api/chat",
            json={"message": "Create a card called AI card in Backlog"},
            headers=auth_header,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "Done! I added the card."
    backlog = data["board"]["columns"][0]
    assert len(backlog["cards"]) == original_count + 1
    assert backlog["cards"][-1]["title"] == "AI card"


def test_chat_updates_card(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    card_id = board["columns"][0]["cards"][0]["id"]

    ai_resp = AIResponse(
        message="Updated the card title.",
        board_updates=[
            {"action": "update_card", "card_id": card_id, "title": "Renamed by AI"},
        ],
    )

    with _mock_ai_response(ai_resp):
        resp = client.post(
            "/api/chat",
            json={"message": "Rename the first card"},
            headers=auth_header,
        )

    assert resp.status_code == 200
    assert resp.json()["board"]["columns"][0]["cards"][0]["title"] == "Renamed by AI"


def test_chat_moves_card(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    card_id = board["columns"][0]["cards"][0]["id"]
    done_col_id = board["columns"][4]["id"]
    backlog_count = len(board["columns"][0]["cards"])
    done_count = len(board["columns"][4]["cards"])

    ai_resp = AIResponse(
        message="Moved it to Done.",
        board_updates=[
            {"action": "move_card", "card_id": card_id, "target_column_id": done_col_id, "position": 0},
        ],
    )

    with _mock_ai_response(ai_resp):
        resp = client.post(
            "/api/chat",
            json={"message": "Move the first Backlog card to Done"},
            headers=auth_header,
        )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["board"]["columns"][0]["cards"]) == backlog_count - 1
    assert len(data["board"]["columns"][4]["cards"]) == done_count + 1


def test_chat_deletes_card(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    card_id = board["columns"][0]["cards"][0]["id"]
    original_count = len(board["columns"][0]["cards"])

    ai_resp = AIResponse(
        message="Card deleted.",
        board_updates=[
            {"action": "delete_card", "card_id": card_id},
        ],
    )

    with _mock_ai_response(ai_resp):
        resp = client.post(
            "/api/chat",
            json={"message": "Delete the first card"},
            headers=auth_header,
        )

    assert resp.status_code == 200
    assert len(resp.json()["board"]["columns"][0]["cards"]) == original_count - 1


def test_chat_multiple_operations(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    col_id = board["columns"][0]["id"]
    card_to_delete = board["columns"][0]["cards"][0]["id"]

    ai_resp = AIResponse(
        message="Created one and deleted one.",
        board_updates=[
            {"action": "delete_card", "card_id": card_to_delete},
            {"action": "create_card", "column_id": col_id, "title": "Replacement", "details": ""},
        ],
    )

    with _mock_ai_response(ai_resp):
        resp = client.post(
            "/api/chat",
            json={"message": "Replace the first card with a new one"},
            headers=auth_header,
        )

    assert resp.status_code == 200
    cards = resp.json()["board"]["columns"][0]["cards"]
    titles = [c["title"] for c in cards]
    assert "Replacement" in titles


def test_chat_invalid_card_id_is_skipped(client, auth_header):
    ai_resp = AIResponse(
        message="Tried to update a nonexistent card.",
        board_updates=[
            {"action": "delete_card", "card_id": 99999},
        ],
    )

    with _mock_ai_response(ai_resp):
        resp = client.post(
            "/api/chat",
            json={"message": "Delete card 99999"},
            headers=auth_header,
        )

    # Should still succeed, just skips the invalid operation
    assert resp.status_code == 200
    assert resp.json()["message"] == "Tried to update a nonexistent card."


def test_chat_with_history(client, auth_header):
    ai_resp = AIResponse(message="Sure, based on our conversation...", board_updates=[])

    with _mock_ai_response(ai_resp) as mock_fn:
        resp = client.post(
            "/api/chat",
            json={
                "message": "What did I just ask?",
                "history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"},
                ],
            },
            headers=auth_header,
        )

    assert resp.status_code == 200
    # Verify history was passed through
    call_args = mock_fn.call_args
    history = call_args[0][2]
    assert len(history) == 2
    assert history[0]["content"] == "Hello"


def test_chat_requires_auth(client):
    resp = client.post("/api/chat", json={"message": "hi"})
    assert resp.status_code == 401
