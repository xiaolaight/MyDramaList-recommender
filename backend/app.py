import os
import uvicorn
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from mysql.connector import errors as mysql_errors
from pydantic import BaseModel, Field

try:
    from . import db_manager as db
except ImportError:
    import db_manager as db

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

GOOGLE_CLIENT_ID = (
    os.getenv("GOOGLE_CLIENT_ID") or os.getenv("client_id") or ""
).strip()
if not GOOGLE_CLIENT_ID:
    raise RuntimeError(
        "Set GOOGLE_CLIENT_ID or client_id in project .env (Google OAuth Web client ID)"
    )

app = FastAPI(title="MyDramaList recommender API")

_cors = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
)
allow_origins = [o.strip() for o in _cors.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_credential(credential: str) -> dict:
    try:
        return id_token.verify_oauth2_token(
            credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google credential: {e}") from e


def rows_to_payload(rows):
    return [
        {"id": r[0], "title": r[1], "pic_url": r[2]}
        for r in rows
    ]


def pack_display(uid: str):
    comp_one, comp_two = db.display(uid)
    return {
        "google_sub": uid,
        "watched": rows_to_payload(comp_one),
        "recommendations": rows_to_payload(comp_two),
    }


class CredentialBody(BaseModel):
    credential: str = Field(..., min_length=1)


class WatchBody(BaseModel):
    credential: str = Field(..., min_length=1)
    drama_id: int


@app.post("/api/auth/signup")
def auth_signup(body: CredentialBody):
    info = verify_credential(body.credential)
    sub = info.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing sub")
    picture = info.get("picture") or ""
    try:
        db.make_user(sub, picture)
    except mysql_errors.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Account already exists. Use Log in instead.",
        ) from None
    return pack_display(sub)


@app.post("/api/auth/login")
def auth_login(body: CredentialBody):
    info = verify_credential(body.credential)
    sub = info.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing sub")
    if not db.user_exists(sub):
        raise HTTPException(
            status_code=404,
            detail="No account for this Google user. Sign up first.",
        )
    return pack_display(sub)


@app.post("/api/display")
def refresh_display(body: CredentialBody):
    info = verify_credential(body.credential)
    sub = info.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing sub")
    if not db.user_exists(sub):
        raise HTTPException(status_code=404, detail="User not registered")
    return pack_display(sub)


@app.get("/api/search")
def search(q: str = Query("", min_length=1)):
    rows = db.search_drama(q)
    return [{"title": r[0], "id": r[1]} for r in rows]


@app.post("/api/watch")
def add_watch(body: WatchBody):
    info = verify_credential(body.credential)
    sub = info.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing sub")
    if not db.user_exists(sub):
        raise HTTPException(status_code=404, detail="User not registered")
    try:
        comp_one, comp_two = db.add_watch(sub, body.drama_id)
    except mysql_errors.IntegrityError:
        raise HTTPException(status_code=409, detail="Already in watch list") from None
    return {
        "watched": rows_to_payload(comp_one),
        "recommendations": rows_to_payload(comp_two),
    }


if __name__ == "__main__":
    # API on 8000 so Vite (5173) can proxy /api here. Run: python app.py from backend/
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
