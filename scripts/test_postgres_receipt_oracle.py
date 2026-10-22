"""Pure falsifiers of the market SQL oracle. No PG/native/API entrypoint runs."""
from copy import deepcopy
import unittest

from postgres_receipt_oracle import fingerprint, verify_market, verify_order, verify_sql_witness, verify_unchanged


def fixture():
    spec = dict(buyer="buyer", seller="seller", outsider="outsider", item="original-item",
                listing="original-listing", key="3c74ec8e-77c7-455d-8661-b43f2f29aead", price=400, fee=12)
    response = {"item": dict(id="original-item", definition_id="obsidian_rare", rarity="Rare", pattern_seed=314159,
                             wear=0.1234, variant="standard", acquired_at="2026-10-22T06:59:10+00:00",
                             collection="Obsidian", kind="weapon_skin", name="Obsidian / Carbon", reserved=False,
                             trade_eligible=True, marketplace_eligible=True), "credits": 600, "fee": 12}
    before = dict(database="owned_receipt_test", system_identifier="cluster-1", role="fixture-role",
                  postmaster_started="2026-10-22 06:59:00+00", schema_versions=[1, 2, 3, 4],
                  sql_clock="2026-10-22 07:00:00+00", business={
        "players": [dict(id=p, credits=c, xp=0, active=True) for p, c in (("buyer", 1000), ("seller", 100), ("outsider", 0))],
        "items": [dict(id="original-item", owner_id="seller", consumed=False, reservation="market:original-listing",
                       pattern_seed=314159, wear=1234, definition_id="obsidian_rare", rarity="Rare", variant="standard",
                       acquired_at="2026-10-22T06:59:10+00:00")],
        "listings": [dict(id="original-listing", item_id="original-item", seller_id="seller", buyer_id=None, price=400, state="active")],
        "ledger": [dict(id="seed-b", player_id="buyer", amount=1000, balance_after=1000, reason="fictional_test_fixture", reference="run"),
                   dict(id="seed-s", player_id="seller", amount=100, balance_after=100, reason="fictional_test_fixture", reference="run")],
        "operations": [], "audit": [dict(id="fixture", actor="seller", action="listed", details={})],
        "loadouts": [dict(player_id="seller", slot="rifle", item_id="original-item")], "rewards": [], "game_ticket_count": 0})
    settled = deepcopy(before)
    b = settled["business"]
    b["players"][0]["credits"] = 600
    b["players"][1]["credits"] = 488
    b["items"][0].update(owner_id="buyer", reservation=None)
    b["listings"][0].update(buyer_id="buyer", state="sold")
    b["loadouts"] = []
    b["ledger"].extend([dict(id="debit", player_id="buyer", amount=-400, balance_after=600, reason="market_purchase", reference="original-listing"),
                        dict(id="sale", player_id="seller", amount=388, balance_after=488, reason="market_sale", reference="original-listing")])
    b["operations"] = [dict(id="buyer:buy:original-listing:" + spec["key"],
                            request_hash=fingerprint(dict(idempotency_key=spec["key"], expected_price=400)), response=deepcopy(response))]
    b["audit"].append(dict(id="settled", actor="buyer", action="market_settled",
                           details=dict(listing_id="original-listing", item_id="original-item", from_player="seller", to_player="buyer", fee=12)))
    return before, settled, spec, response


class MarketOracleTests(unittest.TestCase):
    def test_declared_effect_and_repeat_observation(self):
        before, settled, spec, response = fixture()
        verify_market(before, settled, spec, response)
        verify_unchanged(settled, deepcopy(settled))

    def test_wallet_owner_metadata_listing_loadout_and_match_value_poison(self):
        paths = [("players", 0, "credits", 601), ("players", 1, "credits", 500),
                 ("players", 2, "credits", 1), ("players", 0, "xp", 1),
                 ("items", 0, "owner_id", "outsider"), ("items", 0, "pattern_seed", 2),
                 ("items", 0, "reservation", "still-reserved"), ("listings", 0, "state", "active"),
                 ("listings", 0, "buyer_id", "outsider")]
        for table, index, field, poison in paths:
            with self.subTest(table=table, field=field):
                before, settled, spec, response = fixture()
                settled["business"][table][index][field] = poison
                with self.assertRaises(AssertionError): verify_market(before, settled, spec, response)
        for table, poison in (("loadouts", [dict(player_id="seller", slot="rifle", item_id="original-item")]),
                              ("rewards", [dict(id="invented-match-value")]), ("game_ticket_count", 1)):
            with self.subTest(table=table):
                before, settled, spec, response = fixture()
                settled["business"][table] = poison
                with self.assertRaises(AssertionError): verify_market(before, settled, spec, response)

    def test_duplicate_missing_and_changed_ledger_rows_reject(self):
        for change in ("duplicate", "missing", "old_seed", "fee", "reference"):
            with self.subTest(change=change):
                before, settled, spec, response = fixture()
                rows = settled["business"]["ledger"]
                if change == "duplicate": rows.append(dict(rows[-1], id="extra-sale"))
                elif change == "missing": rows.pop()
                elif change == "old_seed": rows[0]["amount"] = 999
                elif change == "fee": rows[-1]["amount"] = 400
                else: rows[-1]["reference"] = "different-listing"
                with self.assertRaises(AssertionError): verify_market(before, settled, spec, response)

    def test_operation_key_hash_result_and_audit_poison(self):
        for change in ("duplicate_operation", "operation_id", "changed_price_hash", "wrong_result", "audit_fee", "extra_audit"):
            with self.subTest(change=change):
                before, settled, spec, response = fixture()
                b = settled["business"]
                if change == "duplicate_operation": b["operations"].append(deepcopy(b["operations"][0]))
                elif change == "operation_id": b["operations"][0]["id"] = "outsider:buy:original-listing:" + spec["key"]
                elif change == "changed_price_hash": b["operations"][0]["request_hash"] = fingerprint(dict(idempotency_key=spec["key"], expected_price=401))
                elif change == "wrong_result": b["operations"][0]["response"]["item"]["id"] = "other-item"
                elif change == "audit_fee": b["audit"][-1]["details"]["fee"] = 0
                else: b["audit"].append(dict(id="extra", actor="buyer", action="market_settled", details={}))
                with self.assertRaises(AssertionError): verify_market(before, settled, spec, response)

    def test_matched_poisoned_response_and_operation_metadata_rejects(self):
        changes = dict(pattern_seed=1, definition_id="other", rarity="Common", variant="other", wear=0.9999,
                       acquired_at="2026-10-22T06:59:11+00:00", reserved=True, trade_eligible=False,
                       marketplace_eligible=False, collection="other", kind="key", name="other")
        for field, poison in changes.items():
            with self.subTest(field=field):
                before, settled, spec, response = fixture()
                response["item"][field] = poison
                settled["business"]["operations"][0]["response"] = deepcopy(response)
                with self.assertRaises(AssertionError): verify_market(before, settled, spec, response)

    def test_wrong_cluster_database_schema_and_seed_reject(self):
        for field, poison in (("database", "shared_dev"), ("system_identifier", "other-cluster"),
                              ("role", "other-role"), ("postmaster_started", "restarted"), ("schema_versions", [1, 2, 3])):
            with self.subTest(field=field):
                before, settled, spec, response = fixture()
                settled[field] = poison
                with self.assertRaises(AssertionError): verify_market(before, settled, spec, response)
        before, settled, spec, response = fixture()
        before["business"]["players"][0]["credits"] = 1001
        with self.assertRaises(AssertionError): verify_market(before, settled, spec, response)

    def test_replay_business_change_rejects(self):
        _, settled, _, _ = fixture()
        for table in settled["business"]:
            with self.subTest(table=table):
                changed = deepcopy(settled)
                changed["business"][table] = (1 if table == "game_ticket_count" else
                                               [] if settled["business"][table] else [{"unwanted_row": True}])
                with self.assertRaises(AssertionError): verify_unchanged(settled, changed)

    def test_missing_duplicate_old_query_and_clock_disagreement_reject(self):
        phases = ["backend_200", "sql_retained", "native_alive", "kill_requested", "kill_ack", "final_refreshed", "final_sql_requested"]
        events = [dict(phase=p, monotonic_ns=i + 1, wall_ns=i + 11) for i, p in enumerate(phases)]
        verify_order(events, phases)
        for change in ("missing", "duplicate", "post_query_before_refresh", "wall_disagrees"):
            with self.subTest(change=change):
                poisoned = deepcopy(events)
                if change == "missing": poisoned.pop()
                elif change == "duplicate": poisoned.append(deepcopy(poisoned[-1]))
                elif change == "post_query_before_refresh": poisoned[-1]["monotonic_ns"] = 1
                else: poisoned[-1]["wall_ns"] = 1
                with self.assertRaises(AssertionError): verify_order(poisoned, phases)

    def test_sql_witness_must_be_fresh_complete_and_inside_real_query(self):
        event = dict(monotonic_ns=100, wall_ns=999998000)
        snapshot = dict(phase="post_final_refresh", query_id="unique-query", requested_monotonic_ns=101,
                        completed_monotonic_ns=103, requested_wall_ns=999999000, completed_wall_ns=1000001000,
                        sql_clock="1970-01-01 00:00:01+00")
        verify_sql_witness(snapshot, "post_final_refresh", event)
        for field, poison in (("phase", "pre_final"), ("query_id", ""), ("requested_monotonic_ns", 99),
                              ("requested_wall_ns", 999997000), ("completed_monotonic_ns", 100),
                              ("sql_clock", "1970-01-01 00:00:02+00"), ("sql_clock", "1970-01-01 00:00:01")):
            with self.subTest(field=field, poison=poison):
                changed = dict(snapshot)
                changed[field] = poison
                with self.assertRaises(AssertionError): verify_sql_witness(changed, "post_final_refresh", event)


if __name__ == "__main__":
    unittest.main(verbosity=2)
