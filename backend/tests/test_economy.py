"""Adversarial integration tests on real PostgreSQL, never on SQLite.

Run only against a dedicated disposable database whose name ends in _test.
Fictional balances/items are fixtures written directly through trusted DB code.
"""
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from pathlib import Path
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text, select, func
from sqlalchemy.exc import DBAPIError
from app import app, engine, Base, transaction, mint, credit, password_hasher, digest, now
from models import Player, Session, Item, Ledger, Trade, Operation

@pytest.fixture(autouse=True)
def clean_database():
    assert engine.url.database.endswith('_test'), 'Refusing to reset a non-test database'
    Base.metadata.create_all(engine)
    with engine.begin() as db:
        db.exec_driver_sql((Path(__file__).parents[1]/'migrations/001_integrity.sql').read_text())
        db.execute(text('TRUNCATE '+', '.join('"'+t+'"' for t in Base.metadata.tables)+' CASCADE'))
    yield
@pytest.fixture
def client(): return TestClient(app)
def player(balance=0):
    name='p'+uuid4().hex[:12]; token=uuid4().hex
    with transaction() as db:
        p=Player(username=name,display_name=name,password_hash='fixture-unusable')
        db.add(p); db.flush(); pid=p.id
        if balance: credit(db,p,balance,'fictional_test_fixture',name)
        db.add(Session(token_hash=digest(token),player_id=pid,expires_at=now()+timedelta(hours=1)))
    return pid, {'Authorization':'Bearer '+token}
def item(pid,definition='obsidian_rare'):
    with transaction() as db: return mint(db,pid,definition).id
def idem(**fields): return dict(idempotency_key=str(uuid4()),**fields)
def post(client,path,headers,body=None): return client.post(path,headers=headers,json=body or {})

def test_new_account_has_no_value_and_rejects_client_balance(client):
    body=dict(username='honest_user',password='long-test-password',display_name='Fictional')
    assert client.post('/auth/register',json={**body,'credits':1000}).status_code==422
    result=client.post('/auth/register',json=body); assert result.status_code==201
    headers={'Authorization':'Bearer '+result.json()['token']}
    assert client.get('/me',headers=headers).json()['credits']==0
    assert client.get('/inventory',headers=headers).json()=={'items':[]}
    assert client.post('/auth/login',json={k:body[k] for k in ('username','password')}).status_code==200
    assert post(client,'/auth/logout',headers).status_code==200
    assert client.get('/me',headers=headers).status_code==401

def test_password_is_argon2_and_tokens_are_hashed(client):
    body=dict(username='hash_user',password='long-test-password',display_name='Fictional')
    token=client.post('/auth/register',json=body).json()['token']
    with transaction() as db:
        p=db.scalar(select(Player)); assert p.password_hash.startswith('$argon2id$')
        assert db.get(Session,token) is None
        s=db.get(Session,digest(token)); s.expires_at=now()-timedelta(seconds=1)
    assert client.get('/me',headers={'Authorization':'Bearer '+token}).status_code==401

def test_store_replay_and_changed_payload(client):
    pid,h=player(1000); payload=idem(definition_id='obsidian_case')
    first=post(client,'/store/buy',h,payload); assert first.status_code==200
    assert post(client,'/store/buy',h,payload).json()==first.json()
    assert post(client,'/store/buy',h,{**payload,'definition_id':'key'}).status_code==409
    assert client.get('/me',headers=h).json()['credits']==650
    assert len(client.get('/inventory',headers=h).json()['items'])==1

def test_concurrent_double_spend(client):
    pid,h=player(350)
    def buy(_):
        with TestClient(app) as c: return post(c,'/store/buy',h,idem(definition_id='obsidian_case')).status_code
    with ThreadPoolExecutor(max_workers=2) as pool: statuses=list(pool.map(buy,range(2)))
    assert sorted(statuses)==[200,409]
    assert client.get('/me',headers=h).json()['credits']==0
    assert len(client.get('/inventory',headers=h).json()['items'])==1

def test_case_open_replay_consumes_once(client):
    pid,h=player(); case=item(pid,'obsidian_case'); key=item(pid,'key')
    body=idem(case_id=case,key_id=key)
    result=post(client,'/cases/open',h,body); assert result.status_code==200
    assert post(client,'/cases/open',h,body).json()==result.json()
    assert post(client,'/cases/open',h,idem(case_id=case,key_id=key)).status_code==409
    assert len(client.get('/inventory',headers=h).json()['items'])==1
    assert 0<=result.json()['roll']<10000

def test_case_open_rejects_unowned_or_fake_selection(client):
    a,ha=player(); b,hb=player(); case=item(a,'obsidian_case'); key=item(b,'key')
    assert post(client,'/cases/open',ha,idem(case_id=case,key_id=key)).status_code==409
    assert post(client,'/cases/open',ha,{**idem(case_id=case,key_id=key),'rarity':'Mythic'}).status_code==422

def test_concurrent_market_purchase_one_owner(client):
    seller,hs=player(); a,ha=player(1000); b,hb=player(1000); iid=item(seller)
    listing=post(client,'/market/list',hs,dict(item_id=iid,price=400)).json()['id']
    bodies=[idem(),idem()]
    def buy(pair):
        h,body=pair
        with TestClient(app) as c: return post(c,f'/market/{listing}/buy',h,body)
    with ThreadPoolExecutor(max_workers=2) as pool: results=list(pool.map(buy,[(ha,bodies[0]),(hb,bodies[1])]))
    assert sorted(r.status_code for r in results)==[200,409]
    winner=0 if results[0].status_code==200 else 1
    wh=[ha,hb][winner]
    assert post(client,f'/market/{listing}/buy',wh,bodies[winner]).json()==results[winner].json()
    assert client.get('/me',headers=hs).json()['credits']==388
    with transaction() as db:
        assert db.get(Item,iid).owner_id==[a,b][winner]
        assert db.scalar(select(func.sum(Player.credits)))==1988

def test_market_reservation_cancel_and_ownership(client):
    a,ha=player(); b,hb=player(); iid=item(a)
    listing=post(client,'/market/list',ha,dict(item_id=iid,price=400)).json()['id']
    assert post(client,'/market/list',ha,dict(item_id=iid,price=1)).status_code==409
    assert post(client,f'/market/{listing}/cancel',hb).status_code==404
    assert post(client,f'/market/{listing}/cancel',ha).status_code==200
    assert post(client,'/market/list',ha,dict(item_id=iid,price=400)).status_code==201

def test_trade_revision_invalidates_confirmation_and_transfers_once(client):
    a,ha=player(); b,hb=player(); ia=item(a); ib=item(b)
    t=post(client,'/trades',ha,dict(partner_id=b)).json(); tid=t['id']
    t=client.put(f'/trades/{tid}/offer',headers=ha,json=dict(item_ids=[ia],revision=0)).json()
    assert post(client,f'/trades/{tid}/confirm',ha,dict(revision=1)).json()['confirmations']==[a]
    t=client.put(f'/trades/{tid}/offer',headers=hb,json=dict(item_ids=[ib],revision=1)).json()
    assert t['confirmations']==[] and t['revision']==2
    assert post(client,f'/trades/{tid}/confirm',ha,dict(revision=1)).status_code==409
    assert post(client,'/market/list',ha,dict(item_id=ia,price=1)).status_code==409
    assert post(client,f'/trades/{tid}/confirm',hb,dict(revision=2)).json()['state']=='open'
    assert post(client,f'/trades/{tid}/confirm',ha,dict(revision=2)).json()['state']=='completed'
    assert post(client,f'/trades/{tid}/confirm',ha,dict(revision=2)).json()['state']=='completed'
    with transaction() as db:
        assert db.get(Item,ia).owner_id==b and db.get(Item,ib).owner_id==a
        assert db.get(Item,ia).reservation is None

def test_trade_rejects_duplicates_unowned_and_releases_cancel(client):
    a,ha=player(); b,hb=player(); ia=item(a); ib=item(b)
    tid=post(client,'/trades',ha,dict(partner_id=b)).json()['id']
    for ids in ([ia,ia],[ib]):
        assert client.put(f'/trades/{tid}/offer',headers=ha,json=dict(item_ids=ids,revision=0)).status_code in (400,409)
    assert client.put(f'/trades/{tid}/offer',headers=ha,json=dict(item_ids=[ia],revision=0)).status_code==200
    assert post(client,f'/trades/{tid}/cancel',hb).status_code==200
    assert post(client,'/market/list',ha,dict(item_id=ia,price=1)).status_code==201

def match_body():
    ended=now(); participants=[]
    for i in range(10):
        pid,_=player(); participants.append(dict(player_id=pid,won=i<5,active_seconds=500,objective_contributions=1))
    return dict(match_id=str(uuid4()),started_at=(ended-timedelta(seconds=600)).isoformat(),ended_at=ended.isoformat(),mode='ranked_5v5',participants=participants)

def test_forged_rewards_rejected_and_trusted_replay_idempotent(client,monkeypatch):
    body=match_body(); secret='fictional-server-secret-'+'x'*32
    monkeypatch.setenv('SIGHTBREAK_SERVER_KEY',secret)
    assert client.post('/server/matches',json=body).status_code==403
    h={'X-Server-Key':secret}
    first=post(client,'/server/matches',h,body); assert first.status_code==200
    assert post(client,'/server/matches',h,body).json()==first.json()
    body['participants'][0]['objective_contributions']=2
    assert post(client,'/server/matches',h,body).status_code==409
    with transaction() as db: assert db.scalar(select(func.count()).select_from(Ledger))==10

def test_bot_count_and_afk_no_rewards(client,monkeypatch):
    body=match_body(); secret='fictional-server-secret-'+'x'*32; monkeypatch.setenv('SIGHTBREAK_SERVER_KEY',secret)
    h={'X-Server-Key':secret}
    assert post(client,'/server/matches',h,{**body,'participants':body['participants'][:2]}).status_code==422
    body['participants'][0]['active_seconds']=0
    result=post(client,'/server/matches',h,body)
    assert result.status_code==200 and result.json()['rewards'][0]['credits']==0

def test_history_append_only_and_rollback_disconnect(client):
    pid,h=player(100)
    with pytest.raises(DBAPIError):
        with transaction() as db: db.execute(text('UPDATE ledger SET amount=999'))
    with pytest.raises(RuntimeError):
        with transaction() as db:
            credit(db,db.get(Player,pid),-50,'interrupted','fixture')
            mint(db,pid,'key'); db.flush(); raise RuntimeError('simulated disconnect before commit')
    assert client.get('/me',headers=h).json()['credits']==100
    assert client.get('/inventory',headers=h).json()['items']==[]

def test_rate_limit_persisted(client):
    pid,h=player()
    for i in range(60): assert post(client,'/store/buy',h,idem(definition_id='key')).status_code==409
    assert post(client,'/store/buy',h,idem(definition_id='key')).status_code==429

def test_overlapping_matches_and_duplicate_humans_rejected(client,monkeypatch):
    body=match_body(); secret='fictional-server-secret-'+'x'*32; monkeypatch.setenv('SIGHTBREAK_SERVER_KEY',secret)
    h={'X-Server-Key':secret}
    assert post(client,'/server/matches',h,body).status_code==200
    assert post(client,'/server/matches',h,{**body,'match_id':str(uuid4())}).status_code==409
    body['participants'][1]['player_id']=body['participants'][0]['player_id']
    assert post(client,'/server/matches',h,{**body,'match_id':str(uuid4())}).status_code==400

def test_concurrent_case_open_exactly_one_draw(client):
    pid,h=player(); case=item(pid,'obsidian_case'); key=item(pid,'key')
    def opening(_):
        with TestClient(app) as c: return post(c,'/cases/open',h,idem(case_id=case,key_id=key)).status_code
    with ThreadPoolExecutor(max_workers=2) as pool: statuses=list(pool.map(opening,range(2)))
    assert sorted(statuses)==[200,409]
    assert len(client.get('/inventory',headers=h).json()['items'])==1

def test_trade_inspection_contains_metadata_without_exposing_to_third_party(client):
    a,ha=player(); b,hb=player(); c,hc=player(); ia=item(a)
    tid=post(client,'/trades',ha,dict(partner_id=b)).json()['id']
    t=client.put(f'/trades/{tid}/offer',headers=ha,json=dict(item_ids=[ia],revision=0)).json()
    assert t['offer_items'][a][0]['id']==ia
    assert t['offer_items'][a][0]['rarity']=='Rare'
    assert client.get('/trades',headers=hc).json()=={'trades':[]}
    assert post(client,f'/trades/{tid}/confirm',hc,dict(revision=1)).status_code==404

def test_database_negative_wallet_constraint():
    pid,h=player()
    with pytest.raises(DBAPIError):
        with transaction() as db: db.get(Player,pid).credits=-1

def issue_ticket(client, headers, server_id='local-relay'):
    response = post(client, '/auth/game-ticket', headers, {'server_id': server_id})
    assert response.status_code == 201
    return response.json()['ticket']

def test_ticket_is_scoped_single_use_and_hash_only(client, monkeypatch):
    from models import GameTicket
    pid, h = player()
    secret = 'fictional-ticket-secret-' + 'x' * 32
    monkeypatch.setenv('SIGHTBREAK_SERVER_KEY', secret)
    ticket = issue_ticket(client, h)
    with transaction() as db:
        assert db.get(GameTicket, ticket) is None
        assert db.get(GameTicket, digest(ticket)).player_id == pid
    headers = {'X-Server-Key': secret}
    assert post(client, '/server/tickets/consume', headers, {'ticket': ticket, 'server_id': 'other-server'}).status_code == 403
    body = {'ticket': ticket, 'server_id': 'local-relay'}
    response = post(client, '/server/tickets/consume', headers, body)
    assert response.status_code == 200 and response.json()['player_id'] == pid
    assert post(client, '/server/tickets/consume', headers, body).status_code == 401

def test_ticket_requires_server_secret_and_account_session(client, monkeypatch):
    pid, h = player()
    ticket = issue_ticket(client, h)
    body = {'ticket': ticket, 'server_id': 'local-relay'}
    monkeypatch.delenv('SIGHTBREAK_SERVER_KEY', raising=False)
    assert post(client, '/server/tickets/consume', {}, body).status_code == 403
    secret = 'fictional-ticket-secret-' + 'x' * 32
    monkeypatch.setenv('SIGHTBREAK_SERVER_KEY', secret)
    assert post(client, '/server/tickets/consume', {'X-Server-Key': 'wrong'}, body).status_code == 403
    assert post(client, '/auth/logout', h).status_code == 200
    assert post(client, '/server/tickets/consume', {'X-Server-Key': secret}, body).status_code == 401
    assert post(client, '/auth/game-ticket', h, {'server_id': 'local-relay'}).status_code == 401

def test_ticket_expiry_and_server_scope_are_enforced(client, monkeypatch):
    from models import GameTicket
    pid, h = player()
    secret = 'fictional-ticket-secret-' + 'x' * 32
    monkeypatch.setenv('SIGHTBREAK_SERVER_KEY', secret)
    assert post(client, '/auth/game-ticket', h, {'server_id': 'unknown'}).status_code == 404
    ticket = issue_ticket(client, h)
    with transaction() as db:
        db.get(GameTicket, digest(ticket)).expires_at = now() - timedelta(seconds=1)
    assert post(client, '/server/tickets/consume', {'X-Server-Key': secret}, {'ticket': ticket, 'server_id': 'local-relay'}).status_code == 401
    fresh = issue_ticket(client, h)
    with transaction() as db:
        db.get(GameTicket, digest(fresh)).server_id = 'other-server'
    assert post(client, '/server/tickets/consume', {'X-Server-Key': secret}, {'ticket': fresh, 'server_id': 'local-relay'}).status_code == 401

def test_concurrent_ticket_consumption_only_one_admission(client, monkeypatch):
    pid, h = player()
    secret = 'fictional-ticket-secret-' + 'x' * 32
    monkeypatch.setenv('SIGHTBREAK_SERVER_KEY', secret)
    ticket = issue_ticket(client, h)
    def consume(_):
        with TestClient(app) as c:
            return post(c, '/server/tickets/consume', {'X-Server-Key': secret}, {'ticket': ticket, 'server_id': 'local-relay'}).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(consume, range(2)))
    assert sorted(statuses) == [200, 401]

def test_ticket_rejects_disabled_account_and_expired_parent_session(client, monkeypatch):
    pid, h = player()
    secret = 'fictional-ticket-secret-' + 'x' * 32
    monkeypatch.setenv('SIGHTBREAK_SERVER_KEY', secret)
    ticket = issue_ticket(client, h)
    with transaction() as db: db.get(Player, pid).active = False
    body = {'ticket': ticket, 'server_id': 'local-relay'}
    assert post(client, '/server/tickets/consume', {'X-Server-Key': secret}, body).status_code == 403
    with transaction() as db:
        db.get(Player, pid).active = True
        db.get(Session, digest(h['Authorization'][7:])).expires_at = now() - timedelta(seconds=1)
    assert post(client, '/server/tickets/consume', {'X-Server-Key': secret}, body).status_code == 401

def equip(client, headers, item_id):
    return client.put('/loadout', headers=headers, json={'slot': 'rifle', 'item_id': item_id})

def test_loadout_owned_compatible_cosmetic_and_unequip(client):
    a, ha = player(); b, hb = player(); skin = item(a); other = item(b); key = item(a, 'key')
    assert client.get('/loadout', headers=ha).json() == {'slots': {}}
    assert equip(client, ha, other).status_code == 409
    assert equip(client, ha, key).status_code == 400
    response = equip(client, ha, skin)
    assert response.status_code == 200
    assert response.json()['slots']['rifle']['id'] == skin
    assert client.get('/loadout', headers=ha).json()['slots']['rifle']['id'] == skin
    assert equip(client, ha, skin).status_code == 200
    assert equip(client, ha, None).json() == {'slots': {}}
    assert client.get('/loadout').status_code == 401

def test_market_transfer_unequips_source_atomically(client):
    from models import Loadout
    a, ha = player(); b, hb = player(1000); skin = item(a)
    assert equip(client, ha, skin).status_code == 200
    lid = post(client, '/market/list', ha, {'item_id': skin, 'price': 400}).json()['id']
    assert equip(client, ha, skin).status_code == 409
    assert post(client, f'/market/{lid}/buy', hb, idem()).status_code == 200
    assert client.get('/loadout', headers=ha).json() == {'slots': {}}
    with transaction() as db:
        assert db.get(Loadout, (a, 'rifle')) is None
    assert equip(client, hb, skin).status_code == 200
    assert equip(client, ha, skin).status_code == 409

def test_trade_transfer_unequips_both_cosmetic_slots(client):
    from models import Loadout
    a, ha = player(); b, hb = player(); ia = item(a); ib = item(b)
    assert equip(client, ha, ia).status_code == 200
    assert equip(client, hb, ib).status_code == 200
    tid = post(client, '/trades', ha, {'partner_id': b}).json()['id']
    assert client.put(f'/trades/{tid}/offer', headers=ha, json={'item_ids': [ia], 'revision': 0}).status_code == 200
    assert client.put(f'/trades/{tid}/offer', headers=hb, json={'item_ids': [ib], 'revision': 1}).status_code == 200
    assert post(client, f'/trades/{tid}/confirm', ha, {'revision': 2}).status_code == 200
    assert post(client, f'/trades/{tid}/confirm', hb, {'revision': 2}).json()['state'] == 'completed'
    assert client.get('/loadout', headers=ha).json() == {'slots': {}}
    assert client.get('/loadout', headers=hb).json() == {'slots': {}}
    with transaction() as db:
        assert db.get(Loadout, (a, 'rifle')) is None and db.get(Loadout, (b, 'rifle')) is None

def test_loadout_read_filters_stale_ownership_and_rejects_other_slots(client):
    from models import Loadout
    a, ha = player(); b, hb = player(); skin = item(a)
    assert client.put('/loadout', headers=ha, json={'slot': 'pistol', 'item_id': skin}).status_code == 422
    assert equip(client, ha, skin).status_code == 200
    with transaction() as db: db.get(Item, skin).owner_id = b
    assert client.get('/loadout', headers=ha).json() == {'slots': {}}


@pytest.mark.parametrize("roll,expected", [
    (0,"Common"),(5799,"Common"),(5800,"Uncommon"),(8399,"Uncommon"),
    (8400,"Rare"),(9499,"Rare"),(9500,"Epic"),(9899,"Epic"),
    (9900,"Legendary"),(9989,"Legendary"),(9990,"Mythic"),(9999,"Mythic"),
])
def test_published_case_odds_match_every_boundary(client, monkeypatch, roll, expected):
    import app as service
    original_randbelow = service.secrets.randbelow
    monkeypatch.setattr(service.secrets, "randbelow", lambda limit: roll if limit == 10000 else original_randbelow(limit))
    probabilities = client.get('/catalog').json()['case_tables']['probabilities']
    assert sum(service.CONFIG['rarities'].values()) == 10000
    assert probabilities == {k: v / 100 for k, v in service.CONFIG['rarities'].items()}
    pid, headers = player()
    body = idem(case_id=item(pid, 'obsidian_case'), key_id=item(pid, 'key'))
    response = post(client, '/cases/open', headers, body)
    assert response.status_code == 200
    assert response.json()['roll'] == roll
    assert response.json()['item']['rarity'] == expected
    assert post(client, '/cases/open', headers, body).json() == response.json()
    assert len(client.get('/inventory', headers=headers).json()['items']) == 1
