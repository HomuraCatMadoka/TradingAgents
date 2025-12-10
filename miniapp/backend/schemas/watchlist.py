from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class WatchlistBase(BaseModel):
    protocol_name: str
    condition_type: str
    threshold: float
    is_active: bool = True
    alert_message: Optional[str] = None


class WatchlistCreate(WatchlistBase):
    pass


class WatchlistUpdate(BaseModel):
    condition_type: Optional[str] = None
    threshold: Optional[float] = None
    is_active: Optional[bool] = None
    alert_message: Optional[str] = None


class Watchlist(WatchlistBase):
    id: int
    user_id: int
    last_notified: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
