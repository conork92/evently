from app.importers.base import normalize_event_dict, EventSource
from app.importers.songkick import songkick_to_events
from app.importers.dice import dice_to_events
from app.importers.timeout import timeout_to_events
from app.importers.chortle import chortle_to_events

IMPORTERS = {
    "songkick": songkick_to_events,
    "dice": dice_to_events,
    "timeout": timeout_to_events,
    "chortle": chortle_to_events,
}


def import_from_source(source: str, payload: dict | list) -> list[dict]:
    if source not in IMPORTERS:
        raise ValueError(f"Unknown source: {source}. Use one of {list(IMPORTERS.keys())}")
    return IMPORTERS[source](payload)
