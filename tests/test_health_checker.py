import time

import pytest
import requests

from defiagents.dataflows.defi import health_checker as hc


@pytest.fixture(autouse=True)
def clear_cache():
    hc.clear_health_cache()
    yield
    hc.clear_health_cache()


def test_caches_within_window(monkeypatch):
    calls = {"count": 0}

    def fake_run():
        calls["count"] += 1
        return {"mock": {"source": "online", "latency": 1}}

    monkeypatch.setattr(hc, "_run_checks", fake_run)
    monkeypatch.setattr(hc, "_current_window_id", lambda now=None: 1)

    first = hc.get_health_status()
    second = hc.get_health_status()

    assert first == second
    assert calls["count"] == 1

    monkeypatch.setattr(hc, "_current_window_id", lambda now=None: 2)
    hc.get_health_status()
    assert calls["count"] == 2


def test_force_refresh_bypasses_cache(monkeypatch):
    calls = {"count": 0}

    def fake_run():
        calls["count"] += 1
        return {"mock": {"source": "online", "latency": 1}}

    monkeypatch.setattr(hc, "_run_checks", fake_run)
    hc.get_health_status(force_refresh=True)
    hc.get_health_status(force_refresh=True)

    assert calls["count"] == 2


def test_timeout_marks_offline(monkeypatch):
    monkeypatch.setattr(hc, "CHECK_TIMEOUT", 0.05)

    def slow():
        time.sleep(0.2)
        return "online"

    def fast():
        return "online"

    monkeypatch.setattr(
        hc,
        "DEFAULT_CHECKERS",
        {"slow": slow, "fast": fast},
    )

    results = hc.get_health_status(force_refresh=True)

    assert results["slow"]["source"] == "offline"
    assert results["slow"]["latency"] >= int(hc.CHECK_TIMEOUT * 1000)
    assert results["fast"]["source"] == "online"


def test_exception_results_offline(monkeypatch):
    def boom():
        raise RuntimeError("fail")

    monkeypatch.setattr(
        hc,
        "DEFAULT_CHECKERS",
        {"bad": boom},
    )

    results = hc.get_health_status(force_refresh=True)
    assert results["bad"]["source"] == "offline"


def test_defillama_and_graph_checks(monkeypatch):
    class FakeResponse:
        def __init__(self, data, status_code=200):
            self._data = data
            self.status_code = status_code

        def raise_for_status(self):
            if self.status_code >= 400:
                raise requests.HTTPError("bad response")

        def json(self):
            return self._data

    # DeFi Llama success
    monkeypatch.setattr(
        hc.requests,
        "get",
        lambda url, timeout: FakeResponse([{"id": 1}]),
    )
    assert hc._check_defillama() == "online"

    # The Graph degraded when empty
    monkeypatch.setattr(
        hc.requests,
        "post",
        lambda url, json, timeout: FakeResponse({"data": {"pools": []}}),
    )
    assert hc._check_the_graph() == "degraded"

    # The Graph online when data present
    monkeypatch.setattr(
        hc.requests,
        "post",
        lambda url, json, timeout: FakeResponse({"data": {"pools": [{"id": "1"}]}}),
    )
    assert hc._check_the_graph() == "online"


def test_coingecko_and_gemini_checks(monkeypatch):
    class FakeCG:
        def __init__(self):
            self.calls = 0

        def ping(self):
            self.calls += 1
            return {"gecko_says": "ok"}

    fake_instance = FakeCG()
    monkeypatch.setattr(hc, "CoinGeckoAPI", lambda: fake_instance)

    assert hc._check_coingecko() == "online"
    assert fake_instance.calls == 1

    # Gemini key missing
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert hc._check_gemini_configuration() == "offline"

    monkeypatch.setenv("GOOGLE_API_KEY", "secret-key")
    assert hc._check_gemini_configuration() == "online"
