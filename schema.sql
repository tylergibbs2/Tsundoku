CREATE TABLE EntryState (
    Type TEXT PRIMARY KEY
);

INSERT INTO EntryState (Type) VALUES
    ('downloading'),
    ('downloaded'),
    ('renamed'),
    ('moved'),
    ('completed');

CREATE TABLE WebhookService (
    Type TEXT PRIMARY KEY
);

INSERT INTO WebhookService (Type) VALUES
    ('discord'),
    ('slack'),
    ('custom');

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    api_key uuid NOT NULL
);

CREATE TABLE shows (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    desired_format TEXT,
    desired_folder TEXT,
    season INTEGER NOT NULL,
    episode_offset INTEGER NOT NULL DEFAULT 0,
    watch BOOLEAN NOT NULL DEFAULT '1',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE show_entry (
    id INTEGER PRIMARY KEY,
    show_id INTEGER NOT NULL REFERENCES shows(id) ON DELETE CASCADE,
    episode INTEGER NOT NULL,
    current_state REFERENCES EntryState(Type) NOT NULL DEFAULT 'downloading',
    torrent_hash TEXT NOT NULL,
    file_path TEXT,
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE encode (
    entry_id INTEGER PRIMARY KEY REFERENCES show_entry(id) ON DELETE CASCADE,
    initial_size INTEGER NOT NULL,
    final_size INTEGER,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE TABLE encode_config (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    enabled BOOLEAN NOT NULL DEFAULT '0',
    quality_preset TEXT NOT NULL DEFAULT 'moderate',
    speed_preset TEXT NOT NULL DEFAULT 'medium',
    maximum_encodes INTEGER NOT NULL DEFAULT 2,
    retry_on_fail BOOLEAN NOT NULL DEFAULT '1'
);

CREATE TABLE kitsu_info (
    show_id INTEGER PRIMARY KEY REFERENCES shows(id) ON DELETE CASCADE,
    kitsu_id INTEGER,
    cached_poster_url TEXT,
    show_status TEXT,
    slug TEXT,
    last_updated TIMESTAMP
);

CREATE TABLE webhook_base (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    base_service REFERENCES WebhookService(Type) NOT NULL,
    base_url TEXT NOT NULL,
    content_fmt TEXT NOT NULL DEFAULT '{name}, episode {episode}, has been marked as {state}'
);

CREATE TABLE webhook (
    show_id INTEGER REFERENCES shows(id) ON DELETE CASCADE,
    base INTEGER REFERENCES webhook_base(id) ON DELETE CASCADE,
    PRIMARY KEY (show_id, base)
);

CREATE TABLE webhook_trigger (
    show_id INTEGER NOT NULL,
    base INTEGER NOT NULL,
    trigger show_state NOT NULL,
    PRIMARY KEY (show_id, base, trigger),
    FOREIGN KEY (show_id, base) REFERENCES webhook (show_id, base) ON DELETE CASCADE
);
