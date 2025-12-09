"""
使用Google Gemini测试DeFi协议分析

运行:
    PYTHONPATH=/Users/wangkunyu/develop/TradingAgents:$PYTHONPATH python3 examples/test_defi_with_gemini.py
"""
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

def main():
    print("\n" + "="*80)
    print("DeFi Agent 测试 - Google Gemini 免费版")
    print("="*80)
    
    # 检查API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("\n❌ 错误: 请先设置 GOOGLE_API_KEY")
        print("运行: export GOOGLE_API_KEY='your_api_key'")
        return False
    
    try:
        # 导入配置
        from gemini_config import GEMINI_CONFIG
        from defiagents.graph.trading_graph import TradingAgentsGraph
        
        print("\n正在初始化DeFi Agent系统...")
        print("  - LLM Provider: Google Gemini")
        print("  - Quick Model: gemini-1.5-flash")
        print("  - Deep Model: gemini-1.5-pro")
        print("  - Analysts: DeFi Market, Protocol, Yield, Risk")
        
        # 创建graph实例
        graph = TradingAgentsGraph(
            selected_analysts=["defi_market", "protocol", "yield", "risk"],
            config=GEMINI_CONFIG,
            debug=True  # 打印详细日志
        )
        
        print("\n" + "="*80)
        print("开始分析: Aave V3 协议")
        print("="*80)
        print("  协议: aave-v3")
        print("  链: ethereum")
        print("  日期: " + datetime.now().strftime("%Y-%m-%d"))
        print("\n这可能需要2-5分钟，请耐心等待...\n")
        
        # 运行分析
        result, signal = graph.propagate(
            company_name="aave-v3",
            trade_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        # 打印结果
        print("\n" + "="*80)
        print("✅ 分析完成!")
        print("="*80)
        
        # 打印各个报告
        reports = [
            ("📊 DeFi Market Report", "market_report"),
            ("🏛️ Protocol Fundamentals", "fundamentals_report"),
            ("💰 Yield Analysis", "yield_report"),
            ("⚠️ Risk Assessment", "risk_report"),
            ("🤝 Investment Plan", "investment_plan"),
            ("💼 Trader Plan", "trader_investment_plan"),
        ]
        
        for title, key in reports:
            if result.get(key):
                print(f"\n{title}:")
                print("-"*80)
                content = result[key]
                # 只打印前800字符
                if len(content) > 800:
                    print(content[:800] + "...\n(报告已截断)")
                else:
                    print(content)
        
        # 最终决策
        print("\n" + "="*80)
        print("🎯 最终投资决策")
        print("="*80)
        final_decision = result.get("final_trade_decision", "无决策")
        print(final_decision)
        
        print("\n" + "="*80)
        print("✅ 测试成功完成!")
        print("="*80)
        print("\n💡 提示:")
        print("  - 所有API调用完全免费")
        print("  - 每分钟最多60次请求")
        print("  - 可以分析任意DeFi协议")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        return False
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
