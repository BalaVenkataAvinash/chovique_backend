from fastapi import APIRouter
from app.api.v1 import auth
from app.api.v1 import users

api_router = APIRouter()

# /api/v1/auth/* — register, login, google, logout
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])

# /api/v1/users/* — /me, profile update, etc.
api_router.include_router(users.router, prefix="/users", tags=["Users"])
