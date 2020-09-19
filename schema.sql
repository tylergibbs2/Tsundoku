CREATE TYPE show_state AS ENUM ('downloading', 'downloaded', 'renamed', 'moved', 'completed');
CREATE TYPE webhook_service AS ENUM ('discord', 'slack', 'custom');

CREATE TABLE IF NOT EXISTS users (
    id SMALLSERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS shows (
    id SMALLSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    desired_format TEXT,
    desired_folder TEXT,
    season SMALLINT NOT NULL,
    episode_offset SMALLINT NOT NULL DEFAULT 0,
    kitsu_id INT,
    cached_poster_url TEXT
);

CREATE TABLE IF NOT EXISTS show_entry (
    id SMALLSERIAL PRIMARY KEY,
    show_id SMALLINT NOT NULL REFERENCES shows(id) ON DELETE CASCADE,
    episode SMALLINT NOT NULL,
    current_state show_state NOT NULL DEFAULT 'downloading',
    torrent_hash TEXT NOT NULL,
    file_path TEXT
);

CREATE TABLE IF NOT EXISTS webhook (
    id SMALLSERIAL PRIMARY KEY,
    show_id SMALLINT REFERENCES shows(id) ON DELETE CASCADE,
    wh_service webhook_service,
    wh_url TEXT NOT NULL,
    content_fmt TEXT NOT NULL DEFAULT '[{name}], episode [{episode}] has been marked as [{state}]'
);

CREATE TABLE IF NOT EXISTS wh_trigger (
    wh_id SMALLINT REFERENCES webhook(id) ON DELETE CASCADE,
    trigger show_state,
    PRIMARY KEY (wh_id, trigger)
);