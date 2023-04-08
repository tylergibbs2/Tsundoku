CREATE TABLE temp (
    entry_id INTEGER PRIMARY KEY REFERENCES show_entry(id) ON DELETE CASCADE,
    initial_size INTEGER,
    final_size INTEGER,
    queued_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    ended_at TIMESTAMP
);

INSERT INTO temp (
    entry_id,
    initial_size,
    final_size,
    started_at,
    ended_at
) SELECT * FROM encode;

UPDATE
    temp
SET
    queued_at = started_at;

UPDATE
    temp
SET
    started_at = NULL
WHERE
    ended_at IS NULL;

DROP TABLE encode;

ALTER TABLE temp RENAME TO encode;
