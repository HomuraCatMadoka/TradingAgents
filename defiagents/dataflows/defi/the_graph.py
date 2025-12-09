"""
The Graph subgraph integration.

Provides access to on-chain data via GraphQL subgraphs.
Documentation: https://thegraph.com/docs/

Features:
- Query any subgraph via GraphQL
- Pre-built queries for popular protocols (Uniswap, Aave, etc.)
- Multi-chain support
- Caching support
"""

import time
import logging
from typing import Dict, List, Optional, Any
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

logger = logging.getLogger(__name__)


class TheGraphClient:
    """The Graph subgraph client."""

    GATEWAY_URL = "https://gateway.thegraph.com/api"
    PUBLIC_URL = "https://api.thegraph.com/subgraphs/name"

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_gateway: bool = False,
        cache_ttl: int = 300,
    ):
        """
        Initialize The Graph client.

        Args:
            api_key: The Graph API key (optional, for gateway access)
            use_gateway: Whether to use the gateway (requires API key)
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)
        """
        self.api_key = api_key
        self.use_gateway = use_gateway and api_key is not None
        self.cache_ttl = cache_ttl
        self._cache: Dict[str, tuple[Any, float]] = {}
        self._clients: Dict[str, Client] = {}

    def _get_cached(self, key: str) -> Optional[Any]:
        """Get cached data if not expired."""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"Cache hit for key: {key}")
                return data
            else:
                logger.debug(f"Cache expired for key: {key}")
                del self._cache[key]
        return None

    def _set_cache(self, key: str, data: Any):
        """Cache data with timestamp."""
        self._cache[key] = (data, time.time())
        logger.debug(f"Cached data for key: {key}")

    def _get_subgraph_url(self, subgraph_id: str) -> str:
        """
        Get full subgraph URL.

        Args:
            subgraph_id: Subgraph ID in format 'org/name' or full URL

        Returns:
            Full subgraph URL
        """
        # If already a full URL, return as is
        if subgraph_id.startswith('http'):
            return subgraph_id

        # Build URL based on gateway/public
        if self.use_gateway:
            return f"{self.GATEWAY_URL}/{self.api_key}/subgraphs/id/{subgraph_id}"
        else:
            return f"{self.PUBLIC_URL}/{subgraph_id}"

    def _get_client(self, subgraph_url: str) -> Client:
        """Get or create GQL client for subgraph."""
        if subgraph_url not in self._clients:
            transport = RequestsHTTPTransport(
                url=subgraph_url,
                verify=True,
                retries=3,
            )
            self._clients[subgraph_url] = Client(
                transport=transport,
                fetch_schema_from_transport=True,
            )
        return self._clients[subgraph_url]

    def query(
        self,
        subgraph_id: str,
        query_string: str,
        variables: Optional[Dict] = None,
    ) -> Dict:
        """
        Execute GraphQL query on a subgraph.

        Args:
            subgraph_id: Subgraph identifier or URL
            query_string: GraphQL query string
            variables: Query variables (optional)

        Returns:
            Query result as dictionary

        Example:
            >>> client = TheGraphClient()
            >>> query = '''
            ... {
            ...   pools(first: 5) {
            ...     id
            ...     token0 { symbol }
            ...     token1 { symbol }
            ...   }
            ... }
            ... '''
            >>> result = client.query('uniswap/uniswap-v3', query)
        """
        # Generate cache key
        cache_key = f"thegraph:{subgraph_id}:{query_string}:{variables}"
        cached_data = self._get_cached(cache_key)
        if cached_data is not None:
            return cached_data

        # Execute query
        subgraph_url = self._get_subgraph_url(subgraph_id)
        logger.info(f"Querying subgraph: {subgraph_url}")

        try:
            client = self._get_client(subgraph_url)
            query_obj = gql(query_string)
            result = client.execute(query_obj, variable_values=variables)

            # Cache the result
            self._set_cache(cache_key, result)

            return result
        except Exception as e:
            logger.error(f"The Graph query failed: {e}")
            raise


# Global instance
_client_instance: Optional[TheGraphClient] = None


def get_client_instance(
    api_key: Optional[str] = None,
    use_gateway: bool = False,
) -> TheGraphClient:
    """Get or create global client instance."""
    global _client_instance
    if _client_instance is None:
        _client_instance = TheGraphClient(api_key=api_key, use_gateway=use_gateway)
    return _client_instance


def query_subgraph(
    subgraph_id: str,
    query_string: str,
    variables: Optional[Dict] = None,
) -> Dict:
    """
    Execute GraphQL query on a subgraph.

    Args:
        subgraph_id: Subgraph identifier
        query_string: GraphQL query
        variables: Query variables (optional)

    Returns:
        Query result dictionary
    """
    client = get_client_instance()
    return client.query(subgraph_id, query_string, variables)


# ========== Protocol-Specific Queries ==========


def get_uniswap_pools(
    subgraph_id: str = "uniswap/uniswap-v3",
    limit: int = 10,
    order_by: str = "totalValueLockedUSD",
) -> List[Dict]:
    """
    Get Uniswap V3 pools.

    Args:
        subgraph_id: Uniswap subgraph ID (default: Ethereum mainnet)
        limit: Number of pools to return
        order_by: Field to sort by

    Returns:
        List of pool dictionaries
    """
    query = """
    query GetPools($limit: Int!, $orderBy: String!) {
      pools(
        first: $limit,
        orderBy: $orderBy,
        orderDirection: desc
      ) {
        id
        token0 {
          symbol
          name
          decimals
        }
        token1 {
          symbol
          name
          decimals
        }
        totalValueLockedUSD
        volumeUSD
        feeTier
        liquidity
        token0Price
        token1Price
      }
    }
    """

    variables = {
        "limit": limit,
        "orderBy": order_by,
    }

    result = query_subgraph(subgraph_id, query, variables)
    return result.get('pools', [])


def get_uniswap_pool_by_id(
    pool_id: str,
    subgraph_id: str = "uniswap/uniswap-v3",
) -> Optional[Dict]:
    """
    Get specific Uniswap V3 pool by ID.

    Args:
        pool_id: Pool contract address
        subgraph_id: Uniswap subgraph ID

    Returns:
        Pool data dictionary or None if not found
    """
    query = """
    query GetPool($poolId: ID!) {
      pool(id: $poolId) {
        id
        token0 {
          symbol
          name
          decimals
        }
        token1 {
          symbol
          name
          decimals
        }
        totalValueLockedUSD
        volumeUSD
        feeTier
        liquidity
        token0Price
        token1Price
        poolDayData(first: 7, orderBy: date, orderDirection: desc) {
          date
          volumeUSD
          tvlUSD
          feesUSD
        }
      }
    }
    """

    variables = {"poolId": pool_id.lower()}
    result = query_subgraph(subgraph_id, query, variables)
    return result.get('pool')


def get_aave_reserves(
    subgraph_id: str = "aave/protocol-v3",
    limit: int = 20,
) -> List[Dict]:
    """
    Get Aave V3 reserves (assets).

    Args:
        subgraph_id: Aave subgraph ID
        limit: Number of reserves to return

    Returns:
        List of reserve dictionaries
    """
    query = """
    query GetReserves($limit: Int!) {
      reserves(first: $limit) {
        id
        symbol
        name
        decimals
        liquidityRate
        variableBorrowRate
        stableBorrowRate
        totalLiquidity
        totalATokenSupply
        totalCurrentVariableDebt
        availableLiquidity
        utilizationRate
        liquidationThreshold
        liquidationBonus
        baseLTVasCollateral
      }
    }
    """

    variables = {"limit": limit}
    result = query_subgraph(subgraph_id, query, variables)
    return result.get('reserves', [])


def get_aave_reserve_by_symbol(
    symbol: str,
    subgraph_id: str = "aave/protocol-v3",
) -> Optional[Dict]:
    """
    Get specific Aave reserve by symbol.

    Args:
        symbol: Asset symbol (e.g., 'USDC', 'ETH')
        subgraph_id: Aave subgraph ID

    Returns:
        Reserve data dictionary or None if not found
    """
    reserves = get_aave_reserves(subgraph_id=subgraph_id, limit=100)
    for reserve in reserves:
        if reserve.get('symbol', '').upper() == symbol.upper():
            return reserve
    return None


def format_uniswap_pool(pool: Dict) -> str:
    """
    Format Uniswap pool data into readable string.

    Args:
        pool: Pool data dictionary

    Returns:
        Formatted markdown string
    """
    token0 = pool.get('token0', {})
    token1 = pool.get('token1', {})
    tvl = pool.get('totalValueLockedUSD', 0)
    volume = pool.get('volumeUSD', 0)
    fee_tier = pool.get('feeTier', 0)

    # Format numbers
    tvl_str = f"${float(tvl):,.0f}" if tvl else "N/A"
    volume_str = f"${float(volume):,.0f}" if volume else "N/A"
    fee_pct = int(fee_tier) / 10000 if fee_tier else 0

    return f"""## {token0.get('symbol')}/{token1.get('symbol')} Pool

**Fee Tier**: {fee_pct}%
**TVL**: {tvl_str}
**Volume**: {volume_str}
**Pool Address**: `{pool.get('id')}`
"""


def format_aave_reserve(reserve: Dict) -> str:
    """
    Format Aave reserve data into readable string.

    Args:
        reserve: Reserve data dictionary

    Returns:
        Formatted markdown string
    """
    symbol = reserve.get('symbol', 'Unknown')
    name = reserve.get('name', 'Unknown')

    # Convert rates from Ray (27 decimals) to percentage
    def ray_to_percent(ray_value):
        if not ray_value:
            return 0.0
        return float(ray_value) / 1e27 * 100

    deposit_apy = ray_to_percent(reserve.get('liquidityRate'))
    borrow_apy = ray_to_percent(reserve.get('variableBorrowRate'))
    utilization = ray_to_percent(reserve.get('utilizationRate'))

    total_liquidity = reserve.get('totalLiquidity', 0)
    available = reserve.get('availableLiquidity', 0)

    return f"""## {symbol} ({name})

**Deposit APY**: {deposit_apy:.2f}%
**Borrow APY**: {borrow_apy:.2f}%
**Utilization Rate**: {utilization:.2f}%
**Total Liquidity**: {float(total_liquidity):,.0f} {symbol}
**Available**: {float(available):,.0f} {symbol}
**Reserve Address**: `{reserve.get('id')}`
"""


if __name__ == "__main__":
    # Example usage
    import sys

    logging.basicConfig(level=logging.INFO)

    print("Testing The Graph API...\n")

    try:
        # Test Uniswap pools
        print("=== Top 5 Uniswap V3 Pools ===\n")
        pools = get_uniswap_pools(limit=5)
        for pool in pools:
            print(format_uniswap_pool(pool))
            print()

        print("\n" + "="*60 + "\n")

        # Test Aave reserves
        print("=== USDC Reserve on Aave V3 ===\n")
        reserve = get_aave_reserve_by_symbol('USDC')
        if reserve:
            print(format_aave_reserve(reserve))
        else:
            print("USDC reserve not found")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
