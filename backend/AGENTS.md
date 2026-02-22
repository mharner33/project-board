# Backend

Python FastAPI application. Serves the statically-exported Next.js frontend and provides the REST API.

## Stack

- Python 3.12+, FastAPI, Uvicorn
- SQLite for persistence (auto-created if missing)
- OpenAI SDK via OpenRouter for AI chat (model: `openai/gpt-oss-120b`)
- `uv` as the Python package manager

## Responsibilities

- Serve the static frontend build at `/`
- Auth endpoint: POST `/api/auth/login` (hardcoded user/password for MVP)
- Kanban CRUD: REST endpoints under `/api/board/` for columns and cards
- AI chat: POST `/api/chat` -- sends board state + conversation history to OpenRouter, returns structured output (AI reply + optional board mutations)

## Layout (planned)

```
backend/
  main.py           FastAPI app entry point, mounts static files and API router
  routers/
    auth.py         Login/logout endpoints
    board.py        Kanban CRUD endpoints
    chat.py         AI chat endpoint
  models.py         SQLite schema / ORM models
  database.py       DB connection and initialization
  ai.py             OpenRouter client and structured output handling
```