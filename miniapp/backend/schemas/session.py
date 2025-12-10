from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
    user_id: int
    token: str
    expires_at: datetime


class SessionCreate(SessionBase):
    pass


class Session(SessionBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
