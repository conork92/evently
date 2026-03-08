-- Run this in Supabase SQL Editor to create the evently_events table.
-- Project: SQL Editor → New query → paste → Run

CREATE TABLE IF NOT EXISTS evently_events (
    id              SERIAL PRIMARY KEY,
    title            VARCHAR(512) NOT NULL,
    event_date       TIMESTAMP NOT NULL,
    location         VARCHAR(512) NOT NULL,
    area             VARCHAR(256),
    venue_name       VARCHAR(256),
    address          TEXT,
    lat              DOUBLE PRECISION,
    lng              DOUBLE PRECISION,
    price_min        DOUBLE PRECISION,
    price_max        DOUBLE PRECISION,
    price_display    VARCHAR(64),
    category         VARCHAR(64),
    source           VARCHAR(32) NOT NULL,
    external_id      VARCHAR(128),
    url              TEXT,
    description      TEXT,
    created_at       TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);

CREATE INDEX IF NOT EXISTS ix_evently_events_title ON evently_events (title);
CREATE INDEX IF NOT EXISTS ix_evently_events_event_date ON evently_events (event_date);
CREATE INDEX IF NOT EXISTS ix_evently_events_area ON evently_events (area);
CREATE INDEX IF NOT EXISTS ix_evently_events_category ON evently_events (category);
CREATE INDEX IF NOT EXISTS ix_evently_events_source ON evently_events (source);
CREATE INDEX IF NOT EXISTS ix_evently_events_external_id ON evently_events (external_id);

-- Good reviews (stuff you liked)
CREATE TABLE IF NOT EXISTS evently_reviews (
    id         SERIAL PRIMARY KEY,
    title      VARCHAR(512) NOT NULL,
    body       TEXT NOT NULL,
    rating     SMALLINT CHECK (rating >= 1 AND rating <= 5),
    url        TEXT,
    event_id   INTEGER,
    created_at TIMESTAMP DEFAULT (NOW() AT TIME ZONE 'utc')
);
CREATE INDEX IF NOT EXISTS ix_evently_reviews_created_at ON evently_reviews (created_at DESC);
