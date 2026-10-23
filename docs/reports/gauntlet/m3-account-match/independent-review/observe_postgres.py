#!/usr/bin/env python3
"""Read only the generated local DB after the real result commit; retain no key."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time

import psycopg

run = Path(sys.argv[1]).resolve()
output = Path(sys.argv[2]).resolve()
deadline = time.monotonic() + 1500
diagnostics = []
while time.monotonic() < deadline:
    boundary = run / 'backend-committed-ack-held.json'
    if not boundary.exists():
        time.sleep(.1)
        continue
    try:
        receipt = json.loads(boundary.read_text())
        pid = next(p['pid'] for p in receipt['processes'] if p['name'] == 'api')
        entries = Path(f'/proc/{pid}/environ').read_bytes().split(b'\0')
        database_url = next(e.split(b'=', 1)[1].decode() for e in entries if e.startswith(b'DATABASE_URL='))
        assert '@127.0.0.1:' in database_url and database_url.endswith('/sightbreak_match_test')
        with psycopg.connect(database_url.replace('postgresql+psycopg:', 'postgresql:', 1)) as db:
            db.execute('SET TRANSACTION READ ONLY')
            queries = {
                'players': 'SELECT id,display_name,credits,xp FROM players ORDER BY id',
                'ledger': 'SELECT player_id,amount,balance_after,reason,reference FROM ledger ORDER BY player_id',
                'rewards': 'SELECT player_id,details FROM rewards ORDER BY player_id',
                'operations': "SELECT id,request_hash,response FROM operations WHERE id LIKE 'match:%' ORDER BY id",
                'consumed_tickets': 'SELECT player_id,server_id,consumed_at IS NOT NULL FROM game_tickets ORDER BY player_id',
            }
            tables = {name: [list(r) for r in db.execute(query)] for name, query in queries.items()}
        result = dict(status='observed', at_utc=datetime.now(timezone.utc).isoformat(),
                      method='Independent read-only PostgreSQL connection using generated local API configuration in memory; credential not retained',
                      tables=tables, prior_error_types=diagnostics)
        output.write_text(json.dumps(result, indent=2) + '\n')
        print('Independent PostgreSQL snapshot retained:', output, flush=True)
        break
    except Exception as error:
        name = type(error).__name__
        if not diagnostics or diagnostics[-1] != name:
            diagnostics.append(name)
        time.sleep(.05)
else:
    output.write_text(json.dumps(dict(status='not_observed', error_types=diagnostics), indent=2) + '\n')
    raise SystemExit('Independent PostgreSQL observation deadline expired')
