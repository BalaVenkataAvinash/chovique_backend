# Chovique Backend API

FastAPI backend for the **CHOVIQUE** e-commerce chocolate store platform.

---

## 📅 Summary of Changes & Fixes (July 20, 2026)

Today, we resolved critical backend configuration errors, Google OAuth integration issues, and Pydantic v2 dependency imports.

### 1. Fixed Google OAuth Origin & Authentication Flow
- **Issue**: Google Sign-In failed due to missing client credentials, origin mismatch, or invalid token verification.
- **Root Cause**: `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` were missing or using placeholders in the backend environment files, and `GoogleOAuthProvider` needed proper frontend integration.
- **Resolution**:
  - Configured `VITE_GOOGLE_CLIENT_ID` in the frontend `.env` (`chocolate-store/.env`).
  - Added `GoogleOAuthProvider` wrapping the root App component in `main.tsx`.
  - Configured Google OAuth verification on the FastAPI backend in `app/services/auth_services.py` via Google's `tokeninfo` endpoint.
  - Ensured `http://localhost:5173` and `http://localhost:3000` are listed as allowed origins in `ALLOWED_ORIGINS` for CORS.

---

### 2. Resolved Missing `BaseSettings` Import in `config.py`
- **Issue**: Server error `Could not find name 'BaseSettings'` at `app/core/config.py:L7`.
- **Root Cause**: In Pydantic v2, `BaseSettings` and `SettingsConfigDict` were moved to the `pydantic-settings` package. `config.py` used `BaseSettings`, `SettingsConfigDict`, and `@lru_cache` without importing them at the top of the file.
- **Resolution**:
  - Updated `app/core/config.py` to import `BaseSettings` and `SettingsConfigDict` from `pydantic_settings`.
  - Added `lru_cache` import from standard library `functools`.
  - Verified `pydantic-settings==2.5.2` in `requirements.txt`.

---

### 3. Configured Google OAuth Client Secret Across Environment Files
- **Issue**: The root backend `.env` had placeholder string `GOOGLE_CLIENT_SECRET=PASTE_YOUR_SECRET_HERE`, which was taking precedence over subfolder configurations due to Pydantic's `env_file` search order.
- **Root Cause**: `SettingsConfigDict` was loading `PROJECT_ROOT / .env` prior to `BASE_DIR / .env`.
- **Resolution**:
  - Updated both `chovique_backend/.env` and `chovique_backend/app/.env` with the active Google Client Secret (`your_google_client_secret`).
  - Verified that backend Google OAuth token validation now loads the correct secret dynamically.

---

## 🛠️ Environment Configuration Guide

Ensure your `.env` file in `chovique_backend/` contains:

```env
# App Config
APP_ENV=development
SECRET_KEY=CHANGE_ME_TO_A_LONG_RANDOM_STRING_AT_LEAST_32_CHARS
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Database
DATABASE_URL=postgresql://postgres:1234@localhost:5433/chovique_db

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Google OAuth 2.0
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# SMTP & OTP Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@example.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your_email@example.com
OTP_EXPIRE_SECONDS=120
```

---

## 🚀 Running the Server

```bash
# Activate virtual environment if applicable
# Install dependencies
pip install -r requirements.txt

# Run FastAPI development server
cd app
uvicorn main:app --reload
```
