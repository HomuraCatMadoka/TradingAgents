from datetime import datetime
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    avatar_url: Optional[HttpUrl] = Field(default=None, max_length=512)
    bio: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    username: Optional[str] = None
    avatar_url: Optional[HttpUrl] = Field(default=None, max_length=512)
    bio: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None


class UserSettings(BaseModel):
    theme: Optional[Literal["light", "dark"]] = None
    language: Optional[str] = Field(default=None, min_length=2, max_length=10)
    notifications: Optional[Dict[str, bool]] = None

    @field_validator("notifications")
    @classmethod
    def validate_notifications(cls, value: Optional[Dict[str, Any]]) -> Optional[Dict[str, bool]]:
        if value is None:
            return None
        for key, val in value.items():
            if not isinstance(val, bool):
                raise ValueError(f"notifications.{key} must be a boolean")
        return value


class UserStats(BaseModel):
    analysis_count: int
    favorite_count: int
    watchlist_count: int
    last_analysis_at: Optional[datetime] = None


class User(UserBase):
    id: int
    created_at: datetime
    last_active: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
