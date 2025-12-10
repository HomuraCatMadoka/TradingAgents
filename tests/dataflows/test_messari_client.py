import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
import requests

from defiagents.dataflows.defi.messari import (
    MessariAPIError,
    MessariClient,
    MessariNotFoundError,
    MessariRateLimitError,
)


class MockResponse:
    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] | None = None):
        self.status_code = status_code
        self._json_data = json_data or {}
        self.ok = 200 <= status_code < 300

    def json(self):
        if isinstance(self._json_data, Exception):
            raise self._json_data
        return self._json_data


def _write_deployment(tmp_path, content: Dict[str, Any]):
    path = tmp_path / "deployment.json"
    path.write_text(json.dumps(content), encoding="utf-8")
    return str(path)


def test_get_protocol_tvl_with_cache(monkeypatch, tmp_path):
    deployment = {
        "uniswap-v3": {
            "schema": "dex-amm",
            "deployments": {
                "uniswap-v3-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy-eth"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    call_count = {"count": 0}

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        call_count["count"] += 1
        return MockResponse(
            status_code=200,
            json_data={"data": {"dexAmmProtocol": {"totalValueLockedUSD": 123.45}}},
        )

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)

    first = client.get_protocol_tvl("uniswap-v3", "ethereum")
    second = client.get_protocol_tvl("uniswap-v3", "ethereum")

    assert first == pytest.approx(123.45)
    assert second == pytest.approx(123.45)
    assert call_count["count"] == 1  # 缓存命中


def test_get_lending_markets(monkeypatch, tmp_path):
    deployment = {
        "aave-v3": {
            "schema": "lending",
            "deployments": {
                "aave-v3-arbitrum": {
                    "network": "arbitrum",
                    "services": {"decentralized-network": {"query-id": "deploy-arb"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return MockResponse(
            status_code=200,
            json_data={
                "data": {
                    "lendingProtocol": {
                        "markets": [
                            {
                                "id": "m1",
                                "name": "USDC",
                                "totalValueLockedUSD": "10",
                                "totalDepositBalanceUSD": "8",
                                "totalBorrowBalanceUSD": "5",
                                "inputToken": {"id": "t1", "symbol": "USDC", "name": "USD Coin", "decimals": 6},
                                "outputToken": None,
                                "rewardTokens": [{"token": {"id": "r1", "symbol": "AAVE", "name": "Aave", "decimals": 18}}],
                                "rates": [{"side": "LENDER", "rate": "0.01", "type": "VARIABLE"}],
                            }
                        ]
                    }
                }
            },
        )

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)
    markets = client.get_lending_markets("aave-v3", "arbitrum")

    assert len(markets) == 1
    market = markets[0]
    assert market["id"] == "m1"
    assert market["tvl_usd"] == pytest.approx(10.0)
    assert market["input_token"]["symbol"] == "USDC"
    assert market["rates"][0]["rate"] == pytest.approx(0.01)


def test_get_dex_pools_schema_mismatch(monkeypatch, tmp_path):
    deployment = {
        "aave-v3": {
            "schema": "lending",
            "deployments": {
                "aave-v3-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy-eth"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)
    client = MessariClient(deployment_json_path=path)

    with pytest.raises(MessariNotFoundError):
        client.get_dex_pools("aave-v3", "ethereum")


def test_rate_limit_error(monkeypatch, tmp_path):
    deployment = {
        "curve": {
            "schema": "dex-amm",
            "deployments": {
                "curve-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy-curve"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return MockResponse(status_code=429, json_data={})

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)

    with pytest.raises(MessariRateLimitError):
        client.get_protocol_tvl("curve", "ethereum")


def test_protocol_not_found(tmp_path):
    deployment = {}
    path = _write_deployment(tmp_path, deployment)
    client = MessariClient(deployment_json_path=path)

    with pytest.raises(MessariNotFoundError):
        client.get_protocol_tvl("unknown", "ethereum")


def test_graphql_errors_raise(monkeypatch, tmp_path):
    deployment = {
        "uniswap-v3": {
            "schema": "dex-amm",
            "deployments": {
                "uniswap-v3-optimism": {
                    "network": "optimism",
                    "services": {"decentralized-network": {"query-id": "deploy-opt"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return MockResponse(status_code=200, json_data={"errors": [{"message": "boom"}]})

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)

    with pytest.raises(MessariAPIError):
        client.get_protocol_metrics("uniswap-v3", "optimism")


def test_lending_markets_schema_mismatch(monkeypatch, tmp_path):
    deployment = {
        "uniswap-v3": {
            "schema": "dex-amm",
            "deployments": {
                "uniswap-v3-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)
    client = MessariClient(deployment_json_path=path)
    with pytest.raises(MessariNotFoundError):
        client.get_lending_markets("uniswap-v3", "ethereum")


def test_cache_expiry_branch(monkeypatch, tmp_path):
    deployment = {
        "uniswap-v3": {
            "schema": "dex-amm",
            "deployments": {
                "uniswap-v3-polygon": {
                    "network": "matic",
                    "services": {"decentralized-network": {"query-id": "deploy-poly"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    call_count = {"count": 0}

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        call_count["count"] += 1
        return MockResponse(json_data={"data": {"dexAmmProtocol": {"totalValueLockedUSD": 50}}})

    monkeypatch.setattr("requests.post", fake_post)

    client = MessariClient(deployment_json_path=path, cache_ttl=1)
    client.get_protocol_tvl("uniswap-v3", "polygon")

    # 将缓存时间戳回写为过期值
    cache_key = "messari:uniswap-v3:polygon:tvl"
    client._cache[cache_key] = (client._cache[cache_key][0], 0)  # type: ignore[attr-defined]
    monkeypatch.setattr("defiagents.dataflows.defi.messari.time.time", lambda: 10)

    client.get_protocol_tvl("uniswap-v3", "polygon")  # 第二次应触发过期分支

    assert call_count["count"] == 2


def test_dex_pools_success_and_cache(monkeypatch, tmp_path):
    deployment = {
        "uniswap-v3": {
            "schema": "dex-amm",
            "deployments": {
                "uniswap-v3-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)
    call_count = {"count": 0}

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        call_count["count"] += 1
        return MockResponse(
            json_data={
                "data": {
                    "dexAmmProtocol": {
                        "pools": [
                            {
                                "id": "p1",
                                "name": "USDC/ETH",
                                "totalValueLockedUSD": 1,
                                "cumulativeVolumeUSD": 2,
                                "feesUSD": 3,
                                "inputTokens": [{"id": "t0", "symbol": "USDC", "name": "USD Coin", "decimals": 6}],
                                "rewardTokens": [{"token": {"id": "r1", "symbol": "UNI", "name": "Uniswap", "decimals": 18}}],
                            }
                        ]
                    }
                }
            }
        )

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)
    pools_first = client.get_dex_pools("uniswap-v3", "ethereum")
    pools_second = client.get_dex_pools("uniswap-v3", "ethereum")

    assert pools_first[0]["id"] == "p1"
    assert pools_second == pools_first  # 缓存命中
    assert call_count["count"] == 1


def test_api_key_header_and_metrics(monkeypatch, tmp_path):
    deployment = {
        "curve": {
            "schema": "dex-amm",
            "deployments": {
                "curve-base": {
                    "network": "base",
                    "services": {"decentralized-network": {"query-id": "deploy-base"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)
    captured_headers = {}

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        captured_headers.update(headers or {})
        return MockResponse(
            json_data={
                "data": {
                    "dexAmmProtocol": {
                        "totalValueLockedUSD": 1,
                        "cumulativeVolumeUSD": 2,
                        "cumulativeSupplySideRevenueUSD": 3,
                        "cumulativeProtocolSideRevenueUSD": 4,
                        "cumulativeTotalRevenueUSD": 5,
                    }
                }
            }
        )

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path, api_key="secret-key")
    metrics = client.get_protocol_metrics("curve", "base")

    assert captured_headers.get("x-api-key") == "secret-key"
    assert metrics["cumulative_total_revenue_usd"] == 5.0


def test_metrics_cache(monkeypatch, tmp_path):
    deployment = {
        "curve": {
            "schema": "dex-amm",
            "deployments": {
                "curve-base": {
                    "network": "base",
                    "services": {"decentralized-network": {"query-id": "deploy-base"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)
    call_count = {"count": 0}

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        call_count["count"] += 1
        return MockResponse(
            json_data={
                "data": {
                    "dexAmmProtocol": {
                        "totalValueLockedUSD": 1,
                        "cumulativeVolumeUSD": 2,
                        "cumulativeSupplySideRevenueUSD": 3,
                        "cumulativeProtocolSideRevenueUSD": 4,
                        "cumulativeTotalRevenueUSD": 5,
                    }
                }
            }
        )

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)
    first = client.get_protocol_metrics("curve", "base")
    second = client.get_protocol_metrics("curve", "base")

    assert first["tvl_usd"] == 1.0
    assert second == first
    assert call_count["count"] == 1


def test_non_json_response(monkeypatch, tmp_path):
    deployment = {
        "balancer": {
            "schema": "dex-amm",
            "deployments": {
                "balancer-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy-bal"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return MockResponse(json_data=ValueError("bad json"))

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)

    with pytest.raises(MessariAPIError):
        client.get_protocol_tvl("balancer", "ethereum")


def test_unsupported_chain(monkeypatch, tmp_path):
    deployment = {
        "aave-v3": {
            "schema": "lending",
            "deployments": {
                "aave-v3-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)
    client = MessariClient(deployment_json_path=path)
    with pytest.raises(MessariNotFoundError):
        client.get_protocol_tvl("aave-v3", "arbitrum")


def test_network_error(monkeypatch, tmp_path):
    deployment = {
        "curve": {
            "schema": "dex-amm",
            "deployments": {
                "curve-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        raise requests.RequestException("boom")

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)
    with pytest.raises(MessariAPIError):
        client.get_protocol_tvl("curve", "ethereum")


def test_http_not_found(monkeypatch, tmp_path):
    deployment = {
        "curve": {
            "schema": "dex-amm",
            "deployments": {
                "curve-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return MockResponse(status_code=404, json_data={})

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)
    with pytest.raises(MessariNotFoundError):
        client.get_protocol_tvl("curve", "ethereum")


def test_http_generic_error(monkeypatch, tmp_path):
    deployment = {
        "curve": {
            "schema": "dex-amm",
            "deployments": {
                "curve-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return MockResponse(status_code=500, json_data={})

    monkeypatch.setattr("requests.post", fake_post)
    client = MessariClient(deployment_json_path=path)
    with pytest.raises(MessariAPIError):
        client.get_protocol_tvl("curve", "ethereum")


def test_missing_deployment_file(tmp_path):
    missing = tmp_path / "none.json"
    with pytest.raises(MessariNotFoundError):
        MessariClient(deployment_json_path=str(missing))


def test_invalid_deployment_json(tmp_path):
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not-json}", encoding="utf-8")
    with pytest.raises(MessariAPIError):
        MessariClient(deployment_json_path=str(bad_path))


def test_load_deployment_skips_missing_query_id(tmp_path):
    deployment = {
        "foo": {
            "schema": "dex-amm",
            "deployments": {
                "foo-eth": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {}},  # 缺失 query-id
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)
    client = MessariClient(deployment_json_path=path)
    assert client._deployments["foo"]["deployments"] == {}


def test_convenience_get_client_instance(monkeypatch, tmp_path):
    from defiagents.dataflows.defi import messari

    messari._client_instance = None  # reset global

    deployment = {
        "lido": {
            "schema": "lending",
            "deployments": {
                "lido-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy-lido"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def fake_config():
        return {"messari": {"api_key": "cfg-key"}}

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return MockResponse(
            json_data={
                "data": {
                    "lendingProtocol": {
                        "totalValueLockedUSD": 9,
                        "totalDepositBalanceUSD": 5,
                        "totalBorrowBalanceUSD": 2,
                    }
                }
            }
        )

    monkeypatch.setattr("defiagents.dataflows.defi.messari.Path.exists", lambda self: True)
    monkeypatch.setattr("defiagents.dataflows.defi.messari.Path.open", lambda self, mode="r", encoding=None: open(path, mode, encoding=encoding))  # noqa: B909,E501
    monkeypatch.setattr("defiagents.dataflows.config.get_config", fake_config)
    monkeypatch.setattr("requests.post", fake_post)

    tvl = messari.get_protocol_tvl("lido", "ethereum")
    assert tvl == 9.0
    assert messari._client_instance.api_key == "cfg-key"


def test_get_client_instance_config_error(monkeypatch, tmp_path):
    from defiagents.dataflows.defi import messari

    messari._client_instance = None

    deployment = {
        "balancer": {
            "schema": "dex-amm",
            "deployments": {
                "balancer-ethereum": {
                    "network": "mainnet",
                    "services": {"decentralized-network": {"query-id": "deploy"}},
                }
            },
        }
    }
    path = _write_deployment(tmp_path, deployment)

    def raise_config():
        raise RuntimeError("config error")

    def fake_post(url, headers=None, json=None, timeout=None):  # noqa: A002
        return MockResponse(
            json_data={"data": {"dexAmmProtocol": {"totalValueLockedUSD": 7, "cumulativeVolumeUSD": 0}}}
        )

    monkeypatch.setattr("defiagents.dataflows.defi.messari.Path.exists", lambda self: True)
    monkeypatch.setattr("defiagents.dataflows.defi.messari.Path.open", lambda self, mode="r", encoding=None: open(path, mode, encoding=encoding))  # noqa: B909,E501
    monkeypatch.setattr("defiagents.dataflows.config.get_config", raise_config)
    monkeypatch.setattr("requests.post", fake_post)

    tvl = messari.get_protocol_tvl("balancer", "ethereum")
    assert tvl == 7.0

    messari._client_instance = None
    monkeypatch.setattr("requests.post", fake_post)
    pools = messari.get_dex_pools("balancer", "ethereum")
    metrics = messari.get_protocol_metrics("balancer", "ethereum")

    assert pools == []
    assert metrics["tvl_usd"] == 7.0
