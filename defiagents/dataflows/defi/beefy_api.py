"""
Beefy Finance Official API Integration

Beefy is a multi-chain yield optimizer with a comprehensive official API.

API Base URL: https://api.beefy.finance
Documentation: https://docs.beefy.finance/developer-documentation/api

Key features:
- Multi-chain support (20+ chains)
- Real-time APY calculations
- Auto-compounding vault data
- Historical performance data
- Strategy information

Note: Beefy's API is well-maintained and recommended for all Beefy vault data.
"""

from typing import Dict, List, Optional, Any
import requests
from functools import lru_cache
import time


class BeefyAPI:
    """Client for Beefy Finance official API"""

    BASE_URL = "https://api.beefy.finance"

    # Supported chains by Beefy
    SUPPORTED_CHAINS = [
        "ethereum", "bsc", "polygon", "fantom", "avalanche",
        "arbitrum", "optimism", "base", "moonbeam", "moonriver",
        "celo", "cronos", "harmony", "metis", "aurora",
        "fuse", "emerald", "kava", "gnosis", "zksync"
    ]

    def __init__(self, timeout: int = 30):
        """
        Initialize Beefy API client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Any:
        """
        Make HTTP request to Beefy API with caching.

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
            raise Exception(f"Beefy API request failed: {e}")

    def get_vaults(self) -> List[Dict[str, Any]]:
        """
        Get all Beefy vaults across all chains.

        Returns:
            List of vault data dictionaries:
            [
                {
                    "id": str,
                    "name": str,
                    "token": str,
                    "tokenAddress": str,
                    "earnedToken": str,
                    "earnContractAddress": str,
                    "chain": str,
                    "platform": str,
                    "status": str,
                    "assets": [str],
                    ...
                }
            ]
        """
        return self._make_request("vaults")

    def get_vaults_by_chain(self, chain: str) -> List[Dict[str, Any]]:
        """
        Get all Beefy vaults on a specific chain.

        Args:
            chain: Blockchain name (ethereum, bsc, polygon, arbitrum, etc.)

        Returns:
            List of vault data for the specified chain
        """
        chain_lower = chain.lower()
        if chain_lower not in self.SUPPORTED_CHAINS:
            raise ValueError(f"Unsupported chain: {chain}. Supported: {self.SUPPORTED_CHAINS}")

        all_vaults = self.get_vaults()
        return [v for v in all_vaults if v.get("chain", "").lower() == chain_lower]

    def get_apys(self) -> Dict[str, float]:
        """
        Get current APY for all vaults.

        Returns:
            Dictionary mapping vault ID to APY:
            {
                "beefy-vault-id": 12.34,  # APY as percentage
                ...
            }
        """
        return self._make_request("apy")

    def get_apy(self, vault_id: str) -> float:
        """
        Get APY for a specific vault.

        Args:
            vault_id: Beefy vault ID

        Returns:
            APY as percentage (e.g., 12.34 for 12.34%)
        """
        apys = self.get_apys()
        return apys.get(vault_id, 0.0)

    def get_apy_breakdown(self, vault_id: str) -> Dict[str, Any]:
        """
        Get detailed APY breakdown for a specific vault.

        Args:
            vault_id: Beefy vault ID

        Returns:
            Dictionary with APY breakdown:
            {
                "totalApy": float,
                "vaultApr": float,
                "tradingApr": float,
                "compoundingsPerYear": int,
                ...
            }
        """
        all_breakdowns = self._make_request("apy/breakdown")
        return all_breakdowns.get(vault_id, {})

    def get_tvls(self) -> Dict[str, float]:
        """
        Get current TVL for all vaults.

        Returns:
            Dictionary mapping vault ID to TVL in USD:
            {
                "beefy-vault-id": 1234567.89,
                ...
            }
        """
        return self._make_request("tvl")

    def get_tvl(self, vault_id: str) -> float:
        """
        Get TVL for a specific vault.

        Args:
            vault_id: Beefy vault ID

        Returns:
            TVL in USD
        """
        tvls = self.get_tvls()
        return tvls.get(vault_id, 0.0)

    def get_vault_details(self, vault_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information for a specific vault including APY and TVL.

        Args:
            vault_id: Beefy vault ID

        Returns:
            Dictionary with vault details or None if not found
        """
        vaults = self.get_vaults()

        for vault in vaults:
            if vault.get("id") == vault_id:
                # Enrich with APY and TVL data
                vault["apy"] = self.get_apy(vault_id)
                vault["tvl"] = self.get_tvl(vault_id)
                return vault

        return None

    def get_top_vaults(self, chain: Optional[str] = None, limit: int = 10, sort_by: str = "tvl") -> List[Dict[str, Any]]:
        """
        Get top vaults, optionally filtered by chain.

        Args:
            chain: Optional blockchain name filter (ethereum, bsc, polygon, etc.)
            limit: Maximum number of vaults to return
            sort_by: Sort criteria ("tvl" or "apy")

        Returns:
            List of top vaults with enriched data
        """
        # Get vaults
        if chain:
            vaults = self.get_vaults_by_chain(chain)
        else:
            vaults = self.get_vaults()

        # Filter active vaults
        active_vaults = [v for v in vaults if v.get("status") == "active"]

        # Get APY and TVL data
        apys = self.get_apys()
        tvls = self.get_tvls()

        # Enrich vault data
        for vault in active_vaults:
            vault_id = vault.get("id")
            vault["apy"] = apys.get(vault_id, 0.0)
            vault["tvl"] = tvls.get(vault_id, 0.0)

        # Sort vaults
        if sort_by == "tvl":
            sorted_vaults = sorted(active_vaults, key=lambda v: v.get("tvl", 0), reverse=True)
        elif sort_by == "apy":
            sorted_vaults = sorted(active_vaults, key=lambda v: v.get("apy", 0), reverse=True)
        else:
            sorted_vaults = active_vaults

        return sorted_vaults[:limit]

    def get_total_tvl(self, chain: Optional[str] = None) -> float:
        """
        Get total TVL across vaults, optionally filtered by chain.

        Args:
            chain: Optional blockchain name filter

        Returns:
            Total TVL in USD
        """
        if chain:
            vaults = self.get_vaults_by_chain(chain)
        else:
            vaults = self.get_vaults()

        tvls = self.get_tvls()
        total = sum(tvls.get(v.get("id"), 0) for v in vaults if v.get("status") == "active")
        return total


# Convenience functions
@lru_cache(maxsize=32)
def get_beefy_client() -> BeefyAPI:
    """Get a cached Beefy API client instance."""
    return BeefyAPI()


def get_beefy_vaults(chain: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Get Beefy vaults on a specific chain.

    Args:
        chain: Blockchain name (ethereum, bsc, polygon, arbitrum, optimism, base, etc.)
        limit: Optional limit on number of vaults to return (top by TVL)

    Returns:
        List of vault data dictionaries with APY and TVL

    Example:
        >>> vaults = get_beefy_vaults("arbitrum", limit=5)
        >>> for vault in vaults:
        ...     print(f"{vault['name']}: APY {vault['apy']:.2f}%")
    """
    client = get_beefy_client()

    if limit:
        return client.get_top_vaults(chain=chain, limit=limit)
    else:
        vaults = client.get_vaults_by_chain(chain)
        # Enrich with APY and TVL
        apys = client.get_apys()
        tvls = client.get_tvls()
        for vault in vaults:
            vault_id = vault.get("id")
            vault["apy"] = apys.get(vault_id, 0.0)
            vault["tvl"] = tvls.get(vault_id, 0.0)
        return vaults


def get_beefy_vault_apy(vault_id: str) -> Dict[str, float]:
    """
    Get APY for a specific Beefy vault.

    Args:
        vault_id: Beefy vault ID

    Returns:
        Dictionary with APY data

    Example:
        >>> apy = get_beefy_vault_apy("beefy-aave-usdc")
        >>> print(f"APY: {apy['apy']:.2f}%")
    """
    client = get_beefy_client()
    apy = client.get_apy(vault_id)
    breakdown = client.get_apy_breakdown(vault_id)

    return {
        "apy": apy,
        "breakdown": breakdown
    }


def format_beefy_vault(vault: Dict[str, Any]) -> str:
    """
    Format a Beefy vault data into human-readable string.

    Args:
        vault: Vault data dictionary from Beefy API

    Returns:
        Formatted string with vault information
    """
    name = vault.get("name", "Unknown Vault")
    vault_id = vault.get("id", "")
    chain = vault.get("chain", "").upper()
    platform = vault.get("platform", "")

    assets = vault.get("assets", [])
    apy = vault.get("apy", 0.0)
    tvl = vault.get("tvl", 0.0)

    status = vault.get("status", "unknown")
    status_emoji = "✅" if status == "active" else "⚠️"

    return f"""**{name}** {status_emoji}
- **Chain**: {chain}
- **Platform**: {platform}
- **Assets**: {' + '.join(assets)}
- **APY**: {apy:.2f}%
- **TVL**: ${tvl:,.2f}
- **Vault ID**: `{vault_id}`"""


if __name__ == "__main__":
    # Example usage
    print("Testing Beefy Finance API...")

    try:
        client = BeefyAPI()

        # Test getting vaults
        print("\n1. Top 5 Beefy vaults on Arbitrum:")
        top_vaults = client.get_top_vaults(chain="arbitrum", limit=5)
        for i, vault in enumerate(top_vaults, 1):
            print(f"\n{i}. {format_beefy_vault(vault)}")

        # Test getting total TVL
        print(f"\n2. Total Beefy TVL on Arbitrum:")
        total_tvl = client.get_total_tvl(chain="arbitrum")
        print(f"${total_tvl:,.2f}")

        print("\n✅ Beefy API test successful!")

    except Exception as e:
        print(f"\n❌ Error: {e}")
