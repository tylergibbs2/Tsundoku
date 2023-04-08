CREATE TABLE EntryState (
    Type TEXT PRIMARY KEY
);

INSERT INTO EntryState (Type) VALUES
    ('downloading'),
    ('downloaded'),
    ('renamed'),
    ('moved'),
    ('completed'),
    ('failed');

CREATE TABLE WebhookService (
    Type TEXT PRIMARY KEY
);

INSERT INTO WebhookService (Type) VALUES
    ('discord'),
    ('slack'),
    ('custom');

CREATE TABLE TorrentClient (
    Type TEXT PRIMARY KEY
);

INSERT INTO TorrentClient (Type) VALUES
    ('deluge'),
    ('transmission'),
    ('qbittorrent');

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    api_key uuid NOT NULL,
    readonly BOOLEAN NOT NULL DEFAULT '0'
);

CREATE TABLE seen_release (
    title TEXT NOT NULL,
    release_group TEXT NOT NULL,
    episode INTEGER NOT NULL,
    resolution TEXT NOT NULL,
    version TEXT NOT NULL DEFAULT "v0",
    torrent_destination TEXT NOT NULL,
    seen_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (title, release_group, episode, resolution)
);

CREATE TABLE shows (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    desired_format TEXT,
    desired_folder TEXT,
    season INTEGER NOT NULL,
    episode_offset INTEGER NOT NULL DEFAULT 0,
    watch BOOLEAN NOT NULL DEFAULT '1',
    post_process BOOLEAN NOT NULL DEFAULT '1',
    preferred_resolution TEXT,
    preferred_release_group TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE show_entry (
    id INTEGER PRIMARY KEY,
    show_id INTEGER NOT NULL REFERENCES shows(id) ON DELETE CASCADE,
    episode INTEGER NOT NULL,
    version TEXT NOT NULL DEFAULT "v0",
    current_state REFERENCES EntryState(Type) NOT NULL DEFAULT 'downloading',
    torrent_hash TEXT NOT NULL,
    file_path TEXT,
    created_manually BOOLEAN NOT NULL DEFAULT '0',
    last_update TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE encode (
    entry_id INTEGER PRIMARY KEY REFERENCES show_entry(id) ON DELETE CASCADE,
    initial_size INTEGER,
    final_size INTEGER,
    queued_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);

CREATE TABLE general_config (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    host TEXT NOT NULL DEFAULT 'localhost',
    port INTEGER NOT NULL DEFAULT 6439,
    update_do_check BOOLEAN NOT NULL DEFAULT '0',
    locale TEXT NOT NULL DEFAULT 'en',
    log_level TEXT NOT NULL DEFAULT 'info',
    default_desired_format TEXT NOT NULL DEFAULT '{n} - {s00e00}',
    default_desired_folder TEXT NOT NULL DEFAULT '{n}/Season {s00}',
    unwatch_when_finished BOOLEAN NOT NULL DEFAULT '0'
);

CREATE TABLE feeds_config (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    polling_interval INTEGER NOT NULL DEFAULT 900,
    complete_check_interval INTEGER NOT NULL DEFAULT 15,
    fuzzy_cutoff INTEGER NOT NULL DEFAULT 90,
    seed_ratio_limit REAL NOT NULL DEFAULT 0.0
);

CREATE TABLE torrent_config (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    client REFERENCES TorrentClient(Type) NOT NULL DEFAULT 'qbittorrent',
    host TEXT NOT NULL DEFAULT 'localhost',
    port INTEGER NOT NULL DEFAULT 8080,
    username TEXT,
    password TEXT,
    secure BOOLEAN NOT NULL DEFAULT '0'
);

CREATE TABLE encode_config (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    enabled BOOLEAN NOT NULL DEFAULT '0',
    encoder TEXT NOT NULL DEFAULT 'libx264',
    quality_preset TEXT NOT NULL DEFAULT 'moderate',
    speed_preset TEXT NOT NULL DEFAULT 'medium',
    maximum_encodes INTEGER NOT NULL DEFAULT 2,
    minimum_file_size TEXT NOT NULL DEFAULT 'any',
    timed_encoding BOOLEAN NOT NULL DEFAULT '0',
    hour_start INTEGER NOT NULL DEFAULT 3,
    hour_end INTEGER NOT NULL DEFAULT 6,
    CHECK (
        hour_start >= 0 AND
        hour_end <= 23 AND
        hour_end > hour_start
    )
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

CREATE TABLE webhook_base_default_trigger (
    base INTEGER NOT NULL REFERENCES webhook_base(id) ON DELETE CASCADE,
    trigger show_state NOT NULL,
    PRIMARY KEY (base, trigger)
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
