import asyncio
import importlib
from concurrent.futures import ThreadPoolExecutor

import pytest


class TimeStub:
    def __init__(self, start: float = 0.0):
        self.current = start

    def advance(self, seconds: float) -> None:
        self.current += seconds

    def __call__(self) -> float:
        return self.current


class FakeUser:
    def __init__(self, user_id: int = 1, username: str = "tester"):
        self.id = user_id
        self.username = username


class FakeChat:
    def __init__(self, chat_id: int = 1):
        self.id = chat_id


class FakeMessage:
    def __init__(self, text: str = ""):
        self.text = text
        self.replies = []
        self.edits = []
        self.deleted = False

    async def reply_text(self, text: str, parse_mode: str | None = None):
        self.replies.append(text)
        return self

    async def edit_text(self, text: str, parse_mode: str | None = None):
        self.edits.append(text)
        return self

    async def delete(self):
        self.deleted = True


class FakeUpdate:
    def __init__(self, user_id: int = 1, text: str = ""):
        self.effective_user = FakeUser(user_id=user_id)
        self.effective_chat = FakeChat(chat_id=user_id)
        self.message = FakeMessage(text=text)


class FakeContext:
    def __init__(self, args=None):
        self.args = args or []


class DummyFormatter:
    def __init__(self):
        self.progress_calls = []
        self.errors = []

    def format_welcome(self) -> str:
        return "welcome"

    def format_help(self) -> str:
        return "help"

    def format_error(self, message: str) -> str:
        self.errors.append(message)
        return f"error:{message}"

    def format_progress(self, step: str, current: int, total: int) -> str:
        self.progress_calls.append((step, current, total))
        return f"{step}-{current}/{total}"

    def format_analysis_result(self, result):
        return ["done"]

    def format_security_rejection(self, reason: str) -> str:
        return f"rejected:{reason}"

    def format_backtest_result(self, result):
        return "backtest-result"


class DummyIntent:
    def __init__(self, protocol_name: str = None, investment_amount=None, risk_preference: str = None, target_apy=None):
        self.protocol_name = protocol_name
        self.investment_amount = investment_amount
        self.risk_preference = risk_preference
        self.target_apy = target_apy


class DummySanitizationResult:
    def __init__(self, is_safe=True, rejection_reason=None, intent=None, confidence: float = 1.0):
        self.is_safe = is_safe
        self.rejection_reason = rejection_reason
        self.intent = intent
        self.confidence = confidence


@pytest.fixture
def handler_factory(monkeypatch):
    def _factory(
        admin_ids: str = "99",
        per_user: str = "2",
        window: str = "60",
        start_time: float = 1_000.0,
        enable_sanitization: bool = False,
    ):
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-token")
        monkeypatch.setenv("BOT_RATE_LIMIT_PER_USER", per_user)
        monkeypatch.setenv("BOT_RATE_LIMIT_WINDOW", window)
        monkeypatch.setenv("BOT_ADMIN_USER_IDS", admin_ids)
        monkeypatch.setenv("BOT_ENABLE_SANITIZATION", "true" if enable_sanitization else "false")

        import bot.config as config
        import bot.handlers as handlers

        config = importlib.reload(config)
        handlers = importlib.reload(handlers)

        class DummyWhitelist:
            def __init__(self, *args, **kwargs):
                self.calls = []

            def check(self, slug_or_name, chain=None):
                self.calls.append((slug_or_name, chain))
                return {
                    "status": "trusted",
                    "protocol_slug": slug_or_name or "",
                    "metrics": {},
                    "confidence_score": 1.0,
                    "data_sources": [],
                    "reason": "stubbed",
                }

        class DummyValidator:
            def __init__(self, *args, **kwargs):
                self.calls = []

            def validate(self, text, context=None):
                self.calls.append((text, context))
                return {
                    "is_safe": True,
                    "issues": [],
                    "patched_text": text or "",
                    "original_text": text or "",
                }

        monkeypatch.setattr(handlers, "ProtocolWhitelist", DummyWhitelist)
        monkeypatch.setattr(handlers, "OutputValidator", DummyValidator)

        fake_time = TimeStub(start_time)
        monkeypatch.setattr(handlers.time, "time", fake_time)

        handler = handlers.CommandHandlers()
        return handler, fake_time, handlers, config

    return _factory


def test_admin_bypasses_rate_limit(handler_factory):
    handler, _, _, _ = handler_factory(admin_ids="101")

    for _ in range(5):
        allowed, reason = handler.check_rate_limit(101)
        assert allowed
        assert reason in (None, "")

    stats = handler.get_stats_snapshot()
    assert stats["total_requests"] == 5
    assert stats["active_users"] == 1


def test_rate_limit_blocks_regular_user(handler_factory):
    handler, fake_time, _, _ = handler_factory(admin_ids="", per_user="2", window="60")
    user_id = 555

    allowed, _ = handler.check_rate_limit(user_id)
    assert allowed
    fake_time.advance(1)

    allowed, _ = handler.check_rate_limit(user_id)
    assert allowed
    fake_time.advance(1)

    allowed, reason = handler.check_rate_limit(user_id)
    assert not allowed
    assert "等待" in reason

    stats = handler.get_stats_snapshot()
    assert stats["total_requests"] == 2
    assert stats["active_users"] == 1


def test_window_reset_clears_stats(handler_factory):
    handler, fake_time, _, _ = handler_factory(admin_ids="", per_user="3", window="10", start_time=500.0)

    handler.check_rate_limit(1)
    fake_time.advance(1)
    handler.check_rate_limit(2)

    stats = handler.get_stats_snapshot()
    assert stats["total_requests"] == 2
    assert stats["active_users"] == 2

    fake_time.advance(15)
    allowed, _ = handler.check_rate_limit(1)
    assert allowed

    stats_after_reset = handler.get_stats_snapshot()
    assert stats_after_reset["total_requests"] == 1
    assert stats_after_reset["active_users"] == 1


def test_concurrent_requests_are_thread_safe(handler_factory):
    handler, _, _, _ = handler_factory(admin_ids="", per_user="50", window="60")

    user_ids = list(range(10))

    def _make_call(uid: int) -> bool:
        allowed, _ = handler.check_rate_limit(uid)
        return allowed

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(_make_call, user_ids))

    assert all(results)

    handler._record_response_time(2.0)
    handler._record_response_time(4.0)

    stats = handler.get_stats_snapshot()
    assert stats["total_requests"] == len(user_ids)
    assert stats["active_users"] == len(set(user_ids))
    assert stats["average_response_time"] == pytest.approx(3.0)


def test_invalid_admin_ids_are_ignored(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-token")
    monkeypatch.setenv("BOT_ADMIN_USER_IDS", "abc,123, ,456x,789")

    import bot.config as config

    config = importlib.reload(config)

    assert config.ADMIN_USER_IDS == {123, 789}
    assert config.is_admin(123)
    assert not config.is_admin(456)


def test_bot_config_requires_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")

    import bot.config as config

    config = importlib.reload(config)
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "")

    with pytest.raises(ValueError):
        config.BotConfig()


def test_bot_config_method_is_admin(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "dummy-token")
    monkeypatch.setenv("BOT_ADMIN_USER_IDS", "42")

    import bot.config as config

    config = importlib.reload(config)

    cfg = config.BotConfig()
    assert cfg.is_admin(42)


@pytest.mark.anyio
async def test_start_and_help_commands_send_responses(handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    update = FakeUpdate(user_id=2024)
    context = FakeContext()

    await handler.start_command(update, context)
    await handler.help_command(update, context)

    assert "welcome" in update.message.replies[0]
    assert "help" in update.message.replies[1]


@pytest.mark.anyio
async def test_analyze_command_invokes_analysis(monkeypatch, handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    captured = {}

    async def fake_perform(update, query):
        captured["query"] = query

    monkeypatch.setattr(handler, "_perform_analysis", fake_perform)

    update = FakeUpdate(user_id=321)
    context = FakeContext(args=["aave-v3"])
    await handler.analyze_command(update, context)

    assert captured["query"] == "aave-v3"


@pytest.mark.anyio
async def test_analyze_command_requires_protocol(handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    update = FakeUpdate(user_id=322)
    context = FakeContext(args=[])
    await handler.analyze_command(update, context)

    assert any("请指定协议" in reply for reply in update.message.replies)


@pytest.mark.anyio
async def test_strategy_command_validates_input(handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    update = FakeUpdate(user_id=400)
    context = FakeContext(args=["not-a-number"])

    await handler.strategy_command(update, context)

    assert any("参数格式错误" in reply for reply in update.message.replies)


@pytest.mark.anyio
async def test_compare_command_requires_two_args(handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    update = FakeUpdate(user_id=500)
    context = FakeContext(args=["only-one"])

    await handler.compare_command(update, context)

    assert any("请指定两个协议" in reply for reply in update.message.replies)


@pytest.mark.anyio
async def test_handle_message_runs_sanitization(monkeypatch, handler_factory):
    handler, _, _, _ = handler_factory(per_user="10", enable_sanitization=True)
    handler.formatter = DummyFormatter()

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

    captured = {}

    async def fake_perform(update, query):
        captured["query"] = query

    monkeypatch.setattr(handler, "_perform_analysis", fake_perform)

    update = FakeUpdate(user_id=600, text="analyze aave")
    context = FakeContext(args=[])

    await handler.handle_message(update, context)

    assert captured["query"] == "analyze aave"
    assert any("理解您的需求" in reply for reply in update.message.replies)
    assert any("目标APY" in reply for reply in update.message.replies)


@pytest.mark.anyio
async def test_perform_analysis_records_duration(monkeypatch, handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    async def fake_agent_call(query: str):
        await asyncio.sleep(0)
        return {"result": "ok"}

    monkeypatch.setattr(handler, "_run_agent_analysis", fake_agent_call)

    update = FakeUpdate(user_id=700, text="analysis")
    await handler._perform_analysis(update, "query text")

    stats = handler.get_stats_snapshot()
    assert stats["average_response_time"] >= 0
    assert update.message.replies[-1] == "done"
    assert update.message.deleted is True


@pytest.mark.anyio
async def test_perform_analysis_handles_exception(monkeypatch, handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    async def failing_call(query: str):
        raise RuntimeError("boom")

    monkeypatch.setattr(handler, "_run_agent_analysis", failing_call)

    update = FakeUpdate(user_id=701, text="analysis")

    await handler._perform_analysis(update, "query text")

    assert any("分析出错" in reply for reply in update.message.replies)


@pytest.mark.anyio
async def test_commands_return_error_when_rate_limited(handler_factory):
    handler, _, _, _ = handler_factory(per_user="0")
    handler.formatter = DummyFormatter()

    update = FakeUpdate(user_id=750, text="blocked")

    await handler.analyze_command(update, FakeContext(args=["anything"]))
    await handler.strategy_command(update, FakeContext(args=["1"]))
    await handler.compare_command(update, FakeContext(args=["a", "b"]))
    await handler.handle_message(update, FakeContext(args=[]))

    assert all(reply.startswith("error:") for reply in update.message.replies)


@pytest.mark.anyio
async def test_strategy_command_builds_query(monkeypatch, handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    captured = {}

    async def fake_perform(update, query):
        captured["query"] = query

    monkeypatch.setattr(handler, "_perform_analysis", fake_perform)

    await handler.strategy_command(FakeUpdate(user_id=760), FakeContext(args=["1000", "LOW"]))

    assert "投资金额1000.0美金" in captured["query"]
    assert "风险偏好low" in captured["query"]


@pytest.mark.anyio
async def test_compare_command_runs_analysis(monkeypatch, handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    captured = {}

    async def fake_perform(update, query):
        captured["query"] = query

    monkeypatch.setattr(handler, "_perform_analysis", fake_perform)

    await handler.compare_command(FakeUpdate(user_id=770), FakeContext(args=["uniswap", "curve"]))

    assert captured["query"] == "对比uniswap和curve"


@pytest.mark.anyio
async def test_handle_message_rejects_unsafe_input(handler_factory):
    handler, _, _, _ = handler_factory(per_user="10", enable_sanitization=True)
    handler.formatter = DummyFormatter()

    class UnsafeSanitizer:
        def sanitize(self, text):
            return DummySanitizationResult(is_safe=False, rejection_reason="blocked")

    handler._sanitizer = UnsafeSanitizer()

    update = FakeUpdate(user_id=780, text="bad input")

    await handler.handle_message(update, FakeContext())

    assert update.message.replies[-1].startswith("rejected:")


@pytest.mark.anyio
async def test_perform_analysis_updates_progress(monkeypatch, handler_factory):
    handler, _, handlers_module, _ = handler_factory(per_user="10")
    formatter = DummyFormatter()
    handler.formatter = formatter

    original_sleep = asyncio.sleep

    async def fast_sleep(duration):
        await original_sleep(0)

    monkeypatch.setattr(handlers_module.asyncio, "sleep", fast_sleep)

    async def slow_analysis(query: str):
        await original_sleep(0.01)
        return {"result": "ok"}

    monkeypatch.setattr(handler, "_run_agent_analysis", slow_analysis)

    update = FakeUpdate(user_id=790, text="analysis")
    await handler._perform_analysis(update, "query text")

    assert update.message.edits  # progress updates attempted
    assert formatter.progress_calls


@pytest.mark.anyio
async def test_perform_analysis_handles_timeout_branch(monkeypatch, handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")
    handler.formatter = DummyFormatter()

    async def timeout_call(query: str):
        raise asyncio.TimeoutError()

    monkeypatch.setattr(handler, "_run_agent_analysis", timeout_call)

    update = FakeUpdate(user_id=791, text="analysis")
    await handler._perform_analysis(update, "query text")

    assert any("超时" in reply for reply in update.message.replies)


@pytest.mark.anyio
async def test_run_agent_analysis_uses_stub(handler_factory):
    handler, _, _, _ = handler_factory(per_user="10")

    class StubAgent:
        def propagate(self, company_name: str, trade_date: str):
            return {"company": company_name, "date": trade_date}, None

    handler._agent = StubAgent()
    handler.config.analysis_timeout = 1

    result = await handler._run_agent_analysis("demo")

    assert result["company"] == "demo"
