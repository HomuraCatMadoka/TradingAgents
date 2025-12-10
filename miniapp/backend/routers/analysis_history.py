from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from core.responses import success_response
from crud.analysis import delete_analysis, get_analysis, list_analysis_history
from deps import get_current_user, get_db
from models import User
from schemas.analysis import Analysis as AnalysisSchema
from utils.pagination import paginate

router = APIRouter(prefix="/api/analysis-history", tags=["analysis-history"])


@router.get("")
def list_history(
    page: int = Query(1, ge=0),
    limit: int = Query(20, ge=0),
    protocol: Optional[str] = None,
    query_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    sort: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items, total, safe_page, safe_limit, _offset = list_analysis_history(
        db,
        current_user.id,
        page,
        limit,
        protocol_name=protocol,
        query_type=query_type,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort=sort,
    )
    paginated = paginate(
        [AnalysisSchema.model_validate(item) for item in items],
        total,
        safe_page,
        safe_limit,
    )
    return success_response(paginated.model_dump())


@router.get("/{analysis_id}")
def get_history_item(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = get_analysis(db, current_user.id, analysis_id)
    return success_response(AnalysisSchema.model_validate(record))


@router.delete("/{analysis_id}")
def delete_history_item(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_analysis(db, current_user.id, analysis_id)
    return success_response({"message": "deleted"})
