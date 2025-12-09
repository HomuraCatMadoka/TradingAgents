"""
Google Gemini 配置文件 - 免费方案

使用方法:
    from gemini_config import GEMINI_CONFIG
    graph = TradingAgentsGraph(config=GEMINI_CONFIG)
"""
from defiagents.default_config import DEFAULT_CONFIG
import os

# 复制默认配置
GEMINI_CONFIG = DEFAULT_CONFIG.copy()

# 配置Gemini
GEMINI_CONFIG["llm_provider"] = "google"

# 推荐模型配置（免费）- 使用Gemini 2.0实验版
GEMINI_CONFIG["quick_think_llm"] = "gemini-2.0-flash-exp"    # 快速模型 - 用于分析师
GEMINI_CONFIG["deep_think_llm"] = "gemini-2.0-flash-exp"     # 强大模型 - 用于管理员

# 备注：gemini-1.5系列目前在v1beta API中不可用
# 如需使用1.5版本，请参考Google AI Studio文档

# 验证API key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("⚠️  警告: GOOGLE_API_KEY 环境变量未设置")
    print("请运行: export GOOGLE_API_KEY='your_api_key'")
    print("或在 .env 文件中添加: GOOGLE_API_KEY=your_api_key")
else:
    print("✅ Gemini配置已加载")
    print(f"   API Key: {api_key[:20]}...")
    print(f"   Quick Model: {GEMINI_CONFIG['quick_think_llm']}")
    print(f"   Deep Model: {GEMINI_CONFIG['deep_think_llm']}")

# 其他配置保持不变
