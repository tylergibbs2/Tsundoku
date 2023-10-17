-- depends: 0034_libraries

CREATE TABLE temp (
    id INTEGER PRIMARY KEY,
    library_id INTEGER REFERENCES library(id) ON DELETE SET NULL,
    title TEXT NOT NULL,
    title_local TEXT,
    desired_format TEXT,
    season INTEGER NOT NULL,
    episode_offset INTEGER NOT NULL DEFAULT 0,
    watch BOOLEAN NOT NULL DEFAULT '1',
    post_process BOOLEAN NOT NULL DEFAULT '1',
    preferred_resolution TEXT,
    preferred_release_group TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO temp (
    id,
    library_id,
    title,
    desired_format,
    season,
    episode_offset,
    watch,
    post_process,
    preferred_resolution,
    preferred_release_group,
    created_at
) SELECT
    id,
    (SELECT id FROM library LIMIT 1),
    title,
    desired_format,
    season,
    episode_offset,
    watch,
    post_process,
    preferred_resolution,
    preferred_release_group,
    created_at
FROM shows;

DROP TABLE shows;

ALTER TABLE temp RENAME TO shows;
