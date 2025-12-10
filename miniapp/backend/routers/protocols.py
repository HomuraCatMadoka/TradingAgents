from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.responses import success_response
from deps import get_current_user, get_db
from models import User
from services.agent import AgentService
from services.defi_data import DeFiDataService

router = APIRouter(prefix="/api/protocols", tags=["protocols"])

# Service singletons; tests can monkeypatch these for isolation.
defi_service = DeFiDataService()
agent_service = AgentService()


@router.get("")
def list_protocols(
    search: Optional[str] = Query(default=None, alias="search"),
    chain: Optional[str] = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    protocols = defi_service.list_protocols(search=search, chain=chain, limit=limit)
    return success_response({"protocols": protocols, "count": len(protocols)})


@router.get("/{slug}")
def get_protocol_detail(slug: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    detail = defi_service.get_protocol_detail(slug)
    return success_response(detail)


@router.get("/{slug}/history")
def get_protocol_history(
    slug: str,
    period: Optional[str] = Query(default="30d"),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    days = DeFiDataService.parse_period(period)
    history = defi_service.get_protocol_history(slug, days)
    return success_response(history)


@router.get("/{slug}/market-data")
def get_protocol_market_data(slug: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    data = defi_service.get_market_data(slug)
    return success_response(data)


@router.get("/{slug}/pools")
def get_protocol_pools(
    slug: str,
    chain: Optional[str] = Query(default=None),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    pools = defi_service.get_protocol_pools(slug, chain=chain, limit=limit)
    return success_response(pools)


@router.get("/{slug}/pools/{pool_id}")
def get_pool_detail(slug: str, pool_id: str, current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    detail = defi_service.get_pool_detail(slug, pool_id)
    return success_response(detail)


@router.post("/{slug}/analyze")
def trigger_protocol_analysis(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    record_id, payload = agent_service.trigger_analysis(slug, current_user.id, db)
    return success_response({"record_id": record_id, "status": payload.get("status"), "protocol": slug})
