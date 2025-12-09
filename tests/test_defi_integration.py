"""
Test script for DeFi data sources and tools integration.

This script tests the basic functionality of:
- DeFi Llama API
- The Graph subgraphs
- CoinGecko API
- On-chain data (Web3.py)
- LangChain tool interfaces
"""

import sys
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all modules can be imported."""
    logger.info("=" * 80)
    logger.info("TEST 1: Module Imports")
    logger.info("=" * 80)

    try:
        # Test DeFi data source imports
        from defiagents.dataflows.defi import (
            DefiLlamaAPI,
            get_protocol_tvl,
            get_protocol_info,
            TheGraphClient,
            query_subgraph,
            get_uniswap_pools,
            CoinGeckoAPI,
            get_token_price,
            OnChainClient,
            get_block_number,
        )
        logger.info("✅ DeFi data source imports successful")

        # Test tool imports
        from defiagents.agents.utils.defi_protocol_tools import PROTOCOL_TOOLS
        from defiagents.agents.utils.defi_pool_tools import POOL_TOOLS
        from defiagents.agents.utils.defi_wallet_tools import WALLET_TOOLS
        from defiagents.agents.utils.defi_market_tools import MARKET_TOOLS

        logger.info(f"✅ Tool imports successful")
        logger.info(f"   - Protocol Tools: {len(PROTOCOL_TOOLS)} tools")
        logger.info(f"   - Pool Tools: {len(POOL_TOOLS)} tools")
        logger.info(f"   - Wallet Tools: {len(WALLET_TOOLS)} tools")
        logger.info(f"   - Market Tools: {len(MARKET_TOOLS)} tools")

        return True
    except Exception as e:
        logger.error(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_defillama():
    """Test DeFi Llama API integration."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 2: DeFi Llama API")
    logger.info("=" * 80)

    try:
        from defiagents.dataflows.defi import get_protocol_info, format_protocol_summary

        # Test getting Aave V3 data
        logger.info("Fetching Aave V3 protocol data...")
        aave_data = get_protocol_info('aave-v3')

        logger.info(f"✅ DeFi Llama API working")
        logger.info(f"   - Protocol: {aave_data.get('name')}")
        logger.info(f"   - TVL: ${aave_data.get('tvl', 0):,.0f}")
        logger.info(f"   - Chains: {len(aave_data.get('chains', []))}")

        # Test formatting
        formatted = format_protocol_summary(aave_data)
        logger.info(f"   - Formatted output: {len(formatted)} characters")

        return True
    except Exception as e:
        logger.error(f"❌ DeFi Llama test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_the_graph():
    """Test The Graph subgraph integration."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 3: The Graph Subgraphs")
    logger.info("=" * 80)

    try:
        from defiagents.dataflows.defi import get_uniswap_pools

        # Test getting Uniswap V3 pools
        logger.info("Fetching top 3 Uniswap V3 pools on Ethereum...")
        pools = get_uniswap_pools(limit=3)

        logger.info(f"✅ The Graph API working")
        logger.info(f"   - Pools fetched: {len(pools)}")

        if pools:
            pool = pools[0]
            token0 = pool.get('token0', {})
            token1 = pool.get('token1', {})
            logger.info(f"   - Top pool: {token0.get('symbol')}/{token1.get('symbol')}")
            logger.info(f"   - TVL: ${float(pool.get('totalValueLockedUSD', 0)):,.0f}")

        return True
    except Exception as e:
        logger.error(f"❌ The Graph test failed: {e}")
        logger.info("   Note: The Graph may require a valid subgraph endpoint")
        import traceback
        traceback.print_exc()
        return False


def test_coingecko():
    """Test CoinGecko API integration."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 4: CoinGecko API")
    logger.info("=" * 80)

    try:
        from defiagents.dataflows.defi import get_token_price, format_token_price

        # Test getting Ethereum price
        logger.info("Fetching Ethereum price...")
        eth_price = get_token_price('ethereum')

        logger.info(f"✅ CoinGecko API working")

        if eth_price:
            price = eth_price.get('usd', 0)
            change = eth_price.get('usd_24h_change', 0)
            logger.info(f"   - ETH Price: ${price:,.2f}")
            logger.info(f"   - 24h Change: {change:+.2f}%")

            # Test formatting
            formatted = format_token_price('ethereum', eth_price)
            logger.info(f"   - Formatted output: {len(formatted)} characters")

        return True
    except Exception as e:
        logger.error(f"❌ CoinGecko test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_onchain():
    """Test on-chain data integration."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 5: On-Chain Data (Web3.py)")
    logger.info("=" * 80)

    try:
        from defiagents.dataflows.defi.onchain import get_client_instance

        logger.info("Initializing on-chain client...")
        client = get_client_instance()

        # Check which chains are available
        available_chains = list(client._web3_instances.keys())

        if available_chains:
            logger.info(f"✅ On-chain client initialized")
            logger.info(f"   - Available chains: {', '.join(available_chains)}")

            # Try to get block number from first available chain
            test_chain = available_chains[0]
            block_num = client.get_block_number(test_chain)

            if block_num:
                logger.info(f"   - {test_chain.title()} block number: {block_num:,}")
        else:
            logger.warning("⚠️  No RPC endpoints configured")
            logger.info("   Note: Configure RPC URLs in default_config.py to enable on-chain data")
            logger.info("   This is expected if API keys are not set")

        return True
    except Exception as e:
        logger.error(f"❌ On-chain test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_protocol_tools():
    """Test protocol analysis tools."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 6: Protocol Analysis Tools")
    logger.info("=" * 80)

    try:
        from defiagents.agents.utils.defi_protocol_tools import get_protocol_tvl

        # Test protocol TVL tool
        logger.info("Testing get_protocol_tvl tool...")
        result = get_protocol_tvl.invoke({"protocol_slug": "uniswap-v3"})

        logger.info(f"✅ Protocol tools working")
        logger.info(f"   - Tool output: {result[:100]}...")

        return True
    except Exception as e:
        logger.error(f"❌ Protocol tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_market_tools():
    """Test market data tools."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST 7: Market Data Tools")
    logger.info("=" * 80)

    try:
        from defiagents.agents.utils.defi_market_tools import get_crypto_price

        # Test crypto price tool
        logger.info("Testing get_crypto_price tool...")
        result = get_crypto_price.invoke({"token_id": "bitcoin"})

        logger.info(f"✅ Market tools working")
        logger.info(f"   - Tool output: {result[:100]}...")

        return True
    except Exception as e:
        logger.error(f"❌ Market tools test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 20 + "DeFi Integration Test Suite" + " " * 31 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("\n")

    tests = [
        ("Module Imports", test_imports),
        ("DeFi Llama API", test_defillama),
        ("The Graph Subgraphs", test_the_graph),
        ("CoinGecko API", test_coingecko),
        ("On-Chain Data", test_onchain),
        ("Protocol Tools", test_protocol_tools),
        ("Market Tools", test_market_tools),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Unexpected error in {test_name}: {e}")
            results[test_name] = False

    # Summary
    logger.info("\n" + "=" * 80)
    logger.info("TEST SUMMARY")
    logger.info("=" * 80)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status}: {test_name}")

    logger.info("\n" + "-" * 80)
    logger.info(f"Results: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 All tests passed!")
        return 0
    else:
        logger.info(f"⚠️  {total - passed} test(s) failed")
        logger.info("\nNote: Some failures are expected if API keys are not configured.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
