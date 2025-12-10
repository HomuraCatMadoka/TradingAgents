import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from defiagents.security.input_sanitizer import InputSanitizer


def test_input_length_limit():
    """Ensure inputs over 500 chars are rejected with a friendly message."""
    sanitizer = InputSanitizer(strict_mode=False)

    # 正常长度
    short_input = "分析 aave-v3"
    result = sanitizer.sanitize(short_input)
    assert result.is_safe

    # 超长输入（501 字符）
    long_input = "a" * 501
    result = sanitizer.sanitize(long_input)
    assert not result.is_safe
    assert result.risk_score == 0.3
    assert "输入过长" in (result.rejection_reason or "")
    assert str(len(long_input)) in (result.rejection_reason or "")
    assert result.intent is None
    assert result.confidence == 0.0

    # 临界值（500 字符）
    boundary_input = "a" * 500
    result = sanitizer.sanitize(boundary_input)
    assert result.is_safe
