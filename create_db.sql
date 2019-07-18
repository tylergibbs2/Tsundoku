CREATE TYPE show_state AS ENUM ('downloading', 'complete');

CREATE TABLE IF NOT EXISTS shows (
    id BIGSERIAL PRIMARY KEY,
    search_title TEXT NOT NULL,
    desired_format TEXT,
    desired_folder TEXT,
    season SMALLINT NOT NULL
);

CREATE TABLE IF NOT EXISTS show_entry (
    id BIGSERIAL PRIMARY KEY,
    show_id BIGSERIAL NOT NULL REFERENCES shows(id),
    episode SMALLINT NOT NULL,
    current_state show_state NOT NULL DEFAULT 'downloading',
    torrent_hash TEXT NOT NULL
);