from pydantic import BaseModel, EmailStr


class UserPublic(BaseModel):
    """Read-only user fields safe to return in any response."""
    id: str
    name: str
    email: str
    role: str

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    dob: str | None = None
    gender: str | None = None
    preferences: str | None = None
    address_street: str | None = None
    address_city: str | None = None
    address_state: str | None = None
    address_zip: str | None = None
