CREATE TABLE temp (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    enabled BOOLEAN NOT NULL DEFAULT '0',
    quality_preset TEXT NOT NULL DEFAULT 'moderate',
    speed_preset TEXT NOT NULL DEFAULT 'medium',
    maximum_encodes INTEGER NOT NULL DEFAULT 2,
    timed_encoding BOOLEAN NOT NULL DEFAULT '0',
    hour_start INTEGER NOT NULL DEFAULT 3,
    hour_end INTEGER NOT NULL DEFAULT 6,
    CHECK (
        hour_start >= 0 AND
        hour_end <= 23 AND
        hour_end > hour_start
    )
);

INSERT INTO temp (
    id,
    enabled,
    quality_preset,
    speed_preset,
    maximum_encodes,
    timed_encoding,
    hour_start,
    hour_end
) SELECT
    id,
    enabled,
    quality_preset,
    speed_preset,
    maximum_encodes,
    timed_encoding,
    hour_start,
    hour_end
FROM encode_config;

DROP TABLE encode_config;

ALTER TABLE temp RENAME TO encode_config;
