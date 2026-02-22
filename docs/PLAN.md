# Project Plan

## Part 1: Plan and Documentation

- [x] Enrich this document with detailed substeps, tests, and success criteria
- [x] Create `frontend/AGENTS.md` describing the existing frontend code
- [x] Flesh out `backend/AGENTS.md` and `scripts/AGENTS.md`
- [x] User approves the plan

---

## Part 2: Scaffolding

Set up Docker, FastAPI backend, and start/stop scripts. Confirm a hello-world page and API call work.

- [x] Create `backend/pyproject.toml` with dependencies: fastapi, uvicorn, python-dotenv
- [x] Create `backend/main.py` with a minimal FastAPI app
  - Mount a static directory for serving HTML
  - Add `GET /api/health` returning `{"status": "ok"}`
  - Serve a placeholder `index.html` at `/`
- [x] Create `Dockerfile` in project root
  - Python 3.12 base, install `uv`, install backend deps
  - Copy backend code, expose port 8000
  - CMD: uvicorn main:app
- [x] Create `docker-compose.yml`
  - Pass `.env` file through to container
  - Map port 8000
- [x] Create start/stop scripts in `scripts/`
  - `start.sh` / `stop.sh` for Linux/Mac (auto-detect podman vs docker)
  - `start.bat` / `stop.bat` for Windows
  - Scripts build image if needed, run container, pass `.env`
- [x] Create a placeholder `backend/static/index.html` with "Hello World"

**Tests and success criteria:**
- [x] `podman build` succeeds
- [x] Running the container serves "Hello World" at `http://localhost:8000/`
- [x] `GET /api/health` returns `{"status": "ok"}`
- [x] Start script launches the container; stop script tears it down

---

## Part 3: Add in Frontend

Statically build the Next.js frontend and serve it via FastAPI at `/`.

- [x] Add `output: 'export'` to `frontend/next.config.ts` for static export
- [x] `next/font/google` works with static export (fonts bundled at build time) -- no changes needed
- [x] Update `Dockerfile` with multi-stage build:
  - Stage 1: `node:22-slim`, `npm ci && npm run build`, produces `out/`
  - Stage 2: Python 3.12, copies `out/` into `static/`
- [x] `backend/main.py` already serves `static/` with `html=True` -- no changes needed
- [x] Remove the placeholder `index.html`

**Tests and success criteria:**
- [x] `npm run build` in frontend produces `out/` directory
- [x] `npm run test:unit` passes (6 tests, requires Node >=22)
- [x] Docker build succeeds with frontend included
- [x] Running the container shows the full Kanban board at `http://localhost:8000/`
- [x] CSS and JS assets load correctly (verified via curl)

---

## Part 4: Fake User Sign-In

Add a login gate in the frontend and a login endpoint in the backend. Hardcoded credentials: `user` / `password`.

- [x] Add `POST /api/auth/login` to backend (`backend/routers/auth.py`)
  - Accepts `{ username, password }`
  - Returns JWT token on success, 401 on failure
  - Uses PyJWT with hardcoded 32-byte secret (MVP only)
- [x] Logout is client-side (discard token from localStorage)
- [x] Add `GET /api/auth/me` -- validates token, returns user info
- [x] Create `LoginForm` component in frontend
  - Username + password fields, submit button
  - Styled with project color scheme
  - Shows error on bad credentials
- [x] Add `AuthProvider` context to frontend
  - Stores JWT in localStorage
  - Shows login form when unauthenticated
  - Shows "Signed in as" + Sign out button on the board
- [x] Rebuild static frontend, update Docker build

**Tests and success criteria:**
- [x] Backend: 7 tests pass (login success/failure, /me with/without token, health)
- [x] Frontend: 10 tests pass (3 kanban logic, 4 board incl. auth UI, 3 login form)
- [x] Container: valid login returns token, invalid returns 401
- [x] Container: /me with token returns username, without returns 401
- [x] Container: frontend loads with client-side auth gating

---

## Part 5: Database Modeling

Design the SQLite schema. Document it and get sign-off before implementing.

- [x] Create `docs/DATABASE.md` with the proposed schema
- [x] Design tables:
  - `users` (id, username, password_hash)
  - `boards` (id, user_id, name)
  - `columns` (id, board_id, title, position)
  - `cards` (id, column_id, title, details, position)
- [x] Save the schema as `docs/schema.json` (JSON representation)
- [ ] Get user approval on the schema

**Success criteria:**
- [x] Schema supports multiple users (future-proofed) but MVP uses one
- [x] Schema supports card ordering within columns
- [x] Schema supports column ordering within a board
- [x] Schema documented clearly in `docs/DATABASE.md`

---

## Part 6: Backend API

Implement the Kanban CRUD API with SQLite persistence.

- [x] Create `backend/database.py` -- SQLite connection, auto-create tables, seed data
- [x] Create `backend/models.py` -- Pydantic models for API request/response
- [x] Create `backend/routers/board.py` with endpoints:
  - `GET /api/board` -- return full board (columns + cards) for the authenticated user
  - `PUT /api/board/columns/{id}` -- rename a column
  - `POST /api/board/cards` -- create a card
  - `PUT /api/board/cards/{id}` -- update a card (title, details)
  - `DELETE /api/board/cards/{id}` -- delete a card
  - `PUT /api/board/cards/{id}/move` -- move a card (change column and/or position)
- [x] Seed default board data on first login (5 columns, 8 sample cards)
- [x] All board endpoints require valid JWT (ownership checks via DB joins)
- [x] Auth login now validates against DB instead of hardcoded constants

**Tests and success criteria:**
- [x] 20 backend tests pass (7 auth + 13 board)
- [x] Board is auto-created with default data for new user
- [x] GET returns full board structure (5 columns, 8 cards)
- [x] Rename, create, update, delete, move all persist correctly
- [x] Positions stay contiguous after operations
- [x] All endpoints reject unauthenticated/unauthorized requests
- [x] Manual curl testing against running container confirms all operations

---

## Part 7: Frontend + Backend Integration

Connect the frontend to the real API so the Kanban board is persistent.

- [x] Expand API client (`src/lib/api.ts`) with fetchBoard, renameColumn, createCard, updateCard, deleteCard, moveCard
- [x] Refactor types (`src/lib/kanban.ts`): integer IDs, columns contain `cards[]` directly (matches API shape), dnd-kit ID helpers
- [x] Rewrite `KanbanBoard` to:
  - Load board from API on mount with loading state
  - Call API on drag-end (optimistic local update + API call)
  - Debounced API call on column rename (500ms)
  - API call on card add/delete (replace state with response)
- [x] Update `KanbanColumn`, `KanbanCard` to use numeric IDs + `dndId()` prefix for dnd-kit
- [x] Rebuild static frontend, update Docker build

**Tests and success criteria:**
- [x] 15 frontend tests pass (7 kanban helpers, 5 board with mocked API, 3 login)
- [x] 20 backend tests pass
- [x] Board loads from API, shows loading state, then renders
- [x] Add/rename/delete operations call API and persist in container
- [x] Frontend HTML and JS assets load correctly

---

## Part 8: AI Connectivity

Connect the backend to OpenRouter and verify basic AI calls work.

- [x] Add `openai>=1.82` to dependencies
- [x] Create `backend/ai.py`
  - OpenAI client pointed at `https://openrouter.ai/api/v1`
  - Uses `OPENROUTER_API_KEY` from environment via dotenv
  - Model: `openai/gpt-oss-120b`
  - `simple_chat()` helper for basic prompt/response
- [x] Create `backend/routers/chat.py` with `POST /api/chat/test` (auth-protected)
- [x] `.env` passed through via docker-compose

**Tests and success criteria:**
- [x] 22 backend tests pass (7 auth + 13 board + 2 chat)
- [x] Chat test endpoint mocked correctly in unit tests
- [x] Live test: `/api/chat/test` returns `{"response": "4"}` in container

---

## Part 9: AI Structured Outputs

Extend the AI chat to understand the Kanban board and return structured responses that can mutate it.

- [x] Structured output schema in `models.py`:
  - `AIResponse`: message + board_updates (discriminated union)
  - Operations: `CreateCardOp`, `UpdateCardOp`, `MoveCardOp`, `DeleteCardOp`
  - `ChatRequest` / `ChatResponse` for the API
- [x] `POST /api/chat` endpoint in `routers/chat.py`:
  - Accepts `{ message, history[] }`
  - Loads board, builds system prompt with board JSON
  - Calls AI with `response_format: json_object`
  - Applies board_updates via `apply_board_updates()` in `routers/board.py`
  - Returns AI message + updates + refreshed board
- [x] `ai.py` updated with `chat_with_board()` using detailed system prompt
- [x] Conversation history passed through to AI context

**Tests and success criteria:**
- [x] 31 backend tests pass (7 auth + 13 board + 11 chat)
- [x] Tests cover: simple chat, create/update/move/delete via AI, multiple ops, invalid IDs skipped, history passed, auth required
- [x] Live: "Create card X in Backlog" -> card appears in DB
- [x] Live: "Move card X to Done" -> card moves to Done column

---

## Part 10: AI Chat Sidebar

Add a chat sidebar to the frontend that connects to the AI chat endpoint.

- [x] Create `ChatSidebar` component
  - Slide-out panel on the right side of the screen
  - Toggle button always visible (floating or in header)
  - Message input at the bottom, chat history scrolls above
  - User messages styled differently from AI messages
  - Loading indicator while AI is responding
- [x] Style the sidebar with the project color scheme
  - Purple accent for the toggle/send button
  - Surface bg for AI messages
  - Clean, modern look consistent with the board
- [x] Wire up to `POST /api/chat`
  - Send message + conversation history
  - Display AI response
  - If response includes board updates, refresh the board data automatically
- [x] Maintain conversation history in frontend state (cleared on page refresh is fine for MVP)
- [x] Rebuild static frontend, final Docker build
- [x] Add robust JSON parsing fallback in `ai.py` for malformed AI responses

**Tests and success criteria:**
- [x] Frontend unit test: sidebar opens/closes (9 ChatSidebar tests)
- [x] Frontend unit test: message is sent and response is displayed
- [x] Frontend unit test: board refreshes when AI returns board updates
- [x] E2E: open sidebar, send "Create a card called Test in Backlog", card appears on board (verified via curl)
- [x] E2E: conversation history is maintained across multiple messages
- [x] Visual: sidebar looks good on desktop widths, doesn't break the board layout