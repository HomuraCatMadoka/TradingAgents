from datetime import datetime, timedelta, timezone

import pytest

from core.exceptions import NotFoundError, ValidationError
from crud.analysis import create_analysis, list_analysis_history
from crud.favorite import delete_favorite
from crud.user import get_user_stats, soft_delete_user, update_user_settings
from crud.watchlist import batch_update_watchlist_active, update_watchlist
from db import SessionLocal
from models import AnalysisHistory, Favorite, Session as SessionModel, User, Watchlist
from schemas.analysis import AnalysisCreate
from schemas.user import UserSettings


def _clear_db():
    with SessionLocal() as db:
        for model in (AnalysisHistory, Favorite, Watchlist, SessionModel, User):
            db.query(model).delete()
        db.commit()


def _create_user(telegram_id: int = 12345) -> User:
    with SessionLocal() as db:
        user = User(
            telegram_id=telegram_id,
            settings={"theme": "light", "notifications": {"email": True}},
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


def test_analysis_create_and_end_date():
    _clear_db()
    user = _create_user(telegram_id=11001)
    with SessionLocal() as db:
        payload = AnalysisCreate(
            user_id=user.id,
            protocol_name="curve",
            query_text="manual",
            query_type="summary",
            result={"ok": True},
            duration=0.5,
            cached=False,
        )
        create_analysis(db, user.id, payload)
        end_date = datetime.now(timezone.utc) + timedelta(seconds=1)
        items, total, page, limit, offset = list_analysis_history(
            db,
            user.id,
            page=1,
            limit=10,
            end_date=end_date,
            sort="duration:invalid",
        )
        assert total == 1
        assert items[0].protocol_name == "curve"
        assert page == 1 and limit == 10 and offset == 0


def test_favorite_delete_not_found():
    _clear_db()
    user = _create_user(telegram_id=11002)
    with SessionLocal() as db:
        with pytest.raises(NotFoundError):
            delete_favorite(db, user.id, favorite_id=9999)


def test_watchlist_not_found_and_empty_batch():
    _clear_db()
    user = _create_user(telegram_id=11003)
    with SessionLocal() as db:
        with pytest.raises(NotFoundError):
            update_watchlist(db, user.id, watchlist_id=1, is_active=True)
        with pytest.raises(ValidationError):
            batch_update_watchlist_active(db, user.id, [], is_active=False)


def test_user_stats_settings_and_soft_delete():
    _clear_db()
    user = _create_user(telegram_id=11004)
    with SessionLocal() as db:
        db.add(
            AnalysisHistory(
                user_id=user.id,
                protocol_name="aave",
                query_text="one",
                result={"ok": True},
                duration=1.0,
            )
        )
        db.add(Favorite(user_id=user.id, protocol_name="maker"))
        db.add(Watchlist(user_id=user.id, protocol_name="uni", condition_type="tvl", threshold=1.0))
        db.add(SessionModel(user_id=user.id, token="tok", expires_at=datetime.now(timezone.utc)))
        db.commit()

        stats = get_user_stats(user.id, db)
        assert stats.analysis_count == 1
        assert stats.favorite_count == 1
        assert stats.watchlist_count == 1

        merged = update_user_settings(
            user.id,
            UserSettings(theme="dark", notifications={"push": False}),
            db,
        )
        assert merged["theme"] == "dark"
        assert merged["notifications"]["email"] is True
        assert merged["notifications"]["push"] is False

        soft_delete_user(user.id, db)
        refreshed = db.get(User, user.id)
        assert refreshed.deleted_at is not None
        assert db.query(SessionModel).filter_by(user_id=user.id).count() == 0
