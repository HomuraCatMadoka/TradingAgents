import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("DEFIAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings
    "llm_provider": "openai",
    "deep_think_llm": "o4-mini",
    "quick_think_llm": "gpt-4o-mini",
    "backend_url": "https://api.openai.com/v1",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,

    # ========== Legacy Stock Trading Data Sources ==========
    # (Kept for backward compatibility, will be deprecated)
    "data_vendors": {
        "core_stock_apis": "yfinance",       # Options: yfinance, alpha_vantage, local
        "technical_indicators": "yfinance",  # Options: yfinance, alpha_vantage, local
        "fundamental_data": "alpha_vantage", # Options: openai, alpha_vantage, local
        "news_data": "alpha_vantage",        # Options: openai, alpha_vantage, google, local
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_news": "openai",               # Override category default
    },

    # ========== DeFi Data Sources Configuration ==========
    # Category-level configuration for DeFi data
    "defi_data_vendors": {
        "protocol_data": "defillama",        # Options: defillama, the_graph, dune
        "onchain_data": "the_graph",         # Options: the_graph, alchemy_rpc, infura_rpc
        "market_data": "coingecko",          # Options: coingecko, defillama
        "defi_news": "defillama",            # Options: defillama, crypto_news_api
    },

    # DeFi-specific tool-level configuration
    "defi_tool_vendors": {
        # Example: "get_protocol_tvl": "defillama",
        # Example: "get_pool_data": "the_graph",
    },

    # ========== Blockchain RPC Configuration ==========
    "rpc_providers": {
        "ethereum": {
            "provider": "alchemy",            # Options: alchemy, infura, ankr, public
            "url": os.getenv("ETH_RPC_URL", "https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY"),
        },
        "arbitrum": {
            "provider": "alchemy",
            "url": os.getenv("ARB_RPC_URL", "https://arb-mainnet.g.alchemy.com/v2/YOUR_API_KEY"),
        },
        "optimism": {
            "provider": "alchemy",
            "url": os.getenv("OP_RPC_URL", "https://opt-mainnet.g.alchemy.com/v2/YOUR_API_KEY"),
        },
        "base": {
            "provider": "alchemy",
            "url": os.getenv("BASE_RPC_URL", "https://base-mainnet.g.alchemy.com/v2/YOUR_API_KEY"),
        },
        "polygon": {
            "provider": "alchemy",
            "url": os.getenv("POLYGON_RPC_URL", "https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY"),
        },
    },

    # ========== The Graph Configuration ==========
    "the_graph": {
        "api_key": os.getenv("THE_GRAPH_API_KEY", ""),
        "api_url": "https://gateway.thegraph.com/api",
        # Subgraph deployment IDs (for Gateway API)
        # Note: Use deployment IDs, not org/name format for Gateway
        "subgraphs": {
            # Uniswap V3
            "uniswap_v3_ethereum": "5zvR82QoaXYFyDEKLZ9t6v9adgnptxYpKpSbxtgVENFV",
            "uniswap_v3_arbitrum": "FbCGRftH4a3yZugY7TnbYgPJVEv2LvMT6oF1fxPe9aJM",
            "uniswap_v3_optimism": "Cghf4LfVqPiFw6fp6Y5X5Ubc8UpmUhSfJL82zwiBFLaj",
            "uniswap_v3_polygon": "3hCPRGf4z88VC5rsBKU5AA9FBBq5nF3jbKJG7VZCbhjm",
            "uniswap_v3_base": "43Hwfi3dJSoGpyas92HHyUFbhUFzf2F92rRUGYSDeZvK",

            # Aave V3 (Note: Some may be outdated, will fallback to DeFi Llama)
            "aave_v3_ethereum": "HB1Z2EAw4rtPRYVb2Nz8QGFLHCpym6ByBX6vbCViuE9F",
            "aave_v3_arbitrum": "GQFbb95cE6d8mV989mL5figjaGaKCQB3xqYrr1bRyXqF",
            "aave_v3_optimism": "5JNm6HVwvySNmhYGFwkCmJaKhBaE6YzxqaBXCrg8f6Fd",
            "aave_v3_polygon": "BRMq8fytHKGf3jPCbwPVPLSrqj6o2Nc2tbRYGHN7CyoH",
            "aave_v3_base": "EHKYe7mBMFPsZgbLyx9Nxy98Qm3A3hJPjNRtv8R89k4p",
        },
    },

    # ========== Messari Configuration ==========
    "messari": {
        "api_key": os.getenv("MESSARI_API_KEY", ""),
        "api_url": "https://gateway.thegraph.com/api",
        "deployment_json_path": os.path.abspath(
            os.getenv(
                "MESSARI_DEPLOYMENT_JSON_PATH",
                os.path.join(
                    os.path.dirname(__file__),
                    "../subgraph/deployment/deployment.json",
                ),
            )
        ),
        "cache_ttl": 3600,  # Cache TTL in seconds (1 hour)
        "rate_limit_per_minute": 60,
        "timeout_seconds": 10,
    },

    # ========== Data Source Priority Configuration ==========
    "data_source_priority": {
        "protocol_tvl": ["messari", "defillama", "the_graph", "onchain_rpc"],
        "lending_markets": ["messari", "the_graph", "defillama"],
        "dex_pools": ["messari", "the_graph"],
        "token_prices": ["coingecko", "defillama"],
    },

    # ========== DeFi Llama Configuration ==========
    "defillama": {
        "api_url": "https://api.llama.fi",
        "coins_api_url": "https://coins.llama.fi",
        "cache_ttl": 3600,  # Cache TTL in seconds (1 hour)
    },

    # ========== CoinGecko Configuration ==========
    "coingecko": {
        "api_key": os.getenv("COINGECKO_API_KEY", ""),  # Pro API key (optional)
        "api_url": "https://api.coingecko.com/api/v3",
        "pro_api_url": "https://pro-api.coingecko.com/api/v3",
        "use_pro": False,  # Set to True if using Pro API
        "cache_ttl": 300,  # Cache TTL in seconds (5 minutes)
    },

    # ========== Security Configuration ==========
    "security": {
        "enable_sanitization": True,
        "strict_mode": False,
        "max_input_length": 500,
    },

    "audit": {
        "enabled": True,
        "db_path": "./data/audit.db",
        "retention_days": 90,
    },

    # ========== Telegram Bot Configuration ==========
    "telegram": {
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "allowed_users": [],  # Empty = allow all, or list of user IDs
        "rate_limit": 10,     # Requests per minute per user
    },
}


def validate_messari_config(config: Dict) -> None:
    """验证 Messari 配置完整性。"""
    assert "messari" in config, "Missing 'messari' config section"

    messari_cfg = config["messari"]
    assert messari_cfg.get("deployment_json_path"), "deployment_json_path not set"

    path = messari_cfg["deployment_json_path"]
    if not os.path.exists(path):
        logger.warning("Deployment JSON not found: %s", path)
