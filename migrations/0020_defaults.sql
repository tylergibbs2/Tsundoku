ALTER TABLE
    general_config
ADD COLUMN
    default_desired_format TEXT NOT NULL DEFAULT '{n} - {s00e00}';

ALTER TABLE
    general_config
ADD COLUMN
    default_desired_folder TEXT NOT NULL DEFAULT '{n}/Season {s00}';

ALTER TABLE
    general_config
ADD COLUMN
    unwatch_when_finished BOOLEAN NOT NULL DEFAULT '0';
