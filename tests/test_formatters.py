from datetime import datetime, timedelta

from bot.formatters import TelegramFormatter, add_cache_marker


def _verify_formatter_behaviors():
    formatter = TelegramFormatter(max_length=400)

    health_status = {
        "defi_llama": {"name": "DeFi Llama", "status": "online"},
        "the_graph": {"name": "The Graph", "status": "online"},
        "coingecko": {"name": "CoinGecko", "status": "degraded", "detail": "响应慢"},
        "gemini": {"name": "Gemini_LLM", "status": "configured"},
    }
    rate_limit_status = {"used": 3, "limit": 10, "reset_in_seconds": 300}
    global_stats = {
        "total_requests": 1234,
        "active_users": 56,
        "avg_response_time": 2.3,
        "uptime_seconds": 302400,  # 3天12小时
    }

    user_msg = formatter.format_status_message(
        health_status=health_status,
        rate_limit_status=rate_limit_status,
        is_admin=False,
    )

    assert "📊 系统状态" in user_msg
    assert "🔌 数据源健康度" in user_msg
    assert "✅ DeFi Llama: Online" in user_msg
    assert "⚠️ CoinGecko: Degraded (响应慢)" in user_msg
    assert "✅ Gemini\\_LLM: Configured" in user_msg  # 下划线需要转义
    assert "⏱️ 速率限制状态" in user_msg
    assert "已使用: 3/10 次" in user_msg
    assert "5分钟后" in user_msg
    assert "全局统计" not in user_msg

    admin_msg = formatter.format_status_message(
        health_status=health_status,
        rate_limit_status=rate_limit_status,
        is_admin=True,
        global_stats=global_stats,
    )

    assert "📈 全局统计 (仅管理员可见)" in admin_msg
    assert "总请求数: 1,234 次" in admin_msg
    assert "活跃用户: 56 人" in admin_msg
    assert "平均响应时间: 2.3 秒" in admin_msg
    assert "Bot 运行时间: 3天 12小时" in admin_msg
    assert len(admin_msg) <= formatter.max_length

    # 空健康检查与缺失统计分支
    empty_msg = formatter.format_status_message(
        health_status={},
        rate_limit_status={"used": 0, "limit": 0, "reset_in_seconds": 0},
    )
    assert "暂无健康检查数据" in empty_msg

    admin_no_avg = formatter.format_status_message(
        health_status={},
        rate_limit_status={"used": 0, "limit": 0, "reset_in_seconds": 0},
        is_admin=True,
        global_stats={"total_requests": 0, "active_users": 0, "uptime_seconds": 10},
    )
    assert "平均响应时间: -" in admin_no_avg
    assert "0分钟" in admin_no_avg

    # 其他格式化函数的基本行为（提升覆盖率）
    assert "欢迎使用" in formatter.format_welcome()
    assert "使用指南" in formatter.format_help()
    assert "分析中" in formatter.format_progress("step", 1, 4)
    assert "出错了" in formatter.format_error("boom")
    assert "输入安全检查" in formatter.format_security_rejection("bad input")

    # format_analysis_result 覆盖关键分支（转义、截断、决策提取）
    analysis_formatter = TelegramFormatter(max_length=80)
    analysis_result = {
        "protocol_of_interest": "curve",
        "trade_date": "2024-01-01",
        "market_report": "段落1\n\n段落2带有_markdown_",
        "fundamentals_report": "fundamentals line\n\nmore fundamentals",
        "yield_report": "yield data line",
        "risk_report": "risk detail content",
        "trader_plan": "INVEST now\nBUY token\nSome other lines",
    }
    analysis_messages = analysis_formatter.format_analysis_result(analysis_result)
    assert analysis_messages
    assert any("市场分析" in msg for msg in analysis_messages)
    assert all(len(msg) <= analysis_formatter.max_length for msg in analysis_messages)

    # 长文本截断与无决策分支
    long_text = "x" * 250
    assert "..." in formatter._extract_key_points(long_text, max_points=1)
    fallback_decision = formatter._extract_decision("just some notes")
    assert "just some notes" in fallback_decision

    # 直接覆盖截断和时间格式化的分支
    short_formatter = TelegramFormatter(max_length=50)
    truncated = short_formatter._truncate_message("x" * 200)
    assert "已截断" in truncated
    assert "1小时" in formatter._format_reset_time(3700)
    eta = formatter._resolve_reset_seconds({"reset_at": datetime.now() + timedelta(minutes=10)})
    assert eta is not None and eta > 0
    tiny_formatter = TelegramFormatter(max_length=10)
    tiny_truncated = tiny_formatter._truncate_message("y" * 200)
    assert len(tiny_truncated) <= 10

    # 时间格式化和解析的其它分支
    assert formatter._format_reset_time(None) == "未知"
    assert formatter._format_reset_time("bad") == "未知"
    assert formatter._format_reset_time(0) == "已重置"
    assert formatter._format_reset_time(30) == "不到1分钟后"
    assert "天" in formatter._format_reset_time(172800 + 3600)

    assert formatter._resolve_reset_seconds(None) is None
    assert formatter._resolve_reset_seconds({"reset_in_seconds": "bad"}) is None
    timestamp_eta = formatter._resolve_reset_seconds({"reset_at": datetime.now().timestamp() + 60})
    assert timestamp_eta is not None and timestamp_eta >= 0

    assert formatter._format_uptime(None) == "-"
    assert formatter._format_uptime("bad") == "-"
    assert formatter._format_uptime(0).endswith("分钟")

    # 安全拒绝的建议分支
    rejection_with_suggestions = formatter.format_security_rejection("reason", ["a", "b"])
    assert "a" in rejection_with_suggestions


def test_add_cache_marker():
    cached_at = datetime(2024, 1, 2, 14, 35).timestamp()
    base_message = "analysis summary"
    marked = add_cache_marker(base_message, cached_at)

    assert base_message in marked
    assert "📦 来自缓存" in marked
    assert "14:35" in marked
    assert marked.endswith("14:35）")

    _verify_formatter_behaviors()


def test_format_status_message():
    _verify_formatter_behaviors()
