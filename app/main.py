"""
Chovique FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from middleware.cors import get_cors_kwargs
import models.otp  # noqa: F401
from db.session import engine, Base, SessionLocal
from repositories.user_repository import seed_superadmin
from api.v1 import api_router

settings = get_settings()

from sqlalchemy import text

# ── Create tables & seed superadmin ───────────────────────────────────────────
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    try:
        db.execute(text("ALTER TABLE otp_verifications ADD COLUMN IF NOT EXISTS google_id VARCHAR(120);"))
        db.execute(text("ALTER TABLE otp_verifications ADD COLUMN IF NOT EXISTS avatar_url TEXT;"))
        db.execute(text("ALTER TABLE otp_verifications ALTER COLUMN hashed_password DROP NOT NULL;"))
        db.commit()
    except Exception as e:
        db.rollback()
    seed_superadmin(db)

# ── FastAPI app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="Chovique API",
    version="1.0.0",
    description="Backend API for the Chovique luxury chocolate e-commerce platform.",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(CORSMiddleware, **get_cors_kwargs())

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(api_router, prefix="/api/v1")


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}
