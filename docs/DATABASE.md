# Database Design

SQLite, stored at `/app/data/kanban.db` inside the container (mapped to a Docker volume for persistence). Auto-created on first run if it doesn't exist.

## Tables

### users

| Column        | Type    | Constraints              |
|---------------|---------|--------------------------|
| id            | INTEGER | PRIMARY KEY AUTOINCREMENT|
| username      | TEXT    | NOT NULL UNIQUE          |
| password_hash | TEXT    | NOT NULL                 |

For the MVP, a single row is seeded: `user` / `password` (stored as plaintext hash -- good enough for local-only MVP). The table supports multiple users for future expansion.

### boards

| Column  | Type    | Constraints              |
|---------|---------|--------------------------|
| id      | INTEGER | PRIMARY KEY AUTOINCREMENT|
| user_id | INTEGER | NOT NULL, FK -> users.id |
| name    | TEXT    | NOT NULL DEFAULT 'My Board' |

One board per user for MVP. The FK relationship supports multiple boards per user in future.

### columns

| Column   | Type    | Constraints              |
|----------|---------|--------------------------|
| id       | INTEGER | PRIMARY KEY AUTOINCREMENT|
| board_id | INTEGER | NOT NULL, FK -> boards.id|
| title    | TEXT    | NOT NULL                 |
| position | INTEGER | NOT NULL                 |

`position` is a zero-based index controlling left-to-right column order. Columns are fixed (5 default columns seeded per board) but can be renamed.

### cards

| Column    | Type    | Constraints               |
|-----------|---------|---------------------------|
| id        | INTEGER | PRIMARY KEY AUTOINCREMENT |
| column_id | INTEGER | NOT NULL, FK -> columns.id|
| title     | TEXT    | NOT NULL                  |
| details   | TEXT    | NOT NULL DEFAULT ''       |
| position  | INTEGER | NOT NULL                  |

`position` is a zero-based index controlling top-to-bottom card order within a column. When a card moves between columns, positions are recalculated for both source and target columns.

## Default seed data

On first login, if the user has no board, the system creates:
- 1 board ("My Board")
- 5 columns: Backlog (0), Discovery (1), In Progress (2), Review (3), Done (4)
- 8 sample cards distributed across the columns (matching the current frontend demo data)

## Key design decisions

- **Integer IDs everywhere**: Simple, fast, SQLite-native. The frontend currently uses string IDs like `card-1` -- the API will map between integer DB IDs and the frontend's expectations.
- **Position integers for ordering**: Simple to reason about. On move/reorder, affected positions are rewritten. No fractional indexing needed at MVP scale.
- **No soft deletes**: Cards and columns are hard-deleted. MVP doesn't need undo/history.
- **No timestamps**: No created_at/updated_at. Can be added later if needed.
- **password_hash column**: Named for future bcrypt usage, but MVP stores plaintext.
