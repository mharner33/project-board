def test_get_board_returns_seeded_data(client, auth_header):
    resp = client.get("/api/board", headers=auth_header)
    assert resp.status_code == 200
    board = resp.json()
    assert board["name"] == "My Board"
    assert len(board["columns"]) == 5
    assert board["columns"][0]["title"] == "Backlog"
    assert board["columns"][4]["title"] == "Done"
    total_cards = sum(len(c["cards"]) for c in board["columns"])
    assert total_cards == 8


def test_get_board_requires_auth(client):
    resp = client.get("/api/board")
    assert resp.status_code == 401


def test_rename_column(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    col_id = board["columns"][0]["id"]
    resp = client.put(f"/api/board/columns/{col_id}", json={"title": "Todo"}, headers=auth_header)
    assert resp.status_code == 200
    assert resp.json()["columns"][0]["title"] == "Todo"


def test_rename_column_not_found(client, auth_header):
    resp = client.put("/api/board/columns/9999", json={"title": "X"}, headers=auth_header)
    assert resp.status_code == 404


def test_create_card(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    col_id = board["columns"][0]["id"]
    original_count = len(board["columns"][0]["cards"])
    resp = client.post(
        "/api/board/cards",
        json={"column_id": col_id, "title": "New card", "details": "Some details"},
        headers=auth_header,
    )
    assert resp.status_code == 201
    new_board = resp.json()
    backlog = new_board["columns"][0]
    assert len(backlog["cards"]) == original_count + 1
    assert backlog["cards"][-1]["title"] == "New card"
    assert backlog["cards"][-1]["details"] == "Some details"


def test_create_card_invalid_column(client, auth_header):
    resp = client.post(
        "/api/board/cards",
        json={"column_id": 9999, "title": "X"},
        headers=auth_header,
    )
    assert resp.status_code == 404


def test_update_card(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    card_id = board["columns"][0]["cards"][0]["id"]
    resp = client.put(
        f"/api/board/cards/{card_id}",
        json={"title": "Updated title"},
        headers=auth_header,
    )
    assert resp.status_code == 200
    updated_card = resp.json()["columns"][0]["cards"][0]
    assert updated_card["title"] == "Updated title"
    # details should be unchanged
    assert updated_card["details"] == "Draft quarterly themes with impact statements and metrics."


def test_update_card_not_found(client, auth_header):
    resp = client.put("/api/board/cards/9999", json={"title": "X"}, headers=auth_header)
    assert resp.status_code == 404


def test_delete_card(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    col = board["columns"][0]
    card_id = col["cards"][0]["id"]
    original_count = len(col["cards"])
    resp = client.delete(f"/api/board/cards/{card_id}", headers=auth_header)
    assert resp.status_code == 200
    new_count = len(resp.json()["columns"][0]["cards"])
    assert new_count == original_count - 1


def test_delete_card_not_found(client, auth_header):
    resp = client.delete("/api/board/cards/9999", headers=auth_header)
    assert resp.status_code == 404


def test_move_card_between_columns(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    # Move first card from Backlog (col 0) to Review (col 3)
    card_id = board["columns"][0]["cards"][0]["id"]
    target_col_id = board["columns"][3]["id"]
    backlog_count = len(board["columns"][0]["cards"])
    review_count = len(board["columns"][3]["cards"])

    resp = client.put(
        f"/api/board/cards/{card_id}/move",
        json={"column_id": target_col_id, "position": 0},
        headers=auth_header,
    )
    assert resp.status_code == 200
    new_board = resp.json()
    assert len(new_board["columns"][0]["cards"]) == backlog_count - 1
    assert len(new_board["columns"][3]["cards"]) == review_count + 1
    assert new_board["columns"][3]["cards"][0]["id"] == card_id


def test_move_card_within_column(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    backlog = board["columns"][0]
    card_id = backlog["cards"][0]["id"]
    second_card_id = backlog["cards"][1]["id"]

    resp = client.put(
        f"/api/board/cards/{card_id}/move",
        json={"column_id": backlog["id"], "position": 1},
        headers=auth_header,
    )
    assert resp.status_code == 200
    new_backlog = resp.json()["columns"][0]
    assert new_backlog["cards"][0]["id"] == second_card_id
    assert new_backlog["cards"][1]["id"] == card_id


def test_positions_are_contiguous_after_operations(client, auth_header):
    board = client.get("/api/board", headers=auth_header).json()
    for col in board["columns"]:
        positions = [c["position"] for c in col["cards"]]
        assert positions == list(range(len(positions)))
