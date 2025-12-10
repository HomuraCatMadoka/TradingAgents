"""
Google Gemini 配置文件 - 支持多 API Key 轮询

使用方法:
    from gemini_config import GEMINI_CONFIG
    graph = TradingAgentsGraph(config=GEMINI_CONFIG)

多 Key 配置（推荐）:
    export GOOGLE_API_KEYS='key1,key2,key3'
    或在 .env 添加:
    GOOGLE_API_KEYS=key1,key2,key3

单 Key 配置（向后兼容）:
    export GOOGLE_API_KEY='your_key'
"""
from defiagents.default_config import DEFAULT_CONFIG
import os
import time

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

# ========== 多 API Key 轮询支持 ==========
# 从环境变量加载 API Keys
api_keys_str = os.getenv("GOOGLE_API_KEYS")
if api_keys_str:
    # 多 key 模式（推荐）
    api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
    GEMINI_CONFIG["google_api_keys"] = api_keys
    GEMINI_CONFIG["google_api_key_index"] = 0  # 当前使用的 key 索引
    GEMINI_CONFIG["key_cooldown"] = {}  # 记录每个 key 的冷却时间
    print(f"✅ Gemini 多 Key 轮询模式（{len(api_keys)} 个 key）")
    print(f"   总配额: ~{len(api_keys) * 15} RPM (gemini-2.5-flash)")
    print(f"   总配额: ~{len(api_keys) * 10} RPM (gemini-2.0-flash-exp)")
else:
    # 单 key 模式（向后兼容）
    single_key = os.getenv("GOOGLE_API_KEY")
    if single_key:
        GEMINI_CONFIG["google_api_keys"] = [single_key]
        GEMINI_CONFIG["google_api_key_index"] = 0
        GEMINI_CONFIG["key_cooldown"] = {}
        print("✅ Gemini 单 Key 模式")
        print(f"   API Key: {single_key[:20]}...")
    else:
        print("⚠️  警告: GOOGLE_API_KEY 或 GOOGLE_API_KEYS 环境变量未设置")
        print("请设置环境变量或在 .env 文件中配置")

print(f"   Quick Model: {GEMINI_CONFIG['quick_think_llm']}")
print(f"   Deep Model: {GEMINI_CONFIG['deep_think_llm']}")
print()
print("💡 启用多 Key 轮询:")
print("   1. 创建 3-5 个 Google 账号")
print("   2. 每个账号生成 AI Studio API Key (https://aistudio.google.com/app/apikey)")
print("   3. 设置环境变量: export GOOGLE_API_KEYS='key1,key2,key3'")
print("   4. 或在 .env 添加: GOOGLE_API_KEYS=key1,key2,key3")
print("   5. 重启 Bot，配额将提升到 30-75 RPM")
print()
