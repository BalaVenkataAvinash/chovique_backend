from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent


class Settings(BaseSettings):

    # App
    APP_ENV: str = "development"
    SECRET_KEY: str = "CHANGE_ME_TO_A_LONG_RANDOM_STRING"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    # Database
    DATABASE_URL: str = "postgresql://postgres:1234@localhost:5433/chovique_db"

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Superadmin Defaults
    SUPERADMIN_NAME: str = "Super Admin"
    SUPERADMIN_EMAIL: str = "superadmin@chovique.com"
    SUPERADMIN_PASSWORD: str = "SuperAdminSecret123!"

    # SMTP & OTP Settings
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "noreply@chovique.com"
    OTP_EXPIRE_SECONDS: int = 30

    model_config = SettingsConfigDict(
        env_file=(
            str(PROJECT_ROOT / ".env"),
            str(BASE_DIR / ".env"),
            ".env",
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        return [
            o.strip()
            for o in self.ALLOWED_ORIGINS.split(",")
            if o.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()