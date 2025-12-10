from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.responses import success_response
from crud.watchlist import (
    batch_update_watchlist_active,
    create_watchlist,
    delete_watchlist,
    list_watchlist,
    update_watchlist,
)
from deps import get_current_user, get_db
from models import User
from schemas.watchlist import Watchlist as WatchlistSchema
from schemas.watchlist import WatchlistCreate, WatchlistUpdate

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])


class WatchlistBatchUpdateRequest(BaseModel):
    ids: List[int]
    is_active: bool


@router.get("")
def get_watchlist(
    active: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = list_watchlist(db, current_user.id, is_active=active)
    return success_response([WatchlistSchema.model_validate(item) for item in entries])


@router.post("")
def create_watchlist_item(
    payload: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = create_watchlist(
        db,
        current_user.id,
        payload.protocol_name,
        payload.condition_type,
        payload.threshold,
        is_active=payload.is_active,
        alert_message=payload.alert_message,
    )
    return success_response(WatchlistSchema.model_validate(entry))


@router.patch("/batch")
def batch_update_watchlist(
    payload: WatchlistBatchUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated, missing = batch_update_watchlist_active(
        db, current_user.id, payload.ids, payload.is_active
    )
    return success_response({"updated": updated, "missing": missing})


@router.patch("/{watchlist_id}")
def update_watchlist_item(
    watchlist_id: int,
    payload: WatchlistUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entry = update_watchlist(
        db,
        current_user.id,
        watchlist_id,
        condition_type=payload.condition_type,
        threshold=payload.threshold,
        is_active=payload.is_active,
        alert_message=payload.alert_message,
    )
    return success_response(WatchlistSchema.model_validate(entry))


@router.delete("/{watchlist_id}")
def delete_watchlist_item(
    watchlist_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    delete_watchlist(db, current_user.id, watchlist_id)
    return success_response({"deleted": True, "id": watchlist_id})
