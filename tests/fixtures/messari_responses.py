"""Messari API Mock 响应数据。"""

from __future__ import annotations

import requests

_tvl_protocol = {
    "id": "aave-v3-ethereum",
    "name": "Aave V3",
    "schema": "lending",
    "network": "ethereum",
    "totalValueLockedUSD": 5234567890.12,
    "totalDepositBalanceUSD": 4987654321.0,
    "totalBorrowBalanceUSD": 3456789012.34,
    "cumulativeSupplySideRevenueUSD": 98765432.1,
    "cumulativeProtocolSideRevenueUSD": 123456789.0,
    "cumulativeTotalRevenueUSD": 222222221.1,
}

MOCK_PROTOCOL_TVL_SUCCESS = {
    "protocol": _tvl_protocol,
    "data": {"lendingProtocol": _tvl_protocol},
}

_lending_markets = [
    {
        "id": "aave-v3-usdc",
        "name": "USDC",
        "inputToken": {"id": "usdc", "symbol": "USDC", "name": "USD Coin", "decimals": 6},
        "outputToken": None,
        "rewardTokens": [
            {"token": {"id": "aave", "symbol": "AAVE", "name": "Aave", "decimals": 18}},
        ],
        "rates": [
            {"side": "LENDER", "rate": 0.0345, "type": "VARIABLE"},
            {"side": "BORROWER", "rate": 0.0567, "type": "VARIABLE"},
        ],
        "totalValueLockedUSD": 1234567890.0,
        "totalDepositBalanceUSD": 1000000000.0,
        "totalBorrowBalanceUSD": 750000000.0,
    },
    {
        "id": "aave-v3-weth",
        "name": "WETH",
        "inputToken": {"id": "weth", "symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
        "outputToken": None,
        "rewardTokens": [],
        "rates": [
            {"side": "LENDER", "rate": "0.0123", "type": "STABLE"},
            {"side": "BORROWER", "rate": "0.0275", "type": "STABLE"},
        ],
        "totalValueLockedUSD": 223456789.01,
        "totalDepositBalanceUSD": 200000000.0,
        "totalBorrowBalanceUSD": 120000000.0,
    },
]

MOCK_LENDING_MARKETS_SUCCESS = {
    "markets": _lending_markets,
    "data": {"lendingProtocol": {"id": "aave-v3-ethereum", "markets": _lending_markets}},
}

_dex_pools = [
    {
        "id": "uni-v3-eth-usdc-0.05",
        "name": "USDC/ETH 0.05%",
        "totalValueLockedUSD": 987654321.01,
        "cumulativeVolumeUSD": 12345678901.12,
        "feesUSD": 123456.78,
        "inputTokens": [
            {"id": "usdc", "symbol": "USDC", "name": "USD Coin", "decimals": 6},
            {"id": "weth", "symbol": "WETH", "name": "Wrapped Ether", "decimals": 18},
        ],
        "rewardTokens": [
            {"token": {"id": "uni", "symbol": "UNI", "name": "Uniswap", "decimals": 18}},
        ],
    },
    {
        "id": "curve-3pool",
        "name": "DAI/USDC/USDT",
        "totalValueLockedUSD": "456789012.34",
        "cumulativeVolumeUSD": "7890123456.78",
        "feesUSD": "34567.89",
        "inputTokens": [
            {"id": "dai", "symbol": "DAI", "name": "Dai Stablecoin", "decimals": 18},
            {"id": "usdc", "symbol": "USDC", "name": "USD Coin", "decimals": 6},
            {"id": "usdt", "symbol": "USDT", "name": "Tether USD", "decimals": 6},
        ],
        "rewardTokens": [],
    },
]

MOCK_DEX_POOLS_SUCCESS = {
    "pools": _dex_pools,
    "data": {"dexAmmProtocol": {"id": "uniswap-v3-ethereum", "pools": _dex_pools}},
}

MOCK_404_ERROR = {
    "errors": [
        {"message": "Subgraph not found"},
    ]
}

MOCK_429_ERROR = {
    "errors": [
        {"message": "Rate limit exceeded"},
    ]
}

MOCK_TIMEOUT_ERROR = requests.Timeout("Request timed out")
