"""
User Repository — all DB read/write operations for the User model.
Services call these; no raw SQL anywhere else.
"""

from sqlalchemy.orm import Session
from app.models.users import User


def get_by_id(db: Session, user_id: str) -> User | None:
    return db.query(User).filter(User.id == user_id, User.is_active == True).first()


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower(), User.is_active == True).first()


def get_by_google_id(db: Session, google_id: str) -> User | None:
    return db.query(User).filter(User.google_id == google_id).first()


def create(db: Session, *, name: str, email: str, hashed_password: str | None = None,
           google_id: str | None = None, avatar_url: str | None = None, role: str = "customer") -> User:
    initials = "".join(part[0].upper() for part in name.strip().split() if part) or "U"
    user = User(
        name=name,
        email=email.lower(),
        hashed_password=hashed_password,
        google_id=google_id,
        avatar_url=avatar_url or f"https://api.dicebear.com/7.x/adventurer/svg?seed={name}",
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_superadmin(db: Session) -> User:
    from core.config import get_settings
    from core.database import hash_password

    settings = get_settings()
    superadmin = db.query(User).filter(
        (User.role == "superadmin") | (User.email == settings.SUPERADMIN_EMAIL.lower())
    ).first()

    if not superadmin:
        hashed = hash_password(settings.SUPERADMIN_PASSWORD)
        superadmin = create(
            db,
            name=settings.SUPERADMIN_NAME,
            email=settings.SUPERADMIN_EMAIL,
            hashed_password=hashed,
            role="superadmin",
        )
        print(f"[CHOVIQUE SEED] Superadmin created: {settings.SUPERADMIN_EMAIL}")
    else:
        # Ensure role is superadmin
        if superadmin.role != "superadmin":
            superadmin.role = "superadmin"
            db.commit()
            db.refresh(superadmin)
    return superadmin


def update_profile(db: Session, user: User, **kwargs) -> User:
    for key, value in kwargs.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
