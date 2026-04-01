"""
database.py — MongoDB connection, collections, and models
"""

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import IndexModel, ASCENDING
from datetime import datetime
from typing import Optional, List
import os
from dotenv import load_dotenv

load_dotenv()

# ── MongoDB Connection ─────────────────────────────────────────────────────────
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME   = os.getenv("DB_NAME", "ai_debug_agent")

client = AsyncIOMotorClient(MONGO_URL)
db     = client[DB_NAME]

# ── Collections ────────────────────────────────────────────────────────────────
users_col    = db["users"]       # user accounts
sessions_col = db["sessions"]    # debug sessions per user


# ── Indexes (run once on startup) ──────────────────────────────────────────────
async def create_indexes():
    """Create indexes for fast lookups."""
    await users_col.create_index("username", unique=True)
    await users_col.create_index("email",    unique=True)
    await sessions_col.create_index([("user_id", ASCENDING), ("created_at", ASCENDING)])
    print("✅ MongoDB indexes created")


# ── Helpers ────────────────────────────────────────────────────────────────────
def utcnow() -> datetime:
    return datetime.utcnow()
