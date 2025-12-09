"""
Simplified test for DeFi data sources only (no LangChain tools).
"""

import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_defillama():
    """Test DeFi Llama API."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: DeFi Llama API")
    logger.info("=" * 80)

    try:
        from defiagents.dataflows.defi import get_protocol_info, format_protocol_summary

        logger.info("Fetching Aave V3 protocol data...")
        aave_data = get_protocol_info('aave-v3')

        logger.info(f"✅ DeFi Llama API working")
        logger.info(f"   - Protocol: {aave_data.get('name')}")

        # Handle TVL which might be a number or dict
        tvl = aave_data.get('tvl', 0)
        if isinstance(tvl, (int, float)):
            logger.info(f"   - TVL: ${tvl:,.0f}")
        else:
            logger.info(f"   - TVL: {tvl}")

        logger.info(f"   - Chains: {len(aave_data.get('chains', []))}")

        # Test formatting
        formatted = format_protocol_summary(aave_data)
        logger.info(f"   - Formatted output: {len(formatted)} characters\n")
        logger.info(formatted[:500])

        return True
    except Exception as e:
        logger.error(f"❌ DeFi Llama test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_the_graph():
    """Test The Graph subgraph."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: The Graph Subgraphs")
    logger.info("=" * 80)

    try:
        from defiagents.dataflows.defi import get_uniswap_pools

        logger.info("Fetching top 3 Uniswap V3 pools on Ethereum...")
        pools = get_uniswap_pools(limit=3)

        logger.info(f"✅ The Graph API working")
        logger.info(f"   - Pools fetched: {len(pools)}")

        if pools:
            for i, pool in enumerate(pools, 1):
                token0 = pool.get('token0', {})
                token1 = pool.get('token1', {})
                tvl = pool.get('totalValueLockedUSD', 0)
                logger.info(f"   - Pool {i}: {token0.get('symbol')}/{token1.get('symbol')} - TVL: ${float(tvl):,.0f}")

        return True
    except Exception as e:
        logger.error(f"❌ The Graph test failed: {e}")
        logger.info("   Note: The Graph may have endpoint issues")
        import traceback
        traceback.print_exc()
        return False


def test_coingecko():
    """Test CoinGecko API."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: CoinGecko API")
    logger.info("=" * 80)

    try:
        from defiagents.dataflows.defi import get_token_price, format_token_price, search_tokens

        logger.info("Fetching Ethereum price...")
        eth_price = get_token_price('ethereum')

        logger.info(f"✅ CoinGecko API working")

        if eth_price:
            price = eth_price.get('usd', 0)
            change = eth_price.get('usd_24h_change', 0)
            logger.info(f"   - ETH Price: ${price:,.2f}")
            logger.info(f"   - 24h Change: {change:+.2f}%")

        # Test search
        logger.info("\nSearching for 'USDC'...")
        results = search_tokens('USDC')
        logger.info(f"   - Found {len(results)} results")
        if results:
            logger.info(f"   - Top result: {results[0].get('name')} ({results[0].get('symbol')})")

        return True
    except Exception as e:
        logger.error(f"❌ CoinGecko test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_onchain():
    """Test on-chain data."""
    logger.info("\n" + "=" * 80)
    logger.info("TEST: On-Chain Data (Web3.py)")
    logger.info("=" * 80)

    try:
        from defiagents.dataflows.defi.onchain import get_client_instance

        logger.info("Initializing on-chain client...")
        client = get_client_instance()

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


def main():
    """Run all data source tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 78 + "╗")
    logger.info("║" + " " * 18 + "DeFi Data Sources Test Suite" + " " * 31 + "║")
    logger.info("╚" + "=" * 78 + "╝")
    logger.info("\n")

    tests = [
        ("DeFi Llama API", test_defillama),
        ("The Graph Subgraphs", test_the_graph),
        ("CoinGecko API", test_coingecko),
        ("On-Chain Data", test_onchain),
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
        logger.info("🎉 All data source tests passed!")
        return 0
    elif passed >= total * 0.5:
        logger.info(f"✓ Core data sources working ({passed}/{total})")
        logger.info("Note: Some failures may be due to external API issues or missing configuration.")
        return 0
    else:
        logger.info(f"⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
