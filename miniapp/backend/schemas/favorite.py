from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class FavoriteBase(BaseModel):
    user_id: int
    protocol_name: str
    protocol_type: Optional[str] = None


class FavoriteCreate(FavoriteBase):
    pass


class Favorite(FavoriteBase):
    id: int
    added_at: datetime

    model_config = ConfigDict(from_attributes=True)
