from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class AuditLog:
    """审计日志记录"""
    # 基础信息
    id: Optional[int] = None
    timestamp: Optional[datetime] = None
    event_type: str = ""  # 'analysis_request', 'security_rejection', 'agent_decision'

    # 用户信息
    user_id: int = 0
    username: Optional[str] = None

    # 请求信息
    query: str = ""
    protocol_name: Optional[str] = None
    investment_amount: Optional[float] = None

    # 安全检查
    whitelist_status: Optional[str] = None  # trusted/unverified/suspicious
    input_safe: bool = True
    input_risk_score: float = 0.0
    rejection_reason: Optional[str] = None

    # Agent 决策
    final_decision: Optional[str] = None  # INVEST/HOLD/AVOID
    confidence_score: Optional[float] = None
    validation_issues: Optional[List[Dict]] = None  # S1 输出验证问题

    # 性能指标
    response_time_seconds: Optional[float] = None
    llm_model: Optional[str] = None
    cache_hit: bool = False

    # 元数据
    bot_version: str = "1.0"
    error_message: Optional[str] = None
