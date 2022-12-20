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
