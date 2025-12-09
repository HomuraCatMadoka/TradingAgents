import os

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
        # Subgraph endpoints (will be populated with specific protocols)
        "subgraphs": {
            "uniswap_v3_ethereum": "uniswap/uniswap-v3",
            "aave_v3_ethereum": "aave/protocol-v3",
            # More subgraphs will be added after protocol research
        },
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

    # ========== Telegram Bot Configuration ==========
    "telegram": {
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "allowed_users": [],  # Empty = allow all, or list of user IDs
        "rate_limit": 10,     # Requests per minute per user
    },
}
