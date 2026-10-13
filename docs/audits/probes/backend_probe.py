"""Read-only reproduction of backend audit findings against a disposable *_test DB."""
import os
import statistics
import time
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import text

import app as service
from app import app, engine, Base, transaction, mint
from models import Listing
from test_economy import player, item

assert engine.url.database.endswith('_test')
Base.metadata.create_all(engine)
with engine.begin() as db:
    for migration in sorted((Path(service.__file__).parent / 'migrations').glob('*.sql')):
        db.exec_driver_sql(migration.read_text())
    db.execute(text('TRUNCATE ' + ', '.join('"' + t + '"' for t in Base.metadata.tables) + ' CASCADE'))
client = TestClient(app, raise_server_exceptions=False)

# B-MARKET: filters run after LIMIT 500 in Python.
seller, hs = player()
with transaction() as db:
    for i in range(500):
        it = mint(db, seller, 'obsidian_common')
        listing = Listing(item_id=it.id, seller_id=seller, price=10)
        db.add(listing); db.flush(); it.reservation = 'market:' + listing.id
    mythic = mint(db, seller, 'obsidian_mythic')
    listing = Listing(item_id=mythic.id, seller_id=seller, price=5000)
    db.add(listing); db.flush(); mythic.reservation = 'market:' + listing.id
start = time.perf_counter()
filtered = client.get('/market', params={'rarity': 'Mythic'}).json()['listings']
elapsed = time.perf_counter() - start
print('B-MARKET active_listings=501 mythic_active=1 filtered_result_count=%d (expected 1); unauthenticated request took %.1f ms' % (len(filtered), elapsed * 1000))

# B-KEY: non-ASCII X-Server-Key header produces an unhandled 500 instead of 403.
os.environ['SIGHTBREAK_SERVER_KEY'] = 'fictional-server-secret-' + 'x' * 32
response = client.post('/server/tickets/consume', headers={'X-Server-Key': 'café'.encode('latin-1')},
                       json={'ticket': 'x' * 40, 'server_id': 'local-relay'})
print('B-KEY non_ascii_server_key_status=%d (expected 403)' % response.status_code)

# B-ENUM: login timing distinguishes existing and unknown usernames.
body = dict(username='timing_user', password='long-test-password', display_name='Timing')
client.post('/auth/register', json=body)
known, unknown = [], []
for i in range(6):
    with transaction() as db:
        db.execute(text('DELETE FROM rate_buckets'))
    for target, bucket in (('timing_user', known), ('nobody_here_%d' % i, unknown)):
        start = time.perf_counter()
        status = client.post('/auth/login', json={'username': target, 'password': 'wrong-password-123'}).status_code
        bucket.append((time.perf_counter() - start) * 1000)
        assert status == 401
print('B-ENUM median_ms existing_user_wrong_password=%.1f unknown_user=%.1f' % (statistics.median(known), statistics.median(unknown)))
