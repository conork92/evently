"""
Resolve Google Maps short links (maps.app.goo.gl, goo.gl/maps) to lat/lng.
Used so events can be given a map link and we set lat/lng for the map view.
"""
import re
from typing import Tuple

import httpx

# Final Google Maps URLs use !3dLAT!4dLNG (e.g. !3d51.5899546!4d-0.0621544) or @lat,lng
RE_3D_4D = re.compile(r"!3d(-?\d+\.?\d*)\s*!4d(-?\d+\.?\d*)")
RE_AT_COORDS = re.compile(r"@(-?\d+\.?\d*),(-?\d+\.?\d*)")


def resolve_google_maps_to_lat_lng(url: str) -> Tuple[float, float] | None:
    """
    Follow redirects from a Google Maps short link and extract latitude/longitude
    from the final URL. Returns (lat, lng) or None if resolution failed.
    """
    u = (url or "").strip()
    if not u or "maps" not in u.lower() and "goo.gl" not in u.lower():
        return None
    try:
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            # HEAD may not get full redirect chain; use GET
            r = client.get(u)
            r.raise_for_status()
            final_url = str(r.url)
    except Exception:
        return None
    # Prefer !3d / !4d (exact place) over @ (viewport center)
    m = RE_3D_4D.search(final_url)
    if m:
        try:
            lat, lng = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
        except ValueError:
            pass
    m = RE_AT_COORDS.search(final_url)
    if m:
        try:
            lat, lng = float(m.group(1)), float(m.group(2))
            if -90 <= lat <= 90 and -180 <= lng <= 180:
                return (lat, lng)
        except ValueError:
            pass
    return None
