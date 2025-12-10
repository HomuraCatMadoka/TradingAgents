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

# 多模型混合配置（性能优化）
# - Quick Think: Gemini 2.5 Flash（Phase 1 分析师，更快）
# - Deep Think: Gemini 2.0 Flash Exp（Phase 2-5 决策，更强推理）
GEMINI_CONFIG["quick_think_llm"] = "gemini-2.5-flash"       # Phase 1: 6个分析师（并行）
GEMINI_CONFIG["deep_think_llm"] = "gemini-2.0-flash-exp"    # Phase 2-5: 研究员/交易员/风险管理

# 配额说明：
# - gemini-2.5-flash: 15 requests/分钟（更高配额，适合并行分析师）
# - gemini-2.0-flash-exp: 10 requests/分钟（适合串行决策流程）
#
# 优势：
# 1. 分散配额压力（Phase 1 用 2.5, Phase 2-5 用 2.0）
# 2. 提升 Phase 1 速度（6个分析师更快完成）
# 3. 保留 Phase 2-5 推理质量（关键决策使用 2.0）

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
