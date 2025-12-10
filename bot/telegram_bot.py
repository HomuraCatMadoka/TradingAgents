"""
Telegram Bot主程序

DeFi投资分析助手的Telegram Bot接口。
"""
import logging
import sys
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from .config import get_bot_config
from .handlers import CommandHandlers

# 配置日志
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class DeFiTelegramBot:
    """DeFi Telegram Bot类"""

    def __init__(self):
        """初始化Bot"""
        try:
            self.config = get_bot_config()
            self.handlers = CommandHandlers()
            logger.info("DeFi Telegram Bot initialized")
        except Exception as e:
            logger.error(f"Failed to initialize bot: {e}")
            sys.exit(1)

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """全局错误处理器"""
        logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)

        # 通知用户
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ 抱歉，处理您的请求时出现了错误。请稍后重试。"
                )
            except Exception as e:
                logger.error(f"Failed to send error message: {e}")

    def setup_handlers(self, application: Application):
        """设置命令和消息处理器"""
        # 命令处理器
        application.add_handler(CommandHandler("start", self.handlers.start_command))
        application.add_handler(CommandHandler("help", self.handlers.help_command))
        application.add_handler(CommandHandler("analyze", self.handlers.analyze_command))
        application.add_handler(CommandHandler("strategy", self.handlers.strategy_command))
        application.add_handler(CommandHandler("compare", self.handlers.compare_command))
        application.add_handler(CommandHandler("status", self.handlers.status_command))
        application.add_handler(CommandHandler("clear_cache", self.handlers.clear_cache_command))
        application.add_handler(CommandHandler("chart", self.handlers.chart_command))

        # 文本消息处理器（自然语言）
        application.add_handler(
            MessageHandler(
                filters.TEXT & ~filters.COMMAND,
                self.handlers.handle_message
            )
        )

        # 错误处理器
        application.add_error_handler(self.error_handler)

        logger.info("Bot handlers configured")

    def run(self):
        """运行Bot"""
        logger.info("Starting DeFi Telegram Bot...")

        try:
            # 创建Application
            application = Application.builder().token(self.config.telegram_token).build()

            # 设置处理器
            self.setup_handlers(application)

            # 启动Bot
            logger.info("Bot is running. Press Ctrl-C to stop.")
            application.run_polling(allowed_updates=Update.ALL_TYPES)

        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
        except Exception as e:
            logger.error(f"Bot crashed: {e}", exc_info=True)
            sys.exit(1)


def main():
    """主函数"""
    print("=" * 80)
    print("DeFi投资分析助手 - Telegram Bot")
    print("=" * 80)
    print()

    # 检查环境变量
    try:
        config = get_bot_config()
        print("✅ 配置加载成功")
        print(f"   Token: {config.telegram_token[:20]}...")
        print(f"   Agent: {config.agent_config_type}")
        print(f"   安全检查: {'启用' if config.enable_input_sanitization else '禁用'}")
        print(f"   速率限制: {config.rate_limit_per_user}/小时")
        print()
    except Exception as e:
        print(f"❌ 配置错误: {e}")
        print()
        print("请确保设置了以下环境变量：")
        print("  - TELEGRAM_BOT_TOKEN: Telegram Bot Token")
        print("  - GOOGLE_API_KEY: Google Gemini API Key")
        print("  - THE_GRAPH_API_KEY: The Graph API Key")
        print()
        print("可以在.env文件中设置这些变量")
        sys.exit(1)

    # 创建并运行Bot
    bot = DeFiTelegramBot()
    bot.run()


if __name__ == "__main__":
    main()
