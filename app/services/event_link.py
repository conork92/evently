import re
from datetime import datetime
import json
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.importers.songkick import songkick_to_events
from app.importers.base import normalize_event_dict

SONGKICK_EVENT_URL = re.compile(r"^https?://(?:www\.)?songkick\.com/concerts/(\d+)", re.I)
SEETICKETS_EVENT_URL = re.compile(r"^https?://(?:www\.)?seetickets\.com/event/", re.I)

# Match "Wednesday 08 April 2026" or "08 April 2026" or "08 Apr 2026"
SONGKICK_DATE = re.compile(
    r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)day\s+(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})",
    re.I,
)
SONGKICK_DATE_SHORT = re.compile(
    r"(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{4})",
    re.I,
)
MONTHS = {
    "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
    "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "oct": 10, "october": 10,
    "nov": 11, "november": 11, "dec": 12, "december": 12,
}
PRICE_RE = re.compile(r"£\s*[\d.]+", re.I)


def _parse_songkick_date(text: str, default_hour: int = 19, default_minute: int = 0) -> datetime | None:
    """Parse date from Songkick page text. Returns naive UTC-like datetime."""
    if not text:
        return None
    m = SONGKICK_DATE.search(text) or SONGKICK_DATE_SHORT.search(text)
    if not m:
        return None
    day = int(m.group(1))
    month_name = m.group(2).lower()[:3]
    month = MONTHS.get(month_name) or MONTHS.get(m.group(2).lower())
    if not month:
        return None
    year = int(m.group(3))
    # Doors open: 19:00
    hour, minute = default_hour, default_minute
    doors = re.search(r"[Dd]oors\s+open[:\s]+(\d{1,2})[:\s]*(\d{2})?", text)
    if doors:
        hour = int(doors.group(1))
        minute = int(doors.group(2) or 0)
    try:
        return datetime(year, month, day, hour, minute)
    except ValueError:
        return None


def scrape_songkick_page(url: str) -> dict | None:
    """
    Fetch a Songkick concert page and parse event details. No API key needed.
    Returns a single normalized event dict or None.
    """
    try:
        with httpx.Client(
            timeout=12.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"},
        ) as client:
            r = client.get(url)
            r.raise_for_status()
            html = r.text
    except Exception:
        return None

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    # Title: usually in h1
    title = "Untitled"
    h1 = soup.find("h1")
    if h1:
        title = (h1.get_text() or "").strip() or title
    if title == "Untitled":
        # Fallback: page title often "Artist Venue, Date – Songkick"
        title_tag = soup.find("title")
        if title_tag and "–" in (title_tag.get_text() or ""):
            title = title_tag.get_text().split("–")[0].strip().rstrip(",")

    # Date
    event_date = _parse_songkick_date(text)
    if not event_date:
        return None

    # Venue and location: look for venue link and metro link, or "Venue" section
    venue_name = None
    location = "Unknown"
    address = None
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        link_text = (a.get_text() or "").strip()
        if "/venues/" in href and link_text and not venue_name:
            venue_name = link_text
        if "/metro-areas/" in href and link_text:
            location = link_text
    # Address often after "Venue" heading
    for node in soup.find_all(["p", "div", "span"]):
        t = (node.get_text() or "").strip()
        if t and len(t) > 20 and re.match(r"^\d+[A-Za-z]?\s", t) and ("Road" in t or "Street" in t or "London" in t or "UK" in t):
            address = t
            break
    if not venue_name and location != "Unknown":
        venue_name = location.split(",")[0].strip() if "," in location else location

    # Price: "From £6.74" or "£6.74"
    price_display = None
    pm = PRICE_RE.search(text)
    if pm:
        price_display = pm.group(0).strip()

    # External ID from URL
    event_id = extract_songkick_event_id(url)

    return normalize_event_dict(
        title=title,
        event_date=event_date,
        location=location,
        source="songkick",
        area=location.split(",")[0].strip() if location else None,
        venue_name=venue_name,
        address=address,
        price_display=price_display,
        category="music",
        external_id=event_id,
        url=url,
    )


def _parse_iso_datetime(s: str) -> datetime | None:
    """Parse ISO 8601 datetime (e.g. from schema.org startDate)."""
    if not s or not isinstance(s, str):
        return None
    s = s.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s[:26].rstrip(":"))
    except ValueError:
        pass
    try:
        return datetime.fromisoformat(s[:19])
    except ValueError:
        pass
    return None


def _default_headers() -> dict:
    """Browser-like headers to reduce 403 from ticketing sites."""
    return {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.9",
    }


def scrape_seetickets_page(url: str) -> dict | None:
    """
    Fetch a See Tickets event page and parse event details (JSON-LD schema.org or HTML).
    Returns a single normalized event dict or None.
    """
    # Try without query string first (some sites block ?aff= etc.)
    base_url = url.split("?")[0] if "?" in url else url
    try:
        with httpx.Client(
            timeout=12.0,
            follow_redirects=True,
            headers=_default_headers(),
        ) as client:
            r = client.get(base_url)
            r.raise_for_status()
            html = r.text
    except Exception:
        return None

    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator=" ", strip=True)

    # 1) Prefer JSON-LD schema.org Event
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        try:
            if isinstance(data, dict) and data.get("@type") == "Event":
                name = (data.get("name") or "").strip() or None
                start = _parse_iso_datetime(data.get("startDate") or "")
                loc = data.get("location")
                location_name = "Unknown"
                address = None
                if isinstance(loc, dict):
                    location_name = loc.get("name") or location_name
                    addr = loc.get("address")
                    if isinstance(addr, dict):
                        address = addr.get("streetAddress")
                        loc_part = addr.get("addressLocality") or addr.get("streetAddress")
                        if loc_part:
                            location_name = loc_part
                            if addr.get("addressRegion"):
                                location_name += ", " + str(addr.get("addressRegion"))
                            country = addr.get("addressCountry")
                            if country:
                                location_name += ", " + (country.get("name") if isinstance(country, dict) else str(country))
                elif isinstance(loc, str):
                    location_name = loc
                price_display = None
                offers = data.get("offers")
                if isinstance(offers, dict) and offers.get("price") is not None:
                    price_display = "£" + str(offers["price"]) if not str(offers.get("price", "")).startswith("£") else str(offers["price"])
                elif isinstance(offers, list) and offers:
                    o = offers[0]
                    if isinstance(o, dict) and o.get("price") is not None:
                        price_display = "£" + str(o["price"]) if not str(o.get("price", "")).startswith("£") else str(o["price"])
                if name and start:
                    return normalize_event_dict(
                        title=name,
                        event_date=start,
                        location=location_name,
                        source="seetickets",
                        area=location_name.split(",")[0].strip() if location_name else None,
                        venue_name=location_name if location_name != "Unknown" else None,
                        address=address,
                        price_display=price_display,
                        category="entertainment",
                        external_id=urlparse(base_url).path.rstrip("/").split("/")[-1] if base_url else None,
                        url=url,
                    )
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") == "Event":
                        name = (item.get("name") or "").strip() or None
                        start = _parse_iso_datetime(item.get("startDate") or "")
                        if name and start:
                            loc = item.get("location")
                            location_name = "Unknown"
                            if isinstance(loc, dict):
                                location_name = loc.get("name") or (loc.get("address", {}).get("addressLocality") if isinstance(loc.get("address"), dict) else "Unknown") or "Unknown"
                            elif isinstance(loc, str):
                                location_name = loc
                            return normalize_event_dict(
                                title=name,
                                event_date=start,
                                location=location_name,
                                source="seetickets",
                                area=location_name.split(",")[0].strip() if location_name else None,
                                venue_name=location_name if location_name != "Unknown" else None,
                                price_display=None,
                                category="entertainment",
                                url=url,
                            )
                        break
        except (KeyError, TypeError, ValueError):
            continue

    # 2) Fallback: og:title, meta, h1 and date regex
    title = "Untitled"
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        title = og_title["content"].strip()
    if title == "Untitled":
        h1 = soup.find("h1")
        if h1:
            title = (h1.get_text() or "").strip() or title
    if title == "Untitled" and soup.find("title"):
        title = (soup.find("title").get_text() or "").strip().split("|")[0].strip().split("–")[0].strip().rstrip(",")
    iso_match = re.search(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", text)
    event_date = _parse_songkick_date(text) or (_parse_iso_datetime(iso_match.group(0) + ":00") if iso_match else None)
    if not event_date:
        return None
    venue_name = None
    location = "Unknown"
    for a in soup.find_all("a", href=True):
        t = (a.get_text() or "").strip()
        if t and len(t) > 2 and ("theatre" in t.lower() or "empire" in t.lower() or "hall" in t.lower() or "arena" in t.lower() or "academy" in t.lower()):
            venue_name = t
            break
    if not venue_name:
        venue_name = location
    price_display = None
    pm = PRICE_RE.search(text)
    if pm:
        price_display = pm.group(0).strip()
    return normalize_event_dict(
        title=title,
        event_date=event_date,
        location=location,
        source="seetickets",
        area=location.split(",")[0].strip() if location != "Unknown" else None,
        venue_name=venue_name,
        price_display=price_display,
        category="entertainment",
        url=url,
    )


def extract_songkick_event_id(url: str) -> str | None:
    """Extract Songkick event ID from URL e.g. https://www.songkick.com/concerts/43036093-bby-at-grow."""
    u = url.strip()
    if not u:
        return None
    m = SONGKICK_EVENT_URL.match(u)
    return m.group(1) if m else None


def fetch_songkick_event(event_id: str) -> dict | None:
    """Fetch a single event from Songkick API. Returns API response dict or None."""
    key = settings.songkick_api_key
    if not key:
        return None
    api_url = f"https://api.songkick.com/api/3.0/events/{event_id}.json?apikey={key}"
    try:
        with httpx.Client(timeout=10.0) as client:
            r = client.get(api_url)
            r.raise_for_status()
            return r.json()
    except Exception:
        return None


def add_event_by_url(url: str) -> tuple[list[dict], str | None]:
    """
    Add event(s) from a supported URL. Returns (list of normalized event dicts, error message).
    Songkick: scrapes the page (no API key needed). Falls back to API if SONGKICK_API_KEY is set and scrape fails.
    """
    u = (url or "").strip()
    if not u:
        return [], "No URL provided"
    parsed = urlparse(u)
    if not parsed.scheme or not parsed.netloc:
        return [], "Invalid URL"
    host = (parsed.netloc or "").lower()
    if "songkick.com" in host and "/concerts/" in u:
        # Prefer scraping (no API key required)
        event = scrape_songkick_page(u)
        if event:
            return [event], None
        # Fallback to API if key is set
        event_id = extract_songkick_event_id(u)
        if event_id and settings.songkick_api_key:
            raw = fetch_songkick_event(event_id)
            if raw:
                events = songkick_to_events(raw)
                if events:
                    return events, None
        return [], "Could not get event details from that page. The link may be invalid or the page format may have changed."
    if "seetickets.com" in host and "/event/" in u:
        event = scrape_seetickets_page(u)
        if event:
            return [event], None
        return [], "Could not get event details from that See Tickets page. The site may be blocking requests or the page format may have changed."
    return [], "Unsupported link. Try a Songkick or See Tickets event URL."
