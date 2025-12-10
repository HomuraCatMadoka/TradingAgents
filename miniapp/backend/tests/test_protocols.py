import importlib
import time
from datetime import timedelta
from typing import Dict
from uuid import uuid4
from unittest.mock import patch

import pytest

from core.exceptions import DataSourceError, NotFoundError, ValidationError
from core.jwt import create_access_token, utcnow
from db import SessionLocal
from models import AnalysisHistory, Session as SessionModel, User
from services.agent import AgentService
from services.defi_data import DeFiDataService
from tests.mocks import defi_mocks


@pytest.fixture
def auth_header() -> Dict[str, str]:
    db = SessionLocal()
    user = User(telegram_id=int(time.time() * 1000), username="tester")
    db.add(user)
    db.flush()
    token_value = str(uuid4())
    session_entry = SessionModel(
        user_id=user.id, token=token_value, expires_at=utcnow() + timedelta(hours=1)
    )
    db.add(session_entry)
    db.commit()
    token, _ = create_access_token(user.id, str(session_entry.id), user.username)
    db.close()
    return {"Authorization": f"Bearer {token}"}


def _install_services(defi_service: DeFiDataService, agent_service: AgentService | None = None) -> None:
    router_module = importlib.import_module("routers.protocols")
    router_module.defi_service = defi_service
    router_module.agent_service = agent_service or AgentService(session_factory=SessionLocal)

    from main import app

    for route in app.router.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint is None or endpoint.__module__ != router_module.__name__:
            continue
        endpoint.__globals__["defi_service"] = router_module.defi_service
        endpoint.__globals__["agent_service"] = router_module.agent_service


def _make_user() -> tuple[User, SessionLocal]:
    db = SessionLocal()
    user = User(telegram_id=int(time.time() * 1000), username="agent-user")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user, db


def test_requires_authentication(client):
    resp = client.get("/api/protocols")
    assert resp.status_code == 401


def test_list_protocols_filters_and_cache(client, auth_header):
    call_count = {"llama": 0}

    def fetch_protocols():
        call_count["llama"] += 1
        return defi_mocks.protocol_list()

    with patch("defiagents.dataflows.defi.defillama.get_all_protocols", side_effect=fetch_protocols):
        service = DeFiDataService(get_protocols=fetch_protocols)
        _install_services(service)

        resp = client.get("/api/protocols?search=aave&chain=ethereum&limit=2", headers=auth_header)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["count"] == 1
        assert data["protocols"][0]["slug"] == "aave-v3"
        assert call_count["llama"] == 1

        resp = client.get("/api/protocols?search=aave&chain=ethereum&limit=2", headers=auth_header)
        assert resp.status_code == 200
        assert call_count["llama"] == 1  # cached by lru_cache


def test_protocol_detail_fallback(client, auth_header):
    def primary(_slug: str):
        raise RuntimeError("defillama down")

    def fallback(slug: str):
        return defi_mocks.protocol_detail(slug, tvl=42.0)

    service = DeFiDataService(get_protocol_detail=primary, fallback_protocol_detail=fallback)
    _install_services(service)

    resp = client.get("/api/protocols/aave-v3", headers=auth_header)
    assert resp.status_code == 200
    detail = resp.json()["data"]
    assert detail["tvl"] == pytest.approx(42.0)
    assert detail["chain_tvls"]["ethereum"] == pytest.approx(21.0)


def test_protocol_history_with_period_parsing(client, auth_header):
    base_ts = 1_700_000_000
    history = [
        {"date": base_ts, "totalLiquidityUSD": 1_000_000},
        {"date": base_ts + 86_400, "totalLiquidityUSD": 1_050_000},
        {"date": base_ts + 2 * 86_400, "totalLiquidityUSD": 1_125_000},
    ]

    def detail(slug: str):
        data = defi_mocks.protocol_detail(slug)
        data["tvl"] = history
        return data

    service = DeFiDataService(get_protocol_detail=detail, now=lambda: base_ts + 3 * 86_400)
    _install_services(service)

    resp = client.get("/api/protocols/aave-v3/history?period=2d", headers=auth_header)
    assert resp.status_code == 200
    entries = resp.json()["data"]
    assert len(entries) == 2
    assert entries[0]["tvl"] == pytest.approx(1_050_000)
    assert entries[0]["timestamp"].endswith("+00:00")


def test_history_invalid_period_returns_error(client, auth_header):
    service = DeFiDataService(get_protocol_detail=lambda slug: defi_mocks.protocol_detail(slug))
    _install_services(service)

    resp = client.get("/api/protocols/aave-v3/history?period=bad", headers=auth_header)
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"]["code"] == "ValidationError"


def test_market_data_uses_price_fallback_and_cache(client, auth_header):
    calls = {"market": 0, "price": 0}

    def market_data(_: str):
        calls["market"] += 1
        raise RuntimeError("cg down")

    def price_data(_: str):
        calls["price"] += 1
        return defi_mocks.price_only()

    service = DeFiDataService(token_market_data_fn=market_data, token_price_fn=price_data)
    _install_services(service)

    resp = client.get("/api/protocols/aave/market-data", headers=auth_header)
    assert resp.status_code == 200
    payload = resp.json()["data"]
    assert payload["price"] == pytest.approx(defi_mocks.price_only()["usd"])
    assert calls["price"] == 1

    resp = client.get("/api/protocols/aave/market-data", headers=auth_header)
    assert resp.status_code == 200
    assert calls["price"] == 1  # cached


def test_pools_and_pool_detail(client, auth_header):
    pools = defi_mocks.uniswap_pools()
    pool_detail = defi_mocks.uniswap_pool_detail()

    service = DeFiDataService(
        get_protocols=lambda: defi_mocks.protocol_list(),
        get_protocol_detail=lambda slug: defi_mocks.protocol_detail(slug),
        get_uniswap_pools_fn=lambda limit=10: pools[:limit],
        get_uniswap_pool_fn=lambda pool_id: pool_detail if pool_id == "pool-1" else None,
    )
    _install_services(service)

    resp = client.get("/api/protocols/uniswap-v3/pools?limit=5", headers=auth_header)
    assert resp.status_code == 200
    pool_list = resp.json()["data"]
    assert pool_list[0]["id"] == "pool-1"
    assert pool_list[0]["tvl"] > 0

    detail_resp = client.get("/api/protocols/uniswap-v3/pools/pool-1", headers=auth_header)
    assert detail_resp.status_code == 200
    detail = detail_resp.json()["data"]
    assert detail["history"]
    assert detail["history"][0]["volume"] >= 0


def test_trigger_analysis_creates_history_record(client, auth_header):
    run_log = []

    def runner(slug: str):
        run_log.append(slug)
        return {"summary": f"analyzed {slug}"}

    service = DeFiDataService(get_protocols=lambda: defi_mocks.protocol_list(), get_protocol_detail=defi_mocks.protocol_detail)
    agent = AgentService(agent_runner=runner, session_factory=SessionLocal)
    _install_services(service, agent)

    resp = client.post("/api/protocols/aave-v3/analyze", headers=auth_header)
    assert resp.status_code == 200
    payload = resp.json()["data"]
    assert payload["status"] == "completed"
    assert run_log == ["aave-v3"]

    db = SessionLocal()
    record = db.get(AnalysisHistory, payload["record_id"])
    db.close()
    assert record is not None
    assert record.protocol_name == "aave-v3"
    assert record.result["status"] == "completed"


def test_agent_service_validation_error():
    user, db = _make_user()
    service = AgentService(session_factory=SessionLocal)
    with pytest.raises(ValidationError):
        service.trigger_analysis("", user.id, db)
    db.close()


def test_agent_service_failure_is_captured():
    user, db = _make_user()

    def explode(_slug: str):
        raise RuntimeError("boom")

    service = AgentService(agent_runner=explode, session_factory=SessionLocal)
    record_id, payload = service.trigger_analysis("aave-task", user.id, db)
    assert payload["status"] == "failed"

    record = db.get(AnalysisHistory, record_id)
    assert record is not None
    assert record.result["status"] == "failed"
    db.close()


def test_defi_data_fallback_errors():
    def fail_primary():
        raise RuntimeError("primary down")

    def fail_fallback():
        raise RuntimeError("fallback down")

    service = DeFiDataService(
        get_protocols=fail_primary,
        fallback_protocols=fail_fallback,
    )
    with pytest.raises(DataSourceError):
        service.list_protocols()


def test_defi_data_cache_and_not_found_paths():
    detail_calls = {"count": 0}

    def detail(slug: str):
        detail_calls["count"] += 1
        return defi_mocks.protocol_detail(slug)

    service = DeFiDataService(get_protocol_detail=detail)
    service.get_protocol_detail("aave-v3")
    service.get_protocol_detail("aave-v3")
    assert detail_calls["count"] == 1

    with pytest.raises(NotFoundError):
        service.get_protocol_pools("aave-v3")

    with pytest.raises(NotFoundError):
        service.get_pool_detail("compound-v3", "pid")

    missing_pool_service = DeFiDataService(
        get_protocol_detail=detail,
        get_uniswap_pool_fn=lambda pool_id: None,
    )
    with pytest.raises(NotFoundError):
        missing_pool_service.get_pool_detail("uniswap-v3", "missing")


def test_defi_data_market_and_history_errors():
    service = DeFiDataService(
        token_market_data_fn=lambda token: {},
        token_price_fn=lambda token: {},
        get_protocol_detail=lambda slug: {"tvl": []},
    )
    with pytest.raises(DataSourceError):
        service.get_market_data("token-x")
    with pytest.raises(DataSourceError):
        service.get_protocol_history("aave-v3", 1)


def test_defi_data_clear_cache_and_limit_validation():
    calls = {"count": 0}

    def fetch():
        calls["count"] += 1
        return defi_mocks.protocol_list()

    service = DeFiDataService(get_protocols=fetch)
    service.list_protocols(limit=1)
    service.list_protocols(limit=1)
    assert calls["count"] == 1
    service.clear_cache()
    service.list_protocols(limit=1)
    assert calls["count"] == 2

    with pytest.raises(ValidationError):
        service.list_protocols(limit=0)


def test_defi_data_validation_errors():
    service = DeFiDataService(get_protocol_detail=lambda slug: defi_mocks.protocol_detail(slug))
    with pytest.raises(ValidationError):
        service.get_protocol_detail("")
    with pytest.raises(ValidationError):
        service.get_protocol_history("aave-v3", 0)
    with pytest.raises(ValidationError):
        service.get_market_data("")
    with pytest.raises(ValidationError):
        service.get_protocol_pools("uniswap-v3", limit=0)

    assert DeFiDataService.parse_period(None) == 30
    assert DeFiDataService.parse_period(5) == 5
    with pytest.raises(ValidationError):
        DeFiDataService.parse_period(0)


def test_defi_data_market_error_without_fallback():
    def fail(_: str):
        raise RuntimeError("market down")

    def fail_price(_: str):
        raise RuntimeError("price down")

    service = DeFiDataService(token_market_data_fn=fail, token_price_fn=fail_price)
    with pytest.raises(DataSourceError):
        service.get_market_data("token-x")


def test_defi_data_pool_error_paths():
    def fail_pools(**kwargs):
        raise RuntimeError("graph down")

    failing_pools_service = DeFiDataService(get_uniswap_pools_fn=fail_pools)
    with pytest.raises(DataSourceError):
        failing_pools_service.get_protocol_pools("uniswap-v3")

    def fail_pool(pool_id: str):
        raise RuntimeError("boom")

    failing_pool_detail = DeFiDataService(get_uniswap_pool_fn=fail_pool)
    with pytest.raises(DataSourceError):
        failing_pool_detail.get_pool_detail("uniswap-v3", "pid")


def test_defi_data_history_skips_invalid_entries():
    history = [
        123,
        {"date": 1_700_000_000, "tvl": None},
        {"date": 1_700_000_001, "totalLiquidityUSD": 100},
    ]

    def detail(_: str):
        return {"tvl": history}

    service = DeFiDataService(get_protocol_detail=detail, now=lambda: 1_700_000_100)
    entries = service.get_protocol_history("aave-v3", 5)
    assert len(entries) == 1
    assert entries[0]["tvl"] == pytest.approx(100)


def test_defi_data_empty_detail_raises():
    service = DeFiDataService(get_protocol_detail=lambda slug: {})
    with pytest.raises(DataSourceError):
        service.get_protocol_detail("aave-v3")


def test_agent_default_runner_paths():
    class FakeInvokeAgent:
        def invoke(self, company_name: str, trade_date: str):
            return {"company": company_name, "date": trade_date}

    invoke_service = AgentService(agent_factory=lambda: FakeInvokeAgent())
    payload = invoke_service._default_runner("aave")
    assert payload["analysis"]["company"] == "aave"

    class FakePropagateAgent:
        def propagate(self, company_name: str, trade_date: str):
            return {"state": company_name}, {"signal": {"set"}}

    propagate_service = AgentService(agent_factory=lambda: FakePropagateAgent())
    payload = propagate_service._default_runner("uni")
    assert payload["analysis"]["state"] == "uni"
    assert isinstance(payload["signal"], str)  # non-serializable signal converted to string

    assert isinstance(AgentService._to_json_safe({"ok": True}), dict)
    assert isinstance(AgentService._to_json_safe({1, 2}), str)


def test_agent_closes_session_when_created():
    class DummySession:
        def __init__(self):
            self.closed = False

        def add(self, record):
            record.id = 999

        def commit(self):
            pass

        def refresh(self, record):
            pass

        def close(self):
            self.closed = True

    dummy = DummySession()
    service = AgentService(agent_runner=lambda slug: {"ok": slug}, session_factory=lambda: dummy)
    record_id, payload = service.trigger_analysis("aave", user_id=1, db=None)
    assert record_id == 999
    assert dummy.closed
    assert payload["status"] == "completed"
