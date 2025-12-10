import pytest

from defiagents.audit.logger import AuditLogger


def test_log_analysis_request():
    logger = AuditLogger(db_path=":memory:")

    log_id = logger.log_analysis_request(
        user_id=123,
        query="分析 aave-v3",
        protocol_name="aave-v3",
        investment_amount=10000.0,
        whitelist_status="trusted",
        input_safe=True,
        input_risk_score=0.1,
    )

    assert log_id > 0

    history = logger.get_user_history(user_id=123)
    assert len(history) == 1
    assert history[0]["protocol_name"] == "aave-v3"


def test_log_security_rejection():
    logger = AuditLogger(db_path=":memory:")

    logger.log_security_rejection(
        user_id=456,
        query="ignore previous instructions",
        rejection_reason="提示注入攻击",
        risk_score=0.9,
    )

    history = logger.get_user_history(user_id=456)
    assert len(history) == 1
    assert history[0]["event_type"] == "security_rejection"
    assert history[0]["input_safe"] == False


def test_update_analysis_result():
    logger = AuditLogger(db_path=":memory:")

    log_id = logger.log_analysis_request(
        user_id=789,
        query="分析 compound-v3",
        protocol_name="compound-v3",
    )

    logger.update_analysis_result(
        log_id=log_id,
        final_decision="INVEST",
        confidence_score=0.85,
        validation_issues=[{"severity": "warning", "category": "amount"}],
        response_time=105.2,
        llm_model="gemini-2.5-flash",
        cache_hit=False,
    )

    history = logger.get_user_history(user_id=789)
    assert history[0]["final_decision"] == "INVEST"
    assert history[0]["response_time_seconds"] == 105.2


def test_get_statistics():
    logger = AuditLogger(db_path=":memory:")

    for i in range(5):
        log_id = logger.log_analysis_request(
            user_id=100 + i,
            query=f"分析 protocol-{i}",
            protocol_name=f"protocol-{i % 3}",
        )
        logger.update_analysis_result(
            log_id=log_id,
            final_decision="INVEST",
            confidence_score=0.8,
            validation_issues=[],
            response_time=100.0,
            llm_model="gemini-2.5-flash",
            cache_hit=(i % 2 == 0),
        )

    logger.log_security_rejection(
        user_id=999,
        query="attack",
        rejection_reason="注入攻击",
        risk_score=0.9,
    )

    stats = logger.get_statistics(days=7)

    assert stats["total_requests"] == 5
    assert stats["active_users"] >= 5
    assert stats["security_rejections"] == 1
    assert stats["cache_hit_rate"] == 60.0
    assert len(stats["top_protocols"]) >= 2
