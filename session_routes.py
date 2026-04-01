"""
routes/session_routes.py — Save, list, retrieve, delete debug sessions
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from datetime import datetime

from database import sessions_col, users_col, utcnow
from auth import get_current_user, TokenData

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# ── Models ────────────────────────────────────────────────────────────────────
class SaveSessionRequest(BaseModel):
    code:        str
    language:    str
    bugs:        List[str]
    explanation: str
    fixed_code:  str
    bug_count:   int
    title:       Optional[str] = ""   # auto-generated if empty


class SessionSummary(BaseModel):
    session_id:  str
    title:       str
    language:    str
    bug_count:   int
    created_at:  str
    code_preview: str


class SessionDetail(BaseModel):
    session_id:  str
    title:       str
    language:    str
    code:        str
    bugs:        List[str]
    explanation: str
    fixed_code:  str
    bug_count:   int
    created_at:  str


def make_title(language: str, bugs: List[str], code: str) -> str:
    """Auto-generate a title for the session."""
    first_line = code.strip().splitlines()[0][:40] if code.strip() else "Code snippet"
    bug_word = "bug" if len(bugs) == 1 else "bugs"
    return f"{language} — {len(bugs)} {bug_word} — {first_line}"


# ── Save Session ──────────────────────────────────────────────────────────────
@router.post("/save")
async def save_session(req: SaveSessionRequest, current_user: TokenData = Depends(get_current_user)):
    title = req.title or make_title(req.language, req.bugs, req.code)

    session_doc = {
        "user_id":     current_user.user_id,
        "username":    current_user.username,
        "title":       title,
        "language":    req.language,
        "code":        req.code,
        "bugs":        req.bugs,
        "explanation": req.explanation,
        "fixed_code":  req.fixed_code,
        "bug_count":   req.bug_count,
        "created_at":  utcnow(),
    }

    result = await sessions_col.insert_one(session_doc)

    # Increment user's total sessions counter
    await users_col.update_one(
        {"username": current_user.username},
        {"$inc": {"total_sessions": 1}}
    )

    return {"session_id": str(result.inserted_id), "title": title, "message": "Session saved!"}


# ── List All Sessions for User ────────────────────────────────────────────────
@router.get("/", response_model=List[SessionSummary])
async def list_sessions(current_user: TokenData = Depends(get_current_user)):
    cursor = sessions_col.find(
        {"user_id": current_user.user_id},
        sort=[("created_at", -1)]   # newest first
    )
    sessions = []
    async for doc in cursor:
        sessions.append(SessionSummary(
            session_id   = str(doc["_id"]),
            title        = doc.get("title", "Untitled"),
            language     = doc.get("language", "Unknown"),
            bug_count    = doc.get("bug_count", 0),
            created_at   = doc["created_at"].isoformat(),
            code_preview = doc.get("code", "")[:120] + ("..." if len(doc.get("code","")) > 120 else ""),
        ))
    return sessions


# ── Get Single Session ────────────────────────────────────────────────────────
@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        oid = ObjectId(session_id)
    except Exception:
        raise HTTPException(400, "Invalid session ID")

    doc = await sessions_col.find_one({"_id": oid, "user_id": current_user.user_id})
    if not doc:
        raise HTTPException(404, "Session not found")

    return SessionDetail(
        session_id   = str(doc["_id"]),
        title        = doc.get("title", "Untitled"),
        language     = doc.get("language", "Unknown"),
        code         = doc.get("code", ""),
        bugs         = doc.get("bugs", []),
        explanation  = doc.get("explanation", ""),
        fixed_code   = doc.get("fixed_code", ""),
        bug_count    = doc.get("bug_count", 0),
        created_at   = doc["created_at"].isoformat(),
    )


# ── Delete Session ────────────────────────────────────────────────────────────
@router.delete("/{session_id}")
async def delete_session(session_id: str, current_user: TokenData = Depends(get_current_user)):
    try:
        oid = ObjectId(session_id)
    except Exception:
        raise HTTPException(400, "Invalid session ID")

    result = await sessions_col.delete_one({"_id": oid, "user_id": current_user.user_id})
    if result.deleted_count == 0:
        raise HTTPException(404, "Session not found")

    await users_col.update_one(
        {"username": current_user.username},
        {"$inc": {"total_sessions": -1}}
    )
    return {"message": "Session deleted"}


# ── Search Sessions ───────────────────────────────────────────────────────────
@router.get("/search/{query}", response_model=List[SessionSummary])
async def search_sessions(query: str, current_user: TokenData = Depends(get_current_user)):
    cursor = sessions_col.find({
        "user_id": current_user.user_id,
        "$or": [
            {"title":    {"$regex": query, "$options": "i"}},
            {"language": {"$regex": query, "$options": "i"}},
            {"code":     {"$regex": query, "$options": "i"}},
        ]
    }, sort=[("created_at", -1)])

    sessions = []
    async for doc in cursor:
        sessions.append(SessionSummary(
            session_id   = str(doc["_id"]),
            title        = doc.get("title", "Untitled"),
            language     = doc.get("language", "Unknown"),
            bug_count    = doc.get("bug_count", 0),
            created_at   = doc["created_at"].isoformat(),
            code_preview = doc.get("code", "")[:120],
        ))
    return sessions
