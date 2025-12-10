"""
Telegram Bot配置

管理Bot的配置参数和环境变量。
"""
import os
from typing import Optional, Set
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

DEFAULT_REDIS_URL = "redis://localhost:6379/0"
DEFAULT_CACHE_ENABLED = True
DEFAULT_CACHE_TTL_SECONDS = 1800
DEFAULT_AUDIT_DB_PATH = "./data/audit.db"


def _parse_admin_user_ids(env_value: str) -> Set[int]:
    """Parse admin ids from environment, ignoring invalid entries."""
    admin_ids: Set[int] = set()
    for raw_id in env_value.split(","):
        raw_id = raw_id.strip()
        if not raw_id:
            continue
        try:
            admin_ids.add(int(raw_id))
        except ValueError:
            # Ignore malformed ids silently to avoid breaking startup.
            continue
    return admin_ids


def _load_admin_user_ids() -> Set[int]:
    return _parse_admin_user_ids(os.getenv("BOT_ADMIN_USER_IDS", ""))


def _parse_bool(value: Optional[str], default: bool) -> bool:
    """Parse truthy/falsey strings with a safe default."""
    if value is None:
        return default

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _parse_cache_ttl(value: Optional[str], default: int = DEFAULT_CACHE_TTL_SECONDS) -> int:
    """Parse cache TTL, falling back to default on invalid or negative values."""
    if value is None:
        return default

    try:
        ttl = int(value)
    except (TypeError, ValueError):
        return default

    if ttl < 0:
        return default
    return ttl


ADMIN_USER_IDS: Set[int] = _load_admin_user_ids()


def is_admin(user_id: int) -> bool:
    """检查用户是否为管理员"""
    return user_id in ADMIN_USER_IDS


class BotConfig:
    """Bot配置类"""

    def __init__(self):
        """初始化配置"""
        # Telegram Bot Token
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        if not self.telegram_token:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN not found in environment variables. "
                "Please add it to .env file or set it as environment variable."
            )

        # DeFi Agent配置
        self.agent_config_type = os.getenv("AGENT_CONFIG_TYPE", "gemini")  # gemini/openai/ollama

        # Bot行为配置
        self.max_message_length = int(os.getenv("BOT_MAX_MESSAGE_LENGTH", "4096"))
        self.enable_progress_updates = os.getenv("BOT_ENABLE_PROGRESS", "true").lower() == "true"
        self.analysis_timeout = int(os.getenv("BOT_ANALYSIS_TIMEOUT", "180"))  # 秒

        # 安全配置
        self.enable_input_sanitization = os.getenv("BOT_ENABLE_SANITIZATION", "true").lower() == "true"
        self.rate_limit_per_user = int(os.getenv("BOT_RATE_LIMIT_PER_USER", "10"))  # 每小时
        self.rate_limit_window = int(os.getenv("BOT_RATE_LIMIT_WINDOW", "3600"))  # 秒
        self.audit_enabled = _parse_bool(os.getenv("BOT_AUDIT_ENABLED"), True)
        self.audit_db_path = os.getenv("BOT_AUDIT_DB_PATH", DEFAULT_AUDIT_DB_PATH)

        # 缓存配置
        redis_url_env = os.getenv("REDIS_URL")
        self.redis_url = (redis_url_env or "").strip() or DEFAULT_REDIS_URL
        self.cache_enabled = _parse_bool(os.getenv("BOT_CACHE_ENABLED"), DEFAULT_CACHE_ENABLED)
        self.cache_ttl_seconds = _parse_cache_ttl(os.getenv("BOT_CACHE_TTL_SECONDS"))

        # Admin配置（可选）
        global ADMIN_USER_IDS
        ADMIN_USER_IDS = _load_admin_user_ids()
        self.admin_user_ids = ADMIN_USER_IDS

    def is_admin(self, user_id: int) -> bool:
        """检查用户是否为管理员"""
        return is_admin(user_id)


# 全局配置实例
_config_instance: Optional[BotConfig] = None


def get_bot_config() -> BotConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = BotConfig()
    return _config_instance


if __name__ == "__main__":  # pragma: no cover - manual debug helper
    # 测试配置加载
    try:
        config = get_bot_config()
        print("✅ Bot配置加载成功")
        print(f"   Token: {config.telegram_token[:20]}...")
        print(f"   Agent Config: {config.agent_config_type}")
        print(f"   Progress Updates: {config.enable_progress_updates}")
        print(f"   Rate Limit: {config.rate_limit_per_user}/hour")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
