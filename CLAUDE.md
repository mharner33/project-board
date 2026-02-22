# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Kanban Studio - a project management MVP with a Kanban board and AI chat sidebar. Next.js static frontend served by a Python FastAPI backend, all in one Docker container. AI integration via OpenRouter (`openai/gpt-oss-120b`).

Login credentials: `user` / `password`.

## Commands

### Docker (full app)
```bash
./scripts/start.sh    # build and start (auto-detects docker/podman)
./scripts/stop.sh     # stop
# App runs at http://localhost:8000
```

### Frontend (from `frontend/`)
```bash
npm install           # install deps
npm run dev           # dev server
npm run build         # static export to out/
npm run lint          # eslint
npm run test:unit     # vitest (unit tests)
npm run test:unit:watch  # vitest in watch mode
npm run test:e2e      # playwright (requires running backend)
npm run test:all      # unit + e2e
```

### Backend (from `backend/`)
```bash
uv sync               # install deps
uv run pytest          # all tests
uv run pytest tests/test_auth.py           # single test file
uv run pytest tests/test_auth.py::test_login_success  # single test
uv run uvicorn main:app --reload           # dev server on :8000
```

## Architecture

**Two-part app in one container:**
- `frontend/` - Next.js 16, React 19, Tailwind 4, static export (`output: 'export'`)
- `backend/` - FastAPI serving the API at `/api/*` and the static frontend at `/`

**Frontend key files:**
- `src/app/page.tsx` - Entry point, renders LoginForm or KanbanBoard based on auth state
- `src/components/AuthProvider.tsx` - React Context for JWT auth (stored in localStorage)
- `src/components/KanbanBoard.tsx` - Main board component, owns all board state, handles drag-and-drop via @dnd-kit
- `src/components/ChatSidebar.tsx` - AI chat panel, sends messages and applies returned board updates
- `src/lib/api.ts` - All API fetch helpers with auth headers
- `src/lib/kanban.ts` - TypeScript types and dnd-kit ID helpers

**Backend key files:**
- `main.py` - FastAPI app, mounts static files, includes routers
- `database.py` - SQLite setup (WAL mode, foreign keys), schema creation, seed data
- `auth.py` - JWT creation/validation (HS256, 24h expiry)
- `ai.py` - OpenRouter client, structured JSON output parsing for board operations
- `routers/auth.py` - Login and user info endpoints
- `routers/board.py` - Full board CRUD (columns, cards, move/reorder)
- `routers/chat.py` - AI chat endpoint that can return board mutations

**Data flow for AI chat:** ChatSidebar sends message + history to `POST /api/chat` -> `ai.py` calls OpenRouter with board context -> returns structured JSON with `board_updates` (create/update/move/delete operations) -> backend applies them -> returns updated board -> frontend replaces board state.

**Database:** SQLite at `/app/data/kanban.db`. Tables: users, boards, columns, cards. Auto-seeded with 5 columns and sample cards on first run.

## Coding Standards (from AGENTS.md)

- Keep it simple. Never over-engineer. No unnecessary defensive programming. No extra features.
- No emojis ever.
- Identify root cause before fixing issues. Prove with evidence, then fix.
- Use latest library versions and idiomatic approaches.
- Review `docs/PLAN.md` before making architectural changes.

## Environment

- `.env` in project root must contain `OPENROUTER_API_KEY`
- Frontend path alias: `@/*` maps to `src/*`
- Backend uses `uv` as Python package manager
- Docker build: stage 1 builds frontend, stage 2 sets up backend and copies `out/`
