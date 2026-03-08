"""Parse Timeout-style event JSON (single event or list)."""
from app.importers.base import normalize_event_dict, _parse_datetime


def _one_timeout_event(ev: dict) -> dict | None:
    title = ev.get("title") or ev.get("name", "Untitled")
    start = ev.get("start_date") or ev.get("date") or ev.get("event_date") or ev.get("start")
    if isinstance(start, dict):
        start = start.get("date") or start.get("datetime")
    event_date = _parse_datetime(start)
    if not event_date:
        return None
    location = ev.get("location") or ev.get("city") or ev.get("area") or "Unknown"
    if isinstance(location, dict):
        location = location.get("name") or location.get("city") or location.get("displayName") or "Unknown"
    venue = ev.get("venue") or {}
    if isinstance(venue, str):
        venue = {"name": venue}
    venue_name = venue.get("name") or venue.get("displayName") or ev.get("venue_name")
    area = ev.get("area") or ev.get("region") or (location.split(",")[0].strip() if location else None)
    lat = ev.get("lat") or ev.get("latitude")
    lng = ev.get("lng") or ev.get("longitude")
    if not lat and venue:
        lat = venue.get("lat") or venue.get("latitude")
    if not lng and venue:
        lng = venue.get("lng") or venue.get("longitude")
    price = ev.get("price") or ev.get("price_from")
    price_display = ev.get("price_display") or ev.get("price_text")
    if price is not None and not price_display:
        price_display = f"£{price}" if isinstance(price, (int, float)) else str(price)
    category = ev.get("category") or ev.get("type") or "entertainment"
    return normalize_event_dict(
        title=title,
        event_date=event_date,
        location=location,
        source="timeout",
        area=area,
        venue_name=venue_name,
        address=ev.get("address") or venue.get("address"),
        lat=lat,
        lng=lng,
        price_min=float(price) if price is not None and isinstance(price, (int, float)) else None,
        price_max=float(ev.get("price_max")) if ev.get("price_max") is not None else None,
        price_display=price_display,
        category=category,
        external_id=str(ev.get("id")) if ev.get("id") is not None else None,
        url=ev.get("url") or ev.get("link"),
        description=ev.get("description"),
    )


def timeout_to_events(payload: dict | list) -> list[dict]:
    events = []
    if isinstance(payload, list):
        for ev in payload:
            out = _one_timeout_event(ev)
            if out:
                events.append(out)
        return events
    if "events" in payload and isinstance(payload["events"], list):
        for ev in payload["events"]:
            out = _one_timeout_event(ev)
            if out:
                events.append(out)
        return events
    out = _one_timeout_event(payload)
    if out:
        events.append(out)
    return events
