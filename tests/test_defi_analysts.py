"""
Test script for DeFi Analyst agents.

Tests the 4 new DeFi analysts:
- DeFi Market Analyst
- Protocol Analyst
- Yield Analyst
- DeFi Risk Analyst

Run with:
    PYTHONPATH=/Users/wangkunyu/develop/TradingAgents:$PYTHONPATH python3 tests/test_defi_analysts.py
"""

import sys
import os
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
        for line in details.split('\n'):
            print(f"   {line}")


def test_analyst_imports():
    """Test that all analysts can be imported."""
    print_section("Testing Analyst Imports")

    results = {}

    try:
        from defiagents.agents.analysts.defi_market_analyst import create_defi_market_analyst
        print_test("Import DeFi Market Analyst", "PASS")
        results["market"] = True
    except Exception as e:
        print_test("Import DeFi Market Analyst", "FAIL", str(e))
        results["market"] = False

    try:
        from defiagents.agents.analysts.protocol_analyst import create_protocol_analyst
        print_test("Import Protocol Analyst", "PASS")
        results["protocol"] = True
    except Exception as e:
        print_test("Import Protocol Analyst", "FAIL", str(e))
        results["protocol"] = False

    try:
        from defiagents.agents.analysts.yield_analyst import create_yield_analyst
        print_test("Import Yield Analyst", "PASS")
        results["yield"] = True
    except Exception as e:
        print_test("Import Yield Analyst", "FAIL", str(e))
        results["yield"] = False

    try:
        from defiagents.agents.analysts.defi_risk_analyst import create_defi_risk_analyst
        print_test("Import DeFi Risk Analyst", "PASS")
        results["risk"] = True
    except Exception as e:
        print_test("Import DeFi Risk Analyst", "FAIL", str(e))
        results["risk"] = False

    return all(results.values()), results


def test_analyst_creation():
    """Test that analysts can be created with a mock LLM."""
    print_section("Testing Analyst Creation")

    # Create a very simple mock LLM for testing structure
    class MockLLM:
        def bind_tools(self, tools):
            return self

        def invoke(self, messages):
            class MockResult:
                content = "Mock analysis result"
                tool_calls = []
            return MockResult()

    mock_llm = MockLLM()
    results = {}

    try:
        from defiagents.agents.analysts.defi_market_analyst import create_defi_market_analyst
        analyst = create_defi_market_analyst(mock_llm)
        print_test("Create DeFi Market Analyst", "PASS", "Factory function works")
        results["market"] = True
    except Exception as e:
        print_test("Create DeFi Market Analyst", "FAIL", str(e))
        results["market"] = False

    try:
        from defiagents.agents.analysts.protocol_analyst import create_protocol_analyst
        analyst = create_protocol_analyst(mock_llm)
        print_test("Create Protocol Analyst", "PASS", "Factory function works")
        results["protocol"] = True
    except Exception as e:
        print_test("Create Protocol Analyst", "FAIL", str(e))
        results["protocol"] = False

    try:
        from defiagents.agents.analysts.yield_analyst import create_yield_analyst
        analyst = create_yield_analyst(mock_llm)
        print_test("Create Yield Analyst", "PASS", "Factory function works")
        results["yield"] = True
    except Exception as e:
        print_test("Create Yield Analyst", "FAIL", str(e))
        results["yield"] = False

    try:
        from defiagents.agents.analysts.defi_risk_analyst import create_defi_risk_analyst
        analyst = create_defi_risk_analyst(mock_llm)
        print_test("Create DeFi Risk Analyst", "PASS", "Factory function works")
        results["risk"] = True
    except Exception as e:
        print_test("Create DeFi Risk Analyst", "FAIL", str(e))
        results["risk"] = False

    return all(results.values()), results


def test_analyst_state_handling():
    """Test that analysts can handle state correctly."""
    print_section("Testing Analyst State Handling")

    class MockLLM:
        def bind_tools(self, tools):
            return self

        def invoke(self, messages):
            class MockResult:
                content = "Mock analysis result"
                tool_calls = []
            return MockResult()

    mock_llm = MockLLM()

    # Mock state
    mock_state = {
        "messages": [],
        "trade_date": "2025-12-10",
        "protocol_of_interest": "aave-v3",
        "chain": "arbitrum",
        "investment_amount": 10000,
    }

    results = {}

    # Test DeFi Market Analyst
    try:
        from defiagents.agents.analysts.defi_market_analyst import create_defi_market_analyst
        analyst = create_defi_market_analyst(mock_llm)
        result = analyst(mock_state)

        assert "messages" in result, "Missing 'messages' in result"
        assert "market_report" in result, "Missing 'market_report' in result"
        print_test("DeFi Market Analyst state handling", "PASS",
                   f"Returns: messages, market_report")
        results["market"] = True
    except Exception as e:
        print_test("DeFi Market Analyst state handling", "FAIL", str(e))
        results["market"] = False

    # Test Protocol Analyst
    try:
        from defiagents.agents.analysts.protocol_analyst import create_protocol_analyst
        analyst = create_protocol_analyst(mock_llm)
        result = analyst(mock_state)

        assert "messages" in result, "Missing 'messages' in result"
        assert "fundamentals_report" in result, "Missing 'fundamentals_report' in result"
        print_test("Protocol Analyst state handling", "PASS",
                   f"Returns: messages, fundamentals_report")
        results["protocol"] = True
    except Exception as e:
        print_test("Protocol Analyst state handling", "FAIL", str(e))
        results["protocol"] = False

    # Test Yield Analyst
    try:
        from defiagents.agents.analysts.yield_analyst import create_yield_analyst
        analyst = create_yield_analyst(mock_llm)
        result = analyst(mock_state)

        assert "messages" in result, "Missing 'messages' in result"
        assert "yield_report" in result, "Missing 'yield_report' in result"
        print_test("Yield Analyst state handling", "PASS",
                   f"Returns: messages, yield_report")
        results["yield"] = True
    except Exception as e:
        print_test("Yield Analyst state handling", "FAIL", str(e))
        results["yield"] = False

    # Test DeFi Risk Analyst
    try:
        from defiagents.agents.analysts.defi_risk_analyst import create_defi_risk_analyst
        analyst = create_defi_risk_analyst(mock_llm)
        result = analyst(mock_state)

        assert "messages" in result, "Missing 'messages' in result"
        assert "risk_report" in result, "Missing 'risk_report' in result"
        print_test("DeFi Risk Analyst state handling", "PASS",
                   f"Returns: messages, risk_report")
        results["risk"] = True
    except Exception as e:
        print_test("DeFi Risk Analyst state handling", "FAIL", str(e))
        results["risk"] = False

    return all(results.values()), results


def test_tool_availability():
    """Test that DeFi tools can be imported and are available."""
    print_section("Testing DeFi Tool Availability")

    results = {}

    # Test protocol tools
    try:
        from defiagents.agents.utils.defi_protocol_tools import (
            get_protocol_overview,
            get_protocol_tvl,
            get_all_defi_protocols,
            get_chain_tvl_overview,
            compare_protocols,
            search_protocols_by_category,
        )
        print_test("Import protocol tools", "PASS", "6 tools available")
        results["protocol_tools"] = True
    except Exception as e:
        print_test("Import protocol tools", "FAIL", str(e))
        results["protocol_tools"] = False

    # Test pool tools
    try:
        from defiagents.agents.utils.defi_pool_tools import (
            get_uniswap_top_pools,
            get_uniswap_pool_details,
            get_aave_lending_markets,
            get_aave_asset_details,
            compare_yield_opportunities,
        )
        print_test("Import pool tools", "PASS", "5 tools available")
        results["pool_tools"] = True
    except Exception as e:
        print_test("Import pool tools", "FAIL", str(e))
        results["pool_tools"] = False

    # Test market tools
    try:
        from defiagents.agents.utils.defi_market_tools import (
            get_crypto_price,
            get_crypto_market_data,
            search_crypto_tokens,
            compare_token_prices,
            get_trending_tokens,
            get_global_defi_metrics,
            get_token_by_contract,
        )
        print_test("Import market tools", "PASS", "7 tools available")
        results["market_tools"] = True
    except Exception as e:
        print_test("Import market tools", "FAIL", str(e))
        results["market_tools"] = False

    # Test wallet tools
    try:
        from defiagents.agents.utils.defi_wallet_tools import (
            get_native_balance,
            get_erc20_balance,
            get_token_info,
            get_wallet_portfolio,
            get_current_block,
            get_gas_price,
        )
        print_test("Import wallet tools", "PASS", "6 tools available")
        results["wallet_tools"] = True
    except Exception as e:
        print_test("Import wallet tools", "FAIL", str(e))
        results["wallet_tools"] = False

    return all(results.values()), results


def test_data_sources():
    """Test that DeFi data sources can be imported."""
    print_section("Testing DeFi Data Source Imports")

    results = {}

    # Test DeFi Llama
    try:
        from defiagents.dataflows.defi import DefiLlamaAPI, get_protocol_info
        print_test("DeFi Llama integration", "PASS")
        results["defillama"] = True
    except Exception as e:
        print_test("DeFi Llama integration", "FAIL", str(e))
        results["defillama"] = False

    # Test The Graph
    try:
        from defiagents.dataflows.defi import TheGraphClient, get_uniswap_pools
        print_test("The Graph integration", "PASS")
        results["the_graph"] = True
    except Exception as e:
        print_test("The Graph integration", "FAIL", str(e))
        results["the_graph"] = False

    # Test CoinGecko
    try:
        from defiagents.dataflows.defi import CoinGeckoAPI, get_token_price
        print_test("CoinGecko integration", "PASS")
        results["coingecko"] = True
    except Exception as e:
        print_test("CoinGecko integration", "FAIL", str(e))
        results["coingecko"] = False

    # Test On-chain
    try:
        from defiagents.dataflows.defi import OnChainClient, get_token_balance
        print_test("On-chain (Web3.py) integration", "PASS")
        results["onchain"] = True
    except Exception as e:
        print_test("On-chain (Web3.py) integration", "FAIL", str(e))
        results["onchain"] = False

    # Test Curve API
    try:
        from defiagents.dataflows.defi import CurveAPI, get_curve_pools
        print_test("Curve API integration", "PASS")
        results["curve"] = True
    except Exception as e:
        print_test("Curve API integration", "FAIL", str(e))
        results["curve"] = False

    # Test Yearn API
    try:
        from defiagents.dataflows.defi import YearnAPI, get_yearn_vaults
        print_test("Yearn API integration", "PASS")
        results["yearn"] = True
    except Exception as e:
        print_test("Yearn API integration", "FAIL", str(e))
        results["yearn"] = False

    # Test Beefy API
    try:
        from defiagents.dataflows.defi import BeefyAPI, get_beefy_vaults
        print_test("Beefy API integration", "PASS")
        results["beefy"] = True
    except Exception as e:
        print_test("Beefy API integration", "FAIL", str(e))
        results["beefy"] = False

    return all(results.values()), results


def main():
    """Run all analyst tests."""
    print("\n" + "=" * 80)
    print("  DeFi Analyst Integration Tests")
    print("=" * 80)
    print("\nTesting 4 new DeFi analysts and their dependencies...")

    all_results = {}

    # Test 1: Imports
    success, results = test_analyst_imports()
    all_results["imports"] = success

    # Test 2: Creation
    success, results = test_analyst_creation()
    all_results["creation"] = success

    # Test 3: State handling
    success, results = test_analyst_state_handling()
    all_results["state_handling"] = success

    # Test 4: Tool availability
    success, results = test_tool_availability()
    all_results["tools"] = success

    # Test 5: Data sources
    success, results = test_data_sources()
    all_results["data_sources"] = success

    # Print summary
    print_section("Test Summary")

    passed = sum(1 for v in all_results.values() if v)
    total = len(all_results)

    print(f"\nResults: {passed}/{total} test categories passed\n")

    test_names = {
        "imports": "Analyst Imports",
        "creation": "Analyst Creation",
        "state_handling": "State Handling",
        "tools": "Tool Availability",
        "data_sources": "Data Sources",
    }

    for test_id, result in all_results.items():
        emoji = "✅" if result else "❌"
        status = "PASS" if result else "FAIL"
        print(f"{emoji} {test_names[test_id]}: {status}")

    print("\n" + "=" * 80)

    if passed == total:
        print("🎉 All analyst tests passed!")
        print("\nNext steps:")
        print("1. Update LangGraph routing to use new analysts")
        print("2. Update state schema for DeFi parameters")
        print("3. Run end-to-end workflow tests")
    elif passed > 0:
        print(f"⚠️  {total - passed} test category(ies) failed. Check errors above.")
    else:
        print("❌ All tests failed. Check imports and dependencies.")

    print("=" * 80 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
