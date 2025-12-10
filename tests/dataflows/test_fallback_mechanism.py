import sys
from pathlib import Path

import pytest
import requests

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import defiagents.dataflows.interface as interface  # noqa: E402
from defiagents.dataflows.defi.messari import (  # noqa: E402
    MessariNotFoundError,
    MessariRateLimitError,
)
from defiagents.dataflows.interface import (  # noqa: E402
    AllSourcesFailedError,
    DataSourceType,
)


def test_primary_source_success(monkeypatch):
    calls = []

    def fake_call(source, protocol, method, **kwargs):
        calls.append(source)
        return 123.0

    monkeypatch.setattr(interface, "_call_source_method", fake_call)
    result = interface.get_data_with_fallback(
        "aave-v3", "get_protocol_tvl", [DataSourceType.MESSARI, DataSourceType.DEFILLAMA]
    )

    assert result == pytest.approx(123.0)
    assert calls == [DataSourceType.MESSARI]


def test_fallback_404_to_defillama(monkeypatch):
    calls = []

    def fake_call(source, protocol, method, **kwargs):
        calls.append(source)
        if source == DataSourceType.MESSARI:
            raise MessariNotFoundError("not found")
        return {"tvl": 987.0}

    monkeypatch.setattr(interface, "_call_source_method", fake_call)
    result = interface.get_data_with_fallback(
        "compound-v3", "get_protocol_tvl", [DataSourceType.MESSARI, DataSourceType.DEFILLAMA]
    )

    assert result == pytest.approx(987.0)
    assert calls == [DataSourceType.MESSARI, DataSourceType.DEFILLAMA]


def test_fallback_429_to_thegraph(monkeypatch):
    sequence = iter(
        [
            MessariRateLimitError("rate limit"),
            {"financialsDailySnapshots": [{"totalValueLockedUSD": "10"}, {"totalValueLockedUSD": "20"}]},
        ]
    )

    def fake_call(source, protocol, method, **kwargs):
        value = next(sequence)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(interface, "_call_source_method", fake_call)
    result = interface.get_data_with_fallback(
        "curve",
        "get_protocol_tvl",
        [DataSourceType.MESSARI, DataSourceType.THE_GRAPH],
    )

    assert result == pytest.approx(20.0)


def test_network_retry_success(monkeypatch):
    attempts = {"count": 0}

    def fake_call(source, protocol, method, **kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise requests.Timeout("timeout")
        return 55.0

    monkeypatch.setattr(interface, "_call_source_method", fake_call)
    result = interface.get_data_with_fallback(
        "lido", "get_protocol_tvl", [DataSourceType.MESSARI]
    )

    assert result == pytest.approx(55.0)
    assert attempts["count"] == 2  # 一次失败 + 一次重试


def test_all_sources_fail(monkeypatch):
    def fake_call(source, protocol, method, **kwargs):
        raise RuntimeError(f"{source.value} boom")

    monkeypatch.setattr(interface, "_call_source_method", fake_call)

    with pytest.raises(AllSourcesFailedError) as exc:
        interface.get_data_with_fallback(
            "unknown",
            "get_protocol_tvl",
            [DataSourceType.MESSARI, DataSourceType.DEFILLAMA],
        )

    message = str(exc.value).lower()
    assert "messari" in message
    assert "defillama" in message


def test_data_format_conversion(monkeypatch):
    def fake_call(source, protocol, method, **kwargs):
        return {"financialsDailySnapshots": [{"totalValueLockedUSD": "1"}, {"totalValueLockedUSD": "2"}]}

    monkeypatch.setattr(interface, "_call_source_method", fake_call)
    result = interface.get_data_with_fallback(
        "aave-v3", "get_protocol_tvl", [DataSourceType.THE_GRAPH]
    )
    assert result == pytest.approx(2.0)


def test_custom_priority(monkeypatch):
    calls = []

    def fake_call(source, protocol, method, **kwargs):
        calls.append(source)
        if source == DataSourceType.DEFILLAMA:
            return 777.0
        raise RuntimeError("should not reach")

    monkeypatch.setattr(interface, "_call_source_method", fake_call)
    result = interface.get_data_with_fallback(
        "balancer", "get_protocol_tvl", [DataSourceType.DEFILLAMA, DataSourceType.MESSARI]
    )

    assert result == pytest.approx(777.0)
    assert calls == [DataSourceType.DEFILLAMA]
