"""
Telegram Bot配置

管理Bot的配置参数和环境变量。
"""
import os
from typing import Optional
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


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

        # Admin配置（可选）
        admin_ids_str = os.getenv("BOT_ADMIN_USER_IDS", "")
        self.admin_user_ids = [int(id.strip()) for id in admin_ids_str.split(",") if id.strip()]

    def is_admin(self, user_id: int) -> bool:
        """检查用户是否为管理员"""
        return user_id in self.admin_user_ids


# 全局配置实例
_config_instance: Optional[BotConfig] = None


def get_bot_config() -> BotConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = BotConfig()
    return _config_instance


if __name__ == "__main__":
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
