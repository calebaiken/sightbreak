"""Credential-free PostgreSQL market observations and independent value oracle.

No runtime, database or native process starts when this module is imported.
This oracle checks retained production records; pure tests are not PG proof.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json

IDENTITY_SQL = """SELECT current_database(), current_user, version(),
inet_server_addr()::text, inet_server_port(), pg_postmaster_start_time()::text,
(SELECT system_identifier::text FROM pg_control_system())"""

# One statement supplies one consistent business snapshot. Session/password
# storage and request headers are deliberately outside this selected-field SQL.
BUSINESS_SQL = """SELECT jsonb_build_object(
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
 ))"""


def fingerprint(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def require(value: bool, message: str) -> None:
    if not value:
        raise AssertionError(message)


def verify_market_fixture(before: dict, spec: dict) -> None:
    """Fail before the original mutation if the declared synthetic fixture differs."""
    require(before["database"].endswith("_test") and before["schema_versions"] == [1, 2, 3, 4], "fixture DB/schema mismatch")
    a = before["business"]
    buyer, seller, outsider = spec["buyer"], spec["seller"], spec["outsider"]
    require(len({buyer, seller, outsider}) == 3, "fixture accounts overlap")
    require(spec["price"] == 400 and spec["fee"] == 12, "undeclared fixture price or fee")
    players = {p["id"]: p for p in a["players"]}
    require(set(players) == {buyer, seller, outsider}, "unexpected accounts")
    require({p: players[p]["credits"] for p in players} == {buyer: 1000, seller: 100, outsider: 0}, "wrong seed balances")
    require(all(p["xp"] == 0 and p["active"] is True for p in players.values()), "fixture XP/account state changed")
    require(len(a["items"]) == len(a["listings"]) == 1 and not a["operations"], "fixture already has effects")
    item, listing = a["items"][0], a["listings"][0]
    require(item["id"] == spec["item"] and item["owner_id"] == seller and item["consumed"] is False, "wrong fixture item")
    require(item["reservation"] == "market:" + spec["listing"], "fixture item not reserved")
    require(listing["id"] == spec["listing"] and listing["item_id"] == item["id"] and listing["seller_id"] == seller,
            "wrong fixture listing")
    require(listing["price"] == 400 and listing["state"] == "active" and listing["buyer_id"] is None, "wrong listing state")
    require(a["loadouts"] == [{"player_id": seller, "slot": "rifle", "item_id": item["id"]}], "fixture loadout absent")
    require(not a["rewards"] and a["game_ticket_count"] == 0, "fixture includes match value")
    seeds = {(r["player_id"], r["amount"], r["balance_after"], r["reason"]) for r in a["ledger"]}
    require(len(a["ledger"]) == 2 and seeds == {(buyer, 1000, 1000, "fictional_test_fixture"),
                                               (seller, 100, 100, "fictional_test_fixture")}, "seed ledger mismatch")


def verify_market(before: dict, settled: dict, spec: dict, actual_response: dict) -> None:
    """Require the one declared market effect and no unexplained business rows."""
    verify_market_fixture(before, spec)
    require(before["database"] == settled["database"], "database changed")
    require(before["system_identifier"] == settled["system_identifier"], "cluster changed")
    require(all(before[k] == settled[k] for k in ("role", "postmaster_started")), "SQL owner/postmaster changed")
    require(before["schema_versions"] == settled["schema_versions"] == [1, 2, 3, 4], "schema mismatch")
    a, b = before["business"], settled["business"]
    buyer, seller, outsider = spec["buyer"], spec["seller"], spec["outsider"]
    item = a["items"][0]
    expected = deepcopy(a)
    for player in expected["players"]:
        player["credits"] = {buyer: 600, seller: 488, outsider: 0}[player["id"]]
    expected["items"][0].update(owner_id=buyer, reservation=None)
    expected["listings"][0].update(state="sold", buyer_id=buyer)
    expected["loadouts"] = []
    for table in ("players", "items", "listings", "loadouts", "rewards", "game_ticket_count"):
        require(b[table] == expected[table], "unexpected " + table + " effect")
    before_ledger = {r["id"]: r for r in a["ledger"]}
    after_ledger = {r["id"]: r for r in b["ledger"]}
    require(len(after_ledger) == len(b["ledger"]) == 4 and all(after_ledger.get(k) == v for k, v in before_ledger.items()),
            "old ledger changed or duplicate ledger")
    new_ledger = [r for k, r in after_ledger.items() if k not in before_ledger]
    effects = {(r["player_id"], r["amount"], r["balance_after"], r["reason"], r["reference"]) for r in new_ledger}
    require(len(new_ledger) == 2 and effects == {(buyer, -400, 600, "market_purchase", spec["listing"]),
                                               (seller, 388, 488, "market_sale", spec["listing"])}, "purchase ledger mismatch")
    require(sum(r["amount"] for r in new_ledger) == -12, "fee conservation mismatch")
    payload = {"idempotency_key": spec["key"], "expected_price": 400}
    require(len(b["operations"]) == 1, "duplicate or missing operation")
    operation = b["operations"][0]
    require(operation["id"] == buyer + ":buy:" + spec["listing"] + ":" + spec["key"], "operation not bound to original buyer/route/key")
    require(operation["request_hash"] == fingerprint(payload), "operation request hash changed")
    require(operation["response"] == actual_response and actual_response["item"]["id"] == item["id"]
            and actual_response["credits"] == 600 and actual_response["fee"] == 12, "response not original settlement")
    old_audit = {r["id"]: r for r in a["audit"]}
    new_audit = {r["id"]: r for r in b["audit"]}
    require(len(new_audit) == len(b["audit"]) == len(old_audit) + 1 and all(new_audit.get(k) == v for k, v in old_audit.items()),
            "unexpected audit history change")
    audit = next(r for k, r in new_audit.items() if k not in old_audit)
    require(audit["actor"] == buyer and audit["action"] == "market_settled", "missing market audit")
    require(audit["details"] == {"listing_id": spec["listing"], "item_id": item["id"], "from_player": seller,
                                 "to_player": buyer, "fee": 12}, "market audit details changed")


def verify_unchanged(reference: dict, observed: dict) -> None:
    require(reference["business"] == observed["business"], "replay/control changed business state")
    require(reference["database"] == observed["database"] and reference["system_identifier"] == observed["system_identifier"],
            "observation identity changed")
    require(reference["schema_versions"] == observed["schema_versions"] == [1, 2, 3, 4], "schema changed during replay")
    require(all(reference[k] == observed[k] for k in ("role", "postmaster_started")), "SQL owner/postmaster changed")


def verify_sql_witness(snapshot: dict, phase: str, after_event: dict | None = None) -> None:
    """Reject an old/deduplicated query, including one before final native refresh."""
    require(snapshot["phase"] == phase and isinstance(snapshot["query_id"], str) and bool(snapshot["query_id"]),
            "SQL witness phase/query identity missing")
    start, end = snapshot["requested_monotonic_ns"], snapshot["completed_monotonic_ns"]
    wall_start, wall_end = snapshot["requested_wall_ns"], snapshot["completed_wall_ns"]
    require(start < end and wall_start < wall_end, "SQL request completion missing")
    stamp = datetime.fromisoformat(snapshot["sql_clock"])
    require(stamp.tzinfo is not None, "SQL clock lacks timezone")
    elapsed = stamp.astimezone(timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)
    sql_wall = (elapsed.days * 86400 + elapsed.seconds) * 1000000000 + elapsed.microseconds * 1000
    require(wall_start <= sql_wall <= wall_end, "actual SQL clock outside the owned local query interval")
    if after_event is not None:
        require(start > after_event["monotonic_ns"] and wall_start > after_event["wall_ns"],
                "SQL query was not requested after the required event")


def verify_order(events: list[dict], phases: list[str]) -> None:
    positions = []
    for phase in phases:
        matching = [e for e in events if e["phase"] == phase]
        require(len(matching) == 1, "missing/duplicate event: " + phase)
        positions.append(matching[0])
    for previous, current in zip(positions, positions[1:]):
        require(previous["monotonic_ns"] < current["monotonic_ns"] and previous["wall_ns"] < current["wall_ns"],
                "event order mismatch")
