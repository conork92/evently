from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from supabase import Client

from app import crud, schemas
from app.supabase_client import get_supabase
from app.importers import import_from_source
from app.services.event_link import add_event_by_url
from app.services.map_link import resolve_google_maps_to_lat_lng


class MapUrlBody(BaseModel):
    map_url: str

router = APIRouter(prefix="/api/events", tags=["events"])


def _require_supabase() -> Client:
    client = get_supabase()
    if not client:
        raise HTTPException(status_code=503, detail="Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY.")
    return client


@router.post("/", response_model=schemas.EventRead)
def create_event(event: schemas.EventCreate, supabase: Client = Depends(_require_supabase)):
    data = event.model_dump()
    row = crud.create_event(supabase, data)
    return schemas.EventRead.model_validate(row)


@router.post("/add-by-url", response_model=list[schemas.EventRead])
def add_by_url(
    body: dict,
    supabase: Client = Depends(_require_supabase),
):
    """Add event(s) by pasting a link. Supports Songkick and See Tickets event URLs (page is scraped)."""
    url = (body.get("url") or "").strip()
    events, err = add_event_by_url(url)
    if err:
        raise HTTPException(status_code=400, detail=err)
    created = []
    for data in events:
        row = crud.create_event(supabase, data)
        created.append(schemas.EventRead.model_validate(row))
    return created


@router.post("/import/{source}", response_model=list[schemas.EventRead])
def import_events(source: str, payload: dict | list, supabase: Client = Depends(_require_supabase)):
    """Import events from Dice, Songkick, Timeout or Chortle. POST JSON in that provider's format."""
    try:
        normalized = import_from_source(source, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    created = []
    for data in normalized:
        row = crud.create_event(supabase, data)
        created.append(schemas.EventRead.model_validate(row))
    return created


@router.get("/this-week", response_model=list[schemas.EventRead])
def this_week(
    category: Optional[str] = Query(None, description="Filter by category"),
    area: Optional[str] = Query(None, description="Filter by area"),
    supabase: Client = Depends(_require_supabase),
):
    rows = crud.events_this_week(supabase, category=category, area=area)
    return [schemas.EventRead.model_validate(r) for r in rows]


@router.get("/this-month", response_model=list[schemas.EventRead])
def this_month(
    category: Optional[str] = Query(None, description="Filter by category"),
    area: Optional[str] = Query(None, description="Filter by area"),
    supabase: Client = Depends(_require_supabase),
):
    rows = crud.events_this_month(supabase, category=category, area=area)
    return [schemas.EventRead.model_validate(r) for r in rows]


@router.get("/map", response_model=list[schemas.EventMapPoint])
def map_points(
    category: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    supabase: Client = Depends(_require_supabase),
):
    rows = crud.events_for_map(supabase, category=category, area=area, from_date=from_date, to_date=to_date)
    return [schemas.EventMapPoint.model_validate(r) for r in rows]


@router.get("/categories", response_model=list[str])
def categories(supabase: Client = Depends(_require_supabase)):
    return crud.list_categories(supabase)


@router.get("/areas", response_model=list[str])
def areas(supabase: Client = Depends(_require_supabase)):
    return crud.list_areas(supabase)


@router.get("/", response_model=list[schemas.EventRead])
def list_events(
    category: Optional[str] = Query(None),
    area: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    from_date: Optional[datetime] = Query(None),
    to_date: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    supabase: Client = Depends(_require_supabase),
):
    rows = crud.get_events(
        supabase,
        category=category,
        area=area,
        source=source,
        from_date=from_date,
        to_date=to_date,
        skip=skip,
        limit=limit,
    )
    return [schemas.EventRead.model_validate(r) for r in rows]


@router.get("/{event_id}", response_model=schemas.EventRead)
def get_event(event_id: int, supabase: Client = Depends(_require_supabase)):
    row = crud.get_event(supabase, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    return schemas.EventRead.model_validate(row)


@router.patch("/{event_id}/location-from-map", response_model=schemas.EventRead)
def set_event_location_from_map(
    event_id: int,
    body: MapUrlBody,
    supabase: Client = Depends(_require_supabase),
):
    """Set an event's lat/lng from a Google Maps link (maps.app.goo.gl or goo.gl/maps). Event will then show on the map."""
    row = crud.get_event(supabase, event_id)
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    coords = resolve_google_maps_to_lat_lng(body.map_url.strip())
    if not coords:
        raise HTTPException(
            status_code=400,
            detail="Could not get coordinates from that link. Use a Google Maps link (e.g. maps.app.goo.gl or google.com/maps).",
        )
    lat, lng = coords
    updated = crud.update_event(supabase, event_id, schemas.EventUpdate(lat=lat, lng=lng))
    return schemas.EventRead.model_validate(updated)


@router.patch("/{event_id}", response_model=schemas.EventRead)
def update_event(event_id: int, data: schemas.EventUpdate, supabase: Client = Depends(_require_supabase)):
    row = crud.update_event(supabase, event_id, data)
    if not row:
        raise HTTPException(status_code=404, detail="Event not found")
    return schemas.EventRead.model_validate(row)


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: int, supabase: Client = Depends(_require_supabase)):
    if not crud.delete_event(supabase, event_id):
        raise HTTPException(status_code=404, detail="Event not found")
