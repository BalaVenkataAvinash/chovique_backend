

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db.session import get_db
from middleware.auth import get_current_user
from models.users import User
from schemas.auth import (
    RegisterIn,
    LoginIn,
    GoogleTokenIn,
    AuthResponse,
    UserOut,
    UserProfileOut,
    AddressOut,
    SendOtpIn,
    VerifyOtpIn,
    ResendOtpIn,
    SendOtpResponse,
    GoogleAuthResponse,
)
from services.auth_services import (
    register_user,
    login_user,
    google_auth,
    send_registration_otp,
    verify_registration_otp,
    resend_registration_otp,
)

router = APIRouter()


def _user_to_out(user: User) -> UserOut:
    """Shared serialiser — keeps route handlers thin."""
    initials = "".join(p[0].upper() for p in user.name.strip().split() if p) or "U"
    return UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        role=user.role,
        profile=UserProfileOut(
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
        ),
    )


# ── OTP Verification Routes ──────────────────────────────────────────────────

@router.post("/send-otp", response_model=SendOtpResponse)
async def send_otp(payload: SendOtpIn, db: Session = Depends(get_db)):
    """Generate and send a 6-digit OTP code to the user's email via SMTP."""
    return send_registration_otp(db, name=payload.name, email=payload.email, password=payload.password)


@router.post("/verify-otp", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def verify_otp(payload: VerifyOtpIn, db: Session = Depends(get_db)):
    """Verify 6-digit OTP code (30s expiry) and complete user registration."""
    return verify_registration_otp(db, email=payload.email, otp=payload.otp)


@router.post("/resend-otp", response_model=SendOtpResponse)
async def resend_otp(payload: ResendOtpIn, db: Session = Depends(get_db)):
    """Resend a fresh 6-digit OTP code with a renewed 30s expiration."""
    return resend_registration_otp(db, email=payload.email)


# ── Direct Register ──────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterIn, db: Session = Depends(get_db)):
    """Create a new customer account directly and return a JWT."""
    return register_user(db, name=payload.name, email=payload.email, password=payload.password)


# ── Login (OAuth2 form — used by FastAPI /docs Authorize button) ──────────────

@router.post("/login", response_model=AuthResponse)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Standard OAuth2 form login.
    Frontend authService.ts sends username=email + password as
    application/x-www-form-urlencoded to this endpoint.
    """
    return login_user(db, email=form_data.username, password=form_data.password)


# ── Login (JSON body fallback) ────────────────────────────────────────────────

@router.post("/login/json", response_model=AuthResponse)
async def login_json(payload: LoginIn, db: Session = Depends(get_db)):
    """JSON-body login — alternative for clients that cannot send form data."""
    return login_user(db, email=payload.email, password=payload.password)


# ── Google OAuth ──────────────────────────────────────────────────────────────

@router.post("/google", response_model=GoogleAuthResponse)
async def google_login(payload: GoogleTokenIn, db: Session = Depends(get_db)):
    """
    Verify a Google id_token.
    - Existing users are logged in immediately.
    - New users receive an OTP via email and require 6-digit OTP verification.
    """
    return await google_auth(db, id_token=payload.id_token)


# ── Logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout():
    """
    Server-side logout is a no-op for stateless JWT auth.
    The frontend clears the token from localStorage.
    """
    return None


# ── Current User (GET /users/me) ──────────────────────────────────────────────

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's profile. Used on app init."""
    return _user_to_out(current_user)
