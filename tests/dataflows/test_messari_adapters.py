import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from defiagents.dataflows.defi.adapters import DataAdapter  # noqa: E402
from defiagents.dataflows.interface import DataSourceType  # noqa: E402


def test_normalize_tvl_messari():
    data = {"protocol": {"totalValueLockedUSD": "123.45"}}
    value = DataAdapter.normalize_tvl(data, DataSourceType.MESSARI)
    assert value == pytest.approx(123.45)


def test_normalize_tvl_defillama():
    value_float = DataAdapter.normalize_tvl(12.5, DataSourceType.DEFILLAMA)
    value_dict = DataAdapter.normalize_tvl({"tvl": 50}, DataSourceType.DEFILLAMA)
    value_list = DataAdapter.normalize_tvl([10, 20], DataSourceType.DEFILLAMA)

    assert value_float == pytest.approx(12.5)
    assert value_dict == pytest.approx(50.0)
    assert value_list == pytest.approx(30.0)


def test_normalize_tvl_thegraph():
    data = {"financialsDailySnapshots": [{"totalValueLockedUSD": "1"}, {"totalValueLockedUSD": "3.3"}]}
    value = DataAdapter.normalize_tvl(data, DataSourceType.THE_GRAPH)
    assert value == pytest.approx(3.3)


def test_normalize_lending_markets():
    markets = [
        {
            "id": "m1",
            "input_token": {"symbol": "USDC"},
            "tvl_usd": 10,
            "total_deposit_usd": 8,
            "total_borrow_usd": 3,
            "rates": [
                {"side": "LENDER", "rate": 0.02},
                {"side": "BORROWER", "rate": "0.05"},
            ],
        }
    ]
    normalized = DataAdapter.normalize_lending_markets(markets, DataSourceType.MESSARI)
    assert normalized[0]["asset"] == "USDC"
    assert normalized[0]["supply_rate"] == pytest.approx(0.02)
    assert normalized[0]["borrow_rate"] == pytest.approx(0.05)
    assert normalized[0]["tvl_usd"] == pytest.approx(10.0)

    graph_style = {
        "markets": [
            {"id": "g1", "inputToken": {"symbol": "DAI"}, "totalValueLockedUSD": "5", "supplyRate": "0.1"},
            {"id": "g2", "inputToken": {"symbol": "ETH"}, "totalValueLockedUSD": None},
        ]
    }
    normalized_graph = DataAdapter.normalize_lending_markets(graph_style, DataSourceType.THE_GRAPH)
    assert normalized_graph[0]["asset"] == "DAI"
    assert normalized_graph[0]["supply_rate"] == pytest.approx(0.1)
    assert normalized_graph[0]["borrow_rate"] == 0.0
    assert normalized_graph[1]["tvl_usd"] == 0.0


def test_normalize_dex_pools():
    pools = [
        {
            "id": "p1",
            "name": "USDC/ETH",
            "totalValueLockedUSD": "100",
            "cumulativeVolumeUSD": "250",
            "feesUSD": "1",
            "input_tokens": [{"token": {"symbol": "USDC"}}, {"token": {"symbol": "ETH"}}],
        },
        {
            "id": "p2",
            "token0": {"symbol": "BTC"},
            "token1": {"symbol": "USDT"},
            "tvlUsd": 10,
            "volumeUSD": 20,
        },
    ]
    normalized = DataAdapter.normalize_dex_pools(pools, DataSourceType.MESSARI)

    first = normalized[0]
    assert first["id"] == "p1"
    assert first["tvl_usd"] == pytest.approx(100.0)
    assert first["volume_usd"] == pytest.approx(250.0)
    assert set(first["token_symbols"]) == {"USDC", "ETH"}

    second = normalized[1]
    assert set(second["token_symbols"]) == {"BTC", "USDT"}
    assert second["volume_usd"] == pytest.approx(20.0)
