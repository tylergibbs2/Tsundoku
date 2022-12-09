ALTER TABLE
    show_entry
ADD COLUMN
    version TEXT NOT NULL DEFAULT "v0";

ALTER TABLE
    show_entry
ADD COLUMN
    created_manually BOOLEAN NOT NULL DEFAULT '0';
