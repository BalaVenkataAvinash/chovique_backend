# Re-export Base so Alembic env.py can import it from one place.
from app.db.session import Base  # noqa: F401

# Import all models here so SQLAlchemy registers them before create_all()
from app.models.users import User  # noqa: F401
