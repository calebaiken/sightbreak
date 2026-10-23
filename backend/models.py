"""PostgreSQL authoritative records. UUIDs are generated only by the service."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import String, Integer, BigInteger, Boolean, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

def uid(): return str(uuid4())
def now(): return datetime.now(timezone.utc)
class Base(DeclarativeBase): pass
class Player(Base):
    __tablename__ = 'players'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    username: Mapped[str] = mapped_column(String(32), unique=True)
    display_name: Mapped[str] = mapped_column(String(32))
    password_hash: Mapped[str] = mapped_column(String)
    credits: Mapped[int] = mapped_column(BigInteger, default=0)
    xp: Mapped[int] = mapped_column(BigInteger, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_trade: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    __table_args__ = (CheckConstraint('credits >= 0'), CheckConstraint('xp >= 0'))
class Session(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey('players.id'))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
class Ledger(Base):
    __tablename__ = 'ledger'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    player_id: Mapped[str] = mapped_column(ForeignKey('players.id'), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    balance_after: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(80))
    reference: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint('balance_after >= 0'),)
class Item(Base):
    __tablename__ = 'items'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    owner_id: Mapped[str] = mapped_column(ForeignKey('players.id'), index=True)
    definition_id: Mapped[str] = mapped_column(String(100))
    rarity: Mapped[str] = mapped_column(String(24))
    pattern_seed: Mapped[int] = mapped_column(BigInteger)
    wear: Mapped[int] = mapped_column(Integer)
    variant: Mapped[str] = mapped_column(String(24), default='standard')
    reservation: Mapped[str | None] = mapped_column(String(80), nullable=True)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    __table_args__ = (CheckConstraint('wear >= 0 AND wear <= 10000'),)
class Operation(Base):
    __tablename__ = 'operations'
    id: Mapped[str] = mapped_column(String(220), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    response: Mapped[dict] = mapped_column(JSONB)
class Audit(Base):
    __tablename__ = 'audit'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    actor: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Listing(Base):
    __tablename__ = 'listings'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    item_id: Mapped[str] = mapped_column(ForeignKey('items.id'))
    seller_id: Mapped[str] = mapped_column(ForeignKey('players.id'))
    buyer_id: Mapped[str | None] = mapped_column(ForeignKey('players.id'), nullable=True)
    price: Mapped[int] = mapped_column(BigInteger)
    state: Mapped[str] = mapped_column(String(16), default='active')
    __table_args__ = (CheckConstraint('price > 0'),)
class Trade(Base):
    __tablename__ = 'trades'
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    a: Mapped[str] = mapped_column(ForeignKey('players.id'))
    b: Mapped[str] = mapped_column(ForeignKey('players.id'))
    revision: Mapped[int] = mapped_column(Integer, default=0)
    offers: Mapped[dict] = mapped_column(JSONB, default=dict)
    confirmations: Mapped[list] = mapped_column(JSONB, default=list)
    state: Mapped[str] = mapped_column(String(16), default='open')
class Reward(Base):
    __tablename__ = 'rewards'
    id: Mapped[str] = mapped_column(String(100), primary_key=True)
    player_id: Mapped[str] = mapped_column(ForeignKey('players.id'), index=True)
    day: Mapped[str] = mapped_column(String(10), index=True)
    details: Mapped[dict] = mapped_column(JSONB)
class RateBucket(Base):
    __tablename__ = 'rate_buckets'
    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    count: Mapped[int] = mapped_column(Integer)

class GameTicket(Base):
    __tablename__ = 'game_tickets'
    ticket_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    session_hash: Mapped[str] = mapped_column(String(64))
    player_id: Mapped[str] = mapped_column(ForeignKey('players.id'), index=True)
    server_id: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

class Loadout(Base):
    __tablename__ = 'loadouts'
    player_id: Mapped[str] = mapped_column(ForeignKey('players.id'), primary_key=True)
    slot: Mapped[str] = mapped_column(String(24), primary_key=True)
    item_id: Mapped[str] = mapped_column(ForeignKey('items.id'), unique=True)
