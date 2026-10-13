"""Earned-only economy. Every value mutation is one PostgreSQL transaction.

A transaction advisory lock serializes this initial service's economy writes.
This deliberately trades throughput for a small, auditable locking surface.
"""
import hashlib
import json
import os
import secrets
import time
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import FastAPI, HTTPException, Header, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import DateTime, cast, create_engine, select, text, func, or_
from sqlalchemy.orm import Session as DBSession
from models import Base, Player, Session, Ledger, Item, Operation, Audit, Listing, Trade, Reward, RateBucket, GameTicket, Loadout, now

CONFIG = json.loads((Path(__file__).parent / 'config/economy.json').read_text())
if sum(CONFIG['rarities'].values()) != 10000 or any(w <= 0 for w in CONFIG['rarities'].values()):
    raise RuntimeError('Case weights must be positive integers summing to 10000')
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql+psycopg://sightbreak:sightbreak_local_only@127.0.0.1:55432/sightbreak')
if not DATABASE_URL.startswith('postgresql'):
    raise RuntimeError('Authoritative economy requires PostgreSQL; offline data is never imported')
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=10, max_overflow=10)
password_hasher = PasswordHasher()
# Unknown usernames verify against this hash so login timing does not reveal accounts.
UNKNOWN_USER_HASH = password_hasher.hash(secrets.token_urlsafe(24))
app = FastAPI(title='SIGHTBREAK earned-only economy', version='0.1.0')
LOCK_ID = 0x5349474854

def fail(message, status=409): raise HTTPException(status, message)
def digest(value): return hashlib.sha256(value.encode()).hexdigest()
def fingerprint(value): return digest(json.dumps(value, sort_keys=True, separators=(',', ':')))
def audit(db, actor, action, **details): db.add(Audit(actor=actor, action=action, details=details))

@contextmanager
def transaction():
    with DBSession(engine) as db, db.begin():
        db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': LOCK_ID})
        yield db

def rate(request, category, limit=60):
    # Persisted across workers/restarts; ignore spoofable forwarding headers.
    # One atomic upsert: limit checks never queue behind the economy write lock.
    host = request.client.host if request.client else 'unknown'
    key = f'{category}:{host}:{int(time.time()) // 60}'
    with engine.begin() as db:
        count = db.execute(text('INSERT INTO rate_buckets (id, count) VALUES (:key, 1) '
                                'ON CONFLICT (id) DO UPDATE SET count = rate_buckets.count + 1 RETURNING count'),
                           {'key': key}).scalar_one()
    if count > limit: fail('Rate limit exceeded; retry next minute', 429)

def authenticated(db, authorization):
    if not authorization or not authorization.startswith('Bearer '): fail('Authentication required', 401)
    session = db.get(Session, digest(authorization[7:]))
    if not session or session.expires_at <= now(): fail('Session expired or invalid', 401)
    player = db.get(Player, session.player_id)
    if not player or not player.active: fail('Account unavailable', 403)
    return player

def trusted_server(server_key, server_id=None):
    expected = os.environ.get('SIGHTBREAK_SERVER_KEY')
    # Compare bytes: str comparison raises on non-ASCII header values.
    if not expected or len(expected) < 32 or not server_key or not secrets.compare_digest(server_key.encode(), expected.encode()):
        fail('Trusted game server required', 403)
    configured_id = os.environ.get('SIGHTBREAK_SERVER_ID', 'local-relay')
    if server_id is not None and server_id != configured_id:
        fail('Server identity does not match credential scope', 403)
    return configured_id

def level(xp): return 1 + int((xp / CONFIG['xp_level_base']) ** 0.5)
def profile(p): return dict(player_id=p.id, display_name=p.display_name, xp=p.xp, level=level(p.xp), credits=p.credits)
def credit(db, player, amount, reason, reference):
    if player.credits + amount < 0: fail('Insufficient earned Credits')
    player.credits += amount
    db.add(Ledger(player_id=player.id, amount=amount, balance_after=player.credits, reason=reason, reference=reference))

def definitions():
    output = {'key': dict(id='key',name='Collection key',kind='key',rarity='Common',collection='Universal',price=CONFIG['key_price'])}
    finishes = ['Graphite', 'Brushed Steel', 'Carbon', 'Crimson Etch', 'Iridescence', 'Gilded Fracture']
    for collection in CONFIG['collections']:
        slug = collection.lower().replace(' ', '_')
        output[f'{slug}_case'] = dict(id=f'{slug}_case',name=f'{collection} case',kind='case',rarity='Common',collection=collection,price=CONFIG['case_price'])
        for i, rarity in enumerate(CONFIG['rarities']):
            item_id = f'{slug}_{rarity.lower()}'
            output[item_id] = dict(id=item_id,name=f'{collection} / {finishes[i]}',kind='weapon_skin',weapon='rifle',finish=finishes[i],rarity=rarity,collection=collection)
    return output
DEFINITIONS = definitions()
def item_json(item):
    d = DEFINITIONS[item.definition_id]
    return dict(id=item.id,definition_id=item.definition_id,rarity=item.rarity,pattern_seed=item.pattern_seed,wear=item.wear / 10000.0,variant=item.variant,collection=d['collection'],kind=d['kind'],name=d['name'],reserved=item.reservation is not None,trade_eligible=not item.consumed and not item.reservation,marketplace_eligible=not item.consumed and not item.reservation,acquired_at=item.acquired_at.isoformat())
def mint(db, owner, definition_id):
    d = DEFINITIONS[definition_id]
    item = Item(owner_id=owner,definition_id=definition_id,rarity=d['rarity'],pattern_seed=secrets.randbelow(2**31),wear=secrets.randbelow(10001))
    db.add(item); db.flush()
    audit(db,owner,'item_minted',item_id=item.id,definition_id=definition_id)
    return item

def unequip_transferred_item(db, item_id):
    equipped = db.scalar(select(Loadout).where(Loadout.item_id == item_id))
    if equipped is not None:
        db.delete(equipped)

def loadout_json(db, player):
    slots = {}
    for equipped in db.scalars(select(Loadout).where(Loadout.player_id == player.id)):
        item = db.get(Item, equipped.item_id)
        if item and item.owner_id == player.id and not item.consumed:
            definition = DEFINITIONS[item.definition_id]
            if definition['kind'] == 'weapon_skin' and definition.get('weapon') == equipped.slot:
                slots[equipped.slot] = item_json(item)
    return {'slots': slots}

def owned(db, owner, item_id, reservation=None):
    item = db.get(Item, str(item_id))
    if not item or item.owner_id != owner or item.consumed or item.reservation != reservation: fail('Item unavailable or not owned')
    return item

def replay(db, actor, route, body):
    key = f'{actor}:{route}:{body.idempotency_key}'
    hashed = fingerprint(body.model_dump(mode='json'))
    previous = db.get(Operation, key)
    if previous:
        if previous.request_hash != hashed: fail('Idempotency key reused with a different request')
        return key, hashed, previous.response
    return key, hashed, None

def remember(db, key, hashed, response):
    db.add(Operation(id=key,request_hash=hashed,response=response)); return response

class Strict(BaseModel): model_config = ConfigDict(extra='forbid')
class Login(Strict):
    username: str = Field(min_length=3,max_length=32,pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(min_length=12,max_length=128)
class Register(Login):
    display_name: str = Field(min_length=1,max_length=32)
    @field_validator('display_name')
    @classmethod
    def one_visible_line(cls, value: str) -> str:
        # Names appear inside trade and match text; control, format (bidi) and
        # line/paragraph separators could forge or reorder the surrounding terms.
        if not value.strip() or any(unicodedata.category(c) in ('Cc','Cf','Zl','Zp') for c in value):
            raise ValueError('display name must be one line of visible text')
        return value
class Idempotent(Strict): idempotency_key: UUID
class Buy(Idempotent): definition_id: str = Field(max_length=100)
class Open(Idempotent):
    case_id: UUID
    key_id: UUID
class ListItem(Strict):
    item_id: UUID
    price: int = Field(gt=0,le=10000000)
class NewTrade(Strict): partner_id: UUID
class Revision(Strict): revision: int = Field(ge=0)
class Offer(Revision): item_ids: list[UUID] = Field(max_length=20)
Auth = Annotated[str | None, Header()]

@app.get('/health')
def health():
    with engine.connect() as db: db.execute(text('SELECT 1'))
    return {'status':'ok','storage':'postgresql','economy_version':CONFIG['version']}

def issue_session(db, player):
    token=secrets.token_urlsafe(32); expiry=now()+timedelta(hours=24)
    db.add(Session(token_hash=digest(token),player_id=player.id,expires_at=expiry))
    return dict(token=token,player_id=player.id,expires_at=expiry.isoformat())
@app.post('/auth/register',status_code=201)
def register(body:Register,request:Request):
    rate(request,'auth',15)
    hashed=password_hasher.hash(body.password)
    with transaction() as db:
        if db.scalar(select(Player).where(Player.username==body.username.lower())): fail('Username unavailable')
        p=Player(username=body.username.lower(),display_name=body.display_name,password_hash=hashed)
        db.add(p); db.flush(); audit(db,p.id,'registered')
        return issue_session(db,p)
@app.post('/auth/login')
def login(body:Login,request:Request):
    rate(request,'auth',15)
    with DBSession(engine) as db:
        p=db.scalar(select(Player).where(Player.username==body.username.lower()))
        try:
            password_hasher.verify(p.password_hash if p else UNKNOWN_USER_HASH,body.password)
        except (VerificationError, InvalidHashError): fail('Invalid credentials',401)
        if not p: fail('Invalid credentials',401)
        if not p.active: fail('Account unavailable',403)
        result=issue_session(db,p); db.commit(); return result
@app.post('/auth/logout')
def logout(authorization:Auth=None):
    with transaction() as db:
        authenticated(db,authorization); db.delete(db.get(Session,digest(authorization[7:])))
    return {'logged_out':True}
@app.get('/me')
def me(authorization:Auth=None):
    with DBSession(engine) as db: return profile(authenticated(db,authorization))
@app.get('/inventory')
def inventory(authorization:Auth=None):
    with DBSession(engine) as db:
        p=authenticated(db,authorization)
        return {'items':[item_json(i) for i in db.scalars(select(Item).where(Item.owner_id==p.id,Item.consumed==False).order_by(Item.acquired_at))]}
@app.get('/catalog')
def catalog():
    return {'definitions':list(DEFINITIONS.values()),'case_tables':{'version':CONFIG['version'],'probabilities':{k:v/100 for k,v in CONFIG['rarities'].items()},'key_definition_id':'key'},'prices':{'case':CONFIG['case_price'],'key':CONFIG['key_price']},'market_fee_basis_points':CONFIG['market_fee_basis_points']}
@app.post('/store/buy')
def store_buy(body:Buy,request:Request,authorization:Auth=None):
    rate(request,'economy')
    with transaction() as db:
        p=authenticated(db,authorization); key,h,old=replay(db,p.id,'store',body)
        if old: return old
        d=DEFINITIONS.get(body.definition_id)
        if not d or d['kind'] not in ('case','key'): fail('Only earned-credit cases and keys are sold',400)
        credit(db,p,-d['price'],'store',key)
        item=mint(db,p.id,body.definition_id)
        return remember(db,key,h,{'item':item_json(item),'credits':p.credits})
@app.post('/cases/open')
def open_case(body:Open,request:Request,authorization:Auth=None):
    rate(request,'economy')
    with transaction() as db:
        p=authenticated(db,authorization); key,h,old=replay(db,p.id,'open',body)
        if old: return old
        case=owned(db,p.id,body.case_id); case_key=owned(db,p.id,body.key_id)
        if DEFINITIONS[case.definition_id]['kind']!='case' or case_key.definition_id!='key': fail('A case and matching key are required',400)
        roll=secrets.randbelow(10000); threshold=0; rarity='Common'
        for candidate,weight in CONFIG['rarities'].items():
            threshold+=weight
            if roll<threshold: rarity=candidate; break
        reward_id=case.definition_id.removesuffix('_case')+'_'+rarity.lower()
        case.consumed=True; case_key.consumed=True
        reward=mint(db,p.id,reward_id)
        response={'item':item_json(reward),'table_version':CONFIG['version'],'roll':roll}
        audit(db,p.id,'case_opened',case_id=case.id,key_id=case_key.id,**response)
        return remember(db,key,h,response)
@app.get('/market')
def market(request:Request,collection:str|None=None,rarity:str|None=None,max_price:int|None=None,weapon:str|None=None,finish:str|None=None,limit:int=Query(500,ge=1,le=500)):
    # Filters run in SQL before the cap, in one joined query (CLAUDE_AUDIT_0.3 M-7/M-8).
    rate(request,'market_read',120)
    query=select(Listing,Item).join(Item,Item.id==Listing.item_id).where(Listing.state=='active')
    if rarity: query=query.where(Item.rarity==rarity)
    if max_price is not None: query=query.where(Listing.price<=max_price)
    if collection or weapon or finish:
        matching=[d['id'] for d in DEFINITIONS.values() if (not collection or d['collection']==collection) and (not weapon or d.get('weapon')==weapon) and (not finish or d.get('finish')==finish)]
        query=query.where(Item.definition_id.in_(matching))
    with DBSession(engine) as db:
        rows=db.execute(query.order_by(Listing.price,Listing.id).limit(limit)).all()
        return {'listings':[dict(id=listing.id,seller_id=listing.seller_id,price=listing.price,item=item_json(item)) for listing,item in rows]}
@app.post('/market/list',status_code=201)
def market_list(body:ListItem,request:Request,authorization:Auth=None):
    rate(request,'economy')
    with transaction() as db:
        p=authenticated(db,authorization); item=owned(db,p.id,body.item_id)
        listing=Listing(item_id=item.id,seller_id=p.id,price=body.price)
        db.add(listing); db.flush(); item.reservation='market:'+listing.id
        audit(db,p.id,'listed',listing_id=listing.id,item_id=item.id,price=listing.price)
        return dict(id=listing.id,seller_id=p.id,price=listing.price,item=item_json(item))
@app.post('/market/{listing_id}/cancel')
def market_cancel(listing_id:UUID,request:Request,authorization:Auth=None):
    rate(request,'economy')
    with transaction() as db:
        p=authenticated(db,authorization); listing=db.get(Listing,str(listing_id))
        if not listing or listing.seller_id!=p.id: fail('Listing unavailable',404)
        if listing.state=='cancelled': return {'state':'cancelled'}
        if listing.state!='active': fail('Listing already settled')
        item=owned(db,p.id,listing.item_id,'market:'+listing.id)
        item.reservation=None; listing.state='cancelled'; audit(db,p.id,'listing_cancelled',listing_id=listing.id)
        return {'state':'cancelled'}
@app.post('/market/{listing_id}/buy')
def market_buy(listing_id:UUID,body:Idempotent,request:Request,authorization:Auth=None):
    rate(request,'economy')
    with transaction() as db:
        p=authenticated(db,authorization); key,h,old=replay(db,p.id,'buy:'+str(listing_id),body)
        if old: return old
        listing=db.get(Listing,str(listing_id))
        if not listing or listing.state!='active' or listing.seller_id==p.id: fail('Listing unavailable')
        seller=db.get(Player,listing.seller_id)
        if not seller.active: fail('Seller unavailable')
        item=owned(db,seller.id,listing.item_id,'market:'+listing.id)
        fee=listing.price*CONFIG['market_fee_basis_points']//10000
        credit(db,p,-listing.price,'market_purchase',listing.id); credit(db,seller,listing.price-fee,'market_sale',listing.id)
        unequip_transferred_item(db, item.id)
        item.owner_id=p.id; item.reservation=None; listing.buyer_id=p.id; listing.state='sold'
        audit(db,p.id,'market_settled',listing_id=listing.id,item_id=item.id,from_player=seller.id,to_player=p.id,fee=fee)
        return remember(db,key,h,dict(item=item_json(item),credits=p.credits,fee=fee))

def trade_json(t):
    from sqlalchemy.orm import object_session
    db = object_session(t)
    offer_items = {owner: [item_json(db.get(Item, item_id)) for item_id in ids] for owner, ids in t.offers.items()}
    names = {pid: db.get(Player, pid).display_name for pid in (t.a, t.b)}
    return dict(id=t.id,a=t.a,b=t.b,names=names,revision=t.revision,offers=t.offers,offer_items=offer_items,confirmations=t.confirmations,state=t.state)
def get_trade(db, player, trade_id):
    trade=db.get(Trade,str(trade_id))
    if not trade or player.id not in (trade.a,trade.b): fail('Trade unavailable',404)
    return trade
@app.get('/trades')
def trades(authorization:Auth=None):
    with DBSession(engine) as db:
        p=authenticated(db,authorization)
        return {'trades':[trade_json(t) for t in db.scalars(select(Trade).where(or_(Trade.a==p.id,Trade.b==p.id)))]}
@app.post('/trades',status_code=201)
def new_trade(body:NewTrade,request:Request,authorization:Auth=None):
    rate(request,'trade',20)
    with transaction() as db:
        p=authenticated(db,authorization); other=db.get(Player,str(body.partner_id))
        if not other or not other.active or other.id==p.id: fail('Partner unavailable',400)
        if p.last_trade and (now()-p.last_trade).total_seconds()<CONFIG['trade_cooldown_seconds']: fail('Trade cooldown',429)
        t=Trade(a=p.id,b=other.id,offers={p.id:[],other.id:[]},confirmations=[])
        p.last_trade=now(); db.add(t); db.flush(); audit(db,p.id,'trade_created',trade_id=t.id)
        return trade_json(t)
@app.put('/trades/{trade_id}/offer')
def offer(trade_id:UUID,body:Offer,request:Request,authorization:Auth=None):
    rate(request,'trade',20)
    with transaction() as db:
        p=authenticated(db,authorization); t=get_trade(db,p,trade_id)
        if t.state!='open' or t.revision!=body.revision: fail('Trade changed; refresh the offer')
        ids=[str(i) for i in body.item_ids]
        if len(set(ids))!=len(ids): fail('Duplicate items',400)
        reservation='trade:'+t.id
        # Validate before replacing; reservations are held until cancel/settle.
        for item_id in ids:
            item=db.get(Item,item_id)
            owned(db,p.id,item_id,reservation if item and item.reservation==reservation else None)
        for item_id in t.offers.get(p.id,[]): owned(db,p.id,item_id,reservation).reservation=None
        for item_id in ids: db.get(Item,item_id).reservation=reservation
        t.offers={**t.offers,p.id:ids}; t.confirmations=[]; t.revision+=1
        audit(db,p.id,'trade_revised',trade_id=t.id,revision=t.revision,offers=t.offers)
        return trade_json(t)
@app.post('/trades/{trade_id}/confirm')
def confirm(trade_id:UUID,body:Revision,request:Request,authorization:Auth=None):
    rate(request,'trade',20)
    with transaction() as db:
        p=authenticated(db,authorization); t=get_trade(db,p,trade_id)
        if t.revision!=body.revision: fail('Trade changed; inspect the current revision')
        if t.state=='completed': return trade_json(t)
        if t.state!='open': fail('Trade is closed')
        if not any(t.offers.values()): fail('An empty trade cannot be confirmed')
        for owner in (t.a,t.b):
            if not db.get(Player,owner).active: fail('Account unavailable')
            for item_id in t.offers.get(owner,[]): owned(db,owner,item_id,'trade:'+t.id)
        t.confirmations=list(set(t.confirmations+[p.id]))
        if set(t.confirmations)=={t.a,t.b}:
            for owner,receiver in ((t.a,t.b),(t.b,t.a)):
                for item_id in t.offers.get(owner,[]):
                    item=owned(db,owner,item_id,'trade:'+t.id)
                    unequip_transferred_item(db, item.id)
                    item.owner_id=receiver; item.reservation=None
                    audit(db,p.id,'item_traded',trade_id=t.id,item_id=item_id,from_player=owner,to_player=receiver)
            t.state='completed'
        return trade_json(t)
@app.post('/trades/{trade_id}/cancel')
def cancel_trade(trade_id:UUID,request:Request,authorization:Auth=None):
    rate(request,'trade',20)
    with transaction() as db:
        p=authenticated(db,authorization); t=get_trade(db,p,trade_id)
        if t.state=='cancelled': return trade_json(t)
        if t.state!='open': fail('Trade completed')
        for owner,items in t.offers.items():
            for item_id in items: owned(db,owner,item_id,'trade:'+t.id).reservation=None
        t.state='cancelled'; t.confirmations=[]; audit(db,p.id,'trade_cancelled',trade_id=t.id)
        return trade_json(t)

class MatchParticipant(Strict):
    player_id: UUID
    won: bool
    active_seconds: int = Field(ge=0,le=7200)
    objective_contributions: int = Field(ge=0,le=30)
    abandoned: bool = False
class MatchResult(Strict):
    match_id: UUID
    started_at: datetime
    ended_at: datetime
    participants: list[MatchParticipant] = Field(min_length=10,max_length=10)
    mode: str = Field(pattern='^ranked_5v5$')

@app.post('/server/matches')
def match_result(body:MatchResult,request:Request,x_server_key:Annotated[str|None,Header()]=None):
    rate(request,'server',120)
    trusted_server(x_server_key)
    if not body.started_at.tzinfo or not body.ended_at.tzinfo: fail('UTC timestamps required',400)
    seconds=(body.ended_at-body.started_at).total_seconds()
    if seconds<CONFIG['minimum_match_seconds'] or seconds>7200 or body.ended_at>now()+timedelta(seconds=30) or body.ended_at<now()-timedelta(minutes=15): fail('Ineligible match duration or timestamp',400)
    ids=[str(p.player_id) for p in body.participants]
    if len(set(ids))!=10 or sum(p.won for p in body.participants)!=5: fail('Requires ten unique humans and five winners',400)
    with transaction() as db:
        op_id='match:'+str(body.match_id); hashed=fingerprint(body.model_dump(mode='json')); old=db.get(Operation,op_id)
        if old:
            if old.request_hash!=hashed: fail('Match ID reused with changed results')
            return old.response
        day=body.ended_at.astimezone(timezone.utc).date().isoformat(); rewards=[]
        for result in body.participants:
            p=db.get(Player,str(result.player_id))
            if not p or not p.active: fail('Unknown or inactive match participant',400)
            if result.active_seconds>seconds: fail('Invalid activity duration',400)
            eligible=not result.abandoned and result.active_seconds/seconds>=CONFIG['minimum_active_fraction']
            # Active matches cannot overlap for the same account.
            prior=list(db.scalars(select(Reward).where(Reward.player_id==p.id,Reward.day>=(body.started_at-timedelta(days=1)).date().isoformat())))
            for r in prior:
                if datetime.fromisoformat(r.details['ended_at'])>body.started_at and datetime.fromisoformat(r.details['started_at'])<body.ended_at: fail('Overlapping match for account')
            paid=sum(1 for r in prior if r.day==day and r.details['credits']>0)
            amount=0; xp=0
            if eligible and paid<CONFIG['daily_reward_match_cap']:
                xp=CONFIG['xp_per_match']+CONFIG['xp_per_win']*result.won+CONFIG['xp_per_objective']*result.objective_contributions
                previous_level=level(p.xp); p.xp+=xp
                amount=CONFIG['match_completion']+CONFIG['match_win']*result.won+(CONFIG['daily_first'] if paid==0 else 0)+CONFIG['level_reward']*(level(p.xp)-previous_level)
                credit(db,p,amount,'verified_match',str(body.match_id))
            details={'credits':amount,'xp':xp,'won':result.won,'eligible':eligible,'started_at':body.started_at.isoformat(),'ended_at':body.ended_at.isoformat()}
            db.add(Reward(id=str(body.match_id)+':'+p.id,player_id=p.id,day=day,details=details)); rewards.append({'player_id':p.id,**details})
        response={'match_id':str(body.match_id),'rewards':rewards}
        audit(db,'trusted_server','match_rewards',**response)
        return remember(db,op_id,hashed,response)
@app.get('/history')
def history(authorization:Auth=None):
    with DBSession(engine) as db:
        p=authenticated(db,authorization)
        return {'ledger':[dict(id=r.id,amount=r.amount,balance_after=r.balance_after,reason=r.reason,reference=r.reference,created_at=r.created_at.isoformat()) for r in db.scalars(select(Ledger).where(Ledger.player_id==p.id).order_by(Ledger.created_at.desc()).limit(100))], 'matches':[r.details for r in db.scalars(select(Reward).where(Reward.player_id==p.id).order_by(cast(Reward.details['ended_at'].astext, DateTime(timezone=True)).desc()).limit(100))]}


class TicketRequest(Strict):
    server_id: str = Field(min_length=1, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')

class TicketConsume(TicketRequest):
    ticket: str = Field(min_length=32, max_length=128)

@app.post('/auth/game-ticket', status_code=201)
def game_ticket(body: TicketRequest, request: Request, authorization: Auth = None):
    rate(request, 'game_ticket', 30)
    if body.server_id != os.environ.get('SIGHTBREAK_SERVER_ID', 'local-relay'):
        fail('Unknown game server', 404)
    with transaction() as db:
        p = authenticated(db, authorization)
        token = secrets.token_urlsafe(32)
        expiry = now() + timedelta(seconds=60)
        db.add(GameTicket(ticket_hash=digest(token), session_hash=digest(authorization[7:]),
                          player_id=p.id, server_id=body.server_id, expires_at=expiry))
        audit(db, p.id, 'game_ticket_issued', server_id=body.server_id)
        return {'ticket': token, 'server_id': body.server_id, 'expires_at': expiry.isoformat()}

def valid_game_ticket(db, body: TicketConsume):
    ticket = db.get(GameTicket, digest(body.ticket))
    if not ticket or ticket.consumed_at is not None or ticket.expires_at <= now() or ticket.server_id != body.server_id:
        fail('Join ticket is expired, consumed or invalid', 401)
    session = db.get(Session, ticket.session_hash)
    if not session or session.expires_at <= now() or session.player_id != ticket.player_id:
        fail('Account session revoked or expired', 401)
    player = db.get(Player, ticket.player_id)
    if not player or not player.active:
        fail('Account unavailable', 403)
    return ticket, player

@app.post('/server/tickets/inspect')
def inspect_game_ticket(body: TicketConsume, request: Request,
                        x_server_key: Annotated[str | None, Header()] = None):
    # Trusted-server capacity preflight. It neither consumes nor extends a ticket.
    rate(request, 'server_ticket_inspect', 120)
    trusted_server(x_server_key, body.server_id)
    with DBSession(engine) as db:
        _, player = valid_game_ticket(db, body)
        return {'player_id': player.id, 'display_name': player.display_name}

@app.post('/server/tickets/consume')
def consume_game_ticket(body: TicketConsume, request: Request,
                        x_server_key: Annotated[str | None, Header()] = None):
    rate(request, 'server_ticket', 120)
    trusted_server(x_server_key, body.server_id)
    with transaction() as db:
        ticket, player = valid_game_ticket(db, body)
        ticket.consumed_at = now()
        audit(db, player.id, 'game_ticket_consumed', server_id=body.server_id)
        return {'player_id': player.id, 'display_name': player.display_name}


class EquipRequest(Strict):
    slot: str = Field(pattern=r'^rifle$')
    item_id: UUID | None

@app.get('/loadout')
def get_loadout(authorization: Auth = None):
    with DBSession(engine) as db:
        p = authenticated(db, authorization)
        return loadout_json(db, p)

@app.put('/loadout')
def equip_item(body: EquipRequest, request: Request, authorization: Auth = None):
    rate(request, 'economy')
    with transaction() as db:
        p = authenticated(db, authorization)
        current = db.get(Loadout, (p.id, body.slot))
        if body.item_id is None:
            if current is not None:
                db.delete(current)
        else:
            item = owned(db, p.id, body.item_id)
            definition = DEFINITIONS[item.definition_id]
            if definition['kind'] != 'weapon_skin' or definition.get('weapon') != body.slot:
                fail('Item is not compatible with this cosmetic slot', 400)
            if current is None:
                db.add(Loadout(player_id=p.id, slot=body.slot, item_id=item.id))
            else:
                current.item_id = item.id
        audit(db, p.id, 'loadout_changed', slot=body.slot,
              item_id=str(body.item_id) if body.item_id is not None else None)
        db.flush()
        return loadout_json(db, p)
