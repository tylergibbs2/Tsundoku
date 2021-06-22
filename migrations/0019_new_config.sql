CREATE TABLE TorrentClient (
    Type TEXT PRIMARY KEY
);

INSERT INTO TorrentClient (Type) VALUES
    ('deluge'),
    ('qbittorrent');


CREATE TABLE general_config (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    host TEXT NOT NULL DEFAULT 'localhost',
    port INTEGER NOT NULL DEFAULT 6439,
    update_do_check BOOLEAN NOT NULL DEFAULT '0',
    locale TEXT NOT NULL DEFAULT 'en',
    log_level TEXT NOT NULL DEFAULT 'info'
);

CREATE TABLE feeds_config (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    polling_interval INTEGER NOT NULL DEFAULT 900,
    complete_check_interval INTEGER NOT NULL DEFAULT 15,
    fuzzy_cutoff INTEGER NOT NULL DEFAULT 90
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
