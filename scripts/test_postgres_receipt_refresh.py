"""Pure refresh controls. No native, subprocess, socket, API or database runs."""
import argparse
from contextlib import ExitStack
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest import mock

import postgres_receipt_oracle as oracle
import test_postgres_receipt_recovery as campaign

BASELINE = "ad6cdc20db2a2f3ac179ba3cf3bed502620b6171"
ARCHIVE_SHA256 = "9e3eb7d7a2cb4ebdad8c94b0e0f59b25cc40b6d252074926311213630960d793"


class RefreshTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="receipt-refresh-pure-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.engine = self.root / "fake-engine"
        self.engine.write_bytes(b"never executed")
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        forbidden = mock.Mock(side_effect=AssertionError("runtime entrypoint forbidden"))
        for target in ("subprocess.Popen", "subprocess.run", "subprocess.check_output",
                       "http.client.HTTPConnection", "ThreadingHTTPServer", "socket.socket", "os.killpg"):
            self.stack.enter_context(mock.patch("test_postgres_receipt_recovery." + target, forbidden))
        self.stack.enter_context(mock.patch.dict(sys.modules, {"psycopg": SimpleNamespace(connect=forbidden)}))

    def run_object(self, module=campaign):
        return module.Run(argparse.Namespace(out=self.root / ("out-" + str(len(list(self.root.iterdir())))),
                                              godot=self.engine, component="market"))

    def execute_fixture(self, module, mode):
        """Execute the actual orchestration, replacing only runtime boundaries.

        Settlement/SQL predicates are mocked because this fixture tests the
        refresh acceptance boundary, not database economics. All actual process,
        HTTP, socket and database entrypoints are forbidden above.
        """
        run = self.run_object(module)
        calls = []
        item_id = "original-item"
        account = dict(id="buyer", credits=600, xp=0)
        inventory = [dict(id=item_id)]
        result = dict(result={"ok": True}, account=account, inventory=inventory,
                      pending_before=True, pending_after=False)
        journal = run.out / "client/pending.json"
        first = None

        def request(path, payload=None, token=None, method=None):
            if path == "/auth/register":
                role = next(role for role in ("seller", "buyer", "outsider") if role in payload["username"])
                return 201, dict(player_id=role, token="token-" + role)
            if path == "/me": return 200, dict(credits=0, xp=0)
            if path == "/inventory": return 200, dict(items=[])
            if path == "/loadout": return 200, {}
            if path == "/market/list": return 201, dict(id="listing")
            if path == run.spec["path"]: return 409, {}
            raise AssertionError("unexpected mocked request: " + path)

        def snapshot(phase):
            calls.append("sql:" + phase)
            value = {"phase": phase}
            run.sql_rows[phase] = value
            return value

        def read(path, *, phase="final_recovery", origin="origin1", status=200):
            response = account if path == "/me" else dict(items=inventory)
            # Real ingress timestamps precede the successful response observation.
            with run.lock:
                requested = dict(requested_monotonic_ns=module.time.monotonic_ns(),
                                 requested_wall_ns=module.time.time_ns())
            return run.event("business_read", native_phase=phase, origin=origin,
                             method="GET", path=path, status=status, response=response, **requested)

        def native(phase, mode_arg, who, url, held=None):
            nonlocal first
            if phase in ("wrong_account", "wrong_origin"):
                return dict(pending_before=True, pending_after=True, result={"_error": "refused"})
            if phase == "post_clear_restart":
                return dict(pending_before=False, pending_after=False)
            index = {"original": 1, "first_recovery": 2, "final_recovery": 3}[phase]
            attempt = dict(method="POST", path=run.spec["path"], payload=dict(idempotency_key=run.spec["key"], expected_price=400),
                           raw_body_hex="same-original-body", origin="origin1", authorization_present=True)
            run.mutation_attempts.append(attempt)
            run.market_requests.append(attempt)
            run.responses[index] = result["result"]
            if first is None:
                first = json.dumps(dict(schema=1, transaction=dict(path=run.spec["path"],
                    payload=dict(idempotency_key=run.spec["key"], expected_price=400), method=2,
                    message="synthetic", owner="buyer", server=url))).encode()
                journal.parent.mkdir()
                journal.write_bytes(first)
            if held is not None:
                sql_phase = "settled" if held == 1 else "replay_held"
                run.event("market_" + str(index) + "_backend_200")
                snapshot(sql_phase)
                run.event(sql_phase + "_sql_retained")
                for suffix in ("alive_before_kill", "kill_requested", "kill_ack"):
                    run.event(phase + "_" + suffix)
                return first
            # These successful login reads match the final native values but
            # precede replay. This is the original false-acceptance condition.
            run.reads["final_recovery"] = {"/me": account, "/inventory": dict(items=inventory)}
            read("/me"); read("/inventory")
            run.event("market_3_response_forwarded", native_phase="final_recovery", origin="origin1")
            if mode != "stale":
                for path in ("/me", "/inventory"):
                    if mode == "missing" and path == "/inventory": continue
                    read(path, phase="first_recovery" if mode == "wrong_phase" else "final_recovery",
                         origin="origin2" if mode == "wrong_origin" else "origin1",
                         status=503 if mode == "failed" else 200)
            journal.unlink()
            run.event("final_recovery_response_and_refresh_complete", observation=result)
            return result

        def docker(label, *args, **kwargs):
            if label == "image":
                return json.dumps("pinned-image") + "\n" + json.dumps(["postgres@sha256:" + module.IMAGE.rsplit("sha256:", 1)[1]]), 0
            if label == "postgres-start": return "a" * 64, 0
            return "", 0

        listener = mock.Mock()
        listener.getsockname.return_value = ("127.0.0.1", 12345)
        container = dict(image="pinned-image", ports={"5432/tcp": [dict(HostIp="127.0.0.1", HostPort="12346")]})
        db = mock.MagicMock()
        app = SimpleNamespace(credit=mock.Mock(), engine=mock.Mock(),
                              mint=mock.Mock(return_value=SimpleNamespace(id=item_id)),
                              transaction=mock.Mock(return_value=db))
        with ExitStack() as stack:
            stack.enter_context(mock.patch.dict(os.environ))
            stack.enter_context(mock.patch.object(sys, "path", list(sys.path)))
            stack.enter_context(mock.patch.dict(sys.modules, {"app": app, "models": SimpleNamespace(Player=object)}))
            stack.enter_context(mock.patch.object(module.hashlib, "sha256",
                return_value=SimpleNamespace(hexdigest=lambda: module.PINNED_GODOT_SHA256)))
            stack.enter_context(mock.patch.object(module.socket, "socket", return_value=listener))
            replacements = dict(source=lambda: {"commit": "pure"}, command=lambda *a, **kw: (module.PINNED_GODOT, 0),
                                docker=docker, selected_volume=lambda *a: {}, selected_container=lambda *a: container,
                                verify_mount=lambda *a: None, wait_for=lambda *a: None,
                                sql_identity=lambda *a: {"system_identifier": "pure"}, sql_snapshot=snapshot,
                                start_process=lambda *a, **kw: {"process": mock.Mock(poll=lambda: None)},
                                request=request, start_proxy=lambda name: "http://" + name,
                                observer=lambda phase: calls.append("observer:" + phase), native=native)
            for name, replacement in replacements.items():
                stack.enter_context(mock.patch.object(run, name, side_effect=replacement))
            for name in ("verify_market_fixture", "verify_market", "verify_unchanged", "verify_sql_witness"):
                stack.enter_context(mock.patch.object(module, name))
            try:
                run.execute()
                return run, calls, None
            except AssertionError as error:
                return run, calls, error

    def test_full_execute_rejects_failed_refresh_with_stale_matching_login_values(self):
        run, calls, error = self.execute_fixture(campaign, "stale")
        self.assertIsNotNone(error)
        self.assertIn("fresh final refresh read", str(error))
        self.assertNotIn("sql:after_final_refresh", calls)
        self.assertNotIn("observer:post_final_refresh", calls)
        self.assertNotEqual(run.state["status"], "focused_checks_passed")

    def test_full_execute_rejects_invalid_refresh_before_final_sql(self):
        for mode in ("missing", "failed", "wrong_phase", "wrong_origin"):
            with self.subTest(mode=mode):
                run, calls, error = self.execute_fixture(campaign, mode)
                self.assertIsNotNone(error)
                self.assertNotIn("sql:after_final_refresh", calls)
                self.assertNotIn("observer:post_final_refresh", calls)
                self.assertNotEqual(run.state["status"], "focused_checks_passed")

    def test_full_execute_accepts_fresh_response_bound_reads(self):
        run, calls, error = self.execute_fixture(campaign, "fresh")
        self.assertIsNone(error, str(error))
        self.assertEqual(run.state["status"], "focused_checks_passed")
        self.assertLess(calls.index("sql:after_final_refresh"), calls.index("observer:post_final_refresh"))

    @unittest.skipUnless(os.environ.get("SIGHTBREAK_REFRESH_BASELINE"), "set exact baseline source path; CI supplies git show")
    def test_exact_baseline_full_execute_false_accepts_stale_values(self):
        spec = importlib.util.spec_from_file_location("receipt_refresh_baseline", os.environ["SIGHTBREAK_REFRESH_BASELINE"])
        baseline = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(baseline)
        self.assertEqual(baseline.PINNED_GODOT_SHA256, campaign.PINNED_GODOT_SHA256)
        run, calls, error = self.execute_fixture(baseline, "stale")
        self.assertIsNone(error, str(error))
        self.assertEqual(run.state["status"], "focused_checks_passed")
        self.assertIn("sql:after_final_refresh", calls)
        self.assertIn("observer:post_final_refresh", calls)
        print("BASELINE " + BASELINE + " full mocked execute falsely accepts stale login reads")

    def timeline(self):
        observation = dict(account={"credits": 600}, inventory=[{"id": "item"}])
        def row(phase, ns, **fields): return dict(phase=phase, monotonic_ns=ns, wall_ns=1000 + ns, **fields)
        start = row("market_3_response_forwarded", 10, native_phase="final_recovery", origin="origin1")
        reads = [row("business_read", n, native_phase="final_recovery", origin="origin1", path=path, method="GET", status=200,
                     requested_monotonic_ns=n-1, requested_wall_ns=999+n, response=response)
                 for n, path, response in ((20, "/me", observation["account"]), (30, "/inventory", {"items": observation["inventory"]}))]
        return [start, *reads, row("final_recovery_response_and_refresh_complete", 40, observation=observation)], observation

    def test_oracle_rejects_inflight_stale_duplicate_mismatch_and_bad_order(self):
        for poison in ("ingress", "missing_ingress", "late", "duplicate", "value", "reverse", "marker_phase", "marker_origin"):
            with self.subTest(poison=poison):
                events, observation = self.timeline()
                if poison == "ingress": events[1]["requested_monotonic_ns"] = 5
                if poison == "missing_ingress": del events[1]["requested_wall_ns"]
                if poison == "late": events[2]["wall_ns"] = 1041
                if poison == "duplicate": events.insert(2, dict(events[1]))
                if poison == "value": observation = dict(observation, account={"credits": 999})
                if poison == "reverse": events[1], events[2] = events[2], events[1]
                if poison == "marker_phase": events[0]["native_phase"] = "original"
                if poison == "marker_origin": events[0]["origin"] = "origin2"
                # /me and /inventory may complete in either order. Reverse only
                # poisons retained marker ordering, not a valid parallel refresh.
                if poison == "reverse": events[0], events[-1] = events[-1], events[0]
                with self.assertRaises(AssertionError):
                    oracle.verify_final_market_refresh(events, observation)

    def test_retained_market_timeline_legacy_schema_is_explicit_and_unchanged(self):
        import hashlib
        archive = Path(campaign.ROOT) / "docs/reports/gauntlet/m3-postgres-receipt-recovery/market-receipt-evidence.tar.gz"
        original = archive.read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(), ARCHIVE_SHA256)
        with tarfile.open(fileobj=io.BytesIO(original), mode="r:gz") as evidence:
            members = evidence.getnames()
            timeline_name = next(n for n in members if n.endswith("runtime-r1/timeline.jsonl"))
            report_name = next(n for n in members if n.endswith("runtime-r1/report.json"))
            events = [json.loads(line) for line in evidence.extractfile(timeline_name).read().splitlines()]
            report = json.loads(evidence.extractfile(report_name).read())
        self.assertEqual(report["source_before"]["commit"], "882931dd7024c2b200a72b2a52017dd98b95ee6a")
        observation = next(e["observation"] for e in events if e["phase"] == "final_recovery_response_and_refresh_complete")
        selected = oracle.verify_final_market_refresh(events, observation, legacy_success_only_schema=True)
        self.assertEqual(selected["/me"]["credits"], 600)
        self.assertEqual(len(selected["/inventory"]["items"]), 1)
        with self.assertRaises(AssertionError):
            oracle.verify_final_market_refresh(events, observation)
        self.assertEqual(archive.read_bytes(), original)
        print("RETAINED 882931dd timeline accepted as original success-only schema; strict future schema rejects absent provenance")

    def handler(self, run, path, response, status=200):
        handler = object.__new__(run.proxy_handler("origin1"))
        handler.command, handler.path, handler.headers = "GET", path, {}
        handler.rfile, handler.wfile = io.BytesIO(), io.BytesIO()
        handler.send_response = mock.Mock(); handler.send_header = mock.Mock(); handler.end_headers = mock.Mock()
        backend = mock.Mock(status=status)
        backend.read.return_value = json.dumps(response).encode()
        backend.getheader.return_value = "application/json"
        connection = mock.Mock()
        connection.getresponse.return_value = backend
        return handler, connection

    def test_proxy_keeps_ingress_phase_when_upstream_crosses_phase_boundary(self):
        run = self.run_object()
        run.current_phase = "original"
        handler, connection = self.handler(run, "/me", {"credits": 600})
        connection.request.side_effect = lambda *a, **kw: setattr(run, "current_phase", "final_recovery")
        with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection):
            handler.forward()
        read = next(e for e in run.events if e["phase"] == "business_read")
        self.assertEqual(read["native_phase"], "original")
        self.assertEqual(read["status"], 200)
        self.assertLess(read["requested_monotonic_ns"], read["monotonic_ns"])
        self.assertNotIn("final_recovery", run.reads)

    def test_proxy_failed_write_does_not_publish_successful_read(self):
        run = self.run_object()
        handler, connection = self.handler(run, "/me", {"credits": 600})
        handler.wfile = mock.Mock(write=mock.Mock(side_effect=BrokenPipeError("closed")))
        with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection):
            handler.forward()
        self.assertFalse(any(e["phase"] == "business_read" for e in run.events))
        self.assertFalse(run.reads)
        self.assertEqual(run.events[-1]["phase"], "proxy_failure")

    def test_proxy_market_marker_precedes_concurrent_followup_ingress(self):
        run = self.run_object()
        run.current_phase = "final_recovery"
        run.spec = {"path": "/market/listing/buy"}
        # This represents final replay, after the original and first replay.
        run.market_requests = [{}, {}]
        market, market_connection = self.handler(run, run.spec["path"], {"ok": True})
        market.command = "POST"
        market.rfile = io.BytesIO(b"{}")
        market.headers = {"Content-Length": "2"}
        followup, read_connection = self.handler(run, "/me", {"credits": 600})
        writing = threading.Event()
        attempted_ingress = threading.Event()
        thread_errors = []
        def follow():
            attempted_ingress.set()
            try: followup.forward()
            except BaseException as error: thread_errors.append(error)
        def write(raw):
            writing.set()
            self.assertTrue(attempted_ingress.wait(2), "followup did not attempt ingress")
            return len(raw)
        market.wfile = mock.Mock(write=write)
        def read_dispatch(*a, **kw):
            self.assertTrue(any(e["phase"] == "market_3_response_forwarded" for e in run.events))
        read_connection.request.side_effect = read_dispatch
        def connection(*a, **kw):
            return read_connection if threading.current_thread().name == "refresh-followup" else market_connection
        with mock.patch.object(campaign.http.client, "HTTPConnection", side_effect=connection):
            thread = threading.Thread(target=lambda: (writing.wait(2), follow()), name="refresh-followup", daemon=True)
            thread.start()
            try: market.forward()
            finally: thread.join(3)
        self.assertFalse(thread.is_alive(), "proxy race fixture leaked thread")
        self.assertFalse(thread_errors)
        self.assertFalse(any(e["phase"] == "proxy_failure" for e in run.events))
        marker = next(e for e in run.events if e["phase"] == "market_3_response_forwarded")
        read = next(e for e in run.events if e["phase"] == "business_read")
        self.assertLess(marker["monotonic_ns"], read["requested_monotonic_ns"])
        self.assertLess(marker["wall_ns"], read["requested_wall_ns"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
