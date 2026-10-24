"""Participant-private trade reads, checked against real PostgreSQL fixtures."""
from datetime import datetime, timedelta, timezone
from math import ceil
from uuid import NAMESPACE_URL, uuid5

import pytest
from sqlalchemy import event, text

from app import Base, digest, engine, now, transaction
from models import Item, Player, Session, Trade
from test_economy import clean_database, client  # shared destructive *_test guard/fixtures


def fixture_id(label):
    return str(uuid5(NAMESPACE_URL, 'sightbreak/trade-read/' + label))


def seed_workload(count, per_side):
    """Stable public payloads; no HTTP grants, rate-limit bypass or live accounts."""
    viewer = fixture_id('viewer')
    outsider = fixture_id('outsider')
    hidden_partner = fixture_id('hidden-partner')
    names = {viewer: 'Viewer', outsider: 'Outsider', hidden_partner: 'Hidden partner'}
    names.update({fixture_id(f'partner/{i}'): f'Partner {i}' for i in range(count)})
    acquired = datetime(2026, 10, 1, 12, 0, tzinfo=timezone.utc)
    expected = []
    with transaction() as db:
        # PostgreSQL renders timestamptz in its session timezone on every platform.
        acquired = db.scalar(text('SELECT CAST(:instant AS timestamptz)'), {'instant': acquired})
        db.add_all(Player(id=pid, username='fixture_' + str(i), display_name=name,
                          password_hash='fixture-unusable')
                   for i, (pid, name) in enumerate(names.items()))
        db.flush()
        for pid, token in ((viewer, 'trade-read-viewer'), (outsider, 'trade-read-outsider')):
            db.add(Session(token_hash=digest(token), player_id=pid,
                           expires_at=now() + timedelta(hours=1)))
        for i in range(count):
            partner = fixture_id(f'partner/{i}')
            a, b = (viewer, partner) if i % 2 == 0 else (partner, viewer)
            tid = fixture_id(f'trade/{i}')
            state = ('open', 'completed', 'cancelled')[i % 3]
            reservation = 'trade:' + tid if state == 'open' else None
            offers, metadata = {}, {}
            for owner, receiver in ((a, b), (b, a)):
                ids, values = [], []
                for j in range(per_side):
                    iid = fixture_id(f'item/{i}/{owner}/{j}')
                    ids.append(iid)
                    db.add(Item(id=iid, owner_id=receiver if state == 'completed' else owner,
                                definition_id='obsidian_rare', rarity='Rare',
                                pattern_seed=j, wear=1234, variant='standard',
                                reservation=reservation, acquired_at=acquired))
                    values.append(dict(id=iid, definition_id='obsidian_rare', rarity='Rare',
                                       pattern_seed=j, wear=0.1234, variant='standard',
                                       collection='Obsidian', kind='weapon_skin',
                                       name='Obsidian / Carbon', reserved=reservation is not None,
                                       trade_eligible=reservation is None,
                                       marketplace_eligible=reservation is None,
                                       acquired_at=acquired.isoformat()))
                # A batch must not replace the agreed offer order with SQL/set order.
                offers[owner], metadata[owner] = ids[::-1], values[::-1]
            confirmations = [a] if state == 'open' else [a, b] if state == 'completed' else []
            db.add(Trade(id=tid, a=a, b=b, revision=i + 2, offers=offers,
                         confirmations=confirmations, state=state))
            expected.append(dict(id=tid, a=a, b=b, names={a: names[a], b: names[b]},
                                 revision=i + 2, offers=offers, offer_items=metadata,
                                 confirmations=confirmations, state=state))
        # Unrelated data must never enter the participant's response or name maps.
        db.add(Trade(id=fixture_id('hidden-trade'), a=outsider, b=hidden_partner,
                     offers={outsider: [], hidden_partner: []}, confirmations=[]))
    return {'Authorization': 'Bearer trade-read-viewer'}, expected


def canonical_trades(payload):
    # The route has never promised top-level ordering; offer arrays DO have order.
    return {'trades': sorted(payload['trades'], key=lambda trade: trade['id'])}


def database_snapshot():
    """All authoritative tables, not only the fields exposed by this endpoint."""
    with engine.connect() as db:
        return {name: db.execute(text(f'SELECT to_jsonb(t)::text FROM "{name}" t '
                                     'ORDER BY to_jsonb(t)::text')).scalars().all()
                for name in sorted(Base.metadata.tables)}


@pytest.mark.parametrize('count,per_side', [(0, 0), (1, 0), (1, 2), (40, 1), (40, 20), (501, 0)])
def test_trade_read_payload_privacy_and_query_budget(client, count, per_side):
    headers, expected = seed_workload(count, per_side)
    statements = []
    def record(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)
    event.listen(engine, 'before_cursor_execute', record)
    try:
        response = client.get('/trades', headers=headers)
    finally:
        event.remove(engine, 'before_cursor_execute', record)
    assert response.status_code == 200
    assert canonical_trades(response.json()) == canonical_trades({'trades': expected})
    # Authentication is two SELECTs, then the participant-only trade query.
    # Additional reads scale in bounded 500-ID batches, not with each offer/name.
    budget = 3 + (ceil((count + 1) / 500) if count else 0) + ceil(count * per_side * 2 / 500)
    assert len(statements) <= budget, (len(statements), budget)
    assert all(statement.lstrip().upper().startswith('SELECT') for statement in statements)


def test_trade_reads_keep_current_metadata_for_closed_trades(client):
    headers, expected = seed_workload(3, 2)
    assert canonical_trades(client.get('/trades', headers=headers).json()) == canonical_trades({'trades': expected})
    closed = expected[1]
    partner = next(pid for pid in closed['names'] if pid != fixture_id('viewer'))
    offered = closed['offer_items'][closed['a']][0]
    consumed_key = closed['offer_items'][closed['b']][0]
    with transaction() as db:
        db.get(Player, partner).display_name = 'Updated partner'
        current = db.get(Item, offered['id'])
        current.reservation = 'market:later-listing'
        current.owner_id = fixture_id('outsider')
        key = db.get(Item, consumed_key['id'])
        key.definition_id = 'key'
        key.rarity = 'Common'
        key.consumed = True
    closed['names'][partner] = 'Updated partner'
    offered.update(reserved=True, trade_eligible=False, marketplace_eligible=False)
    consumed_key.update(definition_id='key', rarity='Common', collection='Universal',
                        kind='key', name='Collection key', trade_eligible=False,
                        marketplace_eligible=False)
    assert canonical_trades(client.get('/trades', headers=headers).json()) == canonical_trades({'trades': expected})


def test_trade_reads_preserve_repeated_historical_items(client):
    headers, expected = seed_workload(3, 2)
    viewer = fixture_id('viewer')
    # A once-traded item can appear in several historical offers. It is serialized
    # from the current Item record in each original position, just as before.
    source, target = expected[1], expected[2]
    target['offers'][viewer] = source['offers'][viewer][::-1]
    target['offer_items'][viewer] = source['offer_items'][viewer][::-1]
    with transaction() as db:
        db.get(Trade, target['id']).offers = target['offers']
    assert canonical_trades(client.get('/trades', headers=headers).json()) == canonical_trades({'trades': expected})


def test_trade_read_is_read_only_and_does_not_share_participant_names(client):
    headers, expected = seed_workload(5, 2)
    before = database_snapshot()
    assert canonical_trades(client.get('/trades', headers=headers).json()) == canonical_trades({'trades': expected})
    stranger = client.get('/trades', headers={'Authorization': 'Bearer trade-read-outsider'})
    assert stranger.status_code == 200
    trades = stranger.json()['trades']
    assert len(trades) == 1 and trades[0]['id'] == fixture_id('hidden-trade')
    assert set(trades[0]['names']) == {fixture_id('outsider'), fixture_id('hidden-partner')}
    assert database_snapshot() == before


@pytest.mark.parametrize('condition,status', [('missing', 401), ('expired', 401), ('revoked', 401), ('inactive', 403)])
def test_trade_read_rechecks_authentication(client, condition, status):
    headers, _ = seed_workload(1, 1)
    with transaction() as db:
        if condition == 'missing':
            headers = {}
        elif condition == 'expired':
            db.get(Session, digest('trade-read-viewer')).expires_at = now() - timedelta(seconds=1)
        elif condition == 'revoked':
            db.delete(db.get(Session, digest('trade-read-viewer')))
        else:
            db.get(Player, fixture_id('viewer')).active = False
    assert client.get('/trades', headers=headers).status_code == status
