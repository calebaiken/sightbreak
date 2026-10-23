#!/usr/bin/env python3
"""One owned production PostgreSQL/API market lost-response recovery sequence.

Adapted from test_native_economy.py, the author-preserving B-21 restart harness,
and the owned-resource patterns in m3-backend-regression/run_qualification.py.
No service/native entrypoint runs on import. Bootstrap credentials stay in memory.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import http.client
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import secrets
import signal
import socket
import subprocess
import sys
import threading
import time
import traceback
from uuid import uuid4

from postgres_receipt_oracle import (BUSINESS_SQL, IDENTITY_SQL, fingerprint, require,
                                     verify_final_market_refresh, verify_market, verify_market_fixture, verify_order, verify_sql_witness, verify_unchanged)

ROOT = Path(__file__).resolve().parents[1]
BASE = "89393f3d1e059a3da35533e0bd84e98a098c691c"
IMAGE = "postgres:17@sha256:2d2b8998d31037bf721cfdf764d76ba74171b4fab3431b7f72c27c56ddbdf9e3"
PINNED_GODOT = "4.7.2.stable.official.ed1daf0bf"
PINNED_GODOT_SHA256 = "8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e"
DOCKER = ["docker", "--host=unix:///var/run/docker.sock"]
LABEL = "io.sightbreak.receipt-run"
OWNER = "client_result_recovery_builder"
SECRET_ENV = ("DATABASE_URL", "POSTGRES_PASSWORD", "PGPASSWORD", "SIGHTBREAK_SERVER_KEY",
              "SIGHTBREAK_JOIN_TICKET", "SIGHTBREAK_NATIVE_FIXTURE", "SIGHTBREAK_PG_RECEIPT_AUTH",
              "DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH",
              "PGHOST", "PGHOSTADDR", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSFILE",
              "PGSERVICE", "PGSERVICEFILE", "PGOPTIONS", "PGSSLMODE", "PGSSLKEY", "PGSSLCERT", "PGSSLROOTCERT")


def proc_identity(pid: int) -> dict | None:
    try:
        tail = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return dict(pid=pid, state=tail[0], ppid=int(tail[1]), pgrp=int(tail[2]), start_ticks=int(tail[19]))
    except FileNotFoundError:
        return None


def native_errors(output: str) -> bool:
    return any(value in output for value in ("SCRIPT ERROR", "ERROR:", "Parse Error", "ObjectDB instances leaked", "resources still in use"))


class Run:
    def __init__(self, args):
        self.args, self.out = args, args.out.resolve()
        require(self.out != ROOT and ROOT not in self.out.parents, "output must be outside source")
        self.out.mkdir(parents=True, exist_ok=False, mode=0o700)
        self.run = "sightbreak-pg-receipt-" + uuid4().hex[:12]
        self.db, self.role = "sb_receipt_" + self.run.rsplit("-", 1)[1] + "_test", "sb_receipt"
        self.password = secrets.token_urlsafe(36)
        self.secrets = [self.password]
        self.env = dict(os.environ)
        for key in SECRET_ENV:
            self.env.pop(key, None)
        self.deadline = time.monotonic() + 240
        self.lock = threading.RLock()
        self.children, self.proxies, self.events, self.sessions = [], [], [], {}
        self.cid, self.volume, self.db_port, self.api_port = None, None, None, None
        self.api_listener = None
        self.journal_port = 49152 + int(hashlib.sha256(str(self.out / "client/pending.json").replace("\\", "/").lower().encode()).hexdigest()[:7], 16) % 16384
        self.pg_identity, self.spec, self.current_phase = None, {}, "setup"
        self.holds = {1: threading.Event(), 2: threading.Event()}
        self.releases = {1: threading.Event(), 2: threading.Event()}
        self.mutation_attempts, self.market_requests, self.responses, self.reads, self.sql_rows, self.leaks = [], [], {}, {}, {}, []
        self.state = dict(run=self.run, component="market", status="in_progress", database=self.db, role=self.role,
                          scope="owned synthetic production PostgreSQL/API; native method calls; no player consent or earned-value claim",
                          processes=[], steps=[], snapshots=[], observer_handoffs=[], cleanup={})

    def remaining(self, bound=30):
        value = min(bound, self.deadline - time.monotonic())
        require(value > 0, "whole sequence exceeded declared 240-second bound")
        return value

    def add_secret(self, value):
        if value:
            with self.lock:
                self.secrets.append(value)

    def redact(self, text):
        with self.lock:
            for value in self.secrets:
                if value in text:
                    self.leaks.append(dict(phase=self.current_phase, marker="credential detected before persistence"))
                    text = text.replace(value, "[REDACTED_FIXTURE_CREDENTIAL]")
        return text

    def redact_bytes(self, body):
        # Redact before hex encoding, which would otherwise evade plaintext scans.
        with self.lock:
            for value in self.secrets:
                if value.encode() in body:
                    self.leaks.append(dict(phase=self.current_phase, marker="credential detected in mutation body"))
                    body = body.replace(value.encode(), b"[REDACTED_FIXTURE_CREDENTIAL]")
        return body

    def selected_volume(self, label):
        raw, _ = self.docker(label, ["volume", "inspect", "--format", "{{json .Name}}\n{{json .Labels}}", self.volume])
        name, labels = [json.loads(line) for line in raw.splitlines()]
        require(name == self.volume and labels.get(LABEL) == self.run and labels.get("io.sightbreak.owner") == OWNER,
                "volume ownership mismatch")
        row = dict(name=name, labels=labels)
        self.dump(label + ".json", row)
        return row

    def verify_mount(self, container):
        mounts = container["mounts"]
        require(len(mounts) == 1 and mounts[0].get("Type") == "volume" and mounts[0].get("Name") == self.volume
                and mounts[0].get("Destination") == "/var/lib/postgresql/data" and mounts[0].get("RW") is True,
                "container data mount mismatch")

    def dump(self, name, value):
        raw = self.redact(json.dumps(value, indent=2, sort_keys=True, default=str)) + "\n"
        with self.lock:
            (self.out / name).write_text(raw)

    def event(self, phase, **fields):
        with self.lock:
            row = dict(phase=phase, monotonic_ns=time.monotonic_ns(), wall_ns=time.time_ns(), **fields)
            self.events.append(row)
            with (self.out / "timeline.jsonl").open("a") as log:
                log.write(self.redact(json.dumps(row, sort_keys=True)) + "\n")
        return row

    def save(self):
        self.dump("report.json", self.state)

    def source(self):
        def git(*a): return subprocess.check_output(["git", *a], cwd=ROOT, env=self.env, text=True).strip()
        changed = git("diff", "--name-only", BASE, "HEAD", "--", "game", "backend", "server").splitlines()
        value = dict(commit=git("rev-parse", "HEAD"), status=git("status", "--porcelain", "--untracked-files=all"),
                     trees={p: git("rev-parse", "HEAD:" + p) for p in ("game", "backend", "scripts", "server")},
                     production_equal_base=all(p.startswith("game/tests/") for p in changed),
                     migrations={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT / "backend/migrations").glob("*.sql"))})
        require(not value["status"] and value["production_equal_base"], "source dirty or production source differs from accepted base")
        return value

    def command(self, label, command, env=None, timeout=30, check=True):
        start = time.monotonic()
        bound = self.remaining(timeout)
        process = subprocess.Popen(command, cwd=ROOT, env=env or self.env, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, text=True, start_new_session=True)
        identity = proc_identity(process.pid)
        failure = None
        try:
            output, _ = process.communicate(timeout=bound)
        except BaseException as error:
            if process.poll() is None: os.killpg(process.pid, signal.SIGKILL)
            output, _ = process.communicate(timeout=5)
            failure = error
        (self.out / (label + ".log")).write_text(self.redact(output))
        self.state["steps"].append(dict(label=label, argv=command, process=identity, exit=process.returncode,
                                        seconds=time.monotonic() - start, failure_type=type(failure).__name__ if failure else None))
        self.save()
        if failure is not None: raise failure
        if check:
            require(process.returncode == 0, label + " failed; retained sanitized output")
        return output, process.returncode

    def docker(self, label, args, **kwargs):
        return self.command(label, DOCKER + args, **kwargs)

    def selected_container(self, label):
        raw, _ = self.docker(label, ["inspect", "--format", "{{json .Id}}\n{{json .Name}}\n{{json .Image}}\n{{json .Config.Labels}}\n{{json .NetworkSettings.Ports}}\n{{json .State.Pid}}\n{{json .Mounts}}", self.cid])
        row = dict(zip(("id", "name", "image", "labels", "ports", "pid", "mounts"), [json.loads(v) for v in raw.splitlines()]))
        require(row["id"] == self.cid and row["name"] == "/" + self.run and row["labels"].get(LABEL) == self.run
                and row["labels"].get("io.sightbreak.owner") == OWNER, "container ownership mismatch")
        self.dump(label + ".json", row)
        return row

    def sql_identity(self, label):
        self.remaining()
        import psycopg
        inside, _ = self.docker(label + "-internal", ["exec", "-e", "PGPASSWORD", self.cid, "psql", "-h", "127.0.0.1", "-X", "-At", "-F", "|", "-U", self.role, "-d", self.db, "-c", IDENTITY_SQL],
                                env=dict(self.env, PGPASSWORD=self.password))
        self.remaining()
        with psycopg.connect(host="127.0.0.1", port=self.db_port, user=self.role, password=self.password,
                             dbname=self.db, connect_timeout=5,
                             options="-c default_transaction_read_only=on -c statement_timeout=5000") as db:
            self.remaining()
            external = db.execute(IDENTITY_SQL).fetchone()
        internal = inside.strip().split("|")
        require(external[0] == self.db and self.db.endswith("_test") and external[1] == self.role and external[4] == 5432
                and "PostgreSQL 17." in external[2] and internal[0:2] == [self.db, self.role]
                and internal[4] == "5432" and internal[5] == str(external[5]) and internal[6] == external[6], "owned SQL identity failed")
        row = dict(zip(("database", "role", "version", "server_address", "server_port", "postmaster_started", "system_identifier"), external))
        self.dump(label + ".json", row)
        return row

    def sql_snapshot(self, phase):
        self.remaining()
        import psycopg
        requested = dict(phase=phase, query_id=self.run + ":" + phase + ":" + uuid4().hex,
                         requested_monotonic_ns=time.monotonic_ns(), requested_wall_ns=time.time_ns())
        self.remaining()
        with psycopg.connect(host="127.0.0.1", port=self.db_port, user=self.role, password=self.password,
                             dbname=self.db, connect_timeout=5,
                             options="-c default_transaction_read_only=on -c statement_timeout=5000") as db:
            self.remaining()
            observed = db.execute(BUSINESS_SQL).fetchone()[0]
        row = dict(observed, **requested, completed_monotonic_ns=time.monotonic_ns(), completed_wall_ns=time.time_ns())
        verify_sql_witness(row, phase)
        require(row["database"] == self.db and row["role"] == self.role
                and row["system_identifier"] == self.pg_identity["system_identifier"]
                and datetime.fromisoformat(row["postmaster_started"]) == datetime.fromisoformat(str(self.pg_identity["postmaster_started"])),
                "snapshot identity mismatch")
        self.dump("sql-" + phase + ".json", row)
        with self.lock:
            self.sql_rows[phase] = row
            self.state["snapshots"].append(dict(phase=phase, query_id=row["query_id"]))
        self.event(phase + "_sql_retained", query_id=row["query_id"])
        return row

    def start_process(self, label, argv, env, pass_fds=()):
        self.remaining()
        process = subprocess.Popen(argv, cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   text=True, start_new_session=True, pass_fds=pass_fds)
        record = dict(label=label, argv=argv, identity=proc_identity(process.pid), lines=[], process=process)
        def reader():
            with (self.out / (label + ".log")).open("w") as log:
                for raw in process.stdout:
                    safe = self.redact(raw)
                    with self.lock: record["lines"].append(safe)
                    log.write(safe); log.flush()
        thread = threading.Thread(target=reader, daemon=True); thread.start()
        record["reader"] = thread
        self.children.append(record)
        self.state["processes"].append(dict(label=label, argv=argv, identity=record["identity"]))
        self.event(label + "_started", process=record["identity"])
        self.save()
        return record

    def wait_for(self, predicate, label, bound=30):
        until = time.monotonic() + self.remaining(bound)
        while time.monotonic() < until:
            if predicate(): return
            time.sleep(.05)
        raise AssertionError("timed out: " + label)

    def request(self, path, payload=None, token=None, method=None):
        connection = None
        try:
            connection = http.client.HTTPConnection("127.0.0.1", self.api_port, timeout=self.remaining(10))
            headers = {"Content-Type": "application/json"}
            if token: headers["Authorization"] = "Bearer " + token
            data = None if payload is None else json.dumps(payload).encode()
            self.remaining()
            connection.request(method or ("GET" if payload is None else "POST"), path, body=data, headers=headers)
            response = connection.getresponse(); raw = response.read()
            parsed = json.loads(raw)
            if path.startswith("/auth/") and isinstance(parsed, dict): self.add_secret(parsed.get("token"))
            return response.status, parsed
        except BaseException as error:
            if path.startswith("/auth/"):
                raise RuntimeError("authentication transport failed: " + type(error).__name__) from None
            raise
        finally:
            if connection is not None:
                try: connection.close()
                except BaseException as error:
                    if path.startswith("/auth/"):
                        raise RuntimeError("authentication close failed: " + type(error).__name__) from None
                    raise

    def observer(self, phase):
        directory = self.out / "observer"; directory.mkdir(exist_ok=True, mode=0o700)
        ready, release = directory / (phase + ".ready.json"), directory / (phase + ".release.json")
        event = self.event(phase + "_observer_ready")
        marker = dict(run=self.run, phase=phase, container_id=self.cid, label_key=LABEL, label_value=self.run,
                      database=self.db, role=self.role, source_commit=self.state["source_before"]["commit"],
                      system_identifier=self.pg_identity["system_identifier"], release_marker=str(release),
                      event=event, sql_file=str(directory / "read-only-business.sql"))
        (directory / "read-only-business.sql").write_text(BUSINESS_SQL + ";\n")
        ready.write_text(json.dumps(marker, indent=2) + "\n")
        self.state["observer_handoffs"].append(marker); self.save()
        print("PG_RECEIPT_OBSERVER_READY " + str(ready), flush=True)
        self.wait_for(release.is_file, "independent SQL witness " + phase, 60)
        ack = json.loads(release.read_text())
        require(ack.get("run") == self.run and ack.get("phase") == phase and ack.get("status") == "observed", "observer release mismatch")
        self.event(phase + "_observer_released")

    def proxy_handler(self, name):
        run = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args): pass
            def forward(self):
                connection, attempt, attempt_retained, index = None, None, False, None
                # Freeze provenance at ingress. Another native phase may start
                # while this threaded upstream request is still in flight.
                with run.lock:
                    native_phase = run.current_phase
                    requested = dict(requested_monotonic_ns=time.monotonic_ns(), requested_wall_ns=time.time_ns())
                auth = self.path.startswith("/auth/")
                # Count all non-auth mutations before parsing, validation or an
                # upstream connection; refused/wrong-route attempts cannot hide.
                if not auth and self.command in ("POST", "PUT", "PATCH", "DELETE"):
                    attempt = dict(method=self.command, path=self.path, origin=name, native_phase=native_phase,
                                   authorization_present=bool(self.headers.get("Authorization")),
                                   raw_body_hex=None, payload=None, body_complete=False)
                    with run.lock: run.mutation_attempts.append(attempt)
                try:
                    run.remaining()
                    require(self.path.startswith("/") and not self.path.startswith("//"), "proxy accepts only relative paths")
                    length = int(self.headers.get("Content-Length", "0")); require(0 <= length <= 8192, "proxy body exceeds bound")
                    body = self.rfile.read(length)
                    require(len(body) == length, "proxy body incomplete")
                    if attempt is not None:
                        safe = run.redact_bytes(body)
                        attempt.update(raw_body_hex=safe.hex(), body_complete=True, credential_redacted=safe != body)
                        try: attempt["payload"] = json.loads(safe)
                        except (ValueError, UnicodeDecodeError): attempt["payload_parse_error"] = True
                        run.event("mutation_attempt", **attempt); attempt_retained = True
                    market = self.command == "POST" and self.path == run.spec.get("path")
                    if market:
                        with run.lock:
                            run.market_requests.append(attempt); index = len(run.market_requests)
                        run.event("market_request", index=index, **attempt)
                    headers = {k: v for k, v in self.headers.items() if k.lower() not in ("host", "connection", "proxy-connection", "transfer-encoding")}
                    run.remaining()
                    connection = http.client.HTTPConnection("127.0.0.1", run.api_port, timeout=run.remaining(10))
                    run.remaining()
                    connection.request(self.command, self.path, body=body or None, headers=headers)
                    response = connection.getresponse(); raw = response.read()
                    if auth:
                        parsed = json.loads(raw)
                        if isinstance(parsed, dict) and parsed.get("token"):
                            run.add_secret(parsed["token"])
                            run.sessions[native_phase] = parsed["token"]
                        run.event("auth_response", native_phase=native_phase, origin=name, path=self.path,
                                  status=response.status, body_and_headers_redacted=True)
                    business_read = self.command == "GET" and self.path in ("/me", "/inventory")
                    if business_read:
                        value = json.loads(raw)
                    if market:
                        parsed = json.loads(raw)
                        run.responses[index] = parsed
                        run.event("market_" + str(index) + "_backend_200", status=response.status, response=parsed)
                        require(response.status == 200, "native market request was not actually committed/replayed")
                        if index in (1, 2):
                            phase = "settled" if index == 1 else "replay_held"
                            run.sql_snapshot(phase)
                            run.holds[index].set()
                            require(run.releases[index].wait(15), "held response barrier expired")
                            run.event("market_" + str(index) + "_response_dropped", header_bytes_sent=0)
                            try: self.connection.shutdown(socket.SHUT_RDWR)
                            except OSError: pass
                            self.close_connection = True
                            return
                    # Publish the write and its marker under the ingress lock.
                    # A client can dispatch its next GET as soon as write returns;
                    # it must not overtake the replay response marker.
                    with run.lock:
                        self.connection.settimeout(run.remaining(10))
                        self.send_response(response.status)
                        self.send_header("Content-Type", response.getheader("Content-Type", "application/json"))
                        self.send_header("Content-Length", str(len(raw))); self.end_headers()
                        written = self.wfile.write(raw)
                        require(written == len(raw), "downstream response write incomplete")
                        if market:
                            run.event("market_" + str(index) + "_response_forwarded", native_phase=native_phase, origin=name)
                        if business_read:
                            if response.status == 200:
                                run.reads.setdefault(native_phase, {})[self.path] = value
                            run.event("business_read", native_phase=native_phase, origin=name, method=self.command,
                                      path=self.path, status=response.status, response=value, **requested)
                except BaseException as error:
                    if attempt is not None and not attempt_retained:
                        run.event("mutation_attempt", **attempt)
                    run.event("proxy_failure", origin=name, error_type=type(error).__name__,
                              exception="authentication details withheld" if self.path.startswith("/auth/") else run.redact(str(error)))
                    self.close_connection = True
                finally:
                    if connection is not None:
                        try: connection.close()
                        except BaseException as error:
                            run.event("proxy_failure", origin=name, error_type=type(error).__name__,
                                      exception="authentication close details withheld" if self.path.startswith("/auth/") else run.redact(str(error)))
            do_GET = forward
            do_POST = forward
            do_PUT = forward
            do_PATCH = forward
            do_DELETE = forward
        return Handler

    def start_proxy(self, name):
        self.remaining()
        server = ThreadingHTTPServer(("127.0.0.1", 0), self.proxy_handler(name)); server.daemon_threads = True
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.proxies.append((name, server, thread))
        self.event(name + "_listening", address="127.0.0.1", port=server.server_port, driver_pid=os.getpid())
        return "http://127.0.0.1:" + str(server.server_port)

    def native(self, phase, mode, account, url, held=None):
        with self.lock:
            self.current_phase = phase
        config = dict(mode=mode, url=url, expected_account=account["id"], journal=str(self.out / "client" / "pending.json"),
                      path=self.spec["path"], payload=dict(idempotency_key=self.spec["key"], expected_price=400))
        path = self.out / (phase + "-config.json"); path.write_text(json.dumps(config))
        state = self.out / "client"; state.mkdir(exist_ok=True, mode=0o700)
        env = dict(self.env, XDG_DATA_HOME=str(state / "data"), XDG_CONFIG_HOME=str(state / "config"), XDG_CACHE_HOME=str(state / "cache"),
                   SIGHTBREAK_PG_RECEIPT_CONFIG=str(path), SIGHTBREAK_PG_RECEIPT_AUTH=json.dumps(account["auth"]))
        argv = [str(self.args.godot), "--headless", "--path", str(ROOT / "game"), "--script", "res://tests/postgres_receipt_probe.gd"]
        self.event(phase + "_journal_listener_expected", address="127.0.0.1", port=self.journal_port, journal_path=str(state / "pending.json"))
        child = self.start_process(phase, argv, env); process = child["process"]
        if held is not None:
            self.wait_for(lambda: self.holds[held].is_set() or process.poll() is not None, phase + " held production response", 10)
            require(self.holds[held].is_set() and process.poll() is None, phase + " did not reach held response while alive")
            self.record_journal_listener(phase, process.pid)
            self.event(phase + "_alive_before_kill", process=proc_identity(process.pid))
            self.event(phase + "_kill_requested", process=child["identity"])
            os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=5); child["reader"].join(timeout=5)
            self.event(phase + "_kill_ack", pid=process.pid, returncode=process.returncode)
            require(process.returncode == -9, "forced native kill was not acknowledged")
            self.releases[held].set()
            journal = state / "pending.json"; raw = journal.read_bytes()
            (self.out / (phase + "-journal.json")).write_bytes(raw)
            require(not native_errors("".join(child["lines"])), "killed native emitted an error")
            token = self.sessions[phase]
            require(self.request("/auth/logout", {}, token)[0] == 200 and self.request("/me", token=token)[0] == 401,
                    "old native session was not actually revoked")
            self.event(phase + "_old_session_revoked", logout_status=200, old_me_status=401)
            return raw
        try:
            process.wait(timeout=self.remaining(35))
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=5)
            raise
        finally:
            child["reader"].join(timeout=5)
        output = "".join(child["lines"])
        require(process.returncode == 0 and not native_errors(output), "native phase failed: " + phase)
        results = [json.loads(line.removeprefix("PG_RECEIPT_RESULT ")) for line in output.splitlines() if line.startswith("PG_RECEIPT_RESULT ")]
        logout = [json.loads(line.removeprefix("PG_RECEIPT_LOGOUT ")) for line in output.splitlines() if line.startswith("PG_RECEIPT_LOGOUT ")]
        require(len(results) == len(logout) == 1 and logout[0]["token_cleared"] and logout[0]["account_cleared"], "native completion/logout missing")
        require(self.request("/me", token=self.sessions[phase])[0] == 401, "completed native session not actually revoked")
        self.event(phase + "_response_and_refresh_complete", observation=results[0])
        return results[0]

    def record_journal_listener(self, phase, pid):
        # Linux /proc maps the deterministic journal TCP listener to this native
        # process without connecting to its intentionally protocol-free socket.
        expected = "0100007F:" + format(self.journal_port, "04X")
        rows = [line.split() for line in Path("/proc/net/tcp").read_text().splitlines()[1:]]
        matches = [r for r in rows if r[1] == expected and r[3] == "0A"]
        sockets = set()
        for fd in Path(f"/proc/{pid}/fd").iterdir():
            try: sockets.add(os.readlink(fd))
            except FileNotFoundError: pass
        owned = [r for r in matches if "socket:[" + r[9] + "]" in sockets]
        require(len(matches) == len(owned) == 1, "native journal listener ownership not observed")
        self.event(phase + "_journal_listener_owned", port=self.journal_port, address="127.0.0.1",
                   process=proc_identity(pid), inode=owned[0][9])

    def cleanup(self):
        # Cleanup remains bounded and usable even after the work deadline fails.
        self.deadline = time.monotonic() + 60
        if self.api_listener is not None:
            self.api_listener.close(); self.api_listener = None
        for release in self.releases.values(): release.set()
        for _, server, thread in self.proxies:
            server.shutdown(); server.server_close(); thread.join(timeout=5)
        for child in reversed(self.children):
            process = child["process"]
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGTERM)
                try: process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL); process.wait(timeout=5)
            child["reader"].join(timeout=5)
        cleanup = dict(children_reaped=all(c["process"].poll() is not None for c in self.children))
        if self.cid is None and self.volume:
            raw, status = self.docker("discover-owned-start-failure", ["inspect", "--format", "{{.Id}}", self.run], check=False)
            if status == 0:
                self.cid = raw.strip()
                self.selected_container("discovered-owned-start-failure")
        if self.cid:
            self.selected_container("container-before-cleanup")
            self.docker("remove-owned-container", ["rm", "-f", self.cid])
            _, status = self.docker("container-absent", ["inspect", "--format", "{{.Id}}", self.cid], check=False)
            cleanup["container_absent"] = status == 1
        if self.volume:
            self.selected_volume("volume-before-cleanup")
            self.docker("remove-owned-volume", ["volume", "rm", self.volume])
            _, status = self.docker("volume-absent", ["volume", "inspect", "--format", "{{.Name}}", self.volume], check=False)
            cleanup["volume_absent"] = status == 1
        ports = [p for p in (self.db_port, self.api_port, self.journal_port) if p] + [server.server_port for _, server, _ in self.proxies]
        cleanup["ports"] = {}
        for port in ports:
            with socket.socket() as sock:
                sock.settimeout(.5); cleanup["ports"][str(port)] = sock.connect_ex(("127.0.0.1", port)) != 0
        cleanup["pass"] = cleanup["children_reaped"] and all(cleanup.get(k, True) for k in ("container_absent", "volume_absent")) and all(cleanup["ports"].values())
        self.state["cleanup"] = cleanup; self.save()
        require(cleanup["pass"], "owned resource cleanup incomplete")

    def execute(self):
        # The driver never consults inherited libpq routing/credential selectors.
        # Explicit fixture values below are the only database connection source.
        for key in SECRET_ENV:
            if key.startswith("PG"): os.environ.pop(key, None)
        import psycopg
        self.state["source_before"] = self.source()
        self.state["engine"] = dict(path=str(self.args.godot), sha256=hashlib.sha256(self.args.godot.read_bytes()).hexdigest())
        require(self.state["engine"]["sha256"] == PINNED_GODOT_SHA256, "wrong pinned Linux engine bytes")
        version, _ = self.command("engine-version", [str(self.args.godot), "--version"])
        require(version.strip() == PINNED_GODOT, "wrong pinned engine")
        self.docker("docker-readiness", ["info", "--format", "{{json .ServerVersion}}\n{{json .OSType}}\n{{json .DockerRootDir}}"])
        raw, _ = self.docker("image", ["image", "inspect", "--format", "{{json .Id}}\n{{json .RepoDigests}}", IMAGE])
        image_id, digests = [json.loads(line) for line in raw.splitlines()]
        require("postgres@sha256:" + IMAGE.rsplit("sha256:", 1)[1] in digests, "wrong cached PG image")
        self.volume = self.run + "-data"
        self.docker("volume-create", ["volume", "create", "--label", LABEL + "=" + self.run, "--label", "io.sightbreak.owner=" + OWNER, self.volume])
        self.selected_volume("volume-owned-before-start")
        raw, _ = self.docker("postgres-start", ["run", "-d", "--pull=never", "--name", self.run,
                            "--label", LABEL + "=" + self.run, "--label", "io.sightbreak.owner=" + OWNER,
                            "-p", "127.0.0.1::5432", "-e", "POSTGRES_PASSWORD", "-e", "POSTGRES_USER=" + self.role,
                            "-e", "POSTGRES_DB=" + self.db, "-v", self.volume + ":/var/lib/postgresql/data", IMAGE],
                            env=dict(self.env, POSTGRES_PASSWORD=self.password))
        self.cid = raw.strip(); require(bool(re.fullmatch("[a-f0-9]{64}", self.cid)), "container ID missing")
        container = self.selected_container("container-owned")
        self.verify_mount(container)
        binding = container["ports"]["5432/tcp"]
        require(container["image"] == image_id and len(binding) == 1 and binding[0]["HostIp"] == "127.0.0.1", "container binding/image unsafe")
        self.db_port = int(binding[0]["HostPort"]); require(self.db_port != 55432, "shared DB port selected")
        def ready():
            try:
                self.remaining()
                with psycopg.connect(host="127.0.0.1", port=self.db_port, user=self.role, password=self.password, dbname=self.db, connect_timeout=1): return True
            except psycopg.OperationalError: return False
        self.wait_for(ready, "owned PG readiness", 30)
        self.pg_identity = self.sql_identity("identity-before-migration")
        backend_env = dict(self.env, DATABASE_URL=f"postgresql+psycopg://{self.role}:{self.password}@127.0.0.1:{self.db_port}/{self.db}", PYTHONDONTWRITEBYTECODE="1")
        self.command("migrate", [sys.executable, "-B", "backend/migrate.py"], env=backend_env, timeout=60)
        self.remaining()
        self.api_listener = socket.socket()
        self.api_listener.bind(("127.0.0.1", 0)); self.api_listener.listen(128)
        require(self.api_listener.getsockname()[0] == "127.0.0.1", "API listener not loopback")
        self.api_port = self.api_listener.getsockname()[1]
        descriptor = self.api_listener.fileno()
        api = self.start_process("api", [sys.executable, "-B", "-m", "uvicorn", "app:app", "--app-dir", "backend", "--fd", str(descriptor)],
                                 backend_env, pass_fds=(descriptor,))
        def api_ready():
            if api["process"].poll() is not None: raise AssertionError("owned API exited")
            try: return self.request("/health") == (200, {"status": "ok", "storage": "postgresql", "economy_version": "1"})
            except OSError: return False
        self.wait_for(api_ready, "owned production API readiness", 20)
        self.api_listener.close(); self.api_listener = None
        accounts = {}
        for role in ("seller", "buyer", "outsider"):
            auth = dict(username="receipt_" + role + "_" + secrets.token_hex(4), password=secrets.token_urlsafe(24))
            self.add_secret(auth["password"])
            status, response = self.request("/auth/register", dict(auth, display_name="Receipt " + role))
            require(status == 201, "production fixture registration failed")
            accounts[role] = dict(id=response["player_id"], auth=auth, token=response["token"])
            me = self.request("/me", token=response["token"])[1]
            inventory = self.request("/inventory", token=response["token"])[1]
            require(me["credits"] == me["xp"] == 0 and inventory == {"items": []}, "new fixture account not empty")
            self.event("fixture_registered", fixture_role=role, account=me, inventory=inventory, auth_response_redacted=True)
        # The only value setup is an explicit trusted fictional fixture in the
        # verified owned DB, using existing production helpers and ledger reason.
        os.environ["DATABASE_URL"] = backend_env["DATABASE_URL"]
        sys.path.insert(0, str(ROOT / "backend"))
        from app import credit, engine, mint, transaction
        from models import Player
        self.remaining()
        with transaction() as db:
            credit(db, db.get(Player, accounts["seller"]["id"]), 100, "fictional_test_fixture", self.run)
            credit(db, db.get(Player, accounts["buyer"]["id"]), 1000, "fictional_test_fixture", self.run)
            item_id = mint(db, accounts["seller"]["id"], "obsidian_rare").id
        engine.dispose()
        require(self.request("/loadout", dict(slot="rifle", item_id=item_id), accounts["seller"]["token"], "PUT")[0] == 200, "real seller equip failed")
        status, listing = self.request("/market/list", dict(item_id=item_id, price=400), accounts["seller"]["token"])
        require(status == 201, "real seller listing failed")
        self.event("fixture_listing", status=status, response=listing)
        self.spec = dict(buyer=accounts["buyer"]["id"], seller=accounts["seller"]["id"], outsider=accounts["outsider"]["id"],
                         item=item_id, listing=listing["id"], key=str(uuid4()), price=400, fee=12, path="/market/" + listing["id"] + "/buy")
        self.dump("business-spec.json", self.spec)
        before = self.sql_snapshot("before_original")
        verify_market_fixture(before, self.spec)
        origin = self.start_proxy("origin1"); origin2 = self.start_proxy("origin2")
        self.observer("pre_original")
        first = self.native("original", "send", accounts["buyer"], origin, held=1)
        saved = json.loads(first)
        receipt = saved["transaction"]
        require(saved.get("schema") == 1 and len(first) <= 8192 and set(receipt) == {"path", "payload", "method", "message", "owner", "server"}
                and receipt["owner"] == self.spec["buyer"] and receipt["server"] == origin and receipt["path"] == self.spec["path"]
                and receipt["method"] == 2 and receipt["payload"] == dict(idempotency_key=self.spec["key"], expected_price=400), "journal not bound to original production intent")
        settled = self.sql_rows["settled"]; verify_market(before, settled, self.spec, self.responses[1])
        journal = self.out / "client/pending.json"
        for phase, account, url in (("wrong_account", accounts["outsider"], origin), ("wrong_origin", accounts["buyer"], origin2)):
            count = len(self.mutation_attempts)
            result = self.native(phase, "guard", account, url)
            require(result["pending_before"] and result["pending_after"] and result["result"].get("_error")
                    and journal.read_bytes() == first and len(self.mutation_attempts) == count, "client isolation guard failed")
            verify_unchanged(settled, self.sql_snapshot(phase))
        status, outsider = self.request(self.spec["path"], dict(idempotency_key=self.spec["key"], expected_price=400), accounts["outsider"]["token"])
        require(status == 409 and "item" not in outsider, "outsider received buyer receipt")
        self.event("outsider_api_refused", account=self.spec["outsider"], path=self.spec["path"],
                   payload=dict(idempotency_key=self.spec["key"], expected_price=400), status=status, response=outsider)
        verify_unchanged(settled, self.sql_snapshot("outsider_api"))
        second = self.native("first_recovery", "retry", accounts["buyer"], origin, held=2)
        require(first == second, "second kill changed original journal bytes")
        verify_unchanged(settled, self.sql_rows["replay_held"])
        result = self.native("final_recovery", "retry", accounts["buyer"], origin)
        require(result["result"] == self.responses[1] and not result["pending_after"] and not journal.exists(), "final recovery did not clear original receipt")
        require(result["account"]["credits"] == 600 and [i["id"] for i in result["inventory"]] == [item_id], "native fresh account/inventory mismatch")
        with self.lock:
            verify_final_market_refresh(list(self.events), result)
        require(self.responses[1] == self.responses[2] == self.responses[3], "production replay response differs from original")
        final_event = next(e for e in self.events if e["phase"] == "final_recovery_response_and_refresh_complete")
        final_sql = self.sql_snapshot("after_final_refresh"); verify_sql_witness(final_sql, "after_final_refresh", final_event); verify_unchanged(settled, final_sql)
        self.observer("post_final_refresh")
        count = len(self.mutation_attempts)
        cleared = self.native("post_clear_restart", "post_clear", accounts["buyer"], origin)
        require(not cleared["pending_before"] and not cleared["pending_after"] and len(self.mutation_attempts) == count and not journal.exists(), "post-clear restart recreated a purchase")
        verify_unchanged(settled, self.sql_snapshot("post_clear_restart"))
        status, rejected = self.request(self.spec["path"], dict(idempotency_key=self.spec["key"], expected_price=401), accounts["buyer"]["token"])
        require(status == 409, "changed-price receipt was accepted")
        self.event("changed_price_refused", account=self.spec["buyer"], path=self.spec["path"],
                   payload=dict(idempotency_key=self.spec["key"], expected_price=401), status=status, response=rejected)
        verify_unchanged(settled, self.sql_snapshot("changed_price_rejected"))
        require(len(self.mutation_attempts) == len(self.market_requests) == 3 and all(r["method"] == "POST" and r["path"] == self.spec["path"]
                and r["payload"] == dict(idempotency_key=self.spec["key"], expected_price=400)
                and r["raw_body_hex"] == self.market_requests[0]["raw_body_hex"] and r["origin"] == "origin1"
                and r["authorization_present"] for r in self.market_requests), "request identity/raw-body changed")
        for index, phase, sql_phase in ((1, "original", "settled"), (2, "first_recovery", "replay_held")):
            verify_order(self.events, ["market_" + str(index) + "_backend_200", sql_phase + "_sql_retained",
                                      phase + "_alive_before_kill", phase + "_kill_requested", phase + "_kill_ack"])
        require(not any(e["phase"] == "proxy_failure" for e in self.events), "proxy failure occurred")
        for path in self.out.rglob("*"):
            if path.is_file():
                data = path.read_bytes()
                require(not any(value.encode() in data for value in self.secrets), "credential persisted in owned output/state")
        require(not self.leaks, "credential reached a log before redaction")
        self.state["checks"] = dict(market_settlement=True, exact_receipt=True, two_lost_responses=True,
                                    account_origin_isolation=True, fresh_auth_old_sessions_revoked=True, no_persisted_credentials=True)
        self.state["status"] = "focused_checks_passed"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--component", choices=["market"], required=True)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run = Run(args)
    try:
        run.execute()
    except BaseException as error:
        run.state["status"] = "failed"
        run.state["failure_type"] = type(error).__name__
        run.dump("failure.json", dict(type=type(error).__name__, detail=str(error), traceback=traceback.format_exc()))
    finally:
        try:
            run.cleanup()
            run.state["source_after"] = run.source()
            require(run.state["source_after"] == run.state.get("source_before"), "source changed during run")
            for path in run.out.rglob("*"):
                if path.is_file():
                    require(not any(secret.encode() in path.read_bytes() for secret in run.secrets), "credential persisted after cleanup")
            require(not run.leaks, "credential reached output before redaction")
        except BaseException as error:
            run.state["status"] = "failed"
            run.dump("cleanup-failure.json", dict(type=type(error).__name__, detail=str(error), traceback=traceback.format_exc()))
        run.state["credential_redaction_events"] = run.leaks
        run.save()
    passed = run.state["status"] == "focused_checks_passed" and run.state["cleanup"].get("pass")
    print(json.dumps(dict(pass_=bool(passed), output=str(run.out), status=run.state["status"])), flush=True)
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
