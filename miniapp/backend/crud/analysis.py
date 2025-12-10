from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from core.exceptions import NotFoundError
from models import AnalysisHistory
from schemas.analysis import AnalysisCreate
from utils.pagination import sanitize_pagination

ALLOWED_SORT_FIELDS = {
    "created_at": AnalysisHistory.created_at,
    "duration": AnalysisHistory.duration,
}


def _resolve_sort(sort: Optional[str]):
    if not sort:
        return AnalysisHistory.created_at, "desc"
    field, _, direction = sort.partition(":")
    column = ALLOWED_SORT_FIELDS.get(field.strip()) or AnalysisHistory.created_at
    direction = "desc" if direction.lower() not in {"asc", "desc"} else direction.lower()
    return column, direction


def create_analysis(db: Session, user_id: int, payload: AnalysisCreate) -> AnalysisHistory:
    record = AnalysisHistory(
        user_id=user_id,
        protocol_name=payload.protocol_name,
        query_text=payload.query_text,
        query_type=payload.query_type,
        result=payload.result,
        duration=payload.duration,
        cached=payload.cached,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_analysis_history(
    db: Session,
    user_id: int,
    page: int,
    limit: int,
    *,
    protocol_name: Optional[str] = None,
    query_type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    search: Optional[str] = None,
    sort: Optional[str] = None,
) -> Tuple[List[AnalysisHistory], int, int, int, int]:
    page, limit, offset = sanitize_pagination(page, limit)
    stmt = select(AnalysisHistory).where(AnalysisHistory.user_id == user_id)

    if protocol_name:
        stmt = stmt.where(AnalysisHistory.protocol_name.ilike(f"%{protocol_name}%"))
    if query_type:
        stmt = stmt.where(AnalysisHistory.query_type == query_type)
    if start_date:
        stmt = stmt.where(AnalysisHistory.created_at >= start_date)
    if end_date:
        stmt = stmt.where(AnalysisHistory.created_at <= end_date)
    if search:
        like_value = f"%{search}%"
        stmt = stmt.where(
            or_(
                AnalysisHistory.protocol_name.ilike(like_value),
                AnalysisHistory.query_text.ilike(like_value),
            )
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    sort_column, direction = _resolve_sort(sort)
    order_clause = sort_column.desc() if direction == "desc" else sort_column.asc()
    stmt = stmt.order_by(order_clause).limit(limit).offset(offset)
    items = db.execute(stmt).scalars().all()

    return items, total, page, limit, offset


def get_analysis(db: Session, user_id: int, analysis_id: int) -> AnalysisHistory:
    stmt = (
        select(AnalysisHistory)
        .where(AnalysisHistory.id == analysis_id)
        .where(AnalysisHistory.user_id == user_id)
    )
    record = db.execute(stmt).scalar_one_or_none()
    if not record:
        raise NotFoundError("Analysis", analysis_id)
    return record


def delete_analysis(db: Session, user_id: int, analysis_id: int) -> None:
    record = get_analysis(db, user_id, analysis_id)
    db.delete(record)
    db.commit()
