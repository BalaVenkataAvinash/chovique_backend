"""
Seed Script — creates default admin accounts on first run.

Run with:
  python -m app.db.seed

Hardcoded credentials (change in production!):
  customer@chovique.com / password123
  admin@chovique.com    / password123
  superadmin@chovique.com / password123
"""

from app.db.session import engine, SessionLocal
from app.db import base  # noqa — ensures all models are registered
from app.db.session import Base
from app.core.database import hash_password
from app.models.users import User
from app.repositories import user_repository


def seed():
    # Create tables if they don't exist yet
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    default_users = [
        {
            "name": "Priya Sharma",
            "email": "customer@chovique.com",
            "password": "password123",
            "role": "customer",
        },
        {
            "name": "Alok Mishra",
            "email": "admin@chovique.com",
            "password": "password123",
            "role": "admin",
        },
        {
            "name": "Enterprise Chief",
            "email": "superadmin@chovique.com",
            "password": "password123",
            "role": "superadmin",
        },
    ]

    for u in default_users:
        existing = user_repository.get_by_email(db, u["email"])
        if not existing:
            user = User(
                name=u["name"],
                email=u["email"],
                hashed_password=hash_password(u["password"]),
                role=u["role"],
                avatar_url=f"https://api.dicebear.com/7.x/adventurer/svg?seed={u['name'].split()[0]}",
            )
            db.add(user)
            print(f"  [OK] Created: {u['email']} ({u['role']})")
        else:
            print(f"  [skip] Exists: {u['email']}")

    db.commit()
    db.close()
    print("Seed complete.")


if __name__ == "__main__":
    seed()
