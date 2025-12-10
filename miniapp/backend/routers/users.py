from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from core.responses import success_response
from crud.user import get_user_stats, soft_delete_user, update_user_settings
from deps import get_current_user, get_db
from models import User
from schemas.user import User as UserSchema
from schemas.user import UserSettings, UserStats, UserUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Return current user profile."""
    return success_response(UserSchema.model_validate(current_user))


@router.patch("/me")
def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update basic user fields."""
    if payload.username is not None:
        current_user.username = payload.username
    if payload.avatar_url is not None:
        current_user.avatar_url = str(payload.avatar_url)
    if payload.bio is not None:
        current_user.bio = payload.bio
    if payload.first_name is not None:
        current_user.first_name = payload.first_name
    if payload.last_name is not None:
        current_user.last_name = payload.last_name
    if payload.language_code is not None:
        current_user.language_code = payload.language_code

    db.commit()
    db.refresh(current_user)
    return success_response(UserSchema.model_validate(current_user))


@router.get("/me/settings")
def get_my_settings(current_user: User = Depends(get_current_user)):
    """Return persisted settings for the current user."""
    return success_response(current_user.settings or {})


@router.patch("/me/settings")
def patch_my_settings(
    settings: UserSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Merge user settings."""
    merged = update_user_settings(current_user.id, settings, db)
    return success_response(merged)


@router.get("/me/stats")
def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return aggregate stats for the current user."""
    stats: UserStats = get_user_stats(current_user.id, db)
    return success_response(stats.model_dump())


@router.delete("/me")
def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Soft delete the current user."""
    soft_delete_user(current_user.id, db)
    return success_response({"message": "Account deleted"})
