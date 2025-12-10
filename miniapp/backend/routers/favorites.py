from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.responses import success_response
from crud.favorite import (
    add_favorite,
    batch_delete_favorites,
    delete_favorite,
    list_favorites,
)
from deps import get_current_user, get_db
from models import User
from schemas.favorite import Favorite as FavoriteSchema

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


class FavoriteCreateRequest(BaseModel):
    protocol_name: str
    protocol_type: Optional[str] = None


class FavoriteBatchDeleteRequest(BaseModel):
    ids: List[int]


@router.get("")
def get_favorites(
    chain: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorites = list_favorites(db, current_user.id, protocol_type=chain)
    return success_response([FavoriteSchema.model_validate(item) for item in favorites])


@router.post("")
def create_favorite(
    payload: FavoriteCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = add_favorite(
        db,
        current_user.id,
        payload.protocol_name,
        payload.protocol_type,
    )
    return success_response(FavoriteSchema.model_validate(favorite))


@router.delete("/batch")
def remove_favorites_batch(
    payload: FavoriteBatchDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    deleted, missing = batch_delete_favorites(db, current_user.id, payload.ids)
    return success_response({"deleted": deleted, "missing": missing})


@router.delete("/{favorite_id}")
def remove_favorite(
    favorite_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_favorite(db, current_user.id, favorite_id)
    return success_response({"deleted": True, "id": favorite_id})
