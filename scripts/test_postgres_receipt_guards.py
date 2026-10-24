"""Pure runner failure/privacy/ownership controls; all runtime entrypoints mocked."""
import argparse
import io
import json
import os
from pathlib import Path
import tempfile
import time
import traceback
from types import SimpleNamespace
import unittest
from unittest import mock

import test_postgres_receipt_recovery as campaign


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="receipt-source-controls-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.engine = self.root / "fake-engine"
        self.engine.write_bytes(b"source-only fake; never executed")
        self.args = argparse.Namespace(out=self.root / "out", godot=self.engine, component="market")
        self.run = campaign.Run(self.args)
        for target in ("subprocess.Popen", "socket.socket", "ThreadingHTTPServer", "http.client.HTTPConnection"):
            patch = mock.patch("test_postgres_receipt_recovery." + target, side_effect=AssertionError("runtime entrypoint forbidden in pure controls"))
            patch.start(); self.addCleanup(patch.stop)
        patch = mock.patch.dict("sys.modules", {"psycopg": SimpleNamespace(connect=mock.Mock(side_effect=AssertionError("PG forbidden")))})
        patch.start(); self.addCleanup(patch.stop)

    def test_dirty_or_production_changed_source_rejects(self):
        def outputs(status="", changed=""):
            def git(command, **kwargs):
                if command[1] == "diff": return changed
                if command[1] == "status": return status
                return "fixed-source-or-tree"
            return git
        for status, changed in (("?? unstaged", ""), ("", "backend/app.py"), ("", "game/project.godot"), ("", "server/worker.py")):
            with self.subTest(status=status, changed=changed), mock.patch.object(campaign.subprocess, "check_output", side_effect=outputs(status, changed)):
                with self.assertRaises(AssertionError): self.run.source()
        with mock.patch.object(campaign.subprocess, "check_output", side_effect=outputs("", "game/tests/new_probe.gd")):
            self.assertTrue(self.run.source()["production_equal_base"])

    def test_wrong_engine_rejects_before_any_command_or_service(self):
        with mock.patch.object(self.run, "source", return_value={"commit": "pure"}), mock.patch.object(self.run, "command") as command, mock.patch.object(self.run, "docker") as docker:
            with self.assertRaisesRegex(AssertionError, "engine bytes"): self.run.execute()
            command.assert_not_called(); docker.assert_not_called()

    def test_wrong_cached_image_rejects_before_volume_or_container(self):
        with mock.patch.object(self.run, "source", return_value={"commit": "pure"}), \
             mock.patch.object(campaign.hashlib, "sha256", return_value=SimpleNamespace(hexdigest=lambda: campaign.PINNED_GODOT_SHA256)), \
             mock.patch.object(self.run, "command", return_value=(campaign.PINNED_GODOT, 0)), \
             mock.patch.object(self.run, "docker", return_value=('"wrong-image"\n["postgres@sha256:wrong"]', 0)) as docker:
            with self.assertRaisesRegex(AssertionError, "cached PG image"): self.run.execute()
            self.assertEqual(len(docker.call_args_list), 2)
            self.assertIsNone(self.run.volume); self.assertIsNone(self.run.cid)

    def test_expired_work_deadline_still_allows_owned_cleanup(self):
        self.run.deadline = time.monotonic() - 100
        self.run.cid = "a" * 64
        with mock.patch.object(self.run, "selected_container", return_value={"id": self.run.cid}), \
             mock.patch.object(self.run, "docker", side_effect=[("", 0), ("", 1)]) as docker, \
             mock.patch.object(campaign.socket, "socket") as sockets:
            sockets.return_value.__enter__.return_value.connect_ex.return_value = 1
            self.run.cleanup()
            self.assertTrue(self.run.state["cleanup"]["pass"])
            self.assertGreater(self.run.deadline, time.monotonic())
            self.assertTrue(self.run.state["cleanup"]["ports"][str(self.run.journal_port)])
            self.assertEqual(len(docker.call_args_list), 2)

    def test_ownership_failure_prevents_destructive_command(self):
        self.run.cid = "a" * 64
        with mock.patch.object(self.run, "selected_container", side_effect=AssertionError("owner mismatch")), \
             mock.patch.object(self.run, "docker") as docker:
            with self.assertRaisesRegex(AssertionError, "owner mismatch"): self.run.cleanup()
            docker.assert_not_called()

    def test_volume_labels_and_exact_mount_required_before_use(self):
        self.run.volume = "owned-test-volume"
        valid = dict(Name=self.run.volume, Type="volume", Destination="/var/lib/postgresql/data", RW=True)
        self.run.verify_mount(dict(mounts=[valid]))
        for field, poison in (("Name", "unowned"), ("Type", "bind"), ("Destination", "/other"), ("RW", False)):
            with self.subTest(field=field), self.assertRaisesRegex(AssertionError, "mount"):
                self.run.verify_mount(dict(mounts=[dict(valid, **{field: poison})]))
        with self.assertRaisesRegex(AssertionError, "mount"): self.run.verify_mount(dict(mounts=[valid, valid]))
        for labels in ({}, {campaign.LABEL: "wrong", "io.sightbreak.owner": campaign.OWNER}):
            raw = json.dumps(self.run.volume) + "\n" + json.dumps(labels)
            with mock.patch.object(self.run, "docker", return_value=(raw, 0)) as docker:
                with self.assertRaisesRegex(AssertionError, "volume ownership"): self.run.selected_volume("pure-volume")
                self.assertEqual(docker.call_args.args[1][0:2], ["volume", "inspect"])

    def test_expired_deadline_blocks_all_new_runtime_entrypoints(self):
        self.run.deadline = time.monotonic() - 1
        for name, args in (("start_process", ("pure", [], {})), ("start_proxy", ("pure",)),
                           ("sql_identity", ("pure",)), ("sql_snapshot", ("pure",)),
                           ("command", ("pure", ["must-not-start"]))):
            with self.subTest(name=name), self.assertRaisesRegex(AssertionError, "240-second"):
                getattr(self.run, name)(*args)

    def test_sql_snapshot_rejects_initial_identity_postmaster_and_role_replacement(self):
        self.run.pg_identity = dict(system_identifier="owned-cluster", postmaster_started="2026-10-22 07:00:00+00")
        observed = dict(database=self.run.db, role=self.run.role, system_identifier="owned-cluster", postmaster_started="2026-10-22T07:00:00+00:00")
        for field, poison in (("postmaster_started", "2026-10-22T07:00:01+00:00"), ("role", "other-role"), ("system_identifier", "other-cluster")):
            with self.subTest(field=field):
                connect = mock.MagicMock()
                connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = [dict(observed, **{field: poison})]
                with mock.patch.dict("sys.modules", {"psycopg": SimpleNamespace(connect=connect)}), \
                     mock.patch.object(campaign, "verify_sql_witness"):
                    with self.assertRaisesRegex(AssertionError, "snapshot identity"): self.run.sql_snapshot("pure")
        connect = mock.MagicMock()
        connect.return_value.__enter__.return_value.execute.return_value.fetchone.return_value = [observed]
        with mock.patch.dict("sys.modules", {"psycopg": SimpleNamespace(connect=connect)}), \
             mock.patch.object(campaign, "verify_sql_witness"):
            self.assertEqual(self.run.sql_snapshot("pure-format-equivalence")["postmaster_started"], observed["postmaster_started"])

    def test_secret_attempt_is_redacted_and_recorded_as_failure(self):
        password, token = "synthetic-password-value-123", "synthetic-token-value-456"
        self.run.add_secret(password); self.run.add_secret(token)
        self.run.dump("unexpected.json", dict(error="password " + password, authorization="Bearer " + token))
        raw = (self.run.out / "unexpected.json").read_text()
        self.assertNotIn(password, raw); self.assertNotIn(token, raw)
        self.assertTrue(self.run.leaks)

    def handler(self, response=None, failure=None):
        handler = object.__new__(self.run.proxy_handler("pure-origin"))
        body = json.dumps(dict(username="synthetic", password="never-save-auth-body")).encode()
        handler.command, handler.path = "POST", "/auth/login"
        handler.headers = {"Content-Length": str(len(body)), "Authorization": "Bearer never-save-header"}
        handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
        handler.connection = mock.Mock()
        handler.send_response = mock.Mock(); handler.send_header = mock.Mock(); handler.end_headers = mock.Mock()
        backend = mock.Mock()
        backend.status = 200
        backend.read.side_effect = failure
        backend.read.return_value = json.dumps(response or dict(detail="refused")).encode()
        backend.getheader.return_value = "application/json"
        connection = mock.Mock(); connection.getresponse.return_value = backend
        return handler, connection

    def test_every_wrong_route_mutation_is_observed_before_upstream_even_on_failure(self):
        for method, path, body in (("POST", "/market/other/buy", b'{"idempotency_key":"original-key"}'),
                                   ("POST", "/store/buy", b'{"idempotency_key":"other-key"}'),
                                   ("PUT", "/loadout", b'{}'), ("PATCH", "/other", b'not-json'),
                                   ("DELETE", "/other", b'{}')):
            with self.subTest(method=method, path=path):
                handler, connection = self.handler()
                handler.command, handler.path = method, path
                handler.headers, handler.rfile = {"Content-Length": str(len(body))}, io.BytesIO(body)
                connection.getresponse.return_value.status = 409
                previous = len(self.run.mutation_attempts)
                def assert_before_dispatch(*args, **kwargs):
                    self.assertEqual(len(self.run.mutation_attempts), previous + 1)
                    event = self.run.events[-1]
                    self.assertEqual(event["phase"], "mutation_attempt")
                    self.assertEqual((event["method"], event["path"], event["raw_body_hex"]), (method, path, body.hex()))
                connection.request.side_effect = assert_before_dispatch
                with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection): handler.forward()
                self.assertEqual(len(self.run.mutation_attempts), previous + 1)
                self.assertFalse(self.run.market_requests)
        handler, connection = self.handler()
        handler.path = "/store/buy"
        connection.request.side_effect = RuntimeError("refused upstream")
        with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection): handler.forward()
        self.assertEqual(self.run.events[-1]["phase"], "proxy_failure")
        self.assertEqual(self.run.events[-2]["phase"], "mutation_attempt")

    def test_invalid_or_expired_mutation_still_counted_without_upstream_dispatch(self):
        for condition in ("route", "length", "deadline"):
            with self.subTest(condition=condition):
                handler, _ = self.handler()
                handler.path = "//refused" if condition == "route" else "/store/buy"
                if condition == "length": handler.headers["Content-Length"] = "99999"
                if condition == "deadline": self.run.deadline = time.monotonic() - 1
                previous = len(self.run.mutation_attempts)
                handler.forward()
                self.assertEqual(len(self.run.mutation_attempts), previous + 1)
                self.assertFalse(self.run.mutation_attempts[-1]["body_complete"])
                self.assertEqual(self.run.events[-2]["phase"], "mutation_attempt")
                self.assertEqual(self.run.events[-1]["phase"], "proxy_failure")

    def test_mutation_body_credential_redacted_before_hex_encoding_and_privacy_fails(self):
        secret = "synthetic-mutation-secret"
        self.run.add_secret(secret)
        handler, connection = self.handler()
        body = json.dumps(dict(idempotency_key="key", unexpected=secret)).encode()
        handler.path, handler.rfile = "/store/buy", io.BytesIO(body)
        handler.headers = {"Content-Length": str(len(body))}
        with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection): handler.forward()
        raw = (self.run.out / "timeline.jsonl").read_text()
        self.assertNotIn(secret, raw); self.assertNotIn(secret.encode().hex(), raw)
        self.assertTrue(self.run.leaks)
        self.assertTrue(self.run.mutation_attempts[-1]["credential_redacted"])

    def test_auth_response_and_header_never_enter_retained_proxy_log(self):
        token = "backend-generated-token-must-stay-memory-only"
        handler, connection = self.handler(dict(token=token, player_id="synthetic-account"))
        with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection): handler.forward()
        raw = (self.run.out / "timeline.jsonl").read_text()
        for secret in (token, "never-save-auth-body", "never-save-header"):
            self.assertNotIn(secret, raw)
        self.assertEqual(self.run.sessions["setup"], token)
        self.assertEqual(json.loads(handler.wfile.getvalue())["token"], token)
        self.assertFalse(self.run.leaks)

    def test_auth_failure_does_not_log_unknown_reply_or_exception_contents(self):
        unknown = "unknown-auth-response-secret-not-yet-parsed"
        handler, connection = self.handler(failure=RuntimeError(unknown))
        with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection): handler.forward()
        raw = (self.run.out / "timeline.jsonl").read_text()
        self.assertNotIn(unknown, raw)
        self.assertIn("authentication details withheld", raw)
        self.assertEqual(self.run.events[-1]["phase"], "proxy_failure")

    def test_direct_auth_failure_suppresses_raw_exception_context(self):
        unknown = "unknown-auth-exception-secret"
        for phase in ("construction", "read", "close"):
            with self.subTest(phase=phase):
                connection = mock.Mock()
                connection.getresponse.return_value.status = 401
                connection.getresponse.return_value.read.return_value = b'{"detail":"refused"}'
                if phase == "close": connection.close.side_effect = RuntimeError(unknown)
                if phase == "read": connection.getresponse.return_value.read.side_effect = RuntimeError(unknown)
                with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection,
                                       side_effect=RuntimeError(unknown) if phase == "construction" else None):
                    try: self.run.request("/auth/login", dict(username="x", password="synthetic"))
                    except RuntimeError:
                        output = traceback.format_exc()
                self.assertNotIn(unknown, output)

    def test_timeout_retains_sanitized_output_argv_pid_and_reaps_owned_command(self):
        secret = "synthetic-command-failure-secret"
        self.run.add_secret(secret)
        process = mock.Mock(pid=999999, returncode=-9)
        process.poll.return_value = None
        process.communicate.side_effect = [campaign.subprocess.TimeoutExpired(["pure-command"], 1), ("failure " + secret, None)]
        with mock.patch.object(campaign.subprocess, "Popen", return_value=process), mock.patch.object(campaign.os, "killpg") as kill:
            with self.assertRaises(campaign.subprocess.TimeoutExpired): self.run.command("timeout", ["pure-command"])
            kill.assert_called_once_with(999999, campaign.signal.SIGKILL)
        self.assertNotIn(secret, (self.run.out / "timeout.log").read_text())
        self.assertEqual(self.run.state["steps"][-1]["argv"], ["pure-command"])
        self.assertEqual(self.run.state["steps"][-1]["failure_type"], "TimeoutExpired")
        self.assertEqual(process.communicate.call_count, 2)

    def test_docker_selectors_removed_and_explicit_local_socket_preserved(self):
        with mock.patch.dict(os.environ, {"DOCKER_HOST": "tcp://untrusted:2375", "DOCKER_CONTEXT": "untrusted", "DOCKER_CONFIG": "/tmp/preserve-selector", "PGHOSTADDR": "untrusted", "PGSERVICE": "saved"}):
            args = argparse.Namespace(out=self.root / "selector-out", godot=self.engine, component="market")
            run = campaign.Run(args)
        self.assertNotIn("DOCKER_HOST", run.env); self.assertNotIn("DOCKER_CONTEXT", run.env)
        self.assertEqual(run.env["DOCKER_CONFIG"], "/tmp/preserve-selector")
        self.assertNotIn("PGHOSTADDR", run.env); self.assertNotIn("PGSERVICE", run.env)
        with mock.patch.object(run, "command", return_value=("", 0)) as command:
            run.docker("pure", ["info"])
            self.assertEqual(command.call_args.args[1][:2], ["docker", "--host=unix:///var/run/docker.sock"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
