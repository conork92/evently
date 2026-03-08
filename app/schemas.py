from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EventBase(BaseModel):
    title: str
    event_date: datetime
    location: str
    area: Optional[str] = None
    venue_name: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_display: Optional[str] = None
    category: Optional[str] = None
    source: str = Field(..., pattern="^(dice|songkick|timeout|chortle|seetickets)$")
    external_id: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = None
    event_date: Optional[datetime] = None
    location: Optional[str] = None
    area: Optional[str] = None
    venue_name: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    price_min: Optional[float] = None
    price_max: Optional[float] = None
    price_display: Optional[str] = None
    category: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None


class EventRead(EventBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class EventMapPoint(BaseModel):
    id: int
    title: str
    event_date: datetime
    venue_name: Optional[str] = None
    location: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    category: Optional[str] = None
    price_display: Optional[str] = None
    url: Optional[str] = None

    model_config = {"from_attributes": True}
