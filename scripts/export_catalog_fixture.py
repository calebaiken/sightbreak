#!/usr/bin/env python3
"""Writes game/tests/fixtures/backend_world.json from the backend's own code.

The armory tests used hand-typed catalog and inventory data, which can drift from what the
server really sends (for example, the server states odds as floats such as 58.0). This
generator builds the fixture by calling the backend's own functions: catalog(), profile(),
item_json() and trade_json(), with fixed ids and seeds, so every field name, rarity, price,
probability and item shape is the server's. It needs the backend's Python dependencies
(`uv sync --project backend`) but no database: it never connects to one.

  python3 scripts/export_catalog_fixture.py           write the fixture
  python3 scripts/export_catalog_fixture.py --check   fail if the committed file differs

`--check` is the drift guard: change definitions() or backend/config/economy.json and it fails
until the fixture is regenerated and the armory tests are rerun.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'game/tests/fixtures/backend_world.json'
sys.path.insert(0, str(ROOT / 'backend'))
# Importing the service builds its engine lazily; this URL is never connected to.
os.environ.setdefault('DATABASE_URL', 'postgresql+psycopg://fixture:fixture@127.0.0.1:1/fixture')
import app as service  # noqa: E402
import sqlalchemy.orm  # noqa: E402

SELF = '11111111-1111-4111-8111-111111111111'
OTHER = '22222222-2222-4222-8222-222222222222'
WHEN = datetime(2026, 1, 1, tzinfo=timezone.utc)


def minted(item_id, definition_id, seed, wear, reservation=None):
    definition = service.DEFINITIONS[definition_id]
    return SimpleNamespace(id=item_id, definition_id=definition_id, rarity=definition['rarity'], pattern_seed=seed, wear=wear,
                           variant='standard', reservation=reservation, consumed=False, acquired_at=WHEN)


def build():
    graphite = minted('a0000000-0000-4000-8000-000000000001', 'obsidian_common', 1840233, 1200)
    slate = minted('a0000000-0000-4000-8000-000000000002', 'obsidian_rare', 77120911, 3310, 'market:b0000000-0000-4000-8000-000000000002')
    iris = minted('a0000000-0000-4000-8000-000000000003', 'crimson_archive_legendary', 5521, 150)
    case = minted('a0000000-0000-4000-8000-000000000004', 'obsidian_case', 9, 0)
    key = minted('a0000000-0000-4000-8000-000000000005', 'key', 10, 0)
    theirs = minted('c0000000-0000-4000-8000-000000000001', 'obsidian_mythic', 424242, 40)
    dear = minted('c0000000-0000-4000-8000-000000000002', 'crimson_archive_uncommon', 8675309, 4000)
    rook_item = minted('c0000000-0000-4000-8000-000000000003', 'spectral_circuit_epic', 31337, 2210)
    listings = [
        dict(id='b0000000-0000-4000-8000-000000000001', seller_id=OTHER, price=100, item=service.item_json(theirs)),
        dict(id='b0000000-0000-4000-8000-000000000002', seller_id=SELF, price=1250, item=service.item_json(slate)),
        dict(id='b0000000-0000-4000-8000-000000000003', seller_id=OTHER, price=5000, item=service.item_json(dear)),
    ]
    items = {i.id: i for i in (graphite, slate, iris, case, key, theirs, dear, rook_item)}
    people = {SELF: SimpleNamespace(display_name='QA Fixture'), OTHER: SimpleNamespace(display_name='Rook')}

    class FakeSession:  # what trade_json reads through object_session(); the same field access, no database
        def get(self, model, key):
            return items[key] if model is service.Item else people[key]

    real = sqlalchemy.orm.object_session
    sqlalchemy.orm.object_session = lambda _trade: FakeSession()
    try:
        gift = SimpleNamespace(id='d0000000-0000-4000-8000-000000000001', a=SELF, b=OTHER, revision=3, offers={SELF: [graphite.id], OTHER: []}, confirmations=[], state='open')
        swap = SimpleNamespace(id='d0000000-0000-4000-8000-000000000002', a=OTHER, b=SELF, revision=1, offers={SELF: [iris.id], OTHER: [rook_item.id]}, confirmations=[OTHER], state='open')
        trades = [service.trade_json(gift), service.trade_json(swap)]
    finally:
        sqlalchemy.orm.object_session = real
    account = service.profile(SimpleNamespace(id=SELF, display_name='QA Fixture', xp=1450, credits=1250))
    world = {
        'catalog': json.loads(json.dumps(service.catalog())),
        'account': account,
        'inventory': {'items': [service.item_json(i) for i in (graphite, slate, iris, case, key)]},
        'market': {'listings': listings},
        'trades': {'trades': trades},
        'players': {'self': SELF, 'other': OTHER},
    }
    return {'_generated_by': 'scripts/export_catalog_fixture.py from backend/app.py serializers; do not edit by hand', 'world': world}


def main():
    text = json.dumps(build(), indent=1) + '\n'
    if '--check' in sys.argv:
        if not OUT.exists() or OUT.read_text() != text:
            sys.exit('game/tests/fixtures/backend_world.json differs from what the backend produces. Regenerate it with scripts/export_catalog_fixture.py, then rerun the armory tests.')
        print('backend_world.json matches the backend (%d definitions)' % len(json.loads(text)['world']['catalog']['definitions']))
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print('wrote', OUT.relative_to(ROOT))


main()
