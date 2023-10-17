CREATE TABLE temp (
    id INTEGER PRIMARY KEY CHECK (id = 0),
    host TEXT NOT NULL DEFAULT '0.0.0.0',
    port INTEGER NOT NULL DEFAULT 6439,
    update_do_check BOOLEAN NOT NULL DEFAULT '0',
    locale TEXT NOT NULL DEFAULT 'en',
    log_level TEXT NOT NULL DEFAULT 'info',
    default_desired_format TEXT NOT NULL DEFAULT '{n} - {s00e00}',
    unwatch_when_finished BOOLEAN NOT NULL DEFAULT '0',
    use_season_folder BOOLEAN NOT NULL DEFAULT '1'
);

INSERT INTO temp (
    id,
    host,
    port,
    update_do_check,
    locale,
    log_level,
    default_desired_format,
    unwatch_when_finished,
    use_season_folder
) SELECT
    id,
    host,
    port,
    update_do_check,
    locale,
    log_level,
    default_desired_format,
    unwatch_when_finished,
    use_season_folder
FROM general_config;

DROP TABLE general_config;

ALTER TABLE temp RENAME TO general_config;