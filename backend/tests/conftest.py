import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import database
from database import get_db, init_db
from main import app


@pytest.fixture(autouse=True)
def _use_temp_db(tmp_path):
    db_path = tmp_path / "test.db"
    database.DB_PATH = db_path
    conn = get_db(db_path)
    init_db(conn)
    conn.close()
    yield
    database.DB_PATH = Path(__file__).parent.parent / "data" / "kanban.db"


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def auth_token(client):
    resp = client.post("/api/auth/login", json={"username": "user", "password": "password"})
    return resp.json()["token"]


@pytest.fixture
def auth_header(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
