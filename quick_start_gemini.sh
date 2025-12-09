#!/bin/bash
# Google Gemini 快速启动脚本

echo "========================================"
echo "  DeFi Agent - Google Gemini 免费版"
echo "========================================"
echo ""

# 检查API key
if [ -z "$GOOGLE_API_KEY" ]; then
    echo "⚠️  请先设置 GOOGLE_API_KEY"
    echo ""
    echo "步骤:"
    echo "1. 访问 https://aistudio.google.com/"
    echo "2. 点击 'Get API key' 创建API key"
    echo "3. 运行: export GOOGLE_API_KEY='your_api_key'"
    echo ""
    echo "或者在 .env 文件中添加:"
    echo "GOOGLE_API_KEY=your_api_key"
    echo ""
    exit 1
fi

echo "✅ API Key已设置"
echo ""

# 切换到项目目录
cd /Users/wangkunyu/develop/TradingAgents

# 设置PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH

# 选择操作
echo "请选择操作:"
echo "1) 测试Gemini连接"
echo "2) 运行DeFi分析 (Aave V3)"
echo "3) 运行DeFi分析 (自定义协议)"
echo ""
read -p "请输入选项 (1-3): " choice

case $choice in
    1)
        echo ""
        echo "正在测试Gemini连接..."
        python3 tests/test_gemini_connection.py
        ;;
    2)
        echo ""
        echo "正在分析 Aave V3..."
        python3 examples/test_defi_with_gemini.py
        ;;
    3)
        echo ""
        read -p "请输入协议名称 (如: uniswap-v3, curve, gmx): " protocol
        echo ""
        echo "正在分析 $protocol..."
        python3 << PYEOF
from gemini_config import GEMINI_CONFIG
from defiagents.graph.trading_graph import TradingAgentsGraph
from datetime import datetime

graph = TradingAgentsGraph(
    selected_analysts=["defi_market", "protocol", "yield", "risk"],
    config=GEMINI_CONFIG,
    debug=True
)

result, signal = graph.propagate("$protocol", datetime.now().strftime("%Y-%m-%d"))
print("\n" + "="*80)
print("最终决策:")
print("="*80)
print(result.get("final_trade_decision", "无决策"))
PYEOF
        ;;
    *)
        echo "无效选项"
        exit 1
        ;;
esac
