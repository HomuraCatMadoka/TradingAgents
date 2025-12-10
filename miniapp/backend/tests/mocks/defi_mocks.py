import copy
from datetime import datetime, timedelta, timezone
from typing import Dict, List


def protocol_list() -> List[Dict]:
    return copy.deepcopy(
        [
            {
                "name": "Aave V3",
                "slug": "aave-v3",
                "symbol": "AAVE",
                "tvl": 1_000_000_000,
                "chains": ["ethereum", "arbitrum"],
                "category": "lending",
            },
            {
                "name": "Uniswap V3",
                "slug": "uniswap-v3",
                "symbol": "UNI",
                "tvl": 900_000_000,
                "chains": ["ethereum"],
                "category": "dex",
            },
            {
                "name": "Compound V3",
                "slug": "compound-v3",
                "symbol": "COMP",
                "tvl": 100_000_000,
                "chains": ["ethereum"],
                "category": "lending",
            },
        ]
    )


def protocol_detail(slug: str = "aave-v3", tvl: float = 1_234_567.0) -> Dict:
    return {
        "name": slug.replace("-", " ").title(),
        "slug": slug,
        "symbol": "AAVE",
        "tokenSymbol": "AAVE",
        "tvl": tvl,
        "chains": ["ethereum", "arbitrum"],
        "chainTvls": {"ethereum": tvl / 2, "arbitrum": tvl / 2},
        "description": "Mock protocol detail",
        "category": "lending",
        "url": "https://example.defi",
    }


def protocol_history() -> List[Dict]:
    base = 1_700_000_000
    return [
        {"date": base, "totalLiquidityUSD": 1_000_000},
        {"date": base + 86_400, "totalLiquidityUSD": 1_050_000},
        {"date": base + 2 * 86_400, "totalLiquidityUSD": 1_125_000},
    ]


def market_data() -> Dict:
    return {
        "id": "aave",
        "symbol": "aave",
        "name": "Aave",
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "market_data": {
            "current_price": {"usd": 95.12},
            "market_cap": {"usd": 1_500_000_000},
            "total_volume": {"usd": 250_000_000},
            "price_change_percentage_24h": 2.5,
        },
    }


def price_only() -> Dict:
    return {"usd": 95.12, "usd_market_cap": 1_500_000_000, "usd_24h_vol": 250_000_000, "usd_24h_change": 2.5}


def uniswap_pools() -> List[Dict]:
    return [
        {
            "id": "pool-1",
            "token0": {"symbol": "AAVE", "name": "Aave", "decimals": 18},
            "token1": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
            "totalValueLockedUSD": 10_000_000,
            "volumeUSD": 2_500_000,
            "feeTier": 500,
        }
    ]


def uniswap_pool_detail() -> Dict:
    now = datetime.now(timezone.utc)
    return {
        "id": "pool-1",
        "token0": {"symbol": "AAVE", "name": "Aave", "decimals": 18},
        "token1": {"symbol": "USDC", "name": "USD Coin", "decimals": 6},
        "totalValueLockedUSD": 10_000_000,
        "volumeUSD": 2_500_000,
        "feeTier": 500,
        "poolDayData": [
            {
                "date": int((now - timedelta(days=1)).timestamp()),
                "tvlUSD": 9_500_000,
                "volumeUSD": 1_000_000,
                "feesUSD": 5000,
            },
            {
                "date": int(now.timestamp()),
                "tvlUSD": 10_000_000,
                "volumeUSD": 2_500_000,
                "feesUSD": 12_000,
            },
        ],
    }
