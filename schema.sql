CREATE TYPE show_state AS ENUM ('downloading', 'downloaded', 'renamed', 'moved', 'completed');
CREATE TYPE webhook_service AS ENUM ('discord', 'slack', 'custom');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE shows (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    desired_format TEXT,
    desired_folder TEXT,
    season SMALLINT NOT NULL,
    episode_offset SMALLINT NOT NULL DEFAULT 0
);

CREATE TABLE show_entry (
    id SERIAL PRIMARY KEY,
    show_id SMALLINT NOT NULL REFERENCES shows(id) ON DELETE CASCADE,
    episode SMALLINT NOT NULL,
    current_state show_state NOT NULL DEFAULT 'downloading',
    torrent_hash TEXT NOT NULL,
    file_path TEXT
);

CREATE TABLE kitsu_info (
    show_id SMALLINT PRIMARY KEY REFERENCES shows(id) ON DELETE CASCADE,
    kitsu_id INT,
    cached_poster_url TEXT,
    show_status TEXT,
    slug TEXT,
    last_updated TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE webhook_base (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    base_service webhook_service NOT NULL,
    base_url TEXT NOT NULL,
    content_fmt TEXT NOT NULL DEFAULT '{name}, episode {episode}, has been marked as {state}'
);

CREATE TABLE webhook (
    show_id SMALLINT REFERENCES shows(id) ON DELETE CASCADE,
    base SMALLINT REFERENCES webhook_base(id) ON DELETE CASCADE,
    PRIMARY KEY (show_id, base)
);

CREATE TABLE webhook_trigger (
    wh_id SMALLINT REFERENCES webhook(id) ON DELETE CASCADE,
    trigger show_state,
    PRIMARY KEY (wh_id, trigger)
);