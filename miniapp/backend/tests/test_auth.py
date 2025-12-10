import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import pytest
import jwt

from auth import AUTH_WINDOW_SECONDS, verify_telegram_webapp_data
from core.exceptions import AuthError, NotFoundError, ValidationError
from core.jwt import create_access_token, create_refresh_token, verify_token


def _build_init_data(bot_token: str, user_payload: dict, auth_date: int) -> str:
    params = {
        "query_id": "test_query",
        "user": json.dumps(user_payload),
        "auth_date": str(auth_date),
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


def test_verify_telegram_webapp_data_valid_and_replay():
    now = int(time.time())
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    user_payload = {"id": 123, "username": "alice"}
    init_data = _build_init_data(bot_token, user_payload, now)
    cache: dict[str, int] = {}

    parsed = verify_telegram_webapp_data(init_data, bot_token, now=now, replay_cache=cache)
    assert parsed is not None
    assert parsed["user"]["id"] == 123

    # replay should be blocked
    assert verify_telegram_webapp_data(init_data, bot_token, now=now + 1, replay_cache=cache) is None


def test_verify_telegram_webapp_data_invalid_hash_and_expiry():
    now = int(time.time())
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    user_payload = {"id": 456}

    # wrong secret produces invalid hash
    tampered = _build_init_data("wrong", user_payload, now)
    assert verify_telegram_webapp_data(tampered, bot_token, now=now) is None

    # expired auth_date
    expired = _build_init_data(bot_token, user_payload, now - AUTH_WINDOW_SECONDS - 10)
    assert verify_telegram_webapp_data(expired, bot_token, now=now) is None


def test_verify_telegram_webapp_data_missing_and_malformed():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    # Missing bot token path
    assert verify_telegram_webapp_data("anything", "", now=int(time.time())) is None

    now = int(time.time())
    cache: dict[str, int] = {"stale": now - AUTH_WINDOW_SECONDS - 1}
    params = {
        "query_id": "malformed",
        "user": "not-json",
        "auth_date": str(now),
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    init_data = urlencode(params)
    assert "stale" in cache  # ensure pruning path exercised
    assert verify_telegram_webapp_data(init_data, bot_token, now=now, replay_cache=cache) is None
    assert "stale" not in cache


def test_verify_telegram_webapp_data_missing_fields():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    now = int(time.time())
    user_payload = {"id": 2020, "username": "missing_fields"}
    params_auth_missing = {"user": json.dumps(user_payload)}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params_auth_missing.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    params_auth_missing["hash"] = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()
    missing_auth_date = urlencode(params_auth_missing)
    assert verify_telegram_webapp_data(missing_auth_date, bot_token, now=now) is None

    params = {"query_id": "no_user", "auth_date": str(now)}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    init_data = urlencode(params)
    assert verify_telegram_webapp_data(init_data, bot_token, now=now) is None


def test_jwt_create_and_verify_round_trip():
    access_token, _ = create_access_token(user_id=1, session_id="sid-1", username="alice")
    refresh_token, _ = create_refresh_token(user_id=1, session_id="sid-1")

    access_payload = verify_token(access_token, expected_type="access")
    assert access_payload["sub"] == 1
    assert access_payload["session_id"] == "sid-1"
    assert access_payload["type"] == "access"

    refresh_payload = verify_token(refresh_token, expected_type="refresh")
    assert refresh_payload["type"] == "refresh"


def test_verify_token_expired():
    token, _ = create_access_token(user_id=1, session_id="sid-2", expires_minutes=-1)
    with pytest.raises(AuthError):
        verify_token(token, expected_type="access")


def test_exception_classes_messages():
    nf = NotFoundError("Thing", 10)
    assert nf.status_code == 404
    assert "Thing" in nf.message
    ve = ValidationError("field", "problem")
    assert ve.status_code == 422
    assert "field" in ve.message


def test_auth_endpoints_flow(client):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    now = int(time.time())
    user_payload = {"id": 999, "username": "flow_user", "first_name": "Flow"}
    init_data = _build_init_data(bot_token, user_payload, now)

    login_resp = client.post("/api/auth/telegram", json={"initData": init_data})
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["error"] is None
    data = body["data"]
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    me_resp = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_resp.status_code == 200
    me_body = me_resp.json()
    assert me_body["data"]["telegram_id"] == user_payload["id"]

    refresh_resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_resp.status_code == 200
    new_access = refresh_resp.json()["data"]["access_token"]
    assert new_access != access_token

    logout_resp = client.post(
        "/api/auth/logout", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert logout_resp.status_code == 200

    # After logout, access should fail
    failed_me = client.get(
        "/api/auth/me", headers={"Authorization": f"Bearer {new_access}"}
    )
    assert failed_me.status_code == 401
    assert failed_me.json()["error"]["code"] == "AuthError"

    # Refresh should also be rejected once session is removed
    refresh_again = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert refresh_again.status_code == 401


def test_auth_route_invalid_payload(client):
    resp = client.post("/api/auth/telegram", json={"initData": "bad"})
    assert resp.status_code == 401
    payload = resp.json()
    assert payload["data"] is None
    assert payload["error"]["code"] == "AuthError"


def test_telegram_missing_user_id(client):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    now = int(time.time())
    user_payload = {"username": "no_id"}
    params = {
        "query_id": "noid",
        "user": json.dumps(user_payload),
        "auth_date": str(now),
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    init_data = urlencode(params)

    resp = client.post("/api/auth/telegram", json={"initData": init_data})
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "ValidationError"


def test_refresh_invalid_session_and_revoked(client):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    now = int(time.time())
    user_payload = {"id": 1010, "username": "refresh_user"}
    init_data = _build_init_data(bot_token, user_payload, now)

    login = client.post("/api/auth/telegram", json={"initData": init_data}).json()["data"]
    refresh_token = login["refresh_token"]

    # Tamper session id in token to force invalid UUID
    bad_refresh = jwt.encode(
        {"sub": user_payload["id"], "session_id": "not-a-uuid", "type": "refresh"},
        os.getenv("JWT_SECRET", "test_secret"),
        algorithm="HS256",
    )
    bad_resp = client.post("/api/auth/refresh", json={"refresh_token": bad_refresh})
    assert bad_resp.status_code == 401

    # Mark session revoked by altering stored token
    from db import SessionLocal
    from models import Session as SessionModel

    with SessionLocal() as db:
        session = db.query(SessionModel).filter_by(token=refresh_token).first()
        session.token = "revoked"
        db.commit()

    revoked_resp = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert revoked_resp.status_code == 401
    assert revoked_resp.json()["error"]["code"] == "AuthError"


def test_logout_missing_header(client):
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 401


def test_refresh_missing_fields_and_user_removed(client):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    now = int(time.time())
    user_payload = {"id": 2021, "username": "gone_user"}
    init_data = _build_init_data(bot_token, user_payload, now)

    login = client.post("/api/auth/telegram", json={"initData": init_data}).json()["data"]
    refresh_token = login["refresh_token"]

    missing_fields = jwt.encode(
        {"type": "refresh"}, os.getenv("JWT_SECRET", "test_secret"), algorithm="HS256"
    )
    resp_missing = client.post("/api/auth/refresh", json={"refresh_token": missing_fields})
    assert resp_missing.status_code == 401

    # Remove user to hit not-found path
    from db import SessionLocal
    from models import Session as SessionModel, User

    with SessionLocal() as db:
        session = db.query(SessionModel).filter_by(token=refresh_token).first()
        user = db.get(User, session.user_id)
        db.delete(user)
        db.commit()

    resp_user_missing = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    assert resp_user_missing.status_code == 401


def test_repeat_login_updates_user(client):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    now = int(time.time())
    user_payload = {"id": 3030, "username": "first"}
    init_data = _build_init_data(bot_token, user_payload, now)
    client.post("/api/auth/telegram", json={"initData": init_data})

    updated_payload = {"id": 3030, "username": "second", "first_name": "Updated"}
    updated_init = _build_init_data(bot_token, updated_payload, now + 1)
    second = client.post("/api/auth/telegram", json={"initData": updated_init})
    assert second.status_code == 200
    assert second.json()["data"]["user"]["username"] == "second"
