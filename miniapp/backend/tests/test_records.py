import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from db import SessionLocal
from models import AnalysisHistory, Favorite, Session as SessionModel, User, Watchlist


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


def _login(client, telegram_id: int = 500, username: str = "history_user") -> tuple[dict, int]:
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


def _seed_analysis(db, user_id: int, base_time: datetime) -> list[int]:
    entries = [
        {
            "protocol_name": "aave",
            "query_type": "summary",
            "query_text": "alpha note",
            "duration": 1.1,
            "created_at": base_time - timedelta(minutes=5),
        },
        {
            "protocol_name": "aave",
            "query_type": "detail",
            "query_text": "beta note",
            "duration": 3.2,
            "created_at": base_time - timedelta(minutes=4),
        },
        {
            "protocol_name": "compound",
            "query_type": "summary",
            "query_text": "gamma",
            "duration": 2.5,
            "created_at": base_time - timedelta(minutes=3),
        },
        {
            "protocol_name": "aave",
            "query_type": "summary",
            "query_text": "delta filter",
            "duration": 4.1,
            "created_at": base_time - timedelta(minutes=1),
        },
        {
            "protocol_name": "aave",
            "query_type": "summary",
            "query_text": "epsilon filter",
            "duration": 6.0,
            "created_at": base_time,
        },
    ]
    ids: list[int] = []
    for payload in entries:
        record = AnalysisHistory(
            user_id=user_id,
            protocol_name=payload["protocol_name"],
            query_type=payload["query_type"],
            query_text=payload["query_text"],
            duration=payload["duration"],
            result={"ok": True, "q": payload["query_text"]},
            created_at=payload["created_at"],
            cached=False,
        )
        db.add(record)
        db.flush()
        ids.append(record.id)
    db.commit()
    return ids


def test_analysis_history_pagination_filters_and_sort(client):
    _clear_db()
    headers, user_id = _login(client, telegram_id=701, username="records")
    base_time = datetime.now(timezone.utc)
    with SessionLocal() as db:
        _seed_analysis(db, user_id, base_time)
        db.commit()

    first_page = client.get("/api/analysis-history?page=0&limit=0", headers=headers)
    assert first_page.status_code == 200
    payload = first_page.json()["data"]
    assert payload["pagination"]["limit"] == 20
    assert payload["pagination"]["offset"] == 0
    assert payload["pagination"]["total"] == 5

    filtered = client.get(
        "/api/analysis-history",
        headers=headers,
        params={
            "page": 1,
            "limit": 2,
            "protocol": "aave",
            "query_type": "summary",
            "sort": "duration:asc",
        },
    )
    assert filtered.status_code == 200
    body = filtered.json()["data"]
    durations = [item["duration"] for item in body["data"]]
    assert durations == [1.1, 4.1]
    assert body["pagination"]["has_more"] is True

    second_page = client.get(
        "/api/analysis-history",
        headers=headers,
        params={
            "page": 2,
            "limit": 2,
            "protocol": "aave",
            "query_type": "summary",
            "sort": "duration:asc",
        },
    )
    second_data = second_page.json()["data"]
    assert [item["duration"] for item in second_data["data"]] == [6.0]
    assert second_data["pagination"]["has_more"] is False

    date_filtered = client.get(
        "/api/analysis-history",
        headers=headers,
        params={
            "page": 1,
            "limit": 10,
            "start_date": (base_time - timedelta(minutes=2)).isoformat(),
        },
    )
    date_items = date_filtered.json()["data"]["data"]
    assert len(date_items) == 2

    search_filtered = client.get(
        "/api/analysis-history",
        headers=headers,
        params={"search": "delta", "limit": 10},
    )
    assert search_filtered.status_code == 200
    search_items = search_filtered.json()["data"]["data"]
    assert len(search_items) == 1
    assert search_items[0]["query_text"] == "delta filter"


def test_analysis_history_get_and_delete(client):
    _clear_db()
    headers, user_id = _login(client, telegram_id=702, username="records2")
    base_time = datetime.now(timezone.utc)
    with SessionLocal() as db:
        record_ids = _seed_analysis(db, user_id, base_time)
        target_id = record_ids[0]

    detail = client.get(f"/api/analysis-history/{target_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["data"]["id"] == target_id

    deleted = client.delete(f"/api/analysis-history/{target_id}", headers=headers)
    assert deleted.status_code == 200
    assert deleted.json()["data"]["message"] == "deleted"

    missing = client.get(f"/api/analysis-history/{target_id}", headers=headers)
    assert missing.status_code == 404

    # Ensure isolation between users
    other_headers, other_id = _login(client, telegram_id=703, username="other")
    forbidden = client.get(f"/api/analysis-history/{record_ids[1]}", headers=other_headers)
    assert forbidden.status_code == 404
