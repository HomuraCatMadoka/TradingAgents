import os
import sys
import time

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from defiagents.security.protocol_whitelist import ProtocolWhitelist


@pytest.fixture(autouse=True)
def clear_cache():
    ProtocolWhitelist.clear_cache()
    yield
    ProtocolWhitelist.clear_cache()


def _make_whitelist(cache_ttl: int = 5) -> ProtocolWhitelist:
    return ProtocolWhitelist(cache_ttl=cache_ttl)


def test_blue_chip_protocol_trusted(monkeypatch):
    wl = _make_whitelist()
    now = time.time()

    def fake_llama(slug):
        assert slug == "aave-v3"
        return {"tvl": 150_000_000, "audit_count": 3, "listedAt": now - 200 * 86400}

    monkeypatch.setattr(wl, "_defillama_get_protocol", fake_llama)
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})
    monkeypatch.setattr(wl, "_graph_query", lambda subgraph, query: {"data": {"ok": True}})

    result = wl.check("aave-v3")

    assert result["status"] == "trusted"
    assert result["reason"] == "hardcoded whitelist"
    assert result["metrics"]["on_hardcoded_list"] is True
    assert result["data_sources"] == []


def test_unverified_when_only_one_rule_passes(monkeypatch):
    wl = _make_whitelist()

    def fake_llama(slug):
        return {"tvl": 50_000_000, "audit_count": 2, "listedAt": time.time() - 90 * 86400}

    monkeypatch.setattr(wl, "_defillama_get_protocol", fake_llama)
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})
    monkeypatch.setattr(wl, "_graph_query", lambda subgraph, query: {})

    result = wl.check("emerging-protocol")

    assert result["status"] == "unverified"
    assert result["metrics"]["audit_count"] == 2
    assert result["metrics"]["age_days"] >= 89
    assert not wl.is_trusted("emerging-protocol")


def test_suspicious_when_low_tvl(monkeypatch):
    wl = _make_whitelist()

    monkeypatch.setattr(
        wl,
        "_defillama_get_protocol",
        lambda slug: {"tvl": 5_000_000, "audit_count": 5, "listedAt": time.time() - 400 * 86400},
    )
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})
    monkeypatch.setattr(wl, "_graph_query", lambda subgraph, query: {})

    result = wl.check("lowcap")

    assert result["status"] == "suspicious"
    assert result["metrics"]["tvl"] == 5_000_000
    assert "defillama" in result["data_sources"]


def test_hardcoded_whitelist_short_circuits(monkeypatch):
    wl = _make_whitelist()

    called = {"count": 0}

    def boom(*args, **kwargs):
        called["count"] += 1
        raise AssertionError("should not be called for hardcoded whitelist")

    monkeypatch.setattr(wl, "_defillama_get_protocol", boom)

    result = wl.check("uniswap-v3")

    assert result["status"] == "trusted"
    assert result["reason"] == "hardcoded whitelist"
    assert result["data_sources"] == []
    assert called["count"] == 0


def test_fallback_to_coingecko_when_defillama_fails(monkeypatch):
    wl = _make_whitelist()

    monkeypatch.setattr(wl, "_defillama_get_protocol", lambda slug: (_ for _ in ()).throw(RuntimeError("down")))
    monkeypatch.setattr(
        wl,
        "_coingecko_get_market_data",
        lambda slug: {
            "market_data": {"market_cap": {"usd": 120_000_000}},
            "audit_count": 2,
            "genesis_date": "2020-01-01",
        },
    )
    monkeypatch.setattr(wl, "_graph_query", lambda subgraph, query: {})

    result = wl.check("some-l2-dex")

    assert result["status"] == "trusted"
    assert result["metrics"]["tvl"] == 120_000_000
    assert "coingecko" in result["data_sources"]
    assert "defillama" not in result["data_sources"]


def test_all_sources_fail(monkeypatch):
    wl = _make_whitelist()

    monkeypatch.setattr(wl, "_defillama_get_protocol", lambda slug: (_ for _ in ()).throw(RuntimeError("fail")))
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: (_ for _ in ()).throw(RuntimeError("fail")))
    monkeypatch.setattr(wl, "_graph_query", lambda subgraph, query: (_ for _ in ()).throw(RuntimeError("fail")))

    result = wl.check("unknown")

    assert result["status"] == "unverified"
    assert result["data_sources"] == []
    assert "failed" in result["reason"]


def test_cache_hit_skips_duplicate_calls(monkeypatch):
    wl = _make_whitelist()
    calls = {"llama": 0}

    def fake_llama(slug):
        calls["llama"] += 1
        return {"tvl": 120_000_000, "audit_count": 2, "listedAt": time.time() - 200 * 86400}

    monkeypatch.setattr(wl, "_defillama_get_protocol", fake_llama)
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})

    first = wl.check("cache-protocol")
    second = wl.check("cache-protocol")

    assert first["status"] == second["status"]
    assert calls["llama"] == 1


def test_cache_expiry_refreshes(monkeypatch):
    wl = _make_whitelist(cache_ttl=1)
    calls = {"llama": 0}

    def fake_llama(slug):
        calls["llama"] += 1
        return {"tvl": 120_000_000, "audit_count": 2, "listedAt": time.time() - 200 * 86400}

    monkeypatch.setattr(wl, "_defillama_get_protocol", fake_llama)
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})

    wl.check("cache-refresh")
    time.sleep(1.1)
    wl.check("cache-refresh")

    assert calls["llama"] == 2


def test_protocol_alias_normalization(monkeypatch):
    wl = _make_whitelist()
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})

    result = wl.check("Aave")

    assert result["protocol_slug"] == "aave-v3"
    assert result["status"] == "trusted"


def test_timeout_handling(monkeypatch):
    wl = _make_whitelist()
    monkeypatch.setattr(wl, "DATA_SOURCE_TIMEOUT", 0.05)

    def slow_llama(slug):
        time.sleep(0.2)
        return {"tvl": 120_000_000, "audit_count": 2, "listedAt": time.time() - 200 * 86400}

    monkeypatch.setattr(wl, "_defillama_get_protocol", slow_llama)
    monkeypatch.setattr(
        wl,
        "_coingecko_get_market_data",
        lambda slug: {"market_data": {"market_cap": {"usd": 150_000_000}}, "genesis_date": "2020-01-01"},
    )

    result = wl.check("timeout-protocol")

    assert "coingecko" in result["data_sources"]
    assert "defillama" not in result["data_sources"]
    assert result["status"] in {"trusted", "unverified"}


def test_empty_input(monkeypatch):
    wl = _make_whitelist()

    result_none = wl.check(None)
    result_empty = wl.check("  ")

    assert result_none["status"] == "unverified"
    assert result_none["protocol_slug"] == ""
    assert result_empty["data_sources"] == []


def test_special_characters_normalization(monkeypatch):
    wl = _make_whitelist()

    monkeypatch.setattr(
        wl,
        "_defillama_get_protocol",
        lambda slug: {"tvl": 120_000_000, "audit_count": 2, "listedAt": time.time() - 250 * 86400},
    )
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})

    result = wl.check("Aave!!!")

    assert result["protocol_slug"] == "aave-v3"
    assert result["status"] == "trusted"


def test_custom_trusted_protocols(monkeypatch):
    wl = ProtocolWhitelist(trusted_protocols=["my-protocol"], cache_ttl=1)
    monkeypatch.setattr(wl, "_defillama_get_protocol", lambda slug: {})

    result = wl.check("my-protocol")

    assert result["status"] == "trusted"
    assert result["reason"] == "hardcoded whitelist"


def test_compact_alias_normalization(monkeypatch):
    wl = _make_whitelist()
    wl._alias_map = {"foo-bar": "mapped-slug"}

    assert wl._normalize_slug("foobar") == "mapped-slug"


def test_graph_source_included(monkeypatch):
    wl = _make_whitelist()

    monkeypatch.setattr(wl, "_get_subgraph_id", lambda slug, chain: "demo/id")
    monkeypatch.setattr(wl, "_graph_query", lambda subgraph, query: {"ok": True})
    monkeypatch.setattr(
        wl,
        "_defillama_get_protocol",
        lambda slug: {"tvl": 20_000_000, "audit_count": 0, "listedAt": time.time() - 30 * 86400},
    )
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})

    result = wl.check("graph-heavy")

    assert "the_graph" in result["data_sources"]


def test_defillama_audits_list(monkeypatch):
    wl = _make_whitelist()

    monkeypatch.setattr(
        wl,
        "_defillama_get_protocol",
        lambda slug: {"tvl": 120_000_000, "audits": [1, 2, 3], "listedAt": time.time() - 200 * 86400},
    )
    monkeypatch.setattr(wl, "_coingecko_get_market_data", lambda slug: {})

    result = wl.check("audited-protocol")

    assert result["metrics"]["audit_count"] == 3


def test_age_parsers_handle_invalid(monkeypatch):
    wl = _make_whitelist()

    assert wl._age_from_timestamp("bad") is None
    assert wl._age_from_date("bad-date") is None


def test_compute_trust_level_paths(monkeypatch):
    wl = _make_whitelist()
    metrics_whitelist = {"tvl": 0, "audit_count": 0, "age_days": 0, "on_hardcoded_list": True}
    metrics_none = {"tvl": None, "audit_count": None, "age_days": None, "on_hardcoded_list": False}

    assert wl._compute_trust_level(metrics_whitelist) == "unverified"
    assert wl._compute_trust_level(metrics_none) == "suspicious"


def test_confidence_and_reason_with_whitelist(monkeypatch):
    wl = _make_whitelist()
    metrics = {"tvl": 10_000_000, "audit_count": 2, "age_days": 200, "on_hardcoded_list": True}

    confidence = wl._compute_confidence(metrics, ["defillama", "coingecko"])
    reason = wl._build_reason("trusted", metrics)

    assert confidence == 1.0
    assert "hardcoded=true" in reason
