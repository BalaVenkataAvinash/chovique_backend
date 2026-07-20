"""
CORS configuration helper.
Applied in main.py via app.add_middleware(CORSMiddleware, ...).
"""

from fastapi.middleware.cors import CORSMiddleware
from app.core.config import get_settings

settings = get_settings()


def get_cors_kwargs() -> dict:
    """Return kwargs to pass directly to CORSMiddleware."""
    return {
        "allow_origins": settings.allowed_origins_list,
        "allow_credentials": True,
        "allow_methods": ["*"],
        "allow_headers": ["*"],
    }
