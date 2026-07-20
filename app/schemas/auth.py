"""
Pydantic schemas for Auth and User resources.

Frontend contract (from src/types/index.ts):
  LoginPayload  → POST /auth/login
  RegisterPayload → POST /auth/register
  AuthResponse  ← { access_token, token_type, user: User }
  User          ← { id, name, email, role, profile: UserProfile }
"""

from pydantic import BaseModel, EmailStr, Field


# ─── Embedded sub-schemas ───────────────────────────────────────────────────

class AddressOut(BaseModel):
    street: str = ""
    city: str = ""
    state: str = ""
    zip: str = ""


class UserProfileOut(BaseModel):
    name: str
    email: str
    phone: str = ""
    avatar: str = ""          # initials, e.g. "PS"
    avatarUrl: str | None = None
    dob: str | None = None
    gender: str | None = None
    preferences: str | None = None
    address: AddressOut = AddressOut()


class UserOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    profile: UserProfileOut

    class Config:
        from_attributes = True


# ─── Auth request schemas ───────────────────────────────────────────────────

class RegisterIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


# ─── Auth response schema ───────────────────────────────────────────────────

class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ─── OTP Registration Schemas ───────────────────────────────────────────────

class SendOtpIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class VerifyOtpIn(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)


class ResendOtpIn(BaseModel):
    email: EmailStr


class SendOtpResponse(BaseModel):
    message: str
    email: str
    expires_in: int = 30


# ─── Google OAuth ────────────────────────────────────────────────────────────

class GoogleTokenIn(BaseModel):
    id_token: str


class GoogleAuthResponse(BaseModel):
    require_otp: bool = False
    access_token: str | None = None
    token_type: str = "bearer"
    user: UserOut | None = None
    email: str | None = None
    message: str | None = None
    expires_in: int = 30
