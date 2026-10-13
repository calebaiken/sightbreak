-- Applied by migrate.py after the initial SQLAlchemy schema.
CREATE OR REPLACE FUNCTION forbid_history_mutation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'history is append-only'; END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS ledger_append_only ON ledger;
CREATE TRIGGER ledger_append_only BEFORE UPDATE OR DELETE ON ledger
FOR EACH ROW EXECUTE FUNCTION forbid_history_mutation();
DROP TRIGGER IF EXISTS audit_append_only ON audit;
CREATE TRIGGER audit_append_only BEFORE UPDATE OR DELETE ON audit
FOR EACH ROW EXECUTE FUNCTION forbid_history_mutation();
CREATE UNIQUE INDEX IF NOT EXISTS one_active_listing_per_item ON listings(item_id) WHERE state = 'active';
CREATE TABLE IF NOT EXISTS schema_migrations (version integer PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now());
INSERT INTO schema_migrations(version) VALUES (1) ON CONFLICT DO NOTHING;
