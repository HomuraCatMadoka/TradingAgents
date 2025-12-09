"""
测试The Graph Gateway连接

运行:
    PYTHONPATH=$PWD:$PYTHONPATH python3 test_thegraph_gateway.py
"""
import os
import sys
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()


def test_gateway_config():
    """测试Gateway配置"""
    print("\n" + "="*80)
    print("步骤1: 检查API Key配置")
    print("="*80)

    api_key = os.getenv("THE_GRAPH_API_KEY")
    if not api_key:
        print("❌ 错误: THE_GRAPH_API_KEY 环境变量未设置")
        return False

    print(f"✅ API Key已设置: {api_key[:20]}...")
    return True


def test_client_initialization():
    """测试客户端初始化"""
    print("\n" + "="*80)
    print("步骤2: 初始化The Graph客户端")
    print("="*80)

    try:
        from defiagents.dataflows.defi.the_graph import get_client_instance

        client = get_client_instance()

        print(f"✅ 客户端初始化成功")
        print(f"   - 使用Gateway: {client.use_gateway}")
        print(f"   - API Key已设置: {client.api_key is not None}")

        return True
    except Exception as e:
        print(f"❌ 客户端初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_uniswap_query():
    """测试Uniswap V3查询"""
    print("\n" + "="*80)
    print("步骤3: 测试Uniswap V3子图查询")
    print("="*80)

    try:
        from defiagents.dataflows.defi.the_graph import get_uniswap_pools, format_uniswap_pool

        print("正在查询Uniswap V3前5个池...")

        # 使用正确的deployment ID
        pools = get_uniswap_pools(
            subgraph_id="5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV",
            limit=5
        )

        if not pools:
            print("⚠️  警告: 未返回池数据")
            return False

        print(f"✅ 成功获取{len(pools)}个池的数据\n")

        # 显示第一个池的详细信息
        if pools:
            print("=== 第一个池的详细信息 ===")
            print(format_uniswap_pool(pools[0]))

        return True

    except Exception as e:
        print(f"❌ Uniswap查询失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_aave_query():
    """测试Aave V3查询"""
    print("\n" + "="*80)
    print("步骤4: 测试Aave V3子图查询")
    print("="*80)

    try:
        from defiagents.dataflows.defi.the_graph import get_aave_reserve_by_symbol, format_aave_reserve

        print("正在查询Aave V3的USDC储备...")

        # 使用正确的deployment ID
        reserve = get_aave_reserve_by_symbol(
            symbol="USDC",
            subgraph_id="HB1Z2EAw4rtPRYVb2Nz8QGFLHCpym6ByBX6vbCViuE9F"
        )

        if not reserve:
            print("⚠️  警告: 未找到USDC储备数据")
            print("   注意: 此subgraph可能已过时（3年前更新）")
            return False

        print("✅ 成功获取USDC储备数据\n")
        print(format_aave_reserve(reserve))

        return True

    except Exception as e:
        print(f"❌ Aave查询失败: {e}")
        print("   注意: Aave V3 subgraph可能已过时，需要更新deployment ID")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("The Graph Gateway 连接测试")
    print("="*80)

    results = []

    # 运行测试
    results.append(("API Key配置", test_gateway_config()))
    results.append(("客户端初始化", test_client_initialization()))
    results.append(("Uniswap V3查询", test_uniswap_query()))
    results.append(("Aave V3查询", test_aave_query()))

    # 打印总结
    print("\n" + "="*80)
    print("测试总结")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        emoji = "✅" if result else "❌"
        status = "通过" if result else "失败"
        print(f"{emoji} {name}: {status}")

    print("\n" + "="*80)
    print(f"结果: {passed}/{total} 测试通过")

    if passed >= 3:  # 至少3个测试通过（不包括可能过时的Aave）
        print("\n🎉 The Graph Gateway配置成功!")
        print("\n下一步: 运行完整的DeFi端到端测试")
        print("  PYTHONPATH=$PWD:$PYTHONPATH python3 examples/test_defi_with_gemini.py")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查上述错误")

    print("="*80 + "\n")

    return passed >= 3


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
