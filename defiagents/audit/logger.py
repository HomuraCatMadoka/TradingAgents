from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4


class AuditLogger:
    """审计日志记录器"""

    def __init__(self, db_path: str = "./data/audit.db"):
        """
        Args:
            db_path: SQLite 数据库路径
        """
        self._use_uri = False
        self._is_memory = db_path == ":memory:"
        self.bot_version = "1.0"
        self.db_path = self._prepare_db_path(db_path)
        self._ensure_db_exists()

    def _prepare_db_path(self, db_path: str) -> str:
        """处理内存数据库与 URI 模式。"""
        if db_path == ":memory:":
            self._use_uri = True
            return f"file:audit_log_{uuid4().hex}?mode=memory&cache=shared"
        if db_path.startswith("file:"):
            self._use_uri = True
        return db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, uri=self._use_uri)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db_exists(self):
        """确保数据库和表存在"""
        if not self._is_memory and not self.db_path.startswith("file:"):
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    user_id BIGINT NOT NULL,
                    username VARCHAR(100),
                    query TEXT NOT NULL,
                    protocol_name VARCHAR(100),
                    investment_amount FLOAT,
                    whitelist_status VARCHAR(20),
                    input_safe BOOLEAN NOT NULL,
                    input_risk_score FLOAT,
                    rejection_reason TEXT,
                    final_decision VARCHAR(20),
                    confidence_score FLOAT,
                    validation_issues TEXT,
                    response_time_seconds FLOAT,
                    llm_model VARCHAR(50),
                    cache_hit BOOLEAN,
                    bot_version VARCHAR(20),
                    error_message TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON audit_logs(user_id)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_event_type ON audit_logs(event_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_protocol ON audit_logs(protocol_name)')

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def log_analysis_request(
        self,
        user_id: int,
        query: str,
        protocol_name: Optional[str] = None,
        investment_amount: Optional[float] = None,
        whitelist_status: Optional[str] = None,
        input_safe: bool = True,
        input_risk_score: float = 0.0,
        username: Optional[str] = None,
    ) -> int:
        """记录分析请求"""
        timestamp = self._now()
        with self._connect() as conn:
            cursor = conn.execute(
                '''
                    INSERT INTO audit_logs (
                        timestamp, event_type, user_id, username, query,
                        protocol_name, investment_amount, whitelist_status,
                        input_safe, input_risk_score, bot_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    timestamp,
                    "analysis_request",
                    user_id,
                    username,
                    query,
                    protocol_name,
                    investment_amount,
                    whitelist_status,
                    input_safe,
                    input_risk_score,
                    self.bot_version,
                ),
            )
            return int(cursor.lastrowid)

    def update_analysis_result(
        self,
        log_id: int,
        final_decision: str,
        confidence_score: float,
        validation_issues: Optional[List[Dict]],
        response_time: float,
        llm_model: str,
        cache_hit: bool,
    ) -> None:
        """更新分析结果"""
        issues_json = json.dumps(validation_issues) if validation_issues else None
        with self._connect() as conn:
            conn.execute(
                '''
                    UPDATE audit_logs SET
                        final_decision = ?,
                        confidence_score = ?,
                        validation_issues = ?,
                        response_time_seconds = ?,
                        llm_model = ?,
                        cache_hit = ?
                    WHERE id = ?
                ''',
                (
                    final_decision,
                    confidence_score,
                    issues_json,
                    response_time,
                    llm_model,
                    cache_hit,
                    log_id,
                ),
            )

    def log_security_rejection(
        self,
        user_id: int,
        query: str,
        rejection_reason: str,
        risk_score: float,
        username: Optional[str] = None,
    ) -> int:
        """记录安全拒绝事件"""
        timestamp = self._now()
        with self._connect() as conn:
            cursor = conn.execute(
                '''
                    INSERT INTO audit_logs (
                        timestamp, event_type, user_id, username, query,
                        input_safe, input_risk_score, rejection_reason, bot_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    timestamp,
                    "security_rejection",
                    user_id,
                    username,
                    query,
                    False,
                    risk_score,
                    rejection_reason,
                    self.bot_version,
                ),
            )
            return int(cursor.lastrowid)

    def log_error(
        self,
        user_id: int,
        query: str,
        error_message: str,
        username: Optional[str] = None,
    ) -> int:
        """记录错误"""
        timestamp = self._now()
        with self._connect() as conn:
            cursor = conn.execute(
                '''
                    INSERT INTO audit_logs (
                        timestamp, event_type, user_id, username, query,
                        input_safe, error_message, bot_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    timestamp,
                    "error",
                    user_id,
                    username,
                    query,
                    True,
                    error_message,
                    self.bot_version,
                ),
            )
            return int(cursor.lastrowid)

    def get_user_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """获取用户历史记录"""
        with self._connect() as conn:
            cursor = conn.execute(
                '''
                    SELECT * FROM audit_logs
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''',
                (user_id, limit),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_statistics(self, days: int = 7) -> Dict:
        """获取统计信息"""
        since = datetime.now(timezone.utc) - timedelta(days=days)
        since_value = since.isoformat()

        with self._connect() as conn:
            total_requests = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE event_type='analysis_request' AND timestamp > ?",
                (since_value,),
            ).fetchone()[0] or 0

            active_users = conn.execute(
                "SELECT COUNT(DISTINCT user_id) FROM audit_logs WHERE timestamp > ?",
                (since_value,),
            ).fetchone()[0] or 0

            rejections = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE event_type='security_rejection' AND timestamp > ?",
                (since_value,),
            ).fetchone()[0] or 0

            avg_response = conn.execute(
                "SELECT AVG(response_time_seconds) FROM audit_logs WHERE response_time_seconds IS NOT NULL AND timestamp > ?",
                (since_value,),
            ).fetchone()[0] or 0.0

            cache_hits = conn.execute(
                "SELECT COUNT(*) FROM audit_logs WHERE cache_hit = 1 AND timestamp > ?",
                (since_value,),
            ).fetchone()[0] or 0

            top_protocols = conn.execute(
                '''
                    SELECT protocol_name, COUNT(*) as count
                    FROM audit_logs
                    WHERE protocol_name IS NOT NULL AND timestamp > ?
                    GROUP BY protocol_name
                    ORDER BY count DESC
                    LIMIT 5
                ''',
                (since_value,),
            ).fetchall()

        cache_rate = (cache_hits / total_requests * 100) if total_requests > 0 else 0.0

        return {
            "period_days": days,
            "total_requests": total_requests,
            "active_users": active_users,
            "security_rejections": rejections,
            "avg_response_time": avg_response or 0.0,
            "cache_hit_rate": cache_rate,
            "top_protocols": [(row[0], row[1]) for row in top_protocols],
        }
