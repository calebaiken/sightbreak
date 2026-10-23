SELECT jsonb_build_object(
 'database', current_database(), 'role', current_user, 'sql_clock', clock_timestamp()::text,
 'postmaster_started', pg_postmaster_start_time()::text,
 'system_identifier', (SELECT system_identifier::text FROM pg_control_system()),
 'schema_versions', (SELECT jsonb_agg(version ORDER BY version) FROM schema_migrations),
 'business', jsonb_build_object(
  'players', (SELECT coalesce(jsonb_agg(jsonb_build_object('id',id,'credits',credits,'xp',xp,'active',active) ORDER BY id),'[]'::jsonb) FROM players),
  'items', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]'::jsonb) FROM items t),
  'listings', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]'::jsonb) FROM listings t),
  'ledger', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]'::jsonb) FROM ledger t),
  'operations', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]'::jsonb) FROM operations t),
  'audit', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]'::jsonb) FROM audit t),
  'loadouts', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY player_id,slot),'[]'::jsonb) FROM loadouts t),
  'rewards', (SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY id),'[]'::jsonb) FROM rewards t),
  'game_ticket_count', (SELECT count(*) FROM game_tickets)
 ));
