from datetime import datetime, timedelta
from typing import Optional

from supabase import Client

from app import schemas

TABLE = "evently_events"


def _serialize_event_date(d: datetime) -> str:
    return d.isoformat() if d else None


def create_event(supabase: Client, data: dict) -> dict:
    row = {**data}
    if "event_date" in row and isinstance(row["event_date"], datetime):
        row["event_date"] = _serialize_event_date(row["event_date"])
    r = supabase.table(TABLE).insert(row).execute()
    rows = (r.data or [])
    return rows[0] if rows else row


def get_event(supabase: Client, event_id: int) -> dict | None:
    r = supabase.table(TABLE).select("*").eq("id", event_id).execute()
    rows = r.data or []
    return rows[0] if rows else None


def get_events(
    supabase: Client,
    category: Optional[str] = None,
    area: Optional[str] = None,
    source: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[dict]:
    q = supabase.table(TABLE).select("*")
    if category:
        q = q.eq("category", category)
    if area:
        q = q.ilike("area", f"%{area}%")
    if source:
        q = q.eq("source", source)
    if from_date:
        q = q.gte("event_date", _serialize_event_date(from_date))
    if to_date:
        q = q.lte("event_date", _serialize_event_date(to_date))
    q = q.order("event_date").range(skip, skip + limit - 1)
    r = q.execute()
    return r.data or []


def events_this_week(
    supabase: Client,
    category: Optional[str] = None,
    area: Optional[str] = None,
) -> list[dict]:
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=7)
    return get_events(
        supabase, category=category, area=area, from_date=start, to_date=end, limit=500
    )


def events_this_month(
    supabase: Client,
    category: Optional[str] = None,
    area: Optional[str] = None,
) -> list[dict]:
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=31)
    return get_events(
        supabase, category=category, area=area, from_date=start, to_date=end, limit=500
    )


def events_for_map(
    supabase: Client,
    category: Optional[str] = None,
    area: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
) -> list[dict]:
    q = supabase.table(TABLE).select("id,title,event_date,venue_name,location,lat,lng,category,price_display,url")
    if category:
        q = q.eq("category", category)
    if area:
        q = q.ilike("area", f"%{area}%")
    if from_date:
        q = q.gte("event_date", _serialize_event_date(from_date))
    if to_date:
        q = q.lte("event_date", _serialize_event_date(to_date))
    q = q.order("event_date")
    r = q.execute()
    rows = r.data or []
    return [row for row in rows if row.get("lat") is not None and row.get("lng") is not None]


def list_categories(supabase: Client) -> list[str]:
    r = supabase.table(TABLE).select("category").not_.is_("category", "null").execute()
    rows = r.data or []
    cats = {row["category"] for row in rows if row.get("category")}
    return sorted(cats)


def list_areas(supabase: Client) -> list[str]:
    r = supabase.table(TABLE).select("area").not_.is_("area", "null").execute()
    rows = r.data or []
    areas_set = {row["area"] for row in rows if row.get("area")}
    return sorted(areas_set)


def update_event(supabase: Client, event_id: int, data: schemas.EventUpdate) -> dict | None:
    payload = data.model_dump(exclude_unset=True)
    if "event_date" in payload and isinstance(payload["event_date"], datetime):
        payload["event_date"] = _serialize_event_date(payload["event_date"])
    if not payload:
        return get_event(supabase, event_id)
    r = supabase.table(TABLE).update(payload).eq("id", event_id).execute()
    rows = r.data or []
    return rows[0] if rows else None


def delete_event(supabase: Client, event_id: int) -> bool:
    r = supabase.table(TABLE).delete().eq("id", event_id).execute()
    return bool(r.data and len(r.data) > 0)
