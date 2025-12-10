"""
Telegram Bot命令处理器

处理用户命令和消息，调用DeFi Agent进行分析。
"""
import logging
import asyncio
import time
import hashlib
import json
from threading import Lock
from typing import Any, Dict, List, Optional
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

from defiagents.dataflows.defi import health_checker

from .cache import CacheClient
from .config import get_bot_config, is_admin
from .formatters import TelegramFormatter, add_cache_marker

logger = logging.getLogger(__name__)


class CommandHandlers:
    """命令处理器类"""

    def __init__(self):
        """初始化处理器"""
        self.config = get_bot_config()
        self.formatter = TelegramFormatter(max_length=self.config.max_message_length)

        # 速率限制追踪
        self.rate_limit_tracker: Dict[int, list] = {}  # {user_id: [timestamps]}
        self.global_stats = {
            "total_requests": 0,
            "active_users": set(),
            "total_response_time": 0.0,
            "completed_requests": 0,
            "window_start": time.time(),
        }
        self._lock = Lock()
        self.start_time = time.time()

        # 缓存客户端（Redis 不可用时自动降级）
        self.cache_client: Optional[CacheClient] = None
        if self.config.cache_enabled:
            try:
                self.cache_client = CacheClient(
                    self.config.redis_url,
                    ttl=self.config.cache_ttl_seconds,
                )
            except Exception as exc:  # pragma: no cover - defensive downgrade
                logger.warning("Cache client initialization failed, disabling cache: %s", exc)
                self.cache_client = None

        # 加载DeFi Agent（延迟加载）
        self._agent = None
        self._sanitizer = None

    @property  # pragma: no cover - integration path
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

    @property  # pragma: no cover - integration path
    def sanitizer(self):
        """延迟加载输入净化器"""
        if self._sanitizer is None and self.config.enable_input_sanitization:
            from defiagents.security import get_sanitizer
            self._sanitizer = get_sanitizer(strict_mode=False)
            logger.info("Input sanitizer loaded")
        return self._sanitizer

    def _reset_stats_window_if_needed(self, now: float) -> None:
        """Reset global counters when the tracking window rolls over."""
        window_elapsed = now - self.global_stats["window_start"]
        if window_elapsed >= self.config.rate_limit_window:
            self.global_stats["window_start"] = now
            self.global_stats["total_requests"] = 0
            self.global_stats["total_response_time"] = 0.0
            self.global_stats["completed_requests"] = 0
            self.global_stats["active_users"] = set()

    def _register_request(self, user_id: int) -> None:
        """Record a request in global stats."""
        self.global_stats["total_requests"] += 1
        active_users = self.global_stats["active_users"]
        if user_id not in active_users:
            active_users.add(user_id)

    def _record_response_time(self, duration: float) -> None:
        """Record completed request latency for average calculation."""
        with self._lock:
            self.global_stats["total_response_time"] += duration
            self.global_stats["completed_requests"] += 1

    def _calculate_average_response_time_locked(self) -> float:
        completed = self.global_stats["completed_requests"]
        if completed == 0:
            return 0.0
        return self.global_stats["total_response_time"] / completed

    def get_stats_snapshot(self) -> Dict[str, float]:
        """Return a thread-safe snapshot of global stats."""
        with self._lock:
            return {
                "total_requests": self.global_stats["total_requests"],
                "active_users": len(self.global_stats["active_users"]),
                "average_response_time": self._calculate_average_response_time_locked(),
                "window_start": self.global_stats["window_start"],
                "uptime_seconds": time.time() - self.start_time,
            }

    def check_rate_limit(self, user_id: int) -> tuple[bool, Optional[str]]:
        """
        检查速率限制

        Returns:
            (is_allowed, rejection_reason)
        """
        now = time.time()
        with self._lock:
            self._reset_stats_window_if_needed(now)

            # 管理员豁免
            if is_admin(user_id):
                self._register_request(user_id)
                return True, None

            window_start = now - self.config.rate_limit_window

            # 清理过期记录
            timestamps = self.rate_limit_tracker.get(user_id, [])
            timestamps = [ts for ts in timestamps if ts > window_start]
            self.rate_limit_tracker[user_id] = timestamps

            # 检查限制
            request_count = len(self.rate_limit_tracker[user_id])
            if request_count >= self.config.rate_limit_per_user:
                wait_reference = (
                    self.rate_limit_tracker[user_id][0]
                    if self.rate_limit_tracker[user_id]
                    else now
                )
                wait_time = int(wait_reference + self.config.rate_limit_window - now)
                return False, f"请求过于频繁，请等待{wait_time}秒后再试"

            # 记录本次请求
            self.rate_limit_tracker[user_id].append(now)
            self._register_request(user_id)
            return True, None

    def _get_rate_limit_status(self, user_id: Optional[int]) -> Dict[str, Any]:
        """Build rate limit status without counting this request."""
        if user_id is None:
            return {
                "used": 0,
                "limit": self.config.rate_limit_per_user,
                "reset_in_seconds": 0,
            }

        now = time.time()
        with self._lock:
            self._reset_stats_window_if_needed(now)
            window_start = now - self.config.rate_limit_window
            timestamps = [ts for ts in self.rate_limit_tracker.get(user_id, []) if ts > window_start]
            self.rate_limit_tracker[user_id] = timestamps

            used = len(timestamps)
            reset_in_seconds = (
                max(0.0, min(timestamps) + self.config.rate_limit_window - now)
                if timestamps
                else 0.0
            )
            limit = self.config.rate_limit_per_user

        if is_admin(user_id):
            return {"used": 0, "limit": limit, "reset_in_seconds": 0}

        return {"used": used, "limit": limit, "reset_in_seconds": reset_in_seconds}

    def _format_health_status(self, health_status: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Normalize raw health checker output for the formatter."""
        display_names = {
            "defillama": "DeFi Llama",
            "the_graph": "The Graph",
            "coingecko": "CoinGecko",
            "gemini": "Gemini LLM",
        }
        formatted: Dict[str, Dict[str, Any]] = {}
        for key, info in (health_status or {}).items():
            status = str(info.get("status") or info.get("source") or "offline").lower()
            detail = info.get("detail")
            latency = info.get("latency")
            if latency is not None and not detail:
                detail = f"{latency}ms"

            formatted[key] = {
                "name": display_names.get(key, key.replace("_", " ").title()),
                "status": status,
            }
            if detail:
                formatted[key]["detail"] = detail

        if not formatted:
            formatted["health_checks"] = {
                "name": "Health Checks",
                "status": "degraded",
                "detail": "健康检查暂不可用",
            }

        return formatted

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

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理/status命令（速率限制豁免）。"""
        user_id = update.effective_user.id if update and update.effective_user else None
        is_admin_user = bool(user_id and self.config.is_admin(user_id))

        try:
            try:
                raw_health = health_checker.get_system_health()
            except Exception as exc:  # pragma: no cover - defensive fallback
                logger.warning(f"Health check failed: {exc}")
                raw_health = {}

            health_payload = self._format_health_status(raw_health)
            rate_limit_status = self._get_rate_limit_status(user_id)

            global_stats: Optional[Dict[str, Any]] = None
            if is_admin_user:
                stats = self.get_stats_snapshot()
                stats["uptime_seconds"] = time.time() - self.start_time
                global_stats = stats

            message = self.formatter.format_status_message(
                health_status=health_payload,
                rate_limit_status=rate_limit_status,
                is_admin=is_admin_user,
                global_stats=global_stats,
            )

            await update.message.reply_text(message, parse_mode="Markdown")
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.error(f"Failed to process /status: {exc}", exc_info=True)
            error_message = self.formatter.format_error("无法获取系统状态，请稍后重试。")
            if update and update.message:
                await update.message.reply_text(error_message)

    async def clear_cache_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """清除缓存命令（管理员专用，豁免速率限制）。"""
        user_id = update.effective_user.id if update and update.effective_user else None
        if user_id is None:
            return

        if not self.config.is_admin(user_id):
            await update.message.reply_text("❌ 此命令仅管理员可用")
            return

        cache_client = self.cache_client if self.config.cache_enabled else None
        if not cache_client:
            await update.message.reply_text("⚠️ Redis 不可用，无法清除缓存")
            return

        try:
            cleared = cache_client.clear_prefix("defi_analysis:")
        except Exception as exc:  # pragma: no cover - defensive fallback
            logger.warning("Clear cache command failed: %s", exc)
            cleared = None

        if cleared is None:
            await update.message.reply_text("⚠️ Redis 不可用，无法清除缓存")
            return

        await update.message.reply_text(f"✅ 已清除 {int(cleared)} 个缓存条目")

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

    def _generate_query_hash(self, **params: Any) -> str:
        """Generate a stable 8-char MD5 hash from sorted query params."""
        serialized = json.dumps(params or {}, sort_keys=True, default=str)
        return hashlib.md5(serialized.encode("utf-8")).hexdigest()[:8]

    def _generate_cache_key(self, protocol: str, date: str, **params: Any) -> str:
        """Build cache key as defi_analysis:{protocol}:{date}:{hash}."""
        query_hash = self._generate_query_hash(**params)
        safe_protocol = str(protocol) if protocol is not None else "unknown"
        safe_date = str(date) if date is not None else "unknown"
        return f"defi_analysis:{safe_protocol}:{safe_date}:{query_hash}"

    def _append_cache_marker(self, messages: List[str], result: Optional[Dict[str, Any]]) -> List[str]:
        """Attach cache marker to the first message when result came from cache."""
        if not messages or not result or not result.get("_from_cache"):
            return messages

        cached_at = result.get("_cached_at")
        try:
            timestamp = float(cached_at)
        except (TypeError, ValueError):
            return messages

        messages[0] = add_cache_marker(messages[0], timestamp)
        return messages

    async def _perform_analysis(self, update: Update, query: str):
        """
        执行DeFi分析

        Args:
            update: Telegram更新对象
            query: 分析查询
        """
        start_time = time.time()
        trade_date = datetime.now().strftime("%Y-%m-%d")
        cache_key: Optional[str] = None
        cached_result: Optional[Dict[str, Any]] = None
        cache_allowed = bool(self.config.cache_enabled and self.cache_client)

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

            # 2. 缓存检查
            if cache_allowed:
                try:
                    cache_key = self._generate_cache_key(query, trade_date, query=query)
                    cached_result = self.cache_client.get(cache_key) if self.cache_client else None
                except Exception as exc:  # pragma: no cover - defensive downgrade
                    logger.warning("Cache lookup failed, skipping cache for this request: %s", exc)
                    cache_allowed = False

            if cached_result:
                cached_result["_from_cache"] = True
                cached_result.setdefault("_cached_at", time.time())
                logger.info("Cache hit for %s", cache_key)
                try:
                    await progress_msg.delete()
                except Exception:
                    pass

                messages = self.formatter.format_analysis_result(cached_result)
                messages = self._append_cache_marker(messages, cached_result)
                for message in messages:
                    await update.message.reply_text(message, parse_mode="Markdown")
                    await asyncio.sleep(0.5)
                return

            if cache_key:
                logger.info("Cache miss for %s", cache_key)

            # 3. 调用DeFi Agent
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

            # 缓存写入
            if cache_allowed and cache_key and result:
                try:
                    result["_cached_at"] = time.time()
                    self.cache_client.set(cache_key, result)  # type: ignore[union-attr]
                except Exception as exc:  # pragma: no cover - defensive downgrade
                    logger.warning("Cache write failed for %s: %s", cache_key, exc)

            # 4. 删除进度消息
            try:
                await progress_msg.delete()
            except Exception:
                pass

            # 5. 发送分析结果
            messages = self.formatter.format_analysis_result(result)
            messages = self._append_cache_marker(messages, result)

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
        finally:
            duration = time.time() - start_time
            self._record_response_time(duration)

    async def _run_agent_analysis(self, query: str) -> Dict:  # pragma: no cover - integration path
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
