CREATE TABLE IF NOT EXISTS loadouts (
    player_id varchar(36) NOT NULL REFERENCES players(id),
    slot varchar(24) NOT NULL,
    item_id varchar(36) NOT NULL UNIQUE REFERENCES items(id),
    PRIMARY KEY (player_id, slot)
);
INSERT INTO schema_migrations(version) VALUES (3) ON CONFLICT DO NOTHING;
