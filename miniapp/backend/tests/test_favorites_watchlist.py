import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import pytest

from db import SessionLocal
from models import AnalysisHistory, Favorite, Session as SessionModel, User, Watchlist


def _build_init_data(bot_token: str, user_payload: dict, auth_date: int) -> str:
    params = {
        "query_id": "fav_watch",
        "user": json.dumps(user_payload),
        "auth_date": str(auth_date),
    }
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(params.items()))
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    params["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(params)


def _login(client, telegram_id: int, username: str) -> tuple[dict, int]:
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "test_bot_token")
    now = int(time.time())
    init_data = _build_init_data(bot_token, {"id": telegram_id, "username": username}, now)
    resp = client.post("/api/auth/telegram", json={"initData": init_data})
    assert resp.status_code == 200
    data = resp.json()["data"]
    return {"Authorization": f"Bearer {data['access_token']}"}, data["user"]["id"]


def _clear_db():
    with SessionLocal() as db:
        for model in (AnalysisHistory, Favorite, Watchlist, SessionModel, User):
            db.query(model).delete()
        db.commit()


def test_favorites_dedup_and_batch_operations(client):
    _clear_db()
    headers, _user_id = _login(client, telegram_id=801, username="fav_user")

    fav1 = client.post(
        "/api/favorites",
        headers=headers,
        json={"protocol_name": "aave", "protocol_type": "ethereum"},
    )
    assert fav1.status_code == 200
    fav1_id = fav1.json()["data"]["id"]

    duplicate = client.post(
        "/api/favorites",
        headers=headers,
        json={"protocol_name": "aave", "protocol_type": "ethereum"},
    )
    assert duplicate.status_code == 422
    assert duplicate.json()["error"]["code"] == "ValidationError"

    fav2 = client.post(
        "/api/favorites",
        headers=headers,
        json={"protocol_name": "compound", "protocol_type": "polygon"},
    ).json()["data"]["id"]
    fav3 = client.post(
        "/api/favorites",
        headers=headers,
        json={"protocol_name": "maker", "protocol_type": "ethereum"},
    ).json()["data"]["id"]

    filtered = client.get("/api/favorites?chain=ethereum", headers=headers)
    assert filtered.status_code == 200
    names = {item["protocol_name"] for item in filtered.json()["data"]}
    assert names == {"aave", "maker"}

    empty_batch = client.request("DELETE", "/api/favorites/batch", headers=headers, json={"ids": []})
    assert empty_batch.status_code == 422

    batch = client.request(
        "DELETE",
        "/api/favorites/batch",
        headers=headers,
        json={"ids": [fav1_id, fav3, 9999]},
    )
    assert batch.status_code == 200
    data = batch.json()["data"]
    assert data["deleted"] == 2
    assert data["missing"] == 1

    remaining = client.get("/api/favorites", headers=headers).json()["data"]
    assert [item["id"] for item in remaining] == [fav2]


def test_watchlist_crud_and_batch(client):
    _clear_db()
    headers, _ = _login(client, telegram_id=901, username="watch_user")

    first = client.post(
        "/api/watchlist",
        headers=headers,
        json={
            "protocol_name": "aave",
            "condition_type": "tvl_drop",
            "threshold": 10.0,
            "is_active": True,
            "alert_message": "watch",
        },
    )
    assert first.status_code == 200
    first_id = first.json()["data"]["id"]

    second = client.post(
        "/api/watchlist",
        headers=headers,
        json={
            "protocol_name": "compound",
            "condition_type": "apy_rise",
            "threshold": 2.5,
            "is_active": False,
        },
    )
    assert second.status_code == 200
    second_id = second.json()["data"]["id"]

    duplicate = client.post(
        "/api/watchlist",
        headers=headers,
        json={
            "protocol_name": "aave",
            "condition_type": "tvl_drop",
            "threshold": 5.0,
        },
    )
    assert duplicate.status_code == 422

    active_only = client.get("/api/watchlist?active=true", headers=headers)
    assert active_only.status_code == 200
    assert len(active_only.json()["data"]) == 1

    updated = client.patch(
        f"/api/watchlist/{first_id}",
        headers=headers,
        json={"threshold": 15.0, "is_active": False, "alert_message": "updated"},
    )
    assert updated.status_code == 200
    updated_body = updated.json()["data"]
    assert updated_body["threshold"] == 15.0
    assert updated_body["is_active"] is False
    assert updated_body["alert_message"] == "updated"

    no_fields = client.patch(f"/api/watchlist/{first_id}", headers=headers, json={})
    assert no_fields.status_code == 422

    batch = client.patch(
        "/api/watchlist/batch",
        headers=headers,
        json={"ids": [first_id, second_id, 9999], "is_active": True},
    )
    assert batch.status_code == 200
    batch_body = batch.json()["data"]
    assert batch_body["updated"] == 2
    assert batch_body["missing"] == 1

    deleted = client.delete(f"/api/watchlist/{first_id}", headers=headers)
    assert deleted.status_code == 200

    # Isolation for deletes
    other_headers, _ = _login(client, telegram_id=902, username="watch_other")
    forbidden = client.delete(f"/api/watchlist/{second_id}", headers=other_headers)
    assert forbidden.status_code == 404

    remaining = client.get("/api/watchlist", headers=headers).json()["data"]
    assert len(remaining) == 1
