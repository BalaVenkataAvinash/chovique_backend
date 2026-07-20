import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.sqlite import TEXT
from app.db.session import Base


class OTPRecord(Base):
    __tablename__ = "otp_verifications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(254), index=True, nullable=False, unique=True)
    name = Column(String(120), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    google_id = Column(String(120), nullable=True)
    avatar_url = Column(TEXT, nullable=True)
    otp_code = Column(String(6), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
