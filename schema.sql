CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE FUNCTION now_utc() RETURNS TIMESTAMP AS $$
  SELECT NOW() AT TIME ZONE 'utc';
$$ LANGUAGE SQL;

CREATE TYPE show_state AS ENUM ('downloading', 'downloaded', 'renamed', 'moved', 'completed');
CREATE TYPE webhook_service AS ENUM ('discord', 'slack', 'custom');

CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT now_utc(),
    api_key uuid NOT NULL DEFAULT uuid_generate_v4()
);

CREATE TABLE shows (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    desired_format TEXT,
    desired_folder TEXT,
    season SMALLINT NOT NULL,
    episode_offset SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT now_utc()
);

CREATE TABLE show_entry (
    id SERIAL PRIMARY KEY,
    show_id INT NOT NULL REFERENCES shows(id) ON DELETE CASCADE,
    episode SMALLINT NOT NULL,
    current_state show_state NOT NULL DEFAULT 'downloading',
    torrent_hash TEXT NOT NULL,
    file_path TEXT,
    last_update TIMESTAMP NOT NULL DEFAULT now_utc()
);

CREATE TABLE kitsu_info (
    show_id INT PRIMARY KEY REFERENCES shows(id) ON DELETE CASCADE,
    kitsu_id INT,
    cached_poster_url TEXT,
    show_status TEXT,
    slug TEXT,
    last_updated TIMESTAMP
);

CREATE TABLE webhook_base (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    base_service webhook_service NOT NULL,
    base_url TEXT NOT NULL,
    content_fmt TEXT NOT NULL DEFAULT '{name}, episode {episode}, has been marked as {state}'
);

CREATE TABLE webhook (
    show_id INT REFERENCES shows(id) ON DELETE CASCADE,
    base INT REFERENCES webhook_base(id) ON DELETE CASCADE,
    PRIMARY KEY (show_id, base)
);

CREATE TABLE webhook_trigger (
    show_id INT NOT NULL,
    base INT NOT NULL,
    trigger show_state NOT NULL,
    PRIMARY KEY (show_id, base, trigger),
    FOREIGN KEY (show_id, base) REFERENCES webhook (show_id, base) ON DELETE CASCADE
);
