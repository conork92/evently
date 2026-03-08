-- Set lat/lng for events so they show on the map.
-- Run in Supabase: SQL Editor -> New query -> paste -> Run.
--
-- Going forward: use the API to set location from a Google Maps link (no manual coords needed):
--   PATCH /api/events/{event_id}/location-from-map
--   Body: { "map_url": "https://maps.app.goo.gl/..." }
-- That resolves the link and sets lat/lng automatically.
--
-- bby at Grow (Grow Tottenham) - coords from https://maps.app.goo.gl/grx7eGkZi6ng7BPK8
UPDATE evently_events
SET lat = 51.5899546,
    lng = -0.0621544
WHERE title ILIKE '%bby%'
  AND (lat IS NULL OR lng IS NULL OR (lat = 0 AND lng = 0));

-- Lily Allen
UPDATE evently_events
SET lat = 51.5146,
    lng = -0.1405
WHERE title ILIKE '%lily allen%'
  AND (lat IS NULL OR lng IS NULL OR (lat = 0 AND lng = 0));
