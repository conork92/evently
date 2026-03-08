"""Parse Dice-style event JSON (single event or list of events)."""
from datetime import datetime

from app.importers.base import normalize_event_dict, _parse_datetime


def _one_dice_event(ev: dict) -> dict | None:
    title = ev.get("name") or ev.get("title", "Untitled")
    start = ev.get("start_date") or ev.get("date") or ev.get("start")
    if isinstance(start, dict):
        start = start.get("date") or start.get("datetime") or start.get("time")
    event_date = _parse_datetime(start)
    if not event_date:
        return None
    venue = ev.get("venue") or {}
    if isinstance(venue, str):
        venue = {"name": venue}
    venue_name = venue.get("name") or venue.get("display_name")
    location = ev.get("location") or venue.get("location") or venue.get("city") or "Unknown"
    if isinstance(location, dict):
        location = location.get("name") or location.get("city") or location.get("display_name") or "Unknown"
    area = ev.get("area") or (location.split(",")[0].strip() if location else None)
    lat = ev.get("lat") or venue.get("lat")
    lng = ev.get("lng") or venue.get("lng")
    geo = ev.get("geo") or venue.get("geo")
    if geo and isinstance(geo, dict):
        lat = lat or geo.get("lat")
        lng = lng or geo.get("lng")
    price = ev.get("price") or ev.get("price_min")
    price_max = ev.get("price_max")
    price_display = ev.get("price_display") or ev.get("formatted_price")
    if price is not None and not price_display:
        price_display = f"£{price}" if isinstance(price, (int, float)) else str(price)
    return normalize_event_dict(
        title=title,
        event_date=event_date,
        location=location,
        source="dice",
        area=area,
        venue_name=venue_name,
        address=venue.get("address") or ev.get("address"),
        lat=lat,
        lng=lng,
        price_min=float(price) if price is not None and isinstance(price, (int, float)) else None,
        price_max=float(price_max) if price_max is not None else None,
        price_display=price_display,
        category=ev.get("category") or "music",
        external_id=ev.get("id"),
        url=ev.get("url") or ev.get("link"),
        description=ev.get("description"),
    )


def dice_to_events(payload: dict | list) -> list[dict]:
    events = []
    if isinstance(payload, list):
        for ev in payload:
            out = _one_dice_event(ev)
            if out:
                events.append(out)
        return events
    # Single event or wrapper like { "data": [...] }
    if "data" in payload and isinstance(payload["data"], list):
        for ev in payload["data"]:
            out = _one_dice_event(ev)
            if out:
                events.append(out)
        return events
    out = _one_dice_event(payload)
    if out:
        events.append(out)
    return events
