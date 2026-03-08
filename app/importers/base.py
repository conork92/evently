from datetime import datetime
from typing import Any

EventSource = str  # dice | songkick | timeout | chortle


def _parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        s = value.replace("Z", "+00:00").strip()
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M",
            "%d/%m/%Y",
        ):
            try:
                part = s[:26] if "%z" in fmt else s[:19]
                return datetime.strptime(part, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(s)
        except ValueError:
            pass
    return None


def normalize_event_dict(
    *,
    title: str,
    event_date: datetime | str,
    location: str,
    source: EventSource,
    area: str | None = None,
    venue_name: str | None = None,
    address: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    price_display: str | None = None,
    category: str | None = None,
    external_id: str | None = None,
    url: str | None = None,
    description: str | None = None,
) -> dict:
    dt = event_date if isinstance(event_date, datetime) else _parse_datetime(event_date)
    if not dt:
        raise ValueError(f"Cannot parse event_date: {event_date}")
    return {
        "title": title,
        "event_date": dt,
        "location": location,
        "area": area,
        "venue_name": venue_name,
        "address": address,
        "lat": lat,
        "lng": lng,
        "price_min": price_min,
        "price_max": price_max,
        "price_display": price_display,
        "category": category or _infer_category(source),
        "source": source,
        "external_id": str(external_id) if external_id is not None else None,
        "url": url,
        "description": description,
    }


def _infer_category(source: EventSource) -> str:
    return {"dice": "music", "songkick": "music", "timeout": "entertainment", "chortle": "comedy", "seetickets": "entertainment"}.get(
        source, "event"
    )
