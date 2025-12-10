from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class AnalysisBase(BaseModel):
    user_id: int
    protocol_name: str
    query_text: Optional[str] = None
    query_type: Optional[str] = None
    result: dict = Field(default_factory=dict)
    duration: Optional[float] = None
    cached: bool = False


class AnalysisCreate(AnalysisBase):
    pass


class Analysis(AnalysisBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
