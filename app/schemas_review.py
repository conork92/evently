from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    body: str = Field(..., min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)
    url: Optional[str] = None
    event_id: Optional[int] = None


class ReviewUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=512)
    body: Optional[str] = Field(None, min_length=1)
    rating: Optional[int] = Field(None, ge=1, le=5)
    url: Optional[str] = None
    event_id: Optional[int] = None


class ReviewRead(BaseModel):
    id: int
    title: str
    body: str
    rating: Optional[int] = None
    url: Optional[str] = None
    event_id: Optional[int] = None
    created_at: datetime

    model_config = {"from_attributes": True}
