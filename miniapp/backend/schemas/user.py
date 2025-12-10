from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    settings: dict = Field(default_factory=dict)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    settings: Optional[dict] = None
    last_active: Optional[datetime] = None


class User(UserBase):
    id: int
    created_at: datetime
    last_active: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
