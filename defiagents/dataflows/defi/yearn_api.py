"""
Yearn Finance yDaemon API Integration

yDaemon is Yearn's official API providing real-time vault data, APY calculations,
and strategy information.

API Base URL: https://ydaemon.yearn.fi
Documentation: https://ydaemon.yearn.fi/

Key features:
- Accurate net APY calculations (after fees)
- Multi-chain support (Ethereum, Arbitrum, Optimism, Polygon, Fantom, Base)
- Real-time vault data
- Historical performance data
- Strategy details and risk assessments

Note: yDaemon is the recommended data source for Yearn vaults.
"""

from typing import Dict, List, Optional, Any
import requests
from functools import lru_cache
import time


class YearnAPI:
    """Client for Yearn Finance yDaemon API"""

    BASE_URL = "https://ydaemon.yearn.fi"

    # Chain ID mappings for yDaemon
    CHAIN_IDS = {
        "ethereum": 1,
        "eth": 1,
        "optimism": 10,
        "op": 10,
        "fantom": 250,
        "ftm": 250,
        "arbitrum": 42161,
        "arb": 42161,
        "polygon": 137,
        "matic": 137,
        "base": 8453,
    }

    def __init__(self, timeout: int = 30):
        """
        Initialize Yearn yDaemon API client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to yDaemon API with caching.

        Args:
            endpoint: API endpoint (without base URL)
            params: Query parameters

        Returns:
            Parsed JSON response
        """
        cache_key = f"{endpoint}:{str(params)}"
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if now - cached_time < self._cache_ttl:
                return cached_data

        url = f"{self.BASE_URL}/{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()

            # Cache the result
            self._cache[cache_key] = (data, now)
            return data

        except requests.exceptions.RequestException as e:
            raise Exception(f"Yearn yDaemon API request failed: {e}")

    def _get_chain_id(self, chain: str) -> int:
        """Get chain ID from chain name."""
        chain_lower = chain.lower()
        if chain_lower not in self.CHAIN_IDS:
            raise ValueError(f"Unsupported chain: {chain}. Supported: {list(self.CHAIN_IDS.keys())}")
        return self.CHAIN_IDS[chain_lower]

    def get_vaults(self, chain: str) -> List[Dict[str, Any]]:
        """
        Get all Yearn vaults on a specific chain.

        Args:
            chain: Blockchain name (ethereum, arbitrum, optimism, polygon, base, fantom)

        Returns:
            List of vault data dictionaries:
            [
                {
                    "address": str,
                    "name": str,
                    "symbol": str,
                    "token": {...},
                    "tvl": {...},
                    "apy": {...},
                    "strategies": [...],
                    ...
                }
            ]
        """
        chain_id = self._get_chain_id(chain)
        return self._make_request(f"{chain_id}/vaults/all")

    def get_vault(self, chain: str, vault_address: str) -> Dict[str, Any]:
        """
        Get detailed data for a specific vault.

        Args:
            chain: Blockchain name
            vault_address: Vault contract address

        Returns:
            Vault data dictionary
        """
        chain_id = self._get_chain_id(chain)
        return self._make_request(f"{chain_id}/vaults/{vault_address}")

    def get_vault_apy(self, chain: str, vault_address: str) -> Dict[str, float]:
        """
        Get APY breakdown for a specific vault.

        Args:
            chain: Blockchain name
            vault_address: Vault contract address

        Returns:
            Dictionary with APY components:
            {
                "gross_apy": float,      # Gross APY before fees
                "net_apy": float,        # Net APY after fees (recommended)
                "performance_fee": float # Performance fee percentage
            }
        """
        vault = self.get_vault(chain, vault_address)

        apy_data = vault.get("apy", {})

        # yDaemon provides multiple APY calculations
        net_apy = apy_data.get("net_apy", 0.0)
        gross_apy = apy_data.get("gross_apr", 0.0)  # Note: may be APR, not APY

        # Try to get from different fields (API structure may vary)
        if net_apy == 0.0:
            net_apy = apy_data.get("points", {}).get("week_ago", 0.0)

        if gross_apy == 0.0:
            gross_apy = net_apy  # Fallback

        # Get performance fee
        performance_fee = vault.get("fees", {}).get("performance", {}).get("fee", 0.0)

        return {
            "gross_apy": gross_apy * 100 if gross_apy < 1 else gross_apy,  # Convert to percentage
            "net_apy": net_apy * 100 if net_apy < 1 else net_apy,
            "performance_fee": performance_fee * 100 if performance_fee < 1 else performance_fee
        }

    def get_top_vaults(self, chain: str, limit: int = 10, sort_by: str = "tvl") -> List[Dict[str, Any]]:
        """
        Get top vaults on a specific chain.

        Args:
            chain: Blockchain name
            limit: Maximum number of vaults to return
            sort_by: Sort criteria ("tvl" or "apy")

        Returns:
            List of top vaults
        """
        vaults = self.get_vaults(chain)

        # Filter out empty/deprecated vaults
        active_vaults = [v for v in vaults if v.get("tvl", {}).get("total_assets", 0) > 0]

        # Sort vaults
        if sort_by == "tvl":
            sorted_vaults = sorted(
                active_vaults,
                key=lambda v: v.get("tvl", {}).get("tvl", 0),
                reverse=True
            )
        elif sort_by == "apy":
            sorted_vaults = sorted(
                active_vaults,
                key=lambda v: v.get("apy", {}).get("net_apy", 0),
                reverse=True
            )
        else:
            sorted_vaults = active_vaults

        return sorted_vaults[:limit]

    def get_total_tvl(self, chain: str) -> float:
        """
        Get total TVL across all Yearn vaults on a chain.

        Args:
            chain: Blockchain name

        Returns:
            Total TVL in USD
        """
        vaults = self.get_vaults(chain)
        total = sum(v.get("tvl", {}).get("tvl", 0) for v in vaults)
        return total

    def get_vault_strategies(self, chain: str, vault_address: str) -> List[Dict[str, Any]]:
        """
        Get strategies employed by a specific vault.

        Args:
            chain: Blockchain name
            vault_address: Vault contract address

        Returns:
            List of strategy data dictionaries
        """
        vault = self.get_vault(chain, vault_address)
        return vault.get("strategies", [])


# Convenience functions
@lru_cache(maxsize=32)
def get_yearn_client() -> YearnAPI:
    """Get a cached Yearn API client instance."""
    return YearnAPI()


def get_yearn_vaults(chain: str = "ethereum", limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get Yearn vaults on a specific chain.

    Args:
        chain: Blockchain name (ethereum, arbitrum, optimism, polygon, base, fantom)
        limit: Optional limit on number of vaults to return (top by TVL)

    Returns:
        List of vault data dictionaries

    Example:
        >>> vaults = get_yearn_vaults("ethereum", limit=5)
        >>> for vault in vaults:
        ...     print(f"{vault['name']}: ${vault['tvl']['tvl']:,.2f}")
    """
    client = get_yearn_client()

    if limit:
        return client.get_top_vaults(chain, limit=limit)
    else:
        return client.get_vaults(chain)


def get_yearn_vault_apy(chain: str, vault_address: str) -> Dict[str, float]:
    """
    Get APY for a specific Yearn vault.

    Args:
        chain: Blockchain name
        vault_address: Vault contract address

    Returns:
        Dictionary with APY data (net_apy is recommended for user display)

    Example:
        >>> apy = get_yearn_vault_apy("ethereum", "0xa354f35829ae975e850e23e9615b11da1b3dc4de")
        >>> print(f"Net APY: {apy['net_apy']:.2f}%")
    """
    client = get_yearn_client()
    return client.get_vault_apy(chain, vault_address)


def format_yearn_vault(vault: Dict[str, Any]) -> str:
    """
    Format a Yearn vault data into human-readable string.

    Args:
        vault: Vault data dictionary from yDaemon API

    Returns:
        Formatted string with vault information
    """
    name = vault.get("display_name") or vault.get("name", "Unknown Vault")
    symbol = vault.get("symbol", "")

    tvl_data = vault.get("tvl", {})
    tvl = tvl_data.get("tvl", 0)

    apy_data = vault.get("apy", {})
    net_apy = apy_data.get("net_apy", 0) * 100

    token_data = vault.get("token", {})
    token_symbol = token_data.get("symbol", "?")

    address = vault.get("address", "N/A")

    # Get fees
    fees = vault.get("fees", {})
    perf_fee = fees.get("performance", {}).get("fee", 0) * 100
    mgmt_fee = fees.get("management", {}).get("fee", 0) * 100

    return f"""**{name}** ({symbol})
- **Deposit Token**: {token_symbol}
- **TVL**: ${tvl:,.2f}
- **Net APY**: {net_apy:.2f}% (after fees)
- **Performance Fee**: {perf_fee:.2f}%
- **Management Fee**: {mgmt_fee:.2f}%
- **Address**: `{address}`"""


if __name__ == "__main__":
    # Example usage
    print("Testing Yearn Finance yDaemon API...")

    try:
        client = YearnAPI()

        # Test getting vaults
        print("\n1. Top 5 Yearn vaults on Ethereum:")
        top_vaults = client.get_top_vaults("ethereum", limit=5)
        for i, vault in enumerate(top_vaults, 1):
            print(f"\n{i}. {format_yearn_vault(vault)}")

        # Test getting total TVL
        print(f"\n2. Total Yearn TVL on Ethereum:")
        total_tvl = client.get_total_tvl("ethereum")
        print(f"${total_tvl:,.2f}")

        print("\n✅ Yearn API test successful!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
