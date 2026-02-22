from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
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
app.include_router(auth_router)
app.include_router(board_router)
app.include_router(chat_router)

STATIC_DIR = Path(__file__).parent / "static"


@app.get("/api/health")
def health():
    return {"status": "ok"}


STATIC_DIR.mkdir(exist_ok=True)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
