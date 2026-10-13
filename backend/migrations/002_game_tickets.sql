-- Short-lived join credentials are hashes only. No FK to sessions intentionally:
-- logout deletes the session; consumption must then reject the surviving ticket.
CREATE TABLE IF NOT EXISTS game_tickets (
    ticket_hash varchar(64) PRIMARY KEY,
    session_hash varchar(64) NOT NULL,
    player_id varchar(36) NOT NULL REFERENCES players(id),
    server_id varchar(64) NOT NULL,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz
);
CREATE INDEX IF NOT EXISTS ix_game_tickets_player_id ON game_tickets(player_id);
INSERT INTO schema_migrations(version) VALUES (2) ON CONFLICT DO NOTHING;
