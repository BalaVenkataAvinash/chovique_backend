import uuid
from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.dialects.sqlite import TEXT
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(120), nullable=False)
    email = Column(String(254), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # nullable for Google OAuth users

    role = Column(
        Enum("customer", "admin", "superadmin", name="user_role"),
        nullable=False,
        default="customer",
    )

    # ── Profile extras ───────────────────────────────────────────────────────
    phone = Column(String(30), nullable=True)
    dob = Column(String(10), nullable=True)           # ISO date: YYYY-MM-DD
    gender = Column(String(20), nullable=True)
    preferences = Column(TEXT, nullable=True)
    avatar_url = Column(TEXT, nullable=True)

    # ── Address (flattened for simplicity) ───────────────────────────────────
    address_street = Column(String(255), nullable=True)
    address_city = Column(String(100), nullable=True)
    address_state = Column(String(100), nullable=True)
    address_zip = Column(String(20), nullable=True)

    # ── OAuth ────────────────────────────────────────────────────────────────
    google_id = Column(String(120), nullable=True, unique=True)

    is_active = Column(Boolean, default=True)
