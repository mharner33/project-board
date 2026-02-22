import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import get_db, init_db
from routers.auth import router as auth_router
from routers.board import router as board_router
from routers.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = get_db()
    init_db(conn)
    conn.close()
    yield


app = FastAPI(title="Kanban Studio API", lifespan=lifespan)

cors_origins = os.environ.get("CORS_ORIGINS", "").split(",")
cors_origins = [o.strip() for o in cors_origins if o.strip()]
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth_router)
app.include_router(board_router)
app.include_router(chat_router)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/api/health")
def health():
    conn = get_db()
    try:
        conn.execute("SELECT 1")
    finally:
        conn.close()
    return {"status": "ok"}


STATIC_DIR.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
