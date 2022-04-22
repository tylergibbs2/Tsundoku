ALTER TABLE
    feeds_config
ADD COLUMN
    seed_ratio_limit REAL NOT NULL DEFAULT 0.0;
