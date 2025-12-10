from typing import Iterable, List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import NotFoundError, ValidationError
from models import Watchlist


def create_watchlist(
    db: Session,
    user_id: int,
    protocol_name: str,
    condition_type: str,
    threshold: float,
    *,
    is_active: bool = True,
    alert_message: str | None = None,
) -> Watchlist:
    exists = (
        db.execute(
            select(Watchlist)
            .where(Watchlist.user_id == user_id)
            .where(Watchlist.protocol_name == protocol_name)
        )
        .scalar_one_or_none()
    )
    if exists:
        raise ValidationError("protocol_name", "Already watching protocol")

    entry = Watchlist(
        user_id=user_id,
        protocol_name=protocol_name,
        condition_type=condition_type,
        threshold=threshold,
        is_active=is_active,
        alert_message=alert_message,
        alert_conditions={"condition_type": condition_type, "threshold": threshold},
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_watchlist(
    db: Session, user_id: int, *, is_active: bool | None = None
) -> List[Watchlist]:
    stmt = select(Watchlist).where(Watchlist.user_id == user_id)
    if is_active is not None:
        stmt = stmt.where(Watchlist.is_active.is_(is_active))
    stmt = stmt.order_by(Watchlist.created_at.desc())
    return list(db.execute(stmt).scalars().all())


def update_watchlist(
    db: Session,
    user_id: int,
    watchlist_id: int,
    *,
    condition_type: str | None = None,
    threshold: float | None = None,
    is_active: bool | None = None,
    alert_message: str | None = None,
) -> Watchlist:
    entry = db.get(Watchlist, watchlist_id)
    if not entry or entry.user_id != user_id:
        raise NotFoundError("Watchlist", watchlist_id)

    if (
        condition_type is None
        and threshold is None
        and is_active is None
        and alert_message is None
    ):
        raise ValidationError("payload", "no fields provided")

    if condition_type is not None:
        entry.condition_type = condition_type
    if threshold is not None:
        entry.threshold = threshold
    if condition_type is not None or threshold is not None:
        entry.alert_conditions = {
            "condition_type": entry.condition_type,
            "threshold": entry.threshold,
        }
    if is_active is not None:
        entry.is_active = is_active
    if alert_message is not None:
        entry.alert_message = alert_message

    db.commit()
    db.refresh(entry)
    return entry


def delete_watchlist(db: Session, user_id: int, watchlist_id: int) -> None:
    entry = db.get(Watchlist, watchlist_id)
    if not entry or entry.user_id != user_id:
        raise NotFoundError("Watchlist", watchlist_id)
    db.delete(entry)
    db.commit()


def batch_update_watchlist_active(
    db: Session, user_id: int, watchlist_ids: Iterable[int], is_active: bool
) -> Tuple[int, int]:
    ids = list(watchlist_ids)
    if not ids:
        raise ValidationError("ids", "must provide at least one id")
    stmt = select(Watchlist).where(Watchlist.user_id == user_id).where(
        Watchlist.id.in_(ids)
    )
    entries = db.execute(stmt).scalars().all()
    for entry in entries:
        entry.is_active = is_active
    db.commit()
    updated = len(entries)
    missing = max(len(ids) - updated, 0)
    return updated, missing
