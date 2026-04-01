"""
server.py — FastAPI Backend with Auth + Sessions + Debug Agent (FIXED)
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uvicorn
from contextlib import asynccontextmanager
import traceback

from agent import run_debug_agent
from database import create_indexes
from auth import get_current_user, TokenData
from routes.auth_routes import router as auth_router
from routes.session_routes import router as session_router


# -------------------- APP INIT --------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_indexes()
    yield

app = FastAPI(
    title="AI Code Debugging Agent",
    description="LangGraph-powered debugger with user accounts & session history",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(session_router)


# -------------------- MODELS --------------------

class DebugRequest(BaseModel):
    code: str
    language: Optional[str] = None
    save_session: bool = True

class DebugResponse(BaseModel):
    language: str
    bugs: List[str]
    explanation: str
    fixed_code: str
    bug_count: int
    session_id: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    code: str
    message: str
    history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    language: str
    bugs: List[str]
    fixed_code: str


# -------------------- ROUTES --------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "agent": "AI Code Debugger v2.0",
        "features": ["auth", "sessions", "multi-language"],
    }


# -------------------- DEBUG ROUTE --------------------

@app.post("/debug", response_model=DebugResponse)
async def debug_code(req: DebugRequest, current_user: TokenData = Depends(get_current_user)):

    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")

    try:
        print("\n🔥 ===== DEBUG REQUEST =====")
        print("Code:", req.code)
        print("Language:", req.language)

        # Run agent
        result = run_debug_agent(req.code)

        print("✅ Raw Agent Result:", result)

        if not result:
            raise Exception("Agent returned empty result")

        # SAFE extraction
        language = result.get("language", "unknown")
        bugs = result.get("bugs", []) or []
        explanation = result.get("explanation", "")
        fixed_code = result.get("fixed_code", "")

        session_id = None

        # Save session only if bugs exist
        if req.save_session and len(bugs) > 0:
            from database import sessions_col, users_col, utcnow
            from routes.session_routes import make_title

            title = make_title(language, bugs, req.code)

            doc = {
                "user_id": current_user.user_id,
                "username": current_user.username,
                "title": title,
                "language": language,
                "code": req.code,
                "bugs": bugs,
                "explanation": explanation,
                "fixed_code": fixed_code,
                "bug_count": len(bugs),
                "created_at": utcnow(),
            }

            try:
                ins = await sessions_col.insert_one(doc)
                session_id = str(ins.inserted_id)

                await users_col.update_one(
                    {"username": current_user.username},
                    {"$inc": {"total_sessions": 1}},
                )

            except Exception as db_error:
                print("⚠️ DB ERROR:", db_error)

        return DebugResponse(
            language=language,
            bugs=bugs,
            explanation=explanation,
            fixed_code=fixed_code,
            bug_count=len(bugs),
            session_id=session_id,
        )

    except Exception as e:
        print("\n❌ ===== ERROR IN /debug =====")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- CHAT ROUTE --------------------

@app.post("/chat", response_model=ChatResponse)
async def chat_debug(req: ChatRequest, current_user: TokenData = Depends(get_current_user)):

    if not req.code.strip():
        raise HTTPException(status_code=400, detail="Code cannot be empty.")

    from langchain_core.messages import HumanMessage, AIMessage

    history = []

    try:
        for msg in (req.history or []):
            if msg.role == "user":
                history.append(HumanMessage(content=msg.content))
            else:
                history.append(AIMessage(content=msg.content))

        history.append(HumanMessage(content=req.message))

        print("\n💬 CHAT REQUEST:", req.message)

        result = run_debug_agent(req.code, chat_history=history)

        if not result:
            raise Exception("Agent returned empty result")

        last_ai = next(
            (m.content for m in reversed(result.get("messages", [])) if isinstance(m, AIMessage)),
            "Analyzed."
        )

        return ChatResponse(
            reply=last_ai,
            language=result.get("language", "unknown"),
            bugs=result.get("bugs", []) or [],
            fixed_code=result.get("fixed_code", ""),
        )

    except Exception as e:
        print("\n❌ ===== ERROR IN /chat =====")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# -------------------- RUN --------------------

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)