"""
Messari Subgraph Schema helpers.

提供查询构建与数据解析工具，覆盖 Messari 标准化的 Lending 与 DEX-AMM Schema。
"""

from typing import Any, Dict, List, Tuple

LENDING_SCHEMA = "lending"
DEX_AMM_SCHEMA = "dex-amm"


def normalize_schema(schema: str) -> str:
    """
    标准化 schema 名称。

    Args:
        schema: 原始 schema 字符串。

    Returns:
        小写 schema 名称。
    """

    return (schema or "").strip().lower()


def safe_float(value: Any) -> float:
    """将任意值转换为 float，异常时返回 0.0。"""

    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_tvl_query(schema_type: str, protocol_slug: str) -> Tuple[str, Dict[str, str]]:
    """
    构建 TVL 查询。

    Args:
        schema_type: "lending" 或 "dex-amm"。
        protocol_slug: 协议 slug。

    Returns:
        (GraphQL 查询字符串, 变量字典)。
    """

    if schema_type == LENDING_SCHEMA:
        query = """
        query ProtocolTvl($id: String!) {
          lendingProtocol(id: $id) {
            id
            totalValueLockedUSD
            totalDepositBalanceUSD
            totalBorrowBalanceUSD
          }
        }
        """
    elif schema_type == DEX_AMM_SCHEMA:
        query = """
        query ProtocolTvl($id: String!) {
          dexAmmProtocol(id: $id) {
            id
            totalValueLockedUSD
            cumulativeVolumeUSD
            cumulativeTotalRevenueUSD
          }
        }
        """
    else:
        raise ValueError(f"Unsupported schema type: {schema_type}")

    return query, {"id": protocol_slug}


def build_lending_markets_query(protocol_slug: str) -> Tuple[str, Dict[str, str]]:
    """构建 Lending 市场查询。"""

    query = """
    query LendingMarkets($id: String!) {
      lendingProtocol(id: $id) {
        id
        markets {
          id
          name
          inputToken { id symbol name decimals }
          outputToken { id symbol name decimals }
          rewardTokens { token { id symbol name decimals } }
          rates { side rate type }
          totalValueLockedUSD
          totalDepositBalanceUSD
          totalBorrowBalanceUSD
        }
      }
    }
    """

    return query, {"id": protocol_slug}


def build_dex_pools_query(protocol_slug: str) -> Tuple[str, Dict[str, str]]:
    """构建 DEX 池子查询。"""

    query = """
    query DexPools($id: String!) {
      dexAmmProtocol(id: $id) {
        id
        pools(first: 50, orderBy: totalValueLockedUSD, orderDirection: desc) {
          id
          name
          totalValueLockedUSD
          cumulativeVolumeUSD
          feesUSD
          inputTokens { id symbol name decimals }
          rewardTokens { token { id symbol name decimals } }
        }
      }
    }
    """

    return query, {"id": protocol_slug}


def build_protocol_metrics_query(schema_type: str, protocol_slug: str) -> Tuple[str, Dict[str, str]]:
    """构建协议指标查询。"""

    if schema_type == LENDING_SCHEMA:
        query = """
        query ProtocolMetrics($id: String!) {
          lendingProtocol(id: $id) {
            id
            totalValueLockedUSD
            totalDepositBalanceUSD
            totalBorrowBalanceUSD
            cumulativeSupplySideRevenueUSD
            cumulativeProtocolSideRevenueUSD
            cumulativeTotalRevenueUSD
          }
        }
        """
    elif schema_type == DEX_AMM_SCHEMA:
        query = """
        query ProtocolMetrics($id: String!) {
          dexAmmProtocol(id: $id) {
            id
            totalValueLockedUSD
            cumulativeVolumeUSD
            cumulativeSupplySideRevenueUSD
            cumulativeProtocolSideRevenueUSD
            cumulativeTotalRevenueUSD
          }
        }
        """
    else:
        raise ValueError(f"Unsupported schema type: {schema_type}")

    return query, {"id": protocol_slug}


def _extract_token(token: Dict[str, Any]) -> Dict[str, Any]:
    if not token:
        return {}
    return {
        "id": token.get("id", ""),
        "symbol": token.get("symbol", ""),
        "name": token.get("name", ""),
        "decimals": token.get("decimals"),
    }


def _parse_rates(rates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    parsed: List[Dict[str, Any]] = []
    for rate in rates or []:
        parsed.append(
            {
                "side": rate.get("side", ""),
                "type": rate.get("type", ""),
                "rate": safe_float(rate.get("rate")),
            }
        )
    return parsed


def parse_tvl(protocol_data: Dict[str, Any]) -> float:
    """从协议节点解析 TVL。"""

    return safe_float(protocol_data.get("totalValueLockedUSD"))


def parse_lending_markets(protocol_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析 Lending markets。"""

    markets = protocol_data.get("markets") or []
    parsed: List[Dict[str, Any]] = []
    for market in markets:
        parsed.append(
            {
                "id": market.get("id", ""),
                "name": market.get("name", ""),
                "tvl_usd": safe_float(market.get("totalValueLockedUSD")),
                "total_deposit_usd": safe_float(market.get("totalDepositBalanceUSD")),
                "total_borrow_usd": safe_float(market.get("totalBorrowBalanceUSD")),
                "input_token": _extract_token(market.get("inputToken")),
                "output_token": _extract_token(market.get("outputToken")),
                "reward_tokens": [
                    _extract_token(reward.get("token"))
                    for reward in market.get("rewardTokens") or []
                ],
                "rates": _parse_rates(market.get("rates") or []),
            }
        )
    return parsed


def parse_dex_pools(protocol_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """解析 DEX 池子数据。"""

    pools = protocol_data.get("pools") or []
    parsed: List[Dict[str, Any]] = []
    for pool in pools:
        parsed.append(
            {
                "id": pool.get("id", ""),
                "name": pool.get("name", ""),
                "tvl_usd": safe_float(pool.get("totalValueLockedUSD")),
                "cumulative_volume_usd": safe_float(pool.get("cumulativeVolumeUSD")),
                "fees_usd": safe_float(pool.get("feesUSD")),
                "input_tokens": [
                    _extract_token(token)
                    for token in pool.get("inputTokens") or []
                ],
                "reward_tokens": [
                    _extract_token(reward.get("token"))
                    for reward in pool.get("rewardTokens") or []
                ],
            }
        )
    return parsed


def parse_protocol_metrics(protocol_data: Dict[str, Any]) -> Dict[str, float]:
    """解析协议聚合指标。"""

    return {
        "tvl_usd": safe_float(protocol_data.get("totalValueLockedUSD")),
        "total_deposit_usd": safe_float(protocol_data.get("totalDepositBalanceUSD")),
        "total_borrow_usd": safe_float(protocol_data.get("totalBorrowBalanceUSD")),
        "cumulative_supply_side_revenue_usd": safe_float(
            protocol_data.get("cumulativeSupplySideRevenueUSD")
        ),
        "cumulative_protocol_side_revenue_usd": safe_float(
            protocol_data.get("cumulativeProtocolSideRevenueUSD")
        ),
        "cumulative_total_revenue_usd": safe_float(
            protocol_data.get("cumulativeTotalRevenueUSD")
        ),
        "cumulative_volume_usd": safe_float(protocol_data.get("cumulativeVolumeUSD")),
    }

