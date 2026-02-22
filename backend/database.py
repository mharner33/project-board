import sqlite3
from collections.abc import Generator
from pathlib import Path

import bcrypt

DB_PATH = Path(__file__).parent / "data" / "kanban.db"

SEED_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]
SEED_CARDS = {
    "Backlog": [
        ("Align roadmap themes", "Draft quarterly themes with impact statements and metrics."),
        ("Gather customer signals", "Review support tags, sales notes, and churn feedback."),
    ],
    "Discovery": [
        ("Prototype analytics view", "Sketch initial dashboard layout and key drill-downs."),
    ],
    "In Progress": [
        ("Refine status language", "Standardize column labels and tone across the board."),
        ("Design card layout", "Add hierarchy and spacing for scanning dense lists."),
    ],
    "Review": [
        ("QA micro-interactions", "Verify hover, focus, and loading states."),
    ],
    "Done": [
        ("Ship marketing page", "Final copy approved and asset pack delivered."),
        ("Close onboarding sprint", "Document release notes and share internally."),
    ],
}


def get_db(db_path: Path | None = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS boards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
            name TEXT NOT NULL DEFAULT 'My Board'
        );
        CREATE TABLE IF NOT EXISTS columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            position INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            details TEXT NOT NULL DEFAULT '',
            position INTEGER NOT NULL
        );
    """)
    # Seed the default user if not present
    existing = conn.execute("SELECT id FROM users WHERE username = 'user'").fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("user", bcrypt.hashpw(b"password", bcrypt.gensalt()).decode()),
        )
        conn.commit()


def get_conn() -> Generator[sqlite3.Connection, None, None]:
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()


def ensure_board_for_user(conn: sqlite3.Connection, username: str) -> int:
    user = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        raise ValueError(f"User {username} not found")
    user_id = user["id"]

    conn.execute(
        "INSERT OR IGNORE INTO boards (user_id, name) VALUES (?, 'My Board')", (user_id,)
    )
    board = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
    board_id = board["id"]

    has_columns = conn.execute(
        "SELECT 1 FROM columns WHERE board_id = ? LIMIT 1", (board_id,)
    ).fetchone()
    if not has_columns:
        for pos, col_title in enumerate(SEED_COLUMNS):
            col_cur = conn.execute(
                "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
                (board_id, col_title, pos),
            )
            col_id = col_cur.lastrowid
            for card_pos, (card_title, card_details) in enumerate(SEED_CARDS.get(col_title, [])):
                conn.execute(
                    "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
                    (col_id, card_title, card_details, card_pos),
                )

    conn.commit()
    return board_id
