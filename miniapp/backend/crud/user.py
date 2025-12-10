from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from core.exceptions import NotFoundError
from models import AnalysisHistory, Favorite, Session as SessionModel, User, Watchlist
from schemas.user import UserSettings, UserStats


def _deep_merge(base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge two dictionaries, preferring update values."""
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def get_user_stats(user_id: int, db: Session) -> UserStats:
    """Return aggregate stats for the given user."""
    analysis_count = db.scalar(
        select(func.count()).select_from(AnalysisHistory).where(AnalysisHistory.user_id == user_id)
    )
    favorite_count = db.scalar(
        select(func.count()).select_from(Favorite).where(Favorite.user_id == user_id)
    )
    watchlist_count = db.scalar(
        select(func.count()).select_from(Watchlist).where(Watchlist.user_id == user_id)
    )
    last_analysis_at = db.scalar(
        select(func.max(AnalysisHistory.created_at)).where(AnalysisHistory.user_id == user_id)
    )

    return UserStats(
        analysis_count=analysis_count or 0,
        favorite_count=favorite_count or 0,
        watchlist_count=watchlist_count or 0,
        last_analysis_at=last_analysis_at,
    )


def update_user_settings(user_id: int, settings: UserSettings, db: Session) -> Dict[str, Any]:
    """Merge and persist user settings."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User", user_id)

    current_settings: Dict[str, Any] = user.settings or {}
    new_settings = settings.model_dump(exclude_none=True, exclude_unset=True)
    merged = _deep_merge(current_settings, new_settings)

    user.settings = merged
    db.commit()
    db.refresh(user)
    return merged


def soft_delete_user(user_id: int, db: Session) -> None:
    """Mark a user as deleted and revoke active sessions."""
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User", user_id)

    user.deleted_at = datetime.now(timezone.utc)
    db.query(SessionModel).filter(SessionModel.user_id == user_id).delete()
    db.commit()
