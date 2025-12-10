"""
Gemini 配置 - 多 API Key 轮询支持

使用方法:
    from gemini_config_pooled import GEMINI_CONFIG_POOLED
    graph = TradingAgentsGraph(config=GEMINI_CONFIG_POOLED)
"""
from defiagents.default_config import DEFAULT_CONFIG
import os

# 复制默认配置
GEMINI_CONFIG_POOLED = DEFAULT_CONFIG.copy()

# 配置 Gemini
GEMINI_CONFIG_POOLED["llm_provider"] = "google"

# 多模型混合配置
GEMINI_CONFIG_POOLED["quick_think_llm"] = "gemini-2.5-flash"       # Phase 1: 6个分析师
GEMINI_CONFIG_POOLED["deep_think_llm"] = "gemini-2.0-flash-exp"    # Phase 2-5: 关键决策

# ========== 多 API Key 轮询配置 ==========
# 从环境变量读取多个 API Key（逗号分隔）
# 示例: GOOGLE_API_KEYS=key1,key2,key3

api_keys_str = os.getenv("GOOGLE_API_KEYS")
if api_keys_str:
    api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
    GEMINI_CONFIG_POOLED["google_api_keys"] = api_keys
    print(f"✅ Gemini 多 Key 轮询已启用（{len(api_keys)} 个 key）")
    print(f"   配额总计: ~{len(api_keys) * 15} RPM (gemini-2.5-flash)")
else:
    # 单 key 模式（向后兼容）
    single_key = os.getenv("GOOGLE_API_KEY")
    if single_key:
        GEMINI_CONFIG_POOLED["google_api_keys"] = [single_key]
        print("✅ Gemini 单 Key 模式")
        print(f"   API Key: {single_key[:20]}...")
    else:
        print("⚠️  警告: GOOGLE_API_KEY 或 GOOGLE_API_KEYS 环境变量未设置")

# 配额说明
print(f"   Quick Model: {GEMINI_CONFIG_POOLED['quick_think_llm']} (15 RPM/key)")
print(f"   Deep Model: {GEMINI_CONFIG_POOLED['deep_think_llm']} (10 RPM/key)")
print()
print("💡 多 Key 配置方法:")
print("   export GOOGLE_API_KEYS='key1,key2,key3'")
print("   或在 .env 文件添加:")
print("   GOOGLE_API_KEYS=key1,key2,key3")
