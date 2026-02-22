# Code Review Report

Comprehensive review of the Kanban Studio codebase. Findings organized by severity with actionable remediation for each item.

---

## Critical

### CR-1: Hardcoded JWT Secret Key
**File:** `backend/auth.py:7`

The JWT signing secret is a static string committed to source control:
```python
SECRET_KEY = "kanban-studio-mvp-secret-key-32b!"
```
Anyone who reads the source can forge valid tokens for any user, achieving full authentication bypass.

**Action:** Load from environment variable (`JWT_SECRET_KEY`). Generate a cryptographically random value. Add to `.env` and a new `.env.example`.

### CR-2: Plaintext Password Storage
**Files:** `backend/database.py:69`, `backend/routers/auth.py:34`

The column is named `password_hash` but stores and compares passwords in plaintext. The seed user has password `"password"` stored directly. Login does a raw string comparison.

**Action:** Use `bcrypt` or `argon2` for hashing. Hash on seed insert; verify hash on login.

### CR-3: No `.dockerignore` -- Secrets Leak into Build Context
**Missing file:** `.dockerignore`

Without `.dockerignore`, the entire repo (including `.env` with the API key, `.git`, test files) is sent to the Docker build context. Secrets can leak into intermediate layers.

**Action:** Create `.dockerignore` excluding `.git`, `.env`, `*.sqlite*`, `node_modules`, `__pycache__`, `backend/data/`, `docs/`, etc.

### CR-4: No Rollback on Failed Optimistic Updates
**File:** `frontend/src/components/KanbanBoard.tsx:70-86, 91-111`

`handleDragEnd` performs an optimistic local state update, then fires the API call. On failure, `.catch(console.error)` silently swallows the error. The board stays in the wrong state until page refresh. Same pattern in `handleRenameColumn` -- the debounced API call failure is swallowed.

`handleAddCard` and `handleDeleteCard` also use `.catch(console.error)`, giving the user zero feedback when operations fail.

**Action:** Save previous board state before optimistic updates and restore on error, or re-fetch the board. At minimum, show an error notification to the user.

---

## High

### CR-5: Dockerfile Runs as Root
**File:** `Dockerfile`

No `USER` directive exists. The uvicorn process runs as root. If the app has a vulnerability, an attacker gains root access in the container.

**Action:** Add a non-root user:
```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser -d /app appuser
RUN chown -R appuser:appuser /app
USER appuser
```

### CR-6: Unpinned `uv` Version Breaks Reproducibility
**File:** `Dockerfile:11`

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
```
Every build may pull a different `uv` binary. Combined with the lock file not being used (line 16 does `uv pip install --system -r pyproject.toml` without `--locked`), dependency resolution is non-reproducible.

**Action:** Pin `uv` to a specific version tag. Copy `backend/uv.lock` into the image and use `--locked` or `uv sync --frozen`.

### CR-7: Missing Env Var Crashes with Opaque Error
**File:** `backend/ai.py:25`

```python
api_key=os.environ["OPENROUTER_API_KEY"],
```
If the key is not set, a `KeyError` propagates as an unhandled 500 on first chat request.

**Action:** Validate at startup or use `os.environ.get()` with a clear error message.

### CR-8: `handleDragEnd` Stale Closure Race Condition
**File:** `frontend/src/components/KanbanBoard.tsx:42-89`

`handleDragEnd` closes over `board` via `useCallback([board])`. If the board state changes during a drag (e.g., AI chat updates the board, or a card creation resolves), the handler uses stale data. Target column/position calculations will be wrong.

**Action:** Use a `useRef` to always read the latest board state inside the handler, or use the functional form of `setBoard` for all computations.

### CR-9: E2E Test Selectors Are Wrong
**File:** `frontend/tests/kanban.spec.ts:21-22, 40`

Tests reference `data-testid="card-card-1"` and `data-testid="column-col-review"`, but the actual rendered attributes are `card-1`, `column-1`, etc. (numeric IDs, no double-prefix). The drag-and-drop E2E test will always fail.

**Action:** Fix selectors to match actual `data-testid` values produced by the components.

### CR-10: `move_card` Uses DELETE+INSERT Instead of UPDATE
**File:** `backend/routers/board.py:182-193`

Cards are deleted and re-inserted with the same ID to move them between columns. If the process crashes between DELETE and INSERT, the card is lost. Same pattern in `apply_board_updates` at lines 257-266.

**Action:** Replace with `UPDATE cards SET column_id = ?, position = ? WHERE id = ?`.

### CR-11: Race Condition in Board Seeding
**File:** `backend/database.py:75-103`

`ensure_board_for_user` uses a check-then-insert pattern that is not atomic. Two concurrent requests for a new user can both see no board and both insert, creating duplicates.

**Action:** Add a `UNIQUE` constraint on `boards(user_id)` and use `INSERT ... ON CONFLICT IGNORE`, or wrap in a serializable transaction.

### CR-12: No Input Length Validation on Chat Messages
**File:** `backend/models.py:86`

`ChatRequest.message` and `ChatRequest.history` have no length limits. An attacker can send massive payloads, consuming server memory and causing expensive API calls. The user-controlled `history` can also inject arbitrary "assistant" messages to manipulate the AI.

**Action:** Add `Field(max_length=...)` on `message` and `Field(max_items=...)` on `history`. Consider server-side history management instead of trusting client-supplied history.

### CR-13: Closed ChatSidebar Remains Focusable
**File:** `frontend/src/components/ChatSidebar.tsx:54-58`

When closed, the sidebar is only translated off-screen via `translate-x-full`. It remains in the DOM and focusable. Keyboard users can tab into the invisible panel; screen readers announce it.

**Action:** Add `aria-hidden="true"` and the `inert` attribute when closed, or conditionally unmount.

---

## Medium

### CR-14: `apiFetch` Does Not Handle 401 Responses
**File:** `frontend/src/lib/api.ts:10-20`

Expired or revoked tokens cause every API call to throw a generic error. There is no automatic logout or redirect. The user is stuck on the board with every action silently failing.

**Action:** Detect `res.status === 401` in `apiFetch` and clear the token / trigger logout.

### CR-15: Error Messages Pollute Chat History Sent to Server
**File:** `frontend/src/components/ChatSidebar.tsx:43-48`

When an API error occurs, a fabricated "assistant" message is pushed into the messages array. On the next user message, this error text is included in the `history` sent to the AI, polluting the conversation context.

**Action:** Use a separate display-only field for error messages, or filter them out before building the `history` array.

### CR-16: No CORS Configuration
**File:** `backend/main.py`

No CORS middleware is configured. Frontend dev servers on different ports (e.g., `localhost:3000`) cannot reach the API. In production this works because everything is same-origin, but it blocks local frontend development without Docker.

**Action:** Add `CORSMiddleware` with configurable origins, or document that frontend dev requires the Docker setup.

### CR-17: Missing `ON DELETE CASCADE` on Foreign Keys
**File:** `backend/database.py:46-63`

Foreign keys on `boards`, `columns`, and `cards` lack `ON DELETE CASCADE`. Deleting a user or board will cause a foreign key violation instead of cleaning up children. Latent risk for future features.

**Action:** Add `ON DELETE CASCADE` to all foreign key definitions.

### CR-18: AI Response JSON Extraction Regex Is Greedy
**File:** `backend/ai.py:121-124`

```python
match = re.search(r"\{[\s\S]*\}", raw)
```
This matches from the first `{` to the last `}`, which can capture invalid JSON when multiple JSON objects or surrounding text are present.

**Action:** Use a non-greedy match or a balanced-brace extraction approach.

### CR-19: AI `move_card` Skips Target Column Ownership Check
**File:** `backend/routers/board.py:244-267`

In `apply_board_updates`, the move operation validates that the card belongs to the user but does not validate that `op.target_column_id` belongs to the user. The manual `move_card` endpoint correctly checks this. If the AI hallucinates another user's column ID, the card could be moved cross-user.

**Action:** Add `_verify_column_ownership` call for `op.target_column_id` in `apply_board_updates`.

### CR-20: Docker Compose Missing Health Check and Resource Limits
**File:** `docker-compose.yml`

No health check is configured despite `/api/health` existing. No memory or CPU limits are set. Port binds to `0.0.0.0`, exposing the service to the entire network.

**Action:** Add a `healthcheck` using the existing `/api/health` endpoint. Add resource limits. Bind to `127.0.0.1:8000:8000` for local development.

### CR-21: Rename Timer Not Cleaned Up on Unmount
**File:** `frontend/src/components/KanbanBoard.tsx:27, 102-110`

`renameTimers` ref holds `setTimeout` handles with no cleanup on unmount. If the user renames a column and quickly navigates away, the pending API call fires after unmount.

**Action:** Add a cleanup `useEffect` that clears all pending timers.

### CR-22: No Rate Limiting on AI Chat Endpoints
**File:** `backend/routers/chat.py:22-36`

Every `/api/chat` call triggers an external API call to OpenRouter. No rate limiting exists. An authenticated user can make unlimited requests, running up API costs.

**Action:** Add per-user rate limiting (e.g., `slowapi` or a simple in-memory token bucket).

### CR-23: JWT Lacks `iat` Claim, No Revocation Mechanism
**File:** `backend/auth.py:14-19`

Tokens have no `iat` (issued-at) or `jti` (JWT ID) claim. There is no way to invalidate tokens issued before a password change or security event.

**Action:** Add `iat` to the payload. For MVP, this is acceptable but should be addressed before multi-user support.

### CR-24: Multiple Database Connections Opened Per Request
**File:** `backend/routers/board.py:23-48`

Many endpoints open a connection for the mutation, close it, then `_load_board` opens another. The chat endpoint opens up to three connections per request.

**Action:** Refactor to use a single connection per request (e.g., FastAPI dependency injection), or accept a `conn` parameter in `_load_board`.

### CR-25: Board Grid Hardcoded to 5 Columns
**File:** `frontend/src/components/KanbanBoard.tsx:197`

```tsx
<section className="grid gap-6 lg:grid-cols-5">
```
If the backend ever returns a different number of columns, the layout breaks.

**Action:** Use dynamic grid columns based on the actual column count.

---

## Low

### CR-26: Missing `.env.example`
No `.env.example` or `.env.template` exists. New developers have no guidance on required environment variables.

**Action:** Create `.env.example` with placeholder values.

### CR-27: No Empty String Validation for Card/Column Titles
**File:** `backend/models.py:30-33`

`CreateCardRequest.title` and `RenameColumnRequest.title` accept empty strings.

**Action:** Add `Field(min_length=1)`.

### CR-28: `_parse_ai_response` Silently Swallows Parse Errors
**File:** `backend/ai.py:114-131`

Two bare `except Exception: pass` blocks discard specific Pydantic validation errors, making AI integration debugging difficult.

**Action:** Log exceptions at warning level before falling through to the next strategy.

### CR-29: Health Check Does Not Verify Database
**File:** `backend/main.py:29-31`

`/api/health` always returns `{"status": "ok"}` without checking database connectivity.

**Action:** Add a lightweight DB query (e.g., `SELECT 1`) to the health check.

### CR-30: Windows Scripts Lack Error Handling and Podman Fallback
**Files:** `scripts/start.bat`, `scripts/stop.bat`

The `.bat` scripts always print the success message even if `docker compose` fails. They also do not fall back to Podman like the bash scripts do.

**Action:** Check `%ERRORLEVEL%` after the docker command. Add Podman detection for parity with bash scripts.

### CR-31: Missing `.gitignore` Entries
**File:** `.gitignore`

Missing: `backend/data/`, `*.sqlite-wal`, `*.sqlite-shm`, `.claude/`, `frontend/.env.local`.

**Action:** Add the missing entries.

### CR-32: Dockerfile Missing Python Environment Variables
**File:** `Dockerfile`

Missing `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1`. Without the latter, log output may be delayed in `docker logs`.

**Action:** Add both `ENV` directives to the Python stage.

### CR-33: Unused Import
**File:** `backend/tests/test_chat.py:1`

`import json` is imported but never used.

**Action:** Remove the unused import.

### CR-34: Column Title `aria-label` Not Unique Per Column
**File:** `frontend/src/components/KanbanColumn.tsx:44`

Every column's title input has `aria-label="Column title"`. Screen reader users cannot distinguish which column they are editing.

**Action:** Include the column name: `` aria-label={`Title for column ${column.title}`} ``.

### CR-35: AI Response Parsing Fallbacks Are Untested
**File:** `backend/tests/test_chat.py`

All chat tests mock `chat_with_board` entirely, so the JSON parsing logic in `_parse_ai_response` (markdown fence extraction, regex fallback, plain-text fallback) is never exercised.

**Action:** Add unit tests for `_parse_ai_response` with malformed inputs, markdown-wrapped JSON, and plain text.

### CR-36: `LoginForm` Does Not Trim Whitespace
**File:** `frontend/src/components/LoginForm.tsx:18`

A trailing space in the username field causes a login failure with no helpful feedback.

**Action:** Trim `username` before sending to `login()`.

---

## Summary

| ID | Severity | Category | Location |
|----|----------|----------|----------|
| CR-1 | Critical | Security | `backend/auth.py:7` |
| CR-2 | Critical | Security | `backend/database.py:69`, `backend/routers/auth.py:34` |
| CR-3 | Critical | Security | Missing `.dockerignore` |
| CR-4 | Critical | Data integrity | `frontend/src/components/KanbanBoard.tsx` |
| CR-5 | High | Security | `Dockerfile` |
| CR-6 | High | Reproducibility | `Dockerfile:11,16` |
| CR-7 | High | Reliability | `backend/ai.py:25` |
| CR-8 | High | Race condition | `frontend/src/components/KanbanBoard.tsx:42-89` |
| CR-9 | High | Broken tests | `frontend/tests/kanban.spec.ts` |
| CR-10 | High | Data integrity | `backend/routers/board.py:182-193` |
| CR-11 | High | Concurrency | `backend/database.py:75-103` |
| CR-12 | High | Security/DoS | `backend/models.py:86` |
| CR-13 | High | Accessibility | `frontend/src/components/ChatSidebar.tsx:54-58` |
| CR-14 | Medium | Error handling | `frontend/src/lib/api.ts:10-20` |
| CR-15 | Medium | AI context | `frontend/src/components/ChatSidebar.tsx:43-48` |
| CR-16 | Medium | API design | `backend/main.py` |
| CR-17 | Medium | Database | `backend/database.py:46-63` |
| CR-18 | Medium | AI integration | `backend/ai.py:121-124` |
| CR-19 | Medium | Security (IDOR) | `backend/routers/board.py:244-267` |
| CR-20 | Medium | Infrastructure | `docker-compose.yml` |
| CR-21 | Medium | Resource leak | `frontend/src/components/KanbanBoard.tsx:27` |
| CR-22 | Medium | Security/DoS | `backend/routers/chat.py` |
| CR-23 | Medium | Security | `backend/auth.py:14-19` |
| CR-24 | Medium | Performance | `backend/routers/board.py` |
| CR-25 | Medium | Layout | `frontend/src/components/KanbanBoard.tsx:197` |
| CR-26 | Low | DX | Missing `.env.example` |
| CR-27 | Low | Validation | `backend/models.py:30-33` |
| CR-28 | Low | Debugging | `backend/ai.py:114-131` |
| CR-29 | Low | Reliability | `backend/main.py:29-31` |
| CR-30 | Low | Scripts | `scripts/start.bat`, `scripts/stop.bat` |
| CR-31 | Low | Config | `.gitignore` |
| CR-32 | Low | Docker | `Dockerfile` |
| CR-33 | Low | Code quality | `backend/tests/test_chat.py:1` |
| CR-34 | Low | Accessibility | `frontend/src/components/KanbanColumn.tsx:44` |
| CR-35 | Low | Test coverage | `backend/tests/test_chat.py` |
| CR-36 | Low | UX | `frontend/src/components/LoginForm.tsx:18` |
