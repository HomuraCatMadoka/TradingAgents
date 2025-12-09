"""
Test script for official DeFi protocol APIs.

Tests the newly implemented API clients:
- Curve Finance API
- Yearn Finance API
- Beefy Finance API
- GMX API
- PancakeSwap API

Run with:
    python3 tests/test_official_apis.py
"""

import sys
import time
from typing import Dict, Any


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print('=' * 80)


def print_test(name: str, status: str, details: str = ""):
    """Print test result."""
    emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
    print(f"{emoji} {name}: {status}")
    if details:
        print(f"   {details}")


def test_curve_api():
    """Test Curve Finance API."""
    print_section("Testing Curve Finance API")

    try:
        from defiagents.dataflows.defi import CurveAPI, get_curve_pools

        client = CurveAPI()

        # Test 1: Get pools
        print("\n1. Testing get_pools()...")
        pools_data = client.get_pools("ethereum")

        if pools_data and pools_data.get("success"):
            pool_count = len(pools_data.get("data", {}).get("poolData", []))
            print_test("Get Ethereum pools", "PASS", f"Found {pool_count} pools")
        else:
            print_test("Get Ethereum pools", "FAIL", "No data returned")
            return False

        # Test 2: Get top pools
        print("\n2. Testing get_top_pools()...")
        top_pools = client.get_top_pools("ethereum", limit=3)

        if top_pools and len(top_pools) > 0:
            print_test("Get top pools", "PASS", f"Retrieved {len(top_pools)} pools")
            for i, pool in enumerate(top_pools[:2], 1):
                tvl = pool.get("tvlUSD", 0) or pool.get("usdTotal", 0)
                print(f"   Pool {i}: {pool.get('name', 'Unknown')} - TVL: ${tvl:,.2f}")
        else:
            print_test("Get top pools", "WARN", "No pools returned")

        # Test 3: Get total TVL
        print("\n3. Testing get_total_tvl()...")
        total_tvl = client.get_total_tvl("ethereum")

        if total_tvl > 0:
            print_test("Get total TVL", "PASS", f"${total_tvl:,.2f}")
        else:
            print_test("Get total TVL", "WARN", "TVL is 0")

        # Test 4: Convenience function
        print("\n4. Testing convenience function get_curve_pools()...")
        pools = get_curve_pools("ethereum", limit=2)

        if pools and len(pools) > 0:
            print_test("Convenience function", "PASS", f"Retrieved {len(pools)} pools")
        else:
            print_test("Convenience function", "WARN", "No pools returned")

        return True

    except Exception as e:
        print_test("Curve API", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_yearn_api():
    """Test Yearn Finance API."""
    print_section("Testing Yearn Finance API")

    try:
        from defiagents.dataflows.defi import YearnAPI, get_yearn_vaults

        client = YearnAPI()

        # Test 1: Get vaults
        print("\n1. Testing get_vaults()...")
        vaults = client.get_vaults("ethereum")

        if vaults and len(vaults) > 0:
            print_test("Get Ethereum vaults", "PASS", f"Found {len(vaults)} vaults")
        else:
            print_test("Get Ethereum vaults", "FAIL", "No vaults returned")
            return False

        # Test 2: Get top vaults
        print("\n2. Testing get_top_vaults()...")
        top_vaults = client.get_top_vaults("ethereum", limit=3)

        if top_vaults and len(top_vaults) > 0:
            print_test("Get top vaults", "PASS", f"Retrieved {len(top_vaults)} vaults")
            for i, vault in enumerate(top_vaults[:2], 1):
                name = vault.get("display_name") or vault.get("name", "Unknown")
                tvl = vault.get("tvl", {}).get("tvl", 0)
                apy = vault.get("apy", {}).get("net_apy", 0) * 100
                print(f"   Vault {i}: {name} - TVL: ${tvl:,.2f} - APY: {apy:.2f}%")
        else:
            print_test("Get top vaults", "WARN", "No vaults returned")

        # Test 3: Get total TVL
        print("\n3. Testing get_total_tvl()...")
        total_tvl = client.get_total_tvl("ethereum")

        if total_tvl > 0:
            print_test("Get total TVL", "PASS", f"${total_tvl:,.2f}")
        else:
            print_test("Get total TVL", "WARN", "TVL is 0")

        # Test 4: Convenience function
        print("\n4. Testing convenience function get_yearn_vaults()...")
        vaults = get_yearn_vaults("ethereum", limit=2)

        if vaults and len(vaults) > 0:
            print_test("Convenience function", "PASS", f"Retrieved {len(vaults)} vaults")
        else:
            print_test("Convenience function", "WARN", "No vaults returned")

        return True

    except Exception as e:
        print_test("Yearn API", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_beefy_api():
    """Test Beefy Finance API."""
    print_section("Testing Beefy Finance API")

    try:
        from defiagents.dataflows.defi import BeefyAPI, get_beefy_vaults

        client = BeefyAPI()

        # Test 1: Get all vaults
        print("\n1. Testing get_vaults()...")
        all_vaults = client.get_vaults()

        if all_vaults and len(all_vaults) > 0:
            print_test("Get all vaults", "PASS", f"Found {len(all_vaults)} vaults across all chains")
        else:
            print_test("Get all vaults", "FAIL", "No vaults returned")
            return False

        # Test 2: Get vaults by chain
        print("\n2. Testing get_vaults_by_chain()...")
        arb_vaults = client.get_vaults_by_chain("arbitrum")

        if arb_vaults and len(arb_vaults) > 0:
            print_test("Get Arbitrum vaults", "PASS", f"Found {len(arb_vaults)} vaults")
        else:
            print_test("Get Arbitrum vaults", "WARN", "No vaults returned")

        # Test 3: Get top vaults
        print("\n3. Testing get_top_vaults()...")
        top_vaults = client.get_top_vaults(chain="arbitrum", limit=3)

        if top_vaults and len(top_vaults) > 0:
            print_test("Get top vaults", "PASS", f"Retrieved {len(top_vaults)} vaults")
            for i, vault in enumerate(top_vaults[:2], 1):
                name = vault.get("name", "Unknown")
                tvl = vault.get("tvl", 0)
                apy = vault.get("apy", 0)
                print(f"   Vault {i}: {name} - TVL: ${tvl:,.2f} - APY: {apy:.2f}%")
        else:
            print_test("Get top vaults", "WARN", "No vaults returned")

        # Test 4: Get total TVL for a chain
        print("\n4. Testing get_total_tvl()...")
        total_tvl = client.get_total_tvl(chain="arbitrum")

        if total_tvl > 0:
            print_test("Get Arbitrum TVL", "PASS", f"${total_tvl:,.2f}")
        else:
            print_test("Get Arbitrum TVL", "WARN", "TVL is 0")

        # Test 5: Convenience function
        print("\n5. Testing convenience function get_beefy_vaults()...")
        vaults = get_beefy_vaults("arbitrum", limit=2)

        if vaults and len(vaults) > 0:
            print_test("Convenience function", "PASS", f"Retrieved {len(vaults)} vaults")
        else:
            print_test("Convenience function", "WARN", "No vaults returned")

        return True

    except Exception as e:
        print_test("Beefy API", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_gmx_api():
    """Test GMX API."""
    print_section("Testing GMX API")

    try:
        from defiagents.dataflows.defi import GMXAPI, get_gmx_stats

        client = GMXAPI()

        # Test 1: Get stats
        print("\n1. Testing get_stats()...")
        stats = client.get_stats("arbitrum")

        if stats and len(stats) > 0:
            print_test("Get Arbitrum stats", "PASS", f"Retrieved {len(stats)} metrics")
        else:
            print_test("Get Arbitrum stats", "FAIL", "No stats returned")
            return False

        # Test 2: Get GLP price
        print("\n2. Testing get_glp_price()...")
        glp_price = client.get_glp_price("arbitrum")

        if glp_price > 0:
            print_test("Get GLP price", "PASS", f"${glp_price:.4f}")
        else:
            print_test("Get GLP price", "WARN", "GLP price is 0")

        # Test 3: Get GLP APY
        print("\n3. Testing get_glp_apy()...")
        apy = client.get_glp_apy("arbitrum")

        if apy:
            total_apy = apy.get("total_apy", 0)
            print_test("Get GLP APY", "PASS", f"Total APY: {total_apy:.2f}%")
            print(f"   Fee APY: {apy.get('fee_apy', 0):.2f}%")
            print(f"   esGMX APY: {apy.get('esGMX_apy', 0):.2f}%")
        else:
            print_test("Get GLP APY", "WARN", "No APY data")

        # Test 4: Get total volume
        print("\n4. Testing get_total_volume()...")
        volume = client.get_total_volume("arbitrum")

        if volume > 0:
            print_test("Get total volume", "PASS", f"${volume:,.2f}")
        else:
            print_test("Get total volume", "WARN", "Volume is 0")

        # Test 5: Convenience function
        print("\n5. Testing convenience function get_gmx_stats()...")
        stats = get_gmx_stats("arbitrum")

        if stats:
            print_test("Convenience function", "PASS", "Retrieved GMX stats")
            print(f"   Total Volume: ${stats.get('total_volume', 0):,.2f}")
            print(f"   Total Fees: ${stats.get('total_fees', 0):,.2f}")
            print(f"   Open Interest: ${stats.get('open_interest', 0):,.2f}")
        else:
            print_test("Convenience function", "WARN", "No stats returned")

        return True

    except Exception as e:
        print_test("GMX API", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_pancakeswap_api():
    """Test PancakeSwap API."""
    print_section("Testing PancakeSwap API")

    try:
        from defiagents.dataflows.defi import PancakeSwapAPI, get_pancake_pairs

        client = PancakeSwapAPI()

        # Test 1: Get summary
        print("\n1. Testing get_summary()...")
        summary = client.get_summary()

        if summary and "data" in summary:
            data = summary["data"]
            print_test("Get summary", "PASS", "Retrieved protocol summary")
            print(f"   24h Volume: ${data.get('total_volume_24h', 0):,.2f}")
            print(f"   Total Liquidity: ${data.get('total_liquidity', 0):,.2f}")
            print(f"   Total Pairs: {data.get('total_pairs', 0):,}")
        else:
            print_test("Get summary", "FAIL", "No summary data")
            return False

        # Test 2: Get pairs
        print("\n2. Testing get_pairs()...")
        pairs_data = client.get_pairs()

        if pairs_data and "data" in pairs_data:
            pair_count = len(pairs_data["data"])
            print_test("Get all pairs", "PASS", f"Found {pair_count} pairs")
        else:
            print_test("Get all pairs", "WARN", "No pairs returned")

        # Test 3: Get top pairs
        print("\n3. Testing get_top_pairs()...")
        top_pairs = client.get_top_pairs(limit=3)

        if top_pairs and len(top_pairs) > 0:
            print_test("Get top pairs", "PASS", f"Retrieved {len(top_pairs)} pairs")
            for i, pair in enumerate(top_pairs[:2], 1):
                base = pair.get("base_symbol", "?")
                quote = pair.get("quote_symbol", "?")
                liquidity = float(pair.get("liquidity", 0))
                print(f"   Pair {i}: {base}/{quote} - Liquidity: ${liquidity:,.2f}")
        else:
            print_test("Get top pairs", "WARN", "No pairs returned")

        # Test 4: Get total TVL
        print("\n4. Testing get_total_tvl()...")
        tvl = client.get_total_tvl()

        if tvl > 0:
            print_test("Get total TVL", "PASS", f"${tvl:,.2f}")
        else:
            print_test("Get total TVL", "WARN", "TVL is 0")

        # Test 5: Convenience function
        print("\n5. Testing convenience function get_pancake_pairs()...")
        pairs = get_pancake_pairs(limit=2)

        if pairs and len(pairs) > 0:
            print_test("Convenience function", "PASS", f"Retrieved {len(pairs)} pairs")
        else:
            print_test("Convenience function", "WARN", "No pairs returned")

        return True

    except Exception as e:
        print_test("PancakeSwap API", "FAIL", f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all API tests."""
    print("\n" + "=" * 80)
    print("  DeFi Official API Integration Tests")
    print("=" * 80)
    print("\nTesting 5 newly implemented official API clients...")

    results = {}

    # Run tests
    print("\n⏳ Starting tests... (this may take a minute)")
    time.sleep(1)

    results["Curve"] = test_curve_api()
    time.sleep(1)

    results["Yearn"] = test_yearn_api()
    time.sleep(1)

    results["Beefy"] = test_beefy_api()
    time.sleep(1)

    results["GMX"] = test_gmx_api()
    time.sleep(1)

    results["PancakeSwap"] = test_pancakeswap_api()

    # Print summary
    print_section("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nResults: {passed}/{total} API clients passed tests\n")

    for api, result in results.items():
        emoji = "✅" if result else "❌"
        status = "PASS" if result else "FAIL"
        print(f"{emoji} {api} API: {status}")

    print("\n" + "=" * 80)

    if passed == total:
        print("🎉 All API tests passed!")
    elif passed > 0:
        print(f"⚠️  {total - passed} API client(s) failed. Check errors above.")
    else:
        print("❌ All API tests failed. Check configuration and network connection.")

    print("=" * 80 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
