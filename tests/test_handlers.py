import asyncio
from datetime import datetime
from unittest.mock import Mock

import pytest

from bot.formatters import TelegramFormatter
from tests.test_rate_limit import (
    DummyFormatter,
    DummyIntent,
    DummySanitizationResult,
    FakeContext,
    FakeUpdate,
    TimeStub,
    handler_factory,
)


async def _run_status_flow(monkeypatch, handler_factory):
    handler, fake_time, handlers_module, _ = handler_factory(admin_ids="101", per_user="3", window="60")
    handler.formatter = TelegramFormatter()

    # 清除测试缓存，避免旧数据干扰测试
    if handler.cache_client:
        handler.cache_client.clear_prefix("defi_analysis:")

    # Cover stats window reset and admin rate-limit bypass.
    handler.global_stats["window_start"] = fake_time() - handler.config.rate_limit_window - 1
    handler._reset_stats_window_if_needed(fake_time())
    allowed, reason = handler.check_rate_limit(101)
    assert allowed and reason is None
    assert handler._get_rate_limit_status(None)["used"] == 0

    # Basic start/help commands.
    welcome_update = FakeUpdate(user_id=300)
    await handler.start_command(welcome_update, FakeContext())
    help_update = FakeUpdate(user_id=301)
    await handler.help_command(help_update, FakeContext())

    # Seed rate limit usage for the non-admin path without counting /status.
    fake_time.advance(10)
    handler.rate_limit_tracker[123] = [fake_time()]

    def failing_health():
        raise TimeoutError("boom")

    monkeypatch.setattr(handlers_module.health_checker, "get_system_health", failing_health)

    user_update = FakeUpdate(user_id=123)
    stats_before_status = handler.get_stats_snapshot()["total_requests"]
    await handler.status_command(user_update, FakeContext())

    user_message = user_update.message.replies[-1]
    assert "速率限制状态" in user_message
    assert "健康检查暂不可用" in user_message
    assert handler.rate_limit_tracker[123]  # No additional entries added
    assert handler.get_stats_snapshot()["total_requests"] == stats_before_status  # status is exempt

    # Admin view should include global stats and healthy sources.
    monkeypatch.setattr(
        handlers_module.health_checker,
        "get_system_health",
        lambda: {"defillama": {"source": "online", "latency": 12}},
    )
    handler._record_response_time(2.0)
    handler._record_response_time(4.0)

    admin_update = FakeUpdate(user_id=101)
    await handler.status_command(admin_update, FakeContext())

    admin_message = admin_update.message.replies[-1]
    assert "全局统计" in admin_message
    assert "DeFi Llama" in admin_message
    assert "平均响应时间" in admin_message

    # Switch to dummy formatter for lightweight assertions on command flows.
    handler.formatter = DummyFormatter()

    # Rate limit rejection branch.
    handler.config.rate_limit_per_user = 0
    blocked_update = FakeUpdate(user_id=202)
    await handler.analyze_command(blocked_update, FakeContext(args=["aave"]))
    assert blocked_update.message.replies[-1].startswith("error:")

    # Successful analyze command path with argument parsing.
    handler.config.rate_limit_per_user = 5
    captured = {}

    async def fake_perform(update, query):
        captured["query"] = query

    monkeypatch.setattr(handler, "_perform_analysis", fake_perform)
    await handler.analyze_command(FakeUpdate(user_id=203), FakeContext(args=["aave-v3"]))
    assert captured["query"] == "aave-v3"
    empty_args_update = FakeUpdate(user_id=204)
    await handler.analyze_command(empty_args_update, FakeContext(args=[]))
    assert any("请指定协议" in reply for reply in empty_args_update.message.replies)

    # Strategy command validation error and success branches.
    bad_strategy = FakeUpdate(user_id=205)
    await handler.strategy_command(bad_strategy, FakeContext(args=["oops"]))
    assert any("参数格式错误" in reply for reply in bad_strategy.message.replies)

    captured.clear()
    await handler.strategy_command(FakeUpdate(user_id=206), FakeContext(args=["1000", "LOW"]))
    assert "投资金额1000.0美金" in captured.get("query", "")

    # Compare command validation and success.
    bad_compare = FakeUpdate(user_id=207)
    await handler.compare_command(bad_compare, FakeContext(args=["only-one"]))
    assert any("请指定两个协议" in reply for reply in bad_compare.message.replies)

    captured.clear()
    await handler.compare_command(FakeUpdate(user_id=208), FakeContext(args=["uni", "curve"]))
    assert captured.get("query") == "对比uni和curve"

    # Rate limit rejection branches for strategy/compare/handle_message.
    handler.config.rate_limit_per_user = 0
    blocked_strategy = FakeUpdate(user_id=209)
    await handler.strategy_command(blocked_strategy, FakeContext(args=["1"]))
    blocked_compare = FakeUpdate(user_id=210)
    await handler.compare_command(blocked_compare, FakeContext(args=["a", "b"]))
    blocked_message = FakeUpdate(user_id=211, text="blocked")
    await handler.handle_message(blocked_message, FakeContext())
    assert all(reply.startswith("error:") for reply in blocked_message.message.replies)
    handler.config.rate_limit_per_user = 5

    # Restore original perform method for dedicated tests later.
    handler._perform_analysis = handlers_module.CommandHandlers._perform_analysis.__get__(handler)

    # handle_message with sanitization success path.
    handler.config.enable_input_sanitization = True
    handler._sanitizer = type(
        "UnsafeSanitizer",
        (),
        {"sanitize": lambda self, text: DummySanitizationResult(is_safe=False, rejection_reason="blocked")},
    )()
    unsafe_update = FakeUpdate(user_id=212, text="bad input")
    await handler.handle_message(unsafe_update, FakeContext())
    assert unsafe_update.message.replies[-1].startswith("rejected:")

    handler._sanitizer = type(
        "Sanitizer",
        (),
        {
            "sanitize": lambda self, text: DummySanitizationResult(
                is_safe=True,
                intent=DummyIntent(protocol_name="aave-v3", investment_amount=100000, risk_preference="low", target_apy=8),
                confidence=0.9,
            )
        },
    )()

    captured.clear()

    async def capture_analysis(update, query):
        captured["query"] = query

    handler._perform_analysis = capture_analysis

    sanitized_update = FakeUpdate(user_id=208, text="run analysis")
    await handler.handle_message(sanitized_update, FakeContext())
    assert captured.get("query") == "run analysis"
    assert any("理解您的需求" in reply for reply in sanitized_update.message.replies)

    # _perform_analysis success and error paths.
    formatter = DummyFormatter()
    handler.formatter = formatter
    handler._perform_analysis = handlers_module.CommandHandlers._perform_analysis.__get__(handler)

    original_sleep = handlers_module.asyncio.sleep

    async def fast_sleep(duration):
        await original_sleep(0)

    monkeypatch.setattr(handlers_module.asyncio, "sleep", fast_sleep)

    async def slow_analysis(query: str):
        await original_sleep(0.01)
        return {"result": "ok"}

    monkeypatch.setattr(handler, "_run_agent_analysis", slow_analysis)
    success_update = FakeUpdate(user_id=209, text="analysis")
    await handler._perform_analysis(success_update, "query text")
    assert formatter.progress_calls  # progress updated
    assert success_update.message.replies[-1] == "done"

    handler.config.enable_progress_updates = False
    monkeypatch.setattr(handler, "_run_agent_analysis", lambda query: asyncio.sleep(0))
    no_progress_update = FakeUpdate(user_id=211, text="analysis")
    await handler._perform_analysis(no_progress_update, "quick run")
    handler.config.enable_progress_updates = True

    async def failing_analysis(query: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(handler, "_run_agent_analysis", failing_analysis)
    failure_update = FakeUpdate(user_id=210, text="analysis")
    await handler._perform_analysis(failure_update, "failing query")  # 使用不同的查询避免缓存命中
    assert any("分析出错" in reply for reply in failure_update.message.replies)

    async def timeout_analysis(query: str):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(handler, "_run_agent_analysis", timeout_analysis)
    timeout_update = FakeUpdate(user_id=213, text="analysis")
    await handler._perform_analysis(timeout_update, "timeout query")  # 使用不同的查询避免缓存命中
    assert any("超时" in reply for reply in timeout_update.message.replies)


async def _run_cache_flow(monkeypatch, handler_factory):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-token")
    monkeypatch.setenv("BOT_CACHE_ENABLED", "true")

    import importlib

    import bot.config as config
    import bot.handlers as handlers

    config = importlib.reload(config)
    handlers = importlib.reload(handlers)

    fake_time = TimeStub(start=1000.0)
    monkeypatch.setattr(handlers.time, "time", fake_time)

    class FixedDatetime(datetime):
        @classmethod
        def now(cls):
            return cls(2024, 1, 2)

    monkeypatch.setattr(handlers, "datetime", FixedDatetime)

    real_sleep = handlers.asyncio.sleep

    async def fast_sleep(duration):
        await real_sleep(0)

    monkeypatch.setattr(handlers.asyncio, "sleep", fast_sleep)

    handler = handlers.CommandHandlers()

    class RecordingFormatter(DummyFormatter):
        def __init__(self):
            super().__init__()
            self.payloads = []

        def format_analysis_result(self, result):
            self.payloads.append(result)
            return ["done"]

    class StubCache:
        def __init__(self):
            self.store = {}
            self.get_calls = []
            self.set_calls = []

        def get(self, key):
            self.get_calls.append(key)
            return self.store.get(key)

        def set(self, key, value):
            self.set_calls.append((key, value))
            self.store[key] = value
            return True

    handler.formatter = RecordingFormatter()
    cache = StubCache()
    handler.cache_client = cache

    expected_key = handler._generate_cache_key("aave-v3", "2024-01-02", query="aave-v3")
    assert expected_key.startswith("defi_analysis:aave-v3:2024-01-02:")
    assert len(expected_key.split(":")[-1]) == 8
    assert handler._generate_query_hash(protocol="aave", amount=1) == handler._generate_query_hash(amount=1, protocol="aave")

    calls = 0

    async def fresh_analysis(query: str):
        nonlocal calls
        calls += 1
        return {"result": "fresh"}

    handler._run_agent_analysis = fresh_analysis
    await handler._perform_analysis(FakeUpdate(user_id=1, text="query"), "aave-v3")
    payload = handler.formatter.payloads[-1]
    assert calls == 1
    assert cache.set_calls and cache.set_calls[0][0] == expected_key
    assert "_cached_at" in payload and payload.get("_from_cache") is None

    cache.store[expected_key] = {"result": "cached"}
    calls = 0

    async def fail_if_called(query: str):
        nonlocal calls
        calls += 1
        raise AssertionError("analysis should not run on cache hit")

    handler._run_agent_analysis = fail_if_called
    await handler._perform_analysis(FakeUpdate(user_id=2, text="query"), "aave-v3")
    payload = handler.formatter.payloads[-1]
    assert payload["_from_cache"] is True
    assert payload["_cached_at"] == fake_time()
    assert calls == 0
    assert len(cache.set_calls) == 1  # no new writes on hit

    cache.store.clear()
    cache.set_calls.clear()
    cache.get_calls.clear()
    calls = 0

    async def failing_analysis(query: str):
        nonlocal calls
        calls += 1
        raise RuntimeError("boom")

    handler._run_agent_analysis = failing_analysis
    fail_update = FakeUpdate(user_id=3, text="fail")
    await handler._perform_analysis(fail_update, "aave-v3")
    assert any("error:" in reply for reply in fail_update.message.replies)
    assert calls == 1
    assert cache.set_calls == []

    cache.store.clear()
    cache.get_calls.clear()
    cache.set_calls.clear()
    handler.config.cache_enabled = False

    async def uncached_analysis(query: str):
        return {"result": "no-cache"}

    handler._run_agent_analysis = uncached_analysis
    await handler._perform_analysis(FakeUpdate(user_id=4, text="no-cache"), "aave-v3")
    assert cache.get_calls == [] and cache.set_calls == []

    class ExplodingCache:
        def get(self, key):
            raise RuntimeError("redis down")

        def set(self, key, value):
            raise RuntimeError("redis down")

    handler.config.cache_enabled = True
    handler.cache_client = ExplodingCache()

    calls = 0

    async def runs_with_downgrade(query: str):
        nonlocal calls
        calls += 1
        return {"result": "fallback"}

    handler._run_agent_analysis = runs_with_downgrade
    await handler._perform_analysis(FakeUpdate(user_id=5, text="fallback"), "aave-v3")
    assert calls == 1

    # Additional coverage for command flows
    handler2, fake_time2, handlers_module2, config_module2 = handler_factory(
        admin_ids="7",
        per_user="10",
        window="60",
    )
    handler2.formatter = DummyFormatter()
    handler2.cache_client = StubCache()

    async def zero_sleep(duration):
        await asyncio.sleep(0)

    monkeypatch.setattr(handlers_module2.asyncio, "sleep", zero_sleep)

    async def ok_analysis(query: str):
        await asyncio.sleep(0)
        return {"result": "ok"}

    monkeypatch.setattr(handler2, "_run_agent_analysis", ok_analysis)
    monkeypatch.setattr(
        handlers_module2.health_checker,
        "get_system_health",
        lambda: {"defillama": {"source": "online", "latency": 10}},
    )

    await handler2.start_command(FakeUpdate(user_id=7), FakeContext())
    await handler2.help_command(FakeUpdate(user_id=7), FakeContext())
    await handler2.analyze_command(FakeUpdate(user_id=7), FakeContext(args=["proto-x"]))
    await handler2.strategy_command(FakeUpdate(user_id=7), FakeContext(args=["1000", "LOW"]))
    await handler2.compare_command(FakeUpdate(user_id=7), FakeContext(args=["p1", "p2"]))
    await handler2.handle_message(FakeUpdate(user_id=7, text="run analysis"), FakeContext())
    await handler2.status_command(FakeUpdate(user_id=7), FakeContext())

    handler3, fake_time3, handlers_module3, config_module3 = handler_factory(
        admin_ids="",
        per_user="1",
        window="2",
        start_time=0.0,
        enable_sanitization=True,
    )
    handler3.formatter = DummyFormatter()
    handler3.cache_client = StubCache()

    async def tiny_sleep(duration):
        await asyncio.sleep(0)

    monkeypatch.setattr(handlers_module3.asyncio, "sleep", tiny_sleep)

    async def quick_analysis(query: str):
        await asyncio.sleep(0)
        return {"result": "mini"}

    monkeypatch.setattr(handler3, "_run_agent_analysis", quick_analysis)

    handler3.global_stats["total_requests"] = 3
    handler3.global_stats["active_users"] = {1, 2}
    fake_time3.advance(handler3.config.rate_limit_window + 1)
    handler3._reset_stats_window_if_needed(fake_time3())
    assert handler3.global_stats["total_requests"] == 0
    assert handler3._calculate_average_response_time_locked() == 0.0

    handler3.config.rate_limit_per_user = 1
    allowed, _ = handler3.check_rate_limit(30)
    blocked, reason = handler3.check_rate_limit(30)
    assert allowed and not blocked and "等待" in reason

    status_none = handler3._get_rate_limit_status(None)
    config_module3.ADMIN_USER_IDS.add(99)
    status_admin = handler3._get_rate_limit_status(99)
    status_user = handler3._get_rate_limit_status(30)
    assert status_none["limit"] == handler3.config.rate_limit_per_user
    assert status_admin["used"] == 0
    assert status_user["used"] >= 1

    assert handler3._format_health_status({})["health_checks"]["status"] == "degraded"

    handler3.config.rate_limit_per_user = 0
    handler3.rate_limit_tracker.clear()
    await handler3.analyze_command(FakeUpdate(user_id=31), FakeContext(args=["x"]))

    handler3.config.rate_limit_per_user = 5
    handler3.rate_limit_tracker.clear()
    await handler3.analyze_command(FakeUpdate(user_id=32), FakeContext(args=[]))

    handler3.config.rate_limit_per_user = 5
    await handler3.strategy_command(FakeUpdate(user_id=33), FakeContext(args=["not-number"]))

    handler3.config.rate_limit_per_user = 0
    handler3.rate_limit_tracker.clear()
    await handler3.strategy_command(FakeUpdate(user_id=34), FakeContext(args=["100", "low"]))

    handler3.config.rate_limit_per_user = 5
    handler3.rate_limit_tracker.clear()
    await handler3.compare_command(FakeUpdate(user_id=35), FakeContext(args=["only-one"]))

    handler3.config.rate_limit_per_user = 0
    handler3.rate_limit_tracker.clear()
    await handler3.compare_command(FakeUpdate(user_id=36), FakeContext(args=["p1", "p2"]))

    handler3.config.rate_limit_per_user = 0
    handler3.rate_limit_tracker.clear()
    await handler3.handle_message(FakeUpdate(user_id=37, text="block"), FakeContext())

    handler3.config.rate_limit_per_user = 5
    handler3.rate_limit_tracker.clear()
    handler3.config.enable_input_sanitization = True
    handler3._sanitizer = type(
        "Sanitizer",
        (),
        {
            "sanitize": lambda self, text: DummySanitizationResult(
                is_safe=True,
                intent=DummyIntent(
                    protocol_name="proto",
                    investment_amount=123,
                    risk_preference="low",
                    target_apy=5,
                ),
                confidence=0.9,
            )
        },
    )()
    await handler3.handle_message(FakeUpdate(user_id=38, text="sanitized"), FakeContext())

    handler3.config.enable_progress_updates = False
    await handler3._perform_analysis(FakeUpdate(user_id=39, text="no progress"), "proto-z")

@pytest.mark.anyio
async def test_clear_cache_command(monkeypatch, handler_factory):
    handler, _, _, _ = handler_factory(admin_ids="1", per_user="0", window="60")
    handler.config.cache_enabled = True

    class ClearingCache:
        def __init__(self, count: int):
            self.count = count
            self.calls = 0
            self.prefixes = []

        def clear_prefix(self, prefix: str):
            self.calls += 1
            self.prefixes.append(prefix)
            return self.count

    handler.cache_client = ClearingCache(count=5)

    admin_update = FakeUpdate(user_id=1)
    await handler.clear_cache_command(admin_update, FakeContext())
    assert handler.cache_client.calls == 1
    assert handler.cache_client.prefixes == ["defi_analysis:"]
    assert any("5" in reply for reply in admin_update.message.replies)

    non_admin_update = FakeUpdate(user_id=2)
    await handler.clear_cache_command(non_admin_update, FakeContext())
    assert any("仅管理员" in reply for reply in non_admin_update.message.replies)

    handler.cache_client = None
    unavailable_update = FakeUpdate(user_id=1)
    await handler.clear_cache_command(unavailable_update, FakeContext())
    assert any("Redis 不可用" in reply for reply in unavailable_update.message.replies)

    class ExplodingCache:
        def clear_prefix(self, prefix: str):
            raise RuntimeError("boom")

    handler.cache_client = ExplodingCache()
    exploding_update = FakeUpdate(user_id=1)
    await handler.clear_cache_command(exploding_update, FakeContext())
    assert any("Redis 不可用" in reply for reply in exploding_update.message.replies)
    await _run_status_flow(monkeypatch, handler_factory)
    await _run_cache_flow(monkeypatch, handler_factory)


@pytest.mark.anyio
async def test_status_command(monkeypatch, handler_factory):
    await _run_status_flow(monkeypatch, handler_factory)


@pytest.mark.anyio
async def test_cache_integration(monkeypatch, handler_factory):
    await _run_cache_flow(monkeypatch, handler_factory)


@pytest.mark.anyio
async def test_whitelist_blocks_suspicious_message(handler_factory):
    handler, _, _, _ = handler_factory(per_user="5")
    handler.formatter = DummyFormatter()
    handler.config.enable_input_sanitization = True  # 确保启用输入净化

    class SuspiciousWhitelist:
        def check(self, slug_or_name, chain=None):
            return {
                "status": "suspicious",
                "protocol_slug": slug_or_name,
                "metrics": {},
                "confidence_score": 0.1,
                "data_sources": [],
                "reason": "flagged as高风险",
            }

    handler.whitelist = SuspiciousWhitelist()

    # Mock sanitizer to extract protocol name
    from defiagents.security.input_sanitizer import SanitizationResult
    from defiagents.security.intent_extractor import InvestmentIntent
    handler._sanitizer = Mock()
    handler._sanitizer.sanitize.return_value = SanitizationResult(
        is_safe=True,
        risk_score=0.1,
        rejection_reason=None,
        sanitized_input="aave-v3",
        intent=InvestmentIntent(
            protocol_name="aave-v3",
            investment_amount=None,
            risk_preference=None,
            protocol_type=None,
            target_apy=None,
            chain=None,
            tokens=None,
            confidence=0.8
        ),
        confidence=0.8
    )

    async def should_not_run(*args, **kwargs):
        raise AssertionError("analysis should not run for suspicious protocols")

    handler._perform_analysis = should_not_run

    update = FakeUpdate(user_id=501, text="analyze aave-v3")
    await handler.handle_message(update, FakeContext())
    assert any("suspicious" in reply.lower() or "高风险" in reply for reply in update.message.replies)


@pytest.mark.anyio
async def test_whitelist_warns_unverified_and_continues(handler_factory):
    handler, _, _, _ = handler_factory(per_user="5")
    handler.formatter = DummyFormatter()

    class UnverifiedWhitelist:
        def check(self, slug_or_name, chain=None):
            return {
                "status": "unverified",
                "protocol_slug": slug_or_name,
                "metrics": {},
                "confidence_score": 0.5,
                "data_sources": ["stub"],
                "reason": "no data",
            }

    handler.whitelist = UnverifiedWhitelist()
    calls = {}

    async def should_run(update, query, **kwargs):
        calls["called"] = True
        calls["kwargs"] = kwargs

    handler._perform_analysis = should_run

    update = FakeUpdate(user_id=503, text="maybe protocol")
    await handler.analyze_command(update, FakeContext(args=["maybe-proto"]))
    assert calls.get("called")
    assert any("未在白名单" in reply for reply in update.message.replies)


@pytest.mark.anyio
async def test_output_validation_patches_final_decision(handler_factory):
    handler, _, _, _ = handler_factory(per_user="5")
    handler.config.cache_enabled = False

    class RecordingFormatter(DummyFormatter):
        def __init__(self):
            super().__init__()
            self.payloads = []

        def format_analysis_result(self, result):
            self.payloads.append(result)
            return ["done"]

    class PatchedValidator:
        def __init__(self):
            self.calls = []

        def validate(self, text, context=None):
            self.calls.append((text, context))
            return {
                "is_safe": False,
                "issues": [{"severity": "warning", "category": "danger", "matched_pattern": "x", "location": "", "original_text": text}],
                "patched_text": f"{text} [patched]",
                "original_text": text,
            }

    handler.formatter = RecordingFormatter()
    handler.output_validator = PatchedValidator()

    async def fake_analysis(query: str):
        return {"final_decision": "raw decision"}

    handler._run_agent_analysis = fake_analysis

    update = FakeUpdate(user_id=502, text="run")
    await handler._perform_analysis(
        update,
        "query",
        protocol_name="proto",
        investment_amount=123.0,
        whitelist_result={
            "status": "trusted",
            "protocol_slug": "proto",
            "metrics": {},
            "confidence_score": 1.0,
            "data_sources": [],
            "reason": "hardcoded",
        },
    )

    assert handler.output_validator.calls
    ctx = handler.output_validator.calls[0][1]
    assert ctx["protocol_name"] == "proto"
    assert ctx["investment_amount"] == 123.0
    assert handler.formatter.payloads[-1]["final_decision"] == "raw decision [patched]"
