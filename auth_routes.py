"""
routes/auth_routes.py — Register, Login, Profile endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from datetime import datetime
from bson import ObjectId
import re

from database import users_col, utcnow
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user, TokenData
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ── Request / Response Models ─────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    username: str
    email:    str
    password: str
    full_name: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user: dict


class ProfileResponse(BaseModel):
    user_id:    str
    username:   str
    email:      str
    full_name:  str
    created_at: str
    total_sessions: int


# ── Register ──────────────────────────────────────────────────────────────────
@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    # Validate username
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", req.username):
        raise HTTPException(400, "Username must be 3-20 chars, letters/numbers/underscore only")

    # Validate password strength
    if len(req.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")

    # Check if username/email already taken
    existing = await users_col.find_one({"$or": [{"username": req.username}, {"email": req.email}]})
    if existing:
        if existing["username"] == req.username:
            raise HTTPException(409, "Username already taken")
        raise HTTPException(409, "Email already registered")

    # Create user
    user_doc = {
        "username":       req.username,
        "email":          req.email,
        "full_name":      req.full_name,
        "hashed_password": hash_password(req.password),
        "created_at":     utcnow(),
        "last_login":     utcnow(),
        "total_sessions": 0,
        "is_active":      True,
    }

    result = await users_col.insert_one(user_doc)
    user_id = str(result.inserted_id)

    token = create_access_token({"sub": req.username, "user_id": user_id})

    return AuthResponse(
        access_token=token,
        user={
            "user_id":   user_id,
            "username":  req.username,
            "email":     req.email,
            "full_name": req.full_name,
        }
    )


# ── Login ─────────────────────────────────────────────────────────────────────
@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    user = await users_col.find_one({"username": req.username})
    if not user or not verify_password(req.password, user["hashed_password"]):
        raise HTTPException(401, "Invalid username or password")

    if not user.get("is_active", True):
        raise HTTPException(403, "Account is deactivated")

    # Update last login
    await users_col.update_one({"_id": user["_id"]}, {"$set": {"last_login": utcnow()}})

    user_id = str(user["_id"])
    token = create_access_token({"sub": req.username, "user_id": user_id})

    return AuthResponse(
        access_token=token,
        user={
            "user_id":   user_id,
            "username":  user["username"],
            "email":     user["email"],
            "full_name": user.get("full_name", ""),
        }
    )


# ── Profile ───────────────────────────────────────────────────────────────────
@router.get("/profile", response_model=ProfileResponse)
async def get_profile(current_user: TokenData = Depends(get_current_user)):
    user = await users_col.find_one({"username": current_user.username})
    if not user:
        raise HTTPException(404, "User not found")

    return ProfileResponse(
        user_id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        full_name=user.get("full_name", ""),
        created_at=user["created_at"].isoformat(),
        total_sessions=user.get("total_sessions", 0),
    )


# ── Change Password ───────────────────────────────────────────────────────────
class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@router.post("/change-password")
async def change_password(req: ChangePasswordRequest, current_user: TokenData = Depends(get_current_user)):
    user = await users_col.find_one({"username": current_user.username})
    if not verify_password(req.current_password, user["hashed_password"]):
        raise HTTPException(400, "Current password is incorrect")
    if len(req.new_password) < 6:
        raise HTTPException(400, "New password must be at least 6 characters")
    await users_col.update_one(
        {"_id": user["_id"]},
        {"$set": {"hashed_password": hash_password(req.new_password)}}
    )
    return {"message": "Password changed successfully"}
