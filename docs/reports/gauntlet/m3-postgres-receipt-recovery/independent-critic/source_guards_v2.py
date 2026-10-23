"""Independent no-service guard falsifiers for the production market harness.

Only imports and mocks are allowed here. No Docker, native process, socket,
HTTP service or PostgreSQL query is started by this file.
"""
import argparse
from datetime import datetime, timezone
import io
import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

candidate = Path(sys.argv.pop(1)).resolve()
sys.path.insert(0, str(candidate / "scripts"))
import test_postgres_receipt_recovery as campaign


class IndependentGuards(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="receipt-independent-v2-")
        self.addCleanup(self.directory.cleanup)
        args = argparse.Namespace(out=Path(self.directory.name) / "output", godot=Path(self.directory.name) / "unused", component="market")
        self.run = campaign.Run(args)

    def handler(self, path="/store/buy", method="POST", body=b'{"idempotency_key":"pure-key"}'):
        handler = object.__new__(self.run.proxy_handler("pure-origin"))
        handler.path, handler.command = path, method
        handler.headers = {"Content-Length": str(len(body))}
        handler.rfile, handler.wfile = io.BytesIO(body), io.BytesIO()
        handler.send_response = mock.Mock()
        handler.send_header = mock.Mock()
        handler.end_headers = mock.Mock()
        return handler

    def test_expired_deadline_blocks_native_process_creation(self):
        self.run.deadline = time.monotonic() - 1
        with mock.patch.object(campaign.subprocess, "Popen", side_effect=AssertionError("process constructor must remain unreachable")) as launch:
            with self.assertRaises(AssertionError):
                self.run.start_process("forbidden", ["unused"], {})
        launch.assert_not_called()

    def test_expired_deadline_blocks_proxy_listener_creation(self):
        self.run.deadline = time.monotonic() - 1
        with mock.patch.object(campaign, "ThreadingHTTPServer", side_effect=AssertionError("listener constructor must remain unreachable")) as launch:
            with self.assertRaises(AssertionError):
                self.run.start_proxy("forbidden")
        launch.assert_not_called()

    def test_expired_deadline_blocks_sql_connection(self):
        self.run.deadline = time.monotonic() - 1
        database = types.SimpleNamespace(connect=mock.Mock(side_effect=AssertionError("SQL connector must remain unreachable")))
        with mock.patch.dict(sys.modules, {"psycopg": database}):
            with self.assertRaises(AssertionError):
                self.run.sql_snapshot("forbidden")
        database.connect.assert_not_called()

    def test_expired_proxy_request_is_not_forwarded(self):
        self.run.deadline = time.monotonic() - 1
        handler = self.handler()
        with mock.patch.object(campaign.http.client, "HTTPConnection") as connection:
            handler.forward()
        connection.assert_not_called()
        self.assertTrue(any(e["phase"] == "proxy_failure" for e in self.run.events))

    def test_failed_upstream_mutation_is_retained_before_response(self):
        handler = self.handler(path="/market/wrong-listing/buy")
        self.run.spec = {"path": "/market/expected-listing/buy"}
        connection = mock.Mock()
        connection.getresponse.side_effect = OSError("pure upstream failure")
        with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection):
            handler.forward()
        connection.request.assert_called_once()
        rows = [e for e in self.run.events if e.get("path") == handler.path and e.get("raw_body_hex") == handler.rfile.getvalue().hex()]
        self.assertTrue(rows, "attempt vanished when the upstream response failed")
        self.assertTrue(any(e["phase"] == "proxy_failure" for e in self.run.events))

    def test_nonpost_mutation_attempt_is_retained(self):
        handler = self.handler(path="/loadout", method="PUT")
        response = mock.Mock(status=409)
        response.read.return_value = b'{"detail":"refused"}'
        response.getheader.return_value = "application/json"
        connection = mock.Mock()
        connection.getresponse.return_value = response
        with mock.patch.object(campaign.http.client, "HTTPConnection", return_value=connection):
            handler.forward()
        rows = [e for e in self.run.events if e.get("method") == "PUT" and e.get("path") == "/loadout"]
        self.assertTrue(rows, "PUT mutation omitted from evidence")

    def test_auth_connection_constructor_and_close_failures_hide_details(self):
        password = "independent-private-construction-secret"
        self.run.add_secret(password)
        for failure in ("construct", "request", "read", "close"):
            with self.subTest(failure=failure):
                connection = mock.Mock()
                response = mock.Mock(status=200)
                response.read.return_value = b'{}'
                connection.getresponse.return_value = response
                target = {"request": connection.request, "read": response.read, "close": connection.close}.get(failure)
                if target is not None:
                    target.side_effect = ValueError(password)
                with mock.patch.object(campaign.http.client, "HTTPConnection", side_effect=ValueError(password) if failure == "construct" else None,
                                       return_value=connection):
                    with self.assertRaises(RuntimeError) as caught:
                        self.run.request("/auth/login", {"password": password})
                self.assertNotIn(password, str(caught.exception))
                self.assertIsNone(caught.exception.__cause__)
                self.assertTrue(caught.exception.__suppress_context__)

    def test_initial_postmaster_identity_is_bound_to_snapshots(self):
        self.run.pg_identity = {"system_identifier": "same-cluster", "postmaster_started": "2026-10-22 07:00:00+00"}
        observed = {"database": self.run.db, "role": self.run.role, "system_identifier": "same-cluster",
                    "postmaster_started": "2026-10-22 07:01:00+00", "sql_clock": datetime.now(timezone.utc).isoformat()}
        database = mock.MagicMock()
        connection = database.connect.return_value.__enter__.return_value
        def execute(_sql):
            observed["sql_clock"] = datetime.now(timezone.utc).isoformat()
            return types.SimpleNamespace(fetchone=lambda: (observed,))
        connection.execute.side_effect = execute
        with mock.patch.dict(sys.modules, {"psycopg": database}):
            with self.assertRaises(AssertionError):
                self.run.sql_snapshot("before_original")

    def test_migration_requires_owned_volume_and_exact_mount(self):
        # Execute only the setup path with every external call replaced. Stop at
        # migrate, before the production API/bootstrap path can be reached.
        self.run.args.godot.write_bytes(b"pure unused binary")
        for poison in (None, "label", "mount_name", "mount_destination", "mount_readonly"):
            with self.subTest(poison=poison):
                migration = []
                def command(label, _argv, **_kwargs):
                    if label == "engine-version":
                        return campaign.PINNED_GODOT, 0
                    migration.append(label)
                    raise AssertionError("pure setup deliberately stops before migration")
                def docker(_label, argv, **_kwargs):
                    if argv[0] == "info":
                        return '"mock-local-daemon"\n"linux"\n"/mock-docker-root"', 0
                    if argv[:2] == ["image", "inspect"]:
                        return json.dumps("image-id") + "\n" + json.dumps(["postgres@sha256:" + campaign.IMAGE.rsplit("sha256:", 1)[1]]), 0
                    if argv[:2] == ["volume", "create"]:
                        return self.run.volume, 0
                    if argv[:2] == ["volume", "inspect"]:
                        labels = {campaign.LABEL: self.run.run, "io.sightbreak.owner": campaign.OWNER}
                        if poison == "label": labels[campaign.LABEL] = "someone-else"
                        return json.dumps(self.run.volume) + "\n" + json.dumps(labels), 0
                    if argv[0] == "run":
                        return "a" * 64, 0
                    if argv[0] == "inspect":
                        mount = {"Type": "volume", "Name": self.run.volume, "Destination": "/var/lib/postgresql/data", "RW": True}
                        if poison == "mount_name": mount["Name"] = "someone-else"
                        if poison == "mount_destination": mount["Destination"] = "/wrong-path"
                        if poison == "mount_readonly": mount["RW"] = False
                        fields = ["a" * 64, "/" + self.run.run, "image-id",
                                  {campaign.LABEL: self.run.run, "io.sightbreak.owner": campaign.OWNER},
                                  {"5432/tcp": [{"HostIp": "127.0.0.1", "HostPort": "54321"}]}, 100, [mount]]
                        return "\n".join(json.dumps(v) for v in fields), 0
                    raise AssertionError("unexpected mocked Docker path")
                database = mock.MagicMock()
                with mock.patch.object(self.run, "source", return_value={}), \
                     mock.patch.object(self.run, "command", side_effect=command), \
                     mock.patch.object(self.run, "docker", side_effect=docker), \
                     mock.patch.object(self.run, "sql_identity", return_value={}), \
                     mock.patch.object(campaign.hashlib, "sha256", return_value=types.SimpleNamespace(hexdigest=lambda: campaign.PINNED_GODOT_SHA256)), \
                     mock.patch.dict(sys.modules, {"psycopg": database}), \
                     mock.patch.object(campaign.subprocess, "Popen", side_effect=AssertionError("runtime forbidden")), \
                     mock.patch.object(campaign.socket, "socket", side_effect=AssertionError("runtime forbidden")):
                    with self.assertRaises(AssertionError):
                        self.run.execute()
                self.assertEqual(migration, ["migrate"] if poison is None else [],
                                 "unsafe resource metadata reached migrations")


if __name__ == "__main__":
    unittest.main(verbosity=2)
