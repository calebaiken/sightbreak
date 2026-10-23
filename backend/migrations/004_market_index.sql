-- Active marketplace reads filter and order in SQL (CLAUDE_AUDIT_0.3 M-7/M-8).
CREATE INDEX IF NOT EXISTS ix_listings_active_price ON listings(price, id) WHERE state = 'active';
INSERT INTO schema_migrations(version) VALUES (4) ON CONFLICT DO NOTHING;
