ALTER TABLE
    encode_config
ADD COLUMN
    minimum_file_size TEXT NOT NULL DEFAULT 'any';
