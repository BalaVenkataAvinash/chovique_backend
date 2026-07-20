"""
Auth Service — business logic layer between the route handlers and the repository.

Handles:
  - Email/password registration & login
  - Google OAuth token verification → user upsert
  - Serialising ORM User → Pydantic UserOut (matching frontend types)
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import httpx

from app.core.config import get_settings
from app.core.database import hash_password, verify_password, create_access_token
from app.models.users import User
from app.repositories import user_repository
from app.schemas.auth import UserOut, UserProfileOut, AddressOut, AuthResponse, SendOtpResponse, GoogleAuthResponse

def _get_active_settings():
    get_settings.cache_clear()
    return get_settings()

class SettingsProxy:
    def __getattr__(self, name: str):
        return getattr(_get_active_settings(), name)

settings = SettingsProxy()

# ─── ORM → Pydantic helper ───────────────────────────────────────────────────

def _serialize_user(user: User) -> UserOut:
    initials = "".join(p[0].upper() for p in user.name.strip().split() if p) or "U"
    profile = UserProfileOut(
        name=user.name,
        email=user.email,
        phone=user.phone or "",
        avatar=initials,
        avatarUrl=user.avatar_url,
        dob=user.dob,
        gender=user.gender,
        preferences=user.preferences,
        address=AddressOut(
            street=user.address_street or "",
            city=user.address_city or "",
            state=user.address_state or "",
            zip=user.address_zip or "",
        ),
    )
    return UserOut(id=user.id, name=user.name, email=user.email, role=user.role, profile=profile)


def _make_auth_response(user: User) -> AuthResponse:
    token = create_access_token({"sub": user.id, "role": user.role})
    return AuthResponse(access_token=token, token_type="bearer", user=_serialize_user(user))


# ─── Register & OTP ──────────────────────────────────────────────────────────

def send_registration_otp(db: Session, *, name: str, email: str, password: str) -> SendOtpResponse:
    import random
    from datetime import datetime, timedelta, timezone
    from models.otp import OTPRecord
    from services.email_service import send_otp_email

    email_clean = email.lower()
    if user_repository.get_by_email(db, email_clean):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    otp_code = f"{random.randint(100000, 999999)}"
    hashed = hash_password(password)
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)

    otp_record = db.query(OTPRecord).filter(OTPRecord.email == email_clean).first()
    if otp_record:
        otp_record.name = name
        otp_record.hashed_password = hashed
        otp_record.otp_code = otp_code
        otp_record.created_at = now
        otp_record.expires_at = expires_at
    else:
        otp_record = OTPRecord(
            email=email_clean,
            name=name,
            hashed_password=hashed,
            otp_code=otp_code,
            created_at=now,
            expires_at=expires_at,
        )
        db.add(otp_record)

    db.commit()
    send_otp_email(email_clean, otp_code)
    return SendOtpResponse(
        message="Verification OTP sent to your email.",
        email=email_clean,
        expires_in=settings.OTP_EXPIRE_SECONDS,
    )


def verify_registration_otp(db: Session, *, email: str, otp: str) -> AuthResponse:
    from datetime import datetime, timezone
    from models.otp import OTPRecord

    email_clean = email.lower()
    if user_repository.get_by_email(db, email_clean):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    otp_record = db.query(OTPRecord).filter(OTPRecord.email == email_clean).first()
    if not otp_record or otp_record.otp_code != otp.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP code. Please check and try again.",
        )

    now = datetime.now(timezone.utc)
    expires_at = otp_record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. OTP expiry is 30 seconds. Please request a new OTP.",
        )

    user = user_repository.create(
        db,
        name=otp_record.name,
        email=otp_record.email,
        hashed_password=otp_record.hashed_password,
        google_id=otp_record.google_id,
        avatar_url=otp_record.avatar_url,
        role="customer",
    )

    db.delete(otp_record)
    db.commit()

    return _make_auth_response(user)


def resend_registration_otp(db: Session, *, email: str) -> SendOtpResponse:
    import random
    from datetime import datetime, timedelta, timezone
    from models.otp import OTPRecord
    from services.email_service import send_otp_email

    email_clean = email.lower()
    otp_record = db.query(OTPRecord).filter(OTPRecord.email == email_clean).first()
    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending registration found for this email. Please submit details first.",
        )

    otp_code = f"{random.randint(100000, 999999)}"
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)

    otp_record.otp_code = otp_code
    otp_record.created_at = now
    otp_record.expires_at = expires_at
    db.commit()

    send_otp_email(email_clean, otp_code)
    return SendOtpResponse(
        message="A new OTP has been sent to your email.",
        email=email_clean,
        expires_in=settings.OTP_EXPIRE_SECONDS,
    )


def register_user(db: Session, *, name: str, email: str, password: str) -> AuthResponse:
    if user_repository.get_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    hashed = hash_password(password)
    user = user_repository.create(db, name=name, email=email, hashed_password=hashed)
    return _make_auth_response(user)


# ─── Login ───────────────────────────────────────────────────────────────────

def login_user(db: Session, *, email: str, password: str) -> AuthResponse:
    user = user_repository.get_by_email(db, email)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )
    return _make_auth_response(user)


import logging

logger = logging.getLogger("uvicorn.error")

# ─── Google OAuth ─────────────────────────────────────────────────────────────

async def google_auth(db: Session, *, id_token: str) -> GoogleAuthResponse:
    """
    Verify Google id_token via Google's tokeninfo endpoint.
    - If user exists in DB: log in immediately and return access token.
    - If user is NEW: send OTP via SMTP to user's email, store details in OTPRecord, and require OTP verification.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": id_token},
        )

    if resp.status_code != 200:
        error_detail = "Invalid Google token."
        try:
            err_data = resp.json()
            if "error_description" in err_data:
                error_detail = f"Invalid Google token: {err_data['error_description']}"
        except Exception:
            pass
        logger.warning(f"[Google Auth Failed] tokeninfo status={resp.status_code}, response={resp.text}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error_detail,
        )

    info = resp.json()

    # Validate audience
    configured_client_id = (settings.GOOGLE_CLIENT_ID or "").strip()
    token_aud = str(info.get("aud", "")).strip()
    token_azp = str(info.get("azp", "")).strip()

    if configured_client_id and configured_client_id != token_aud and configured_client_id != token_azp:
        logger.warning(
            f"[Google Auth Failed] Audience mismatch. Configured='{configured_client_id}', aud='{token_aud}', azp='{token_azp}'"
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google token audience mismatch. Configured: '{configured_client_id}', Token aud: '{token_aud}'",
        )

    google_id: str = info["sub"]
    email: str = info["email"]
    name: str = info.get("name", email.split("@")[0])
    avatar_url: str | None = info.get("picture")

    # Try to find existing user
    user = user_repository.get_by_google_id(db, google_id)
    if not user:
        user = user_repository.get_by_email(db, email)
        if user:
            # Link Google account to existing email account
            user.google_id = google_id
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            db.commit()
            db.refresh(user)
        else:
            # Brand-new user via Google -> Require OTP verification before creating user!
            import random
            from datetime import datetime, timedelta, timezone
            from models.otp import OTPRecord
            from services.email_service import send_otp_email

            otp_code = f"{random.randint(100000, 999999)}"
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=settings.OTP_EXPIRE_SECONDS)

            email_clean = email.lower()
            otp_record = db.query(OTPRecord).filter(OTPRecord.email == email_clean).first()
            if otp_record:
                otp_record.name = name
                otp_record.google_id = google_id
                otp_record.avatar_url = avatar_url
                otp_record.otp_code = otp_code
                otp_record.created_at = now
                otp_record.expires_at = expires_at
            else:
                otp_record = OTPRecord(
                    email=email_clean,
                    name=name,
                    google_id=google_id,
                    avatar_url=avatar_url,
                    otp_code=otp_code,
                    created_at=now,
                    expires_at=expires_at,
                )
                db.add(otp_record)

            db.commit()
            send_otp_email(email_clean, otp_code)

            return GoogleAuthResponse(
                require_otp=True,
                email=email_clean,
                message="Verification OTP sent to your Google email.",
                expires_in=settings.OTP_EXPIRE_SECONDS,
            )

    auth_resp = _make_auth_response(user)
    return GoogleAuthResponse(
        require_otp=False,
        access_token=auth_resp.access_token,
        token_type=auth_resp.token_type,
        user=auth_resp.user,
    )


# ─── Get current user by token ────────────────────────────────────────────────

def get_current_user_from_db(db: Session, user_id: str) -> User:
    user = user_repository.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user
