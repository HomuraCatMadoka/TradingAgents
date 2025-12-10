from typing import Iterable, List, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from core.exceptions import NotFoundError, ValidationError
from models import Favorite


def add_favorite(
    db: Session, user_id: int, protocol_name: str, protocol_type: str | None
) -> Favorite:
    exists = (
        db.execute(
            select(Favorite)
            .where(Favorite.user_id == user_id)
            .where(Favorite.protocol_name == protocol_name)
        )
        .scalar_one_or_none()
    )
    if exists:
        raise ValidationError("protocol_name", "Already favorited")

    favorite = Favorite(
        user_id=user_id, protocol_name=protocol_name, protocol_type=protocol_type
    )
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def list_favorites(
    db: Session, user_id: int, *, protocol_type: str | None = None
) -> List[Favorite]:
    stmt = select(Favorite).where(Favorite.user_id == user_id)
    if protocol_type:
        stmt = stmt.where(Favorite.protocol_type == protocol_type)
    stmt = stmt.order_by(Favorite.added_at.desc())
    return list(db.execute(stmt).scalars().all())


def delete_favorite(db: Session, user_id: int, favorite_id: int) -> None:
    favorite = db.get(Favorite, favorite_id)
    if not favorite or favorite.user_id != user_id:
        raise NotFoundError("Favorite", favorite_id)
    db.delete(favorite)
    db.commit()


def batch_delete_favorites(
    db: Session, user_id: int, favorite_ids: Iterable[int]
) -> Tuple[int, int]:
    ids = list(favorite_ids)
    if not ids:
        raise ValidationError("ids", "must provide at least one id")
    stmt = select(Favorite).where(Favorite.user_id == user_id).where(
        Favorite.id.in_(ids)
    )
    found = db.execute(stmt).scalars().all()
    for item in found:
        db.delete(item)
    db.commit()
    deleted_count = len(found)
    missing_count = max(len(ids) - deleted_count, 0)
    return deleted_count, missing_count
