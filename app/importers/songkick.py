"""Parse Songkick API-style JSON (resultsPage.results.event or array of events)."""
from datetime import datetime

from app.importers.base import normalize_event_dict


def _parse_start(obj: dict) -> datetime | None:
    start = obj.get("start")
    if not start:
        return None
    dt_str = start.get("datetime") or start.get("date")
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")[:19])
    except (ValueError, TypeError):
        return None


def _one_songkick_event(ev: dict) -> dict | None:
    if ev.get("status") and ev["status"] != "ok":
        return None
    start_dt = _parse_start(ev)
    if not start_dt:
        return None
    location = ev.get("location") or {}
    city = location.get("city", "")
    lat = location.get("lat")
    lng = location.get("lng")
    venue = ev.get("venue") or {}
    venue_name = venue.get("displayName")
    if not city and venue:
        metro = venue.get("metroArea") or {}
        city = metro.get("displayName", "") or city
    if venue.get("lat") is not None:
        lat = venue.get("lat")
    if venue.get("lng") is not None:
        lng = venue.get("lng")
    if not city:
        city = "Unknown"
    display = ev.get("displayName", "Untitled")
    return normalize_event_dict(
        title=display,
        event_date=start_dt,
        location=city,
        source="songkick",
        area=city.split(",")[0].strip() if city else None,
        venue_name=venue_name,
        lat=lat,
        lng=lng,
        external_id=ev.get("id"),
        url=ev.get("uri"),
        category="music",
    )


def songkick_to_events(payload: dict | list) -> list[dict]:
    events = []
    if isinstance(payload, list):
        for ev in payload:
            out = _one_songkick_event(ev)
            if out:
                events.append(out)
        return events
    # resultsPage.results.event (single) or resultsPage.results.events (list)
    page = payload.get("resultsPage", payload)
    results = page.get("results", {})
    ev_or_list = results.get("event") or results.get("events")
    if ev_or_list is None:
        return events
    if isinstance(ev_or_list, list):
        for ev in ev_or_list:
            out = _one_songkick_event(ev)
            if out:
                events.append(out)
    else:
        out = _one_songkick_event(ev_or_list)
        if out:
            events.append(out)
    return events
