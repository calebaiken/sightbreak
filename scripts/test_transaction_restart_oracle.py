#!/usr/bin/env python3
"""Pure adversarial checks of the receipt campaign's acceptance predicates."""
from copy import deepcopy
import unittest

from validate_transaction_restart import candidate_case_passes, candidate_lifecycle_passes, native_error


def valid_case():
    return dict(kind="market", boundary="recovery_kill", recovered=True, mutation_count=1,
                total_debit=10000000, receipt_reused=True, requests=[{"idempotency_key": "original"}],
                route_and_bytes_reused=True, authority_result_matches=True, credential_persisted=False,
                journal_before_kill=True, journal_after_recovery=False, retained_rejection=True,
                late_order_verified=True)


def valid_lifecycle():
    call = dict(path="/store/buy", method=2, payload={"idempotency_key": "original", "definition_id": "key"})
    return {"retry": {"pending_after_lost_response": True, "retry_status": 409,
                      "pending_after_rejected_retry": True, "journal_after_rejected_retry": True,
                      "calls": [deepcopy(call), deepcopy(call)]},
            "logout": {"pending_after_logout": True, "token_cleared": True, "account_cleared": True,
                       "pending_after_recreation": True, "pending_after_confirmation": False,
                       "calls": [deepcopy(call)], "result": {"item": {"id": "fixture-server-confirmed-item"}},
                       "account": {"credits": 0, "xp": 0}}}


class OracleTests(unittest.TestCase):
    def test_complete_routes_and_boundaries(self):
        for kind in ("store", "case", "market"):
            for boundary in ("before_commit", "after_commit", "late_commit", "recovery_kill"):
                with self.subTest(kind=kind, boundary=boundary):
                    row = valid_case()
                    row.update(kind=kind, boundary=boundary, total_debit=10000000 if kind == "market" else 100)
                    self.assertTrue(candidate_case_passes(row))

    def test_individual_missing_evidence_rejects(self):
        poison = dict(kind="uncovered", boundary="uncovered", recovered=False, mutation_count=2,
                      total_debit=9999999, receipt_reused=False, requests=[], route_and_bytes_reused=False,
                      authority_result_matches=False, credential_persisted=True, journal_before_kill=False,
                      journal_after_recovery=True, retained_rejection=False, late_order_verified=False)
        for field, value in poison.items():
            with self.subTest(field=field):
                row = valid_case()
                row[field] = value
                self.assertFalse(candidate_case_passes(row))
                row.pop(field)
                self.assertFalse(candidate_case_passes(row))

    def test_complete_lifecycle(self):
        self.assertTrue(candidate_lifecycle_passes(valid_lifecycle()))

    def test_logout_and_retry_evidence_required(self):
        result = valid_lifecycle()
        for section, fields in (("retry", ("pending_after_lost_response", "pending_after_rejected_retry", "journal_after_rejected_retry")),
                                ("logout", ("pending_after_logout", "token_cleared", "account_cleared", "pending_after_recreation"))):
            for field in fields:
                with self.subTest(section=section, field=field):
                    row = deepcopy(result)
                    row[section][field] = False
                    self.assertFalse(candidate_lifecycle_passes(row))

    def test_changed_retry_receipt_or_missing_call_rejects(self):
        row = valid_lifecycle()
        row["retry"]["calls"][1]["payload"]["idempotency_key"] = "changed"
        self.assertFalse(candidate_lifecycle_passes(row))
        row = valid_lifecycle()
        row["retry"]["calls"].pop()
        self.assertFalse(candidate_lifecycle_passes(row))

    def test_no_confirmation_or_locally_invented_balance_rejects(self):
        for change in ({"pending_after_confirmation": True}, {"account": {"credits": 999}},
                       {"result": {"item": {"id": "wrong-item"}}}, {"calls": []}):
            with self.subTest(change=change):
                row = valid_lifecycle()
                row["logout"].update(change)
                self.assertFalse(candidate_lifecycle_passes(row))

    def test_native_errors_on_either_output_stream_reject(self):
        self.assertFalse(native_error("Godot Engine 4.7.2\nRECEIPT_PROBE {}\n"))
        for error in ("SCRIPT ERROR: Invalid call", "ERROR: Parse failed", "Parse Error: bad syntax"):
            with self.subTest(error=error):
                self.assertTrue(native_error("ordinary stdout\n" + error))


if __name__ == "__main__":
    unittest.main(verbosity=2)
