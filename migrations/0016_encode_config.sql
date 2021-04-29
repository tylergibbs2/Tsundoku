CREATE TABLE encode_config (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    enabled BOOLEAN NOT NULL DEFAULT '0',
    quality_preset TEXT NOT NULL DEFAULT 'moderate',
    speed_preset TEXT NOT NULL DEFAULT 'medium',
    maximum_encodes INTEGER NOT NULL DEFAULT 2,
    retry_on_fail BOOLEAN NOT NULL DEFAULT '1'
);
