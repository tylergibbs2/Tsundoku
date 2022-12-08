CREATE TABLE webhook_base_default_trigger (
    base INTEGER NOT NULL REFERENCES webhook_base(id) ON DELETE CASCADE,
    trigger show_state NOT NULL,
    PRIMARY KEY (base, trigger)
);
