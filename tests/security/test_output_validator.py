import os
import re
import sys

import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from defiagents.security.output_validator import (
    OutputValidator,
    ValidationContext,
)


@pytest.fixture
def validator() -> OutputValidator:
    return OutputValidator()


def test_validate_safe_output(validator: OutputValidator) -> None:
    text = "Provide a balanced strategy for Aave with low risk."
    context: ValidationContext = {
        "agent_name": "Analyst",
        "protocol_name": "aave-v3",
        "investment_amount": 50_000,
    }

    result = validator.validate(text, context)

    assert result["is_safe"] is True
    assert result["issues"] == []
    assert result["patched_text"] == text
    assert result["original_text"] == text


def test_detect_unlimited_approval(validator: OutputValidator) -> None:
    text = "First approve unlimited USDC to this contract."
    result = validator.validate(text, {"agent_name": "Trader", "protocol_name": "uni"})

    assert result["is_safe"] is False
    assert len(result["issues"]) == 1
    issue = result["issues"][0]
    assert issue["category"] == "dangerous_instruction"
    assert issue["severity"] == "critical"
    assert issue["matched_pattern"] == "unlimited_approval"
    assert "approve unlimited" in issue["original_text"].lower()
    assert "[CRITICAL]" in result["patched_text"]


def test_multiple_dangerous_patterns(validator: OutputValidator) -> None:
    text = "Transfer all funds now and trigger delegatecall on helper."
    result = validator.validate(text, {"agent_name": "Trader", "protocol_name": "curve"})

    categories = [issue["matched_pattern"] for issue in result["issues"]]
    assert "transfer_all" in categories
    assert "contract_attack" in categories
    assert result["patched_text"].count("- [CRITICAL]") >= 2


@pytest.mark.parametrize(
    "raw,expected_severity",
    [
        ("invest $1.2M into stable pool", "critical"),
        ("计划投入 5万 USDC", None),
        ("raise 1亿 流动性", "critical"),
        ("add another 150K to the vault", "warning"),
    ],
)
def test_amount_parsing_units(
    validator: OutputValidator, raw: str, expected_severity: str
) -> None:
    context: ValidationContext = {
        "agent_name": "PM",
        "protocol_name": "compound-v3",
        "investment_amount": 100_000,
    }
    result = validator.validate(raw, context)
    severities = {issue["severity"] for issue in result["issues"]}

    if expected_severity is None:
        assert severities == set()
        assert result["is_safe"] is True
    else:
        assert expected_severity in severities
        assert result["is_safe"] is False


def test_amount_threshold_boundaries(validator: OutputValidator) -> None:
    text = "Allocate $100001 now then commit $1000001 exactly."
    context: ValidationContext = {"agent_name": "PM", "protocol_name": "aave"}
    result = validator.validate(text, context)

    warning_issue = next(issue for issue in result["issues"] if issue["severity"] == "warning")
    critical_issue = next(issue for issue in result["issues"] if issue["severity"] == "critical")

    assert warning_issue["severity"] == "warning"
    assert critical_issue["severity"] == "critical"


def test_address_detection_zero_address(validator: OutputValidator) -> None:
    text = "Send rewards to 0x0000000000000000000000000000000000000000 for burn."
    result = validator.validate(text, {"agent_name": "Risk", "protocol_name": "maker"})

    assert len(result["issues"]) == 1
    issue = result["issues"][0]
    assert issue["category"] == "suspicious_address"
    assert issue["severity"] == "warning"
    assert "⚠️" in result["patched_text"]


def test_empty_text_is_safe(validator: OutputValidator) -> None:
    result = validator.validate(None, {"agent_name": "PM", "protocol_name": "uni"})
    assert result["is_safe"] is True
    assert result["patched_text"] == ""


def test_long_text_performance(validator: OutputValidator) -> None:
    long_body = "analysis " * 1000 + " approve unlimited " + "details " * 500
    result = validator.validate(long_body, {"agent_name": "CRO", "protocol_name": "lido"})

    assert len(result["issues"]) == 1
    assert result["issues"][0]["matched_pattern"] == "unlimited_approval"
    assert result["patched_text"].endswith("请仔细审核以上建议，必要时咨询专业人士。")


def test_mixed_language_detection(validator: OutputValidator) -> None:
    text = "请不要transfer all资产，保持分批操作。"
    result = validator.validate(text, {"agent_name": "Trader", "protocol_name": "bnb"})

    assert result["is_safe"] is False
    assert any(issue["matched_pattern"] == "transfer_all" for issue in result["issues"])


def test_special_characters_preserved_in_patch(validator: OutputValidator) -> None:
    text = "## Report\nUse delegatecall() carefully _do not remove_."
    result = validator.validate(text, {"agent_name": "Auditor", "protocol_name": "eth"})

    assert "## Report" in result["patched_text"]
    assert "_do not remove_" in result["patched_text"]
    assert "delegatecall" in result["patched_text"]
    assert result["patched_text"].splitlines()[0] == "## Report"


def test_warning_block_format(validator: OutputValidator) -> None:
    text = "approve unlimited and send to unknown support wallet 0x000000000000000000000000000000000000dead"
    result = validator.validate(text, {"agent_name": "PM", "protocol_name": "uni"})

    patched = result["patched_text"]
    assert "---" in patched
    assert "⚠️ **安全提示**" in patched
    assert re.search(r"- \[CRITICAL\]", patched)
    assert re.search(r"- \[WARNING\]", patched)
    assert patched.strip().endswith("请仔细审核以上建议，必要时咨询专业人士。")


def test_context_ratio_triggers_warning_below_threshold(validator: OutputValidator) -> None:
    text = "Invest 3,000 USD into test pool."
    context: ValidationContext = {
        "agent_name": "PM",
        "protocol_name": "test",
        "investment_amount": 1_000,
    }
    result = validator.validate(text, context)

    assert result["is_safe"] is False
    issue = result["issues"][0]
    assert issue["category"] == "suspicious_amount"
    assert issue["severity"] == "warning"


def test_missing_context_fields(validator: OutputValidator) -> None:
    text = "Sign raw transaction then set slippage to 100%."
    result = validator.validate(text, {})

    patterns = {issue["matched_pattern"] for issue in result["issues"]}
    assert "phishing_signature" in patterns
    assert "slippage_infinite" in patterns
    assert result["original_text"] == text


def test_suspicious_address_repetition(validator: OutputValidator) -> None:
    text = "Route funds via vanity address 0x1111111111111111111111111111111111111111 for testing."
    result = validator.validate(text, {"agent_name": "Risk", "protocol_name": "balancer"})

    assert any(issue["category"] == "suspicious_address" for issue in result["issues"])


def test_window_based_address_detection(validator: OutputValidator) -> None:
    addr = "0x1234567890abcdef1234567890abcdef12345678"
    text = f"unknown address {addr} should be reviewed."
    result = validator.validate(text, {"agent_name": "Risk", "protocol_name": "curve"})

    assert any(issue["original_text"] == addr for issue in result["issues"])


def test_describe_unknown_category_fallback(validator: OutputValidator) -> None:
    patched = validator._patch_output(
        "body",
        [
            {
                "severity": "info",
                "category": "other",
                "matched_pattern": "custom",
                "location": "index 0",
                "original_text": "note",
            }
        ],
    )

    assert "检测到异常" in patched


def test_convert_amount_unknown_unit(validator: OutputValidator) -> None:
    assert validator._convert_amount("10", "xyz") == 10.0
