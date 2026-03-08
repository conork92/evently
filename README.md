# Evently

FastAPI app to store and view events from **Dice**, **Songkick**, **Timeout** and **Chortle**. Add events to a database, view what’s on this week, filter by category and area, and see events on a map.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Run

**Local (with Make):**
```bash
make install   # first time only
make start     # runs on port 8003
```

**Or without Make:**
```bash
uvicorn app.main:app --reload --port 8003
```

**Docker:**
```bash
make up        # build and start with Docker Compose
make down      # stop
make logs      # tail logs
```

Or: `docker compose up -d --build`. The app listens on port 8003. With Supabase, set `DATABASE_URL` in `.env`.

- **Web UI:** http://127.0.0.1:8003/  
- **Map:** http://127.0.0.1:8003/map  
- **API docs:** http://127.0.0.1:8003/docs  

## Adding events

### Manual (API)

```bash
curl -X POST http://127.0.0.1:8003/api/events/ \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Gig",
    "event_date": "2025-03-15T19:00:00",
    "location": "London",
    "area": "London",
    "venue_name": "The Forum",
    "lat": 51.535,
    "lng": -0.109,
    "price_display": "£25",
    "category": "music",
    "source": "dice",
    "url": "https://example.com/tickets"
  }'
```

### Import from a source

POST JSON in the provider’s format to have it normalized and stored:

- **Songkick** (API-style): `POST /api/events/import/songkick` with body like `{"resultsPage":{"results":{"event":{...}}}}` or an array of event objects.
- **Dice:** `POST /api/events/import/dice` with a single event object or list.
- **Timeout:** `POST /api/events/import/timeout` with event(s).
- **Chortle:** `POST /api/events/import/chortle` with event(s).

Example (Songkick-style single event):

```bash
curl -X POST http://127.0.0.1:8003/api/events/import/songkick \
  -H "Content-Type: application/json" \
  -d '{
    "displayName": "Artist at Venue (March 15, 2025)",
    "start": {"date": "2025-03-15", "datetime": "2025-03-15T19:00:00"},
    "location": {"city": "London, UK", "lat": 51.507, "lng": -0.128},
    "venue": {"displayName": "O2 Arena", "lat": 51.502, "lng": -0.003},
    "status": "ok"
  }'
```

The app will parse and store **date**, **location**, **area**, **venue**, **price** (when present), **category** and **source**. Events with `lat`/`lng` appear on the map.

## API overview

| Endpoint | Description |
|----------|-------------|
| `GET /api/events/this-week` | Events in the next 7 days (optional `category`, `area`) |
| `GET /api/events/map` | Events with coordinates for the map (optional filters) |
| `GET /api/events/` | List events (filter by `category`, `area`, `source`, `from_date`, `to_date`) |
| `GET /api/events/categories` | Distinct categories |
| `GET /api/events/areas` | Distinct areas |
| `POST /api/events/` | Create one event (body: full event schema) |
| `POST /api/events/import/{source}` | Import from `dice` / `songkick` / `timeout` / `chortle` |

## Auto-picking from Dice, Songkick, Timeout, Chortle

There are no public “push” APIs from these sites. To get events in automatically you can:

1. **Use their APIs** (e.g. Songkick) and periodically `POST` the response to `/api/events/import/songkick`.
2. **Browser extension or bookmarklet** that sends the current page’s event data to your `/api/events/import/{source}` endpoint.
3. **Scrapers** (e.g. Apify) that output JSON in a similar shape and you POST that to the matching importer.

The importers are built to accept **provider-shaped JSON** (e.g. Songkick’s `resultsPage.results.event`) and normalize it into Evently’s schema so it can be stored and shown on “this week” and the map.

## Database (Supabase)

Uses the **Supabase native client** (same as e.g. HighgateAvenue). Only two env vars (see `.env.example`):

- **SUPABASE_URL** – e.g. `https://your-project-ref.supabase.co`
- **SUPABASE_ANON_KEY** – anon key (Project Settings → API)

No region, no database password, no SQLAlchemy. Create the table once in the Supabase SQL Editor by running `supabase_schema.sql`.
