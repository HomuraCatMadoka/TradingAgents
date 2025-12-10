import json
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from core.exceptions import ValidationError
from core.jwt import utcnow
from db import SessionLocal
from defiagents.graph.trading_graph import TradingAgentsGraph
from models import AnalysisHistory
from sqlalchemy.orm import Session


class AgentService:
    """Synchronous wrapper to run the DeFi Agent and persist results."""

    def __init__(
        self,
        agent_runner: Optional[Callable[[str], Dict[str, Any]]] = None,
        session_factory: Callable[[], Session] = SessionLocal,
        agent_factory: Optional[Callable[[], Any]] = None,
    ) -> None:
        self._agent_runner = agent_runner or self._default_runner
        self._session_factory = session_factory
        self._agent_factory = agent_factory or TradingAgentsGraph

    def trigger_analysis(self, protocol_slug: str, user_id: int, db: Session | None = None) -> Tuple[int, Dict[str, Any]]:
        if not protocol_slug:
            raise ValidationError("protocol", "protocol slug is required")

        started = time.time()
        try:
            result = self._agent_runner(protocol_slug)
            payload: Dict[str, Any] = {"status": "completed", "protocol": protocol_slug, "result": result}
        except Exception as exc:
            payload = {"status": "failed", "protocol": protocol_slug, "error": str(exc)}
        duration = time.time() - started

        session = db or self._session_factory()
        should_close = db is None
        record = AnalysisHistory(
            user_id=user_id,
            protocol_name=protocol_slug,
            query_text=f"analyze:{protocol_slug}",
            query_type="protocol_analysis",
            result=payload,
            cached=False,
            duration=duration,
            created_at=utcnow(),
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        if should_close:
            session.close()
        return record.id, payload

    def _default_runner(self, protocol_slug: str) -> Dict[str, Any]:
        agent = self._agent_factory()
        trade_date = datetime.now(timezone.utc).date().isoformat()

        if hasattr(agent, "invoke"):
            output = agent.invoke(company_name=protocol_slug, trade_date=trade_date)
            serializable = self._to_json_safe(output)
            return {"analysis": serializable, "trade_date": trade_date}

        state, signal = agent.propagate(protocol_slug, trade_date)
        return {
            "analysis": self._to_json_safe(state),
            "signal": self._to_json_safe(signal),
            "trade_date": trade_date,
        }

    @staticmethod
    def _to_json_safe(value: Any) -> Any:
        try:
            json.dumps(value)
            return value
        except TypeError:
            return str(value)
