"""
Telegram Bot命令处理器

处理用户命令和消息，调用DeFi Agent进行分析。
"""
import logging
import asyncio
import time
from typing import Dict, Optional
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from .config import get_bot_config
from .formatters import TelegramFormatter

logger = logging.getLogger(__name__)


class CommandHandlers:
    """命令处理器类"""

    def __init__(self):
        """初始化处理器"""
        self.config = get_bot_config()
        self.formatter = TelegramFormatter(max_length=self.config.max_message_length)

        # 速率限制追踪
        self.rate_limit_tracker: Dict[int, list] = {}  # {user_id: [timestamps]}

        # 加载DeFi Agent（延迟加载）
        self._agent = None
        self._sanitizer = None

    @property
    def agent(self):
        """延迟加载DeFi Agent"""
        if self._agent is None:
            try:
                if self.config.agent_config_type == "gemini":
                    from gemini_config import GEMINI_CONFIG
                    from defiagents.graph.trading_graph import TradingAgentsGraph
                    self._agent = TradingAgentsGraph(config=GEMINI_CONFIG)
                    logger.info("DeFi Agent loaded with Gemini config")
                else:
                    # 可扩展其他配置
                    raise ValueError(f"Unsupported agent config type: {self.config.agent_config_type}")
            except Exception as e:
                logger.error(f"Failed to load DeFi Agent: {e}")
                raise
        return self._agent

    @property
    def sanitizer(self):
        """延迟加载输入净化器"""
        if self._sanitizer is None and self.config.enable_input_sanitization:
            from defiagents.security import get_sanitizer
            self._sanitizer = get_sanitizer(strict_mode=False)
            logger.info("Input sanitizer loaded")
        return self._sanitizer

    def check_rate_limit(self, user_id: int) -> tuple[bool, Optional[str]]:
        """
        检查速率限制

        Returns:
            (is_allowed, rejection_reason)
        """
        now = time.time()
        window_start = now - self.config.rate_limit_window

        # 清理过期记录
        if user_id in self.rate_limit_tracker:
            self.rate_limit_tracker[user_id] = [
                ts for ts in self.rate_limit_tracker[user_id]
                if ts > window_start
            ]
        else:
            self.rate_limit_tracker[user_id] = []

        # 检查限制
        request_count = len(self.rate_limit_tracker[user_id])
        if request_count >= self.config.rate_limit_per_user:
            wait_time = int(self.rate_limit_tracker[user_id][0] + self.config.rate_limit_window - now)
            return False, f"请求过于频繁，请等待{wait_time}秒后再试"

        # 记录本次请求
        self.rate_limit_tracker[user_id].append(now)
        return True, None

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/start命令"""
        user = update.effective_user
        logger.info(f"User {user.id} ({user.username}) started the bot")

        await update.message.reply_text(
            self.formatter.format_welcome(),
            parse_mode="Markdown"
        )

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/help命令"""
        await update.message.reply_text(
            self.formatter.format_help(),
            parse_mode="Markdown"
        )

    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理/analyze命令

        用法：/analyze <协议名>
        示例：/analyze aave-v3
        """
        user_id = update.effective_user.id

        # 速率限制检查
        is_allowed, rejection_reason = self.check_rate_limit(user_id)
        if not is_allowed:
            await update.message.reply_text(
                self.formatter.format_error(rejection_reason)
            )
            return

        # 提取协议名
        if not context.args or len(context.args) == 0:
            await update.message.reply_text(
                "❌ 请指定协议名称\n\n用法：`/analyze <协议名>`\n示例：`/analyze aave-v3`",
                parse_mode="Markdown"
            )
            return

        protocol_name = " ".join(context.args)

        # 调用分析
        await self._perform_analysis(update, protocol_name)

    async def strategy_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理/strategy命令

        用法：/strategy [金额] [风险偏好]
        示例：/strategy 100000 low
        """
        user_id = update.effective_user.id

        # 速率限制检查
        is_allowed, rejection_reason = self.check_rate_limit(user_id)
        if not is_allowed:
            await update.message.reply_text(
                self.formatter.format_error(rejection_reason)
            )
            return

        # 提取参数
        investment_amount = None
        risk_preference = "medium"

        if context.args:
            try:
                if len(context.args) >= 1:
                    investment_amount = float(context.args[0])
                if len(context.args) >= 2:
                    risk_preference = context.args[1].lower()
            except ValueError:
                await update.message.reply_text(
                    "❌ 参数格式错误\n\n用法：`/strategy [金额] [风险偏好]`\n示例：`/strategy 100000 low`",
                    parse_mode="Markdown"
                )
                return

        # 构建查询
        query = f"推荐一个投资策略"
        if investment_amount:
            query += f"，投资金额{investment_amount}美金"
        query += f"，风险偏好{risk_preference}"

        await self._perform_analysis(update, query)

    async def compare_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理/compare命令

        用法：/compare <协议1> <协议2>
        示例：/compare aave-v3 compound-v3
        """
        user_id = update.effective_user.id

        # 速率限制检查
        is_allowed, rejection_reason = self.check_rate_limit(user_id)
        if not is_allowed:
            await update.message.reply_text(
                self.formatter.format_error(rejection_reason)
            )
            return

        # 提取协议名
        if not context.args or len(context.args) < 2:
            await update.message.reply_text(
                "❌ 请指定两个协议名称\n\n用法：`/compare <协议1> <协议2>`\n示例：`/compare aave-v3 compound-v3`",
                parse_mode="Markdown"
            )
            return

        protocol1 = context.args[0]
        protocol2 = context.args[1]

        query = f"对比{protocol1}和{protocol2}"
        await self._perform_analysis(update, query)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        处理普通文本消息（自然语言输入）
        """
        user_id = update.effective_user.id
        user_input = update.message.text

        # 速率限制检查
        is_allowed, rejection_reason = self.check_rate_limit(user_id)
        if not is_allowed:
            await update.message.reply_text(
                self.formatter.format_error(rejection_reason)
            )
            return

        # 输入净化
        if self.config.enable_input_sanitization:
            sanitization_result = self.sanitizer.sanitize(user_input)

            if not sanitization_result.is_safe:
                logger.warning(f"User {user_id} input rejected: {sanitization_result.rejection_reason}")
                await update.message.reply_text(
                    self.formatter.format_security_rejection(
                        sanitization_result.rejection_reason
                    ),
                    parse_mode="Markdown"
                )
                return

            # 显示提取的参数（如果置信度足够高）
            if sanitization_result.intent and sanitization_result.confidence > 0.6:
                params = []
                intent = sanitization_result.intent
                if intent.protocol_name:
                    params.append(f"✓ 协议：{intent.protocol_name}")
                if intent.investment_amount:
                    params.append(f"✓ 金额：${intent.investment_amount:,.0f}")
                if intent.risk_preference:
                    params.append(f"✓ 风险：{intent.risk_preference}")
                if intent.target_apy:
                    params.append(f"✓ 目标APY：≥{intent.target_apy}%")

                if params:
                    params_text = "\n".join(params)
                    await update.message.reply_text(
                        f"📋 理解您的需求：\n{params_text}\n\n正在分析...",
                        parse_mode="Markdown"
                    )

        # 执行分析
        await self._perform_analysis(update, user_input)

    async def _perform_analysis(self, update: Update, query: str):
        """
        执行DeFi分析

        Args:
            update: Telegram更新对象
            query: 分析查询
        """
        chat_id = update.effective_chat.id

        try:
            # 1. 发送初始进度消息
            if self.config.enable_progress_updates:
                progress_msg = await update.message.reply_text(
                    self.formatter.format_progress("正在初始化...", 0, 8),
                    parse_mode="Markdown"
                )
            else:
                progress_msg = await update.message.reply_text(
                    "🔄 正在分析，请稍候...",
                    parse_mode="Markdown"
                )

            # 2. 调用DeFi Agent
            start_time = time.time()

            # 模拟进度更新（在实际调用期间）
            analysis_task = asyncio.create_task(self._run_agent_analysis(query))

            # 定期更新进度
            step = 0
            steps = [
                "DeFi Market Analyst分析中...",
                "Protocol Fundamentals Analyst工作中...",
                "Yield Analyst计算收益...",
                "Risk Analyst评估风险...",
                "Bull/Bear Researchers辩论中...",
                "Research Manager总结中...",
                "Risk Management Team讨论中...",
                "Trader制定最终策略...",
            ]

            while not analysis_task.done():
                await asyncio.sleep(10)  # 每10秒更新一次
                if step < len(steps) and self.config.enable_progress_updates:
                    try:
                        await progress_msg.edit_text(
                            self.formatter.format_progress(steps[step], step + 1, 8),
                            parse_mode="Markdown"
                        )
                        step += 1
                    except Exception as e:
                        logger.warning(f"Failed to update progress: {e}")

            # 获取结果
            result = await analysis_task
            duration = time.time() - start_time

            logger.info(f"Analysis completed in {duration:.2f}s for query: {query[:50]}")

            # 3. 删除进度消息
            try:
                await progress_msg.delete()
            except Exception:
                pass

            # 4. 发送分析结果
            messages = self.formatter.format_analysis_result(result)

            for message in messages:
                await update.message.reply_text(
                    message,
                    parse_mode="Markdown"
                )
                await asyncio.sleep(0.5)  # 避免发送过快被限制

        except asyncio.TimeoutError:
            logger.error(f"Analysis timeout for query: {query}")
            await update.message.reply_text(
                self.formatter.format_error(
                    f"分析超时（>{self.config.analysis_timeout}秒），请稍后重试或选择其他协议。"
                )
            )

        except Exception as e:
            logger.error(f"Analysis failed: {e}", exc_info=True)
            await update.message.reply_text(
                self.formatter.format_error(
                    f"分析出错：{str(e)[:100]}\n\n请稍后重试。"
                )
            )

    async def _run_agent_analysis(self, query: str) -> Dict:
        """
        运行Agent分析（异步包装）

        Args:
            query: 分析查询

        Returns:
            分析结果字典
        """
        # 在线程池中运行同步的Agent调用
        loop = asyncio.get_event_loop()

        def _sync_analysis():
            result, signal = self.agent.propagate(
                company_name=query,
                trade_date=datetime.now().strftime("%Y-%m-%d")
            )
            return result

        result = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_analysis),
            timeout=self.config.analysis_timeout
        )

        return result
