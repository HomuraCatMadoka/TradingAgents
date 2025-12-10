from uuid import uuid4

from core.jwt import create_access_token, create_refresh_token, utcnow
from db import SessionLocal
from models import AnalysisHistory, Favorite, Session as SessionModel, User, Watchlist


def _create_user_and_tokens(settings: dict | None = None) -> tuple[User, str, str]:
    with SessionLocal() as db:
        user = User(
            telegram_id=uuid4().int % 10_000_000,
            username="testuser",
            settings=settings or {},
            last_active=utcnow(),
        )
        db.add(user)
        db.flush()

        session_id = uuid4()
        refresh_token, refresh_exp = create_refresh_token(user.id, str(session_id))
        session = SessionModel(id=session_id, user_id=user.id, token=refresh_token, expires_at=refresh_exp)
        db.add(session)
        db.commit()

        access_token, _ = create_access_token(user.id, str(session.id), user.username)
        return user, access_token, refresh_token


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_get_profile(client):
    user, access_token, _ = _create_user_and_tokens()
    resp = client.get("/api/users/me", headers=_auth_header(access_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["error"] is None
    assert body["data"]["id"] == user.id
    assert body["data"]["username"] == "testuser"


def test_update_profile_fields(client):
    user, access_token, _ = _create_user_and_tokens()
    resp = client.patch(
        "/api/users/me",
        headers=_auth_header(access_token),
        json={
            "username": "updated",
            "avatar_url": "https://example.com/avatar.png",
            "bio": "hello world",
            "language_code": "en",
        },
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["username"] == "updated"
    assert data["avatar_url"] == "https://example.com/avatar.png"
    assert data["bio"] == "hello world"
    assert data["language_code"] == "en"


def test_settings_merge(client):
    initial_settings = {"theme": "dark", "notifications": {"email": True, "sms": False}}
    user, access_token, _ = _create_user_and_tokens(initial_settings)

    resp = client.patch(
        "/api/users/me/settings",
        headers=_auth_header(access_token),
        json={"language": "en", "notifications": {"push": True}},
    )
    assert resp.status_code == 200
    merged = resp.json()["data"]
    assert merged["theme"] == "dark"
    assert merged["language"] == "en"
    assert merged["notifications"]["email"] is True
    assert merged["notifications"]["sms"] is False
    assert merged["notifications"]["push"] is True


def test_settings_validation(client):
    _, access_token, _ = _create_user_and_tokens()
    resp = client.patch(
        "/api/users/me/settings",
        headers=_auth_header(access_token),
        json={"theme": "blue"},
    )
    assert resp.status_code == 422


def test_get_stats(client):
    user, access_token, _ = _create_user_and_tokens()
    with SessionLocal() as db:
        db.add_all(
            [
                AnalysisHistory(
                    user_id=user.id,
                    protocol_name="aave",
                    query_text="q1",
                    query_type="type",
                    result={},
                    duration=1.0,
                ),
                AnalysisHistory(
                    user_id=user.id,
                    protocol_name="uni",
                    query_text="q2",
                    query_type="type",
                    result={},
                    duration=2.0,
                ),
            ]
        )
        db.add(Favorite(user_id=user.id, protocol_name="aave", protocol_type="defi"))
        db.add(Watchlist(user_id=user.id, protocol_name="eth", alert_conditions={"t": 1}))
        db.commit()

    resp = client.get("/api/users/me/stats", headers=_auth_header(access_token))
    assert resp.status_code == 200
    stats = resp.json()["data"]
    assert stats["analysis_count"] == 2
    assert stats["favorite_count"] == 1
    assert stats["watchlist_count"] == 1
    assert stats["last_analysis_at"] is not None


def test_soft_delete_blocks_access(client):
    user, access_token, _ = _create_user_and_tokens()

    delete_resp = client.delete("/api/users/me", headers=_auth_header(access_token))
    assert delete_resp.status_code == 200

    follow_up = client.get("/api/users/me", headers=_auth_header(access_token))
    assert follow_up.status_code == 401
    assert follow_up.json()["error"]["code"] == "AuthError"

    with SessionLocal() as db:
        db_user = db.get(User, user.id)
        assert db_user.deleted_at is not None
        assert db.query(SessionModel).filter(SessionModel.user_id == user.id).count() == 0


def test_requires_auth(client):
    resp = client.get("/api/users/me")
    assert resp.status_code == 401
