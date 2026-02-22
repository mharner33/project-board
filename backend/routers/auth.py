import sqlite3

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from auth import create_token, get_current_user
from database import get_conn

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


class UserResponse(BaseModel):
    username: str


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, conn: sqlite3.Connection = Depends(get_conn)):
    row = conn.execute(
        "SELECT username, password_hash FROM users WHERE username = ?",
        (body.username,),
    ).fetchone()
    if not row or not bcrypt.checkpw(body.password.encode(), row["password_hash"].encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    token = create_token(body.username)
    return LoginResponse(token=token, username=body.username)


@router.get("/me", response_model=UserResponse)
def me(username: str = Depends(get_current_user)):
    return UserResponse(username=username)
