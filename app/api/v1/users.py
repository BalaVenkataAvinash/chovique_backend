from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_user
from app.models.users import User
from app.schemas.auth import UserOut, UserProfileOut, AddressOut
from app.schemas.users import UserUpdate
from app.repositories.user_repository import user_repository

router = APIRouter()


def _user_to_out(user: User) -> UserOut:
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


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return the authenticated user's full profile.
    Called by authService.getMe() on app init to rehydrate state."""
    return _user_to_out(current_user)


@router.patch("/me", response_model=UserOut)
async def update_me(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Partially update the current user's profile."""
    updated = user_repository.update_profile(
        db,
        current_user,
        **payload.model_dump(exclude_none=True),
    )
    return _user_to_out(updated)
