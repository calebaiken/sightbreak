#!/usr/bin/env python3
"""Native EconomyUI -> HTTP hold proxy -> real PostgreSQL crash/re-auth oracle.

One invocation measures one immutable revision. Run the same frozen harness and
probe for both revisions. Only a unique sightbreak_receipt_<hex>_test DB is
created/dropped. A git archive and copied import cache isolate all native writes.
No production backend/UI files are patched. Published credentials are redacted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import platform
import re
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import uuid
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import psycopg
from psycopg import sql
from psycopg.rows import dict_row

HARNESS = Path(__file__).resolve()
PROBE = HARNESS.with_name("native_transaction_restart_probe.gd")
CONNECT = dict(host="127.0.0.1", port=55439, user="sightbreak", password="sightbreak_local_only")
RETRY_CONFIG_KEYS = {"url", "journal", "mode", "username", "password", "owner"}
NATIVE_ENV_KEYS = {"SYSTEMROOT", "WINDIR", "COMSPEC", "PATH", "PATHEXT", "TEMP", "TMP",
                   "APPDATA", "LOCALAPPDATA", "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
                   "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE", "OS"}
TABLES = {
    "players": "id, username, display_name, credits, xp, active, last_trade",
    "items": "*", "listings": "*", "operations": "*", "ledger": "*",
    "audit": "*", "loadouts": "*", "trades": "*", "rewards": "*",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def identity(root: Path, revision: str) -> dict:
    return dict(checkout_head=git(root, "rev-parse", "HEAD"),
                status=git(root, "status", "--porcelain", "--untracked-files=all"),
                measured_commit=git(root, "rev-parse", revision),
                game_tree=git(root, "rev-parse", revision + ":game"),
                backend_tree=git(root, "rev-parse", revision + ":backend"))


def manifest(root: Path, exclude_cache=False) -> dict:
    return {p.relative_to(root).as_posix(): sha(p.read_bytes()) for p in sorted(root.rglob("*"))
            if p.is_file() and (not exclude_cache or not {".godot", "__pycache__"}.intersection(p.parts))}


class Evidence:
    def __init__(self, directory: Path):
        self.directory = directory
        self.lock = threading.Lock()
        self.secrets: set[str] = set()

    def text(self, text: str) -> str:
        for secret in sorted(self.secrets, key=len, reverse=True):
            text = text.replace(secret, "[REDACTED]")
        return text

    def redact(self, value):
        if isinstance(value, dict):
            return {key: ("[REDACTED]" if key.lower() in {"password", "token", "token_a", "token_b", "authorization"}
                          else self.redact(item)) for key, item in value.items()}
        if isinstance(value, list):
            return [self.redact(item) for item in value]
        return self.text(value) if isinstance(value, str) else value

    def event(self, event: str, **fields) -> dict:
        row = dict(event=event, wall_ns=time.time_ns(), monotonic_ns=time.monotonic_ns(),
                   harness_pid=os.getpid(), **fields)
        with self.lock, (self.directory / "timeline.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(self.redact(row), default=str) + "\n")
        return row


def request(url: str, path: str, body=None, token=""):
    data = None if body is None else json.dumps(body).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url + path, data, headers)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def snapshot(database: str, directory: Path, name: str, evidence: Evidence) -> dict:
    # A new connection sees committed rows, never the service's uncommitted identity map.
    with psycopg.connect(**CONNECT, dbname=database, row_factory=dict_row) as db:
        db.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        metadata = db.execute("SELECT version(), current_database(), pg_backend_pid(), "
                              "inet_server_port(), clock_timestamp(), txid_current_snapshot()::text").fetchone()
        state = {table: db.execute(f'SELECT {columns} FROM "{table}" ORDER BY 1, 2').fetchall()
                 for table, columns in TABLES.items()}
        sessions = db.execute("SELECT token_hash, player_id, expires_at FROM sessions ORDER BY token_hash").fetchall()
    # Round trip timestamps to a stable, serializable representation for exact comparisons.
    state = json.loads(json.dumps(state, default=str))
    write_json(directory / (name + ".json"), dict(postgresql=metadata, economic_state=state, sessions=sessions))
    evidence.event("postgresql_snapshot", name=name, database=database,
                   connection_pid=metadata["pg_backend_pid"], state_sha256=sha(json.dumps(state, sort_keys=True).encode()))
    return state


def journal_snapshot(journal: Path, directory: Path, name: str, evidence: Evidence) -> dict:
    raw = journal.read_bytes() if journal.exists() else b""
    safe = not any(secret.encode() in raw for secret in evidence.secrets) and b"bearer" not in raw.lower()
    if raw and safe:
        (directory / (name + ".raw.json")).write_bytes(raw)
    result = dict(exists=bool(raw), sha256=sha(raw), bytes=len(raw), no_credentials=safe,
                  record=json.loads(raw) if raw and safe else None)
    write_json(directory / (name + ".json"), result)
    if not safe:
        raise RuntimeError("Credential found in journal; raw journal withheld")
    return result


class HoldProxy:
    def __init__(self, backend_port: int, buy_path: str, evidence: Evidence):
        self.reached = threading.Event()
        self.release = threading.Event()
        self.finished = threading.Event()
        self.evidence = evidence
        self.phase = "send"
        self.purchases = []
        self.logins = []
        self.held = None
        proxy = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                self.forward()

            def do_POST(self):
                self.forward()

            def forward(self):
                phase = proxy.phase
                raw = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                body = json.loads(raw) if raw else None
                token = self.headers.get("Authorization", "").removeprefix("Bearer ")
                if token:
                    evidence.secrets.add(token)
                evidence.event("proxy_request", phase=phase, method=self.command, path=self.path,
                               body=body, raw_utf8=evidence.text(raw.decode()),
                               token_sha256=sha(token.encode()) if token else None)
                connection = http.client.HTTPConnection("127.0.0.1", backend_port, timeout=20)
                headers = {"Content-Type": self.headers.get("Content-Type", "application/json")}
                if token:
                    headers["Authorization"] = "Bearer " + token
                try:
                    connection.request(self.command, self.path, body=raw or None, headers=headers)
                    upstream = connection.getresponse()
                    response = upstream.read()
                    status = upstream.status
                finally:
                    connection.close()
                value = json.loads(response)
                if self.path == "/auth/login" and status == 200:
                    evidence.secrets.add(value["token"])
                    proxy.logins.append(dict(phase=phase, player_id=value["player_id"],
                                             token_sha256=sha(value["token"].encode())))
                evidence.event("proxy_upstream_response", phase=phase, path=self.path, status=status,
                               response=value, raw_utf8=evidence.text(response.decode()))
                if self.path == buy_path and self.command == "POST":
                    purchase = dict(phase=phase, body=body, raw_utf8=raw.decode(), status=status,
                                    response=value, response_raw_utf8=response.decode(),
                                    token_sha256=sha(token.encode()))
                    proxy.purchases.append(purchase)
                    if proxy.held is None:
                        proxy.held = purchase
                        purchase["barrier"] = evidence.event("response_held_before_any_client_headers",
                                                            phase=phase, status=status, sent_bytes=0)
                        proxy.reached.set()
                        proxy.release.wait()
                        # Always discard this connection's response after the kill, never deliver it.
                        evidence.event("held_response_discarded", phase=phase, sent_bytes=0)
                        self.close_connection = True
                        proxy.finished.set()
                        return
                try:
                    self.send_response(status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(response)))
                    self.end_headers()
                    self.wfile.write(response)
                    self.wfile.flush()
                    evidence.event("proxy_response_delivered", phase=phase, path=self.path, status=status)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                    evidence.event("proxy_peer_disconnected", phase=phase, path=self.path)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.url = f"http://127.0.0.1:{self.server.server_port}"

    def close(self):
        self.release.set()
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)


def native_pids(exe: Path) -> list[int]:
    if os.name != "nt":
        raise RuntimeError("This measured host guard currently requires Windows tasklist")
    output = subprocess.check_output(["tasklist", "/FI", "IMAGENAME eq " + exe.name, "/FO", "CSV", "/NH"], text=True)
    return [int(row[1]) for row in csv.reader(io.StringIO(output)) if len(row) > 1 and row[0].lower() == exe.name.lower()]


def launch(command: list[str], environment: dict, evidence: Evidence, phase: str, cwd=None):
    others = native_pids(Path(command[0]))
    if others:
        raise RuntimeError(f"Native slot occupied by PIDs {others}; run serially after they finish")
    # The first process must remain alive while the coordinator waits at the HTTP
    # barrier. Undrained Windows pipes can stall Godot before it reaches the probe.
    # Private files keep capture unbounded without publishing unredacted output.
    temporary = Path(os.environ["LOCALAPPDATA"]) / "Temp/opencode"
    stdout = tempfile.TemporaryFile(dir=temporary)
    stderr = tempfile.TemporaryFile(dir=temporary)
    try:
        process = subprocess.Popen(command, env=environment, cwd=cwd, stdout=stdout, stderr=stderr)
    except Exception:
        stdout.close()
        stderr.close()
        raise
    process.receipt_logs = (stdout, stderr)
    evidence.event("native_started", phase=phase, pid=process.pid, command=command, cwd=str(cwd) if cwd else None, other_native_pids=others)
    return process


def collect(process, directory: Path, phase: str, evidence: Evidence, timeout=45):
    timed_out = False
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=10)
        timed_out = True
    if not hasattr(process, "receipt_output"):
        output = []
        for log in process.receipt_logs:
            log.seek(0)
            output.append(log.read().decode("utf-8", errors="replace"))
            log.close()
        process.receipt_output = output
    stdout, stderr = process.receipt_output
    evidence.event("native_finished", phase=phase, pid=process.pid, returncode=process.returncode)
    (directory / (phase + ".stdout.txt")).write_text(evidence.text(stdout), encoding="utf-8")
    (directory / (phase + ".stderr.txt")).write_text(evidence.text(stderr), encoding="utf-8")
    events = [json.loads(line.removeprefix("NATIVE_RECEIPT_EVENT ")) for line in stdout.splitlines()
              if line.startswith("NATIVE_RECEIPT_EVENT ")]
    if timed_out:
        raise subprocess.TimeoutExpired(process.args, timeout, output=stdout, stderr=stderr)
    return stdout, stderr, events


def seed(service, balance: int, evidence: Evidence):
    password = "receipt-oracle-" + secrets.token_hex(16)
    evidence.secrets.add(password)
    username = "receipt_" + secrets.token_hex(8)
    with service.transaction() as db:
        player = service.Player(username=username, display_name=username,
                                password_hash=service.password_hasher.hash(password))
        db.add(player)
        db.flush()
        service.credit(db, player, balance, "fictional_test_fixture", username)
        session = service.issue_session(db, player)
        fixture = dict(owner=player.id, username=username, password=password, token=session["token"])
    evidence.secrets.add(fixture["token"])
    return fixture


def prepare_database(root: Path, database: str, output: Path, repetitions: int, include_native: bool):
    """Exit this setup interpreter before starting the service/native client on an 8GB host."""
    assert re.fullmatch(r"sightbreak_receipt_[0-9a-f]+_test", database)
    sys.path.insert(0, str(root / "backend"))
    import app as service
    assert service.engine.url.database == database
    service.Base.metadata.create_all(service.engine)
    with service.engine.begin() as db:
        for migration in sorted((root / "backend/migrations").glob("*.sql")):
            db.exec_driver_sql(migration.read_text(encoding="utf-8"))
    evidence = Evidence(output.parent)
    fixtures = {"cases": [], "native": [], "fee_basis_points": service.CONFIG["market_fee_basis_points"]}
    for price in [400, 401, 10000000][:repetitions]:
        buyer, seller = seed(service, price + 1600, evidence), seed(service, 2000, evidence)
        with service.transaction() as db:
            item = service.mint(db, seller["owner"], "obsidian_rare").id
        fixtures["cases"].append(dict(buyer=buyer, seller=seller, item=item, price=price))
    if include_native:
        for _ in range(2):
            a, b = seed(service, 2000, evidence), seed(service, 2000, evidence)
            with service.transaction() as db:
                items = {key: service.mint(db, a["owner"], definition).id
                         for key, definition in [("case", "obsidian_case"), ("key", "key"), ("skin", "obsidian_rare")]}
            fixtures["native"].append(dict(a=a, b=b, items=items))
    write_json(output, fixtures)
    service.engine.dispose()


def verify_commit(before, after, fixture, purchase, fee) -> dict:
    players_before = {row["id"]: row for row in before["players"]}
    players_after = {row["id"]: row for row in after["players"]}
    item = next(row for row in after["items"] if row["id"] == fixture["item"])
    listing = next(row for row in after["listings"] if row["id"] == fixture["listing"])
    new_rows = lambda table: [row for row in after[table] if row["id"] not in {old["id"] for old in before[table]}]
    ledger, operations, audit = new_rows("ledger"), new_rows("operations"), new_rows("audit")
    buyer, seller, price = fixture["owner"], fixture["seller"], fixture["payload"]["expected_price"]
    return dict(
        real_http_200=purchase["status"] == 200,
        integer_body=type(purchase["body"].get("expected_price")) is int,
        original_body=purchase["body"] == fixture["payload"],
        buyer_debit=players_before[buyer]["credits"] - players_after[buyer]["credits"] == price,
        seller_credit=players_after[seller]["credits"] - players_before[seller]["credits"] == price - fee,
        fee_burn=sum(row["credits"] for row in before["players"]) - sum(row["credits"] for row in after["players"]) == fee,
        item_transfer=item["owner_id"] == buyer and item["reservation"] is None and not item["consumed"] and len(before["items"]) == len(after["items"]),
        sold_listing=listing["state"] == "sold" and listing["buyer_id"] == buyer and listing["seller_id"] == seller and listing["price"] == price,
        exact_operation=len(operations) == 1 and operations[0] == dict(id=f'{buyer}:buy:{fixture["listing"]}:{fixture["payload"]["idempotency_key"]}',
            request_hash=sha(json.dumps(fixture["payload"], sort_keys=True, separators=(",", ":")).encode()), response=purchase["response"]),
        exact_ledger=len(ledger) == 2 and {(row["player_id"], row["amount"], row["balance_after"], row["reason"], row["reference"]) for row in ledger} == {
            (buyer, -price, players_after[buyer]["credits"], "market_purchase", fixture["listing"]),
            (seller, price - fee, players_after[seller]["credits"], "market_sale", fixture["listing"])},
        exact_audit=len(audit) == 1 and audit[0]["actor"] == buyer and audit[0]["action"] == "market_settled" and audit[0]["details"] == dict(
            listing_id=fixture["listing"], item_id=fixture["item"], from_player=seller, to_player=buyer, fee=fee),
        complete_result=set(purchase["response"]) == {"item", "credits", "fee"} and purchase["response"]["item"]["id"] == fixture["item"]
            and purchase["response"]["credits"] == players_after[buyer]["credits"] and purchase["response"]["fee"] == fee,
    )


def capture_launch_inputs(config, original, fixture, environment, command, root, directory, phase, evidence):
    """Overwrite the only supplied fixture; retain original purchase data in the driver only."""
    if phase != "send" and (set(config) != RETRY_CONFIG_KEYS or config["mode"] != "retry"):
        raise RuntimeError("Restart config must contain exactly the six permitted keys")
    if set(key.upper() for key in environment) - NATIVE_ENV_KEYS - {"SIGHTBREAK_RECEIPT_FIXTURE"}:
        raise RuntimeError("Unexpected native environment variable")
    write_json(fixture, config)  # Truncates the send fixture; no sibling original is retained here.
    raw = fixture.read_bytes()
    assert json.loads(raw) == config
    purchase_values = [original[key] for key in ["path", "item", "listing", "seller"]]
    purchase_values.append(original["payload"]["idempotency_key"])
    other_inputs = json.dumps(dict(environment=environment, command=command))
    if any(value in other_inputs for value in purchase_values):
        raise RuntimeError("Original purchase data found in native environment/argv")
    if phase != "send" and any(value.encode() in raw for value in purchase_values):
        raise RuntimeError("Original purchase data found in restart fixture")
    redacted = directory / (phase + ".fixture.redacted.json")
    write_json(redacted, evidence.redact(config))
    source_files = {"driver": HARNESS, "probe": PROBE,
                    "economy_ui": root / "game/scripts/ui/economy_ui.gd",
                    "economy_api": root / "game/scripts/ui/economy_api.gd",
                    "transaction_journal": root / "game/scripts/ui/transaction_journal.gd"}
    binding = dict(phase=phase, fixture_path=str(fixture), keys=sorted(config),
                   fixture_sha256=sha(raw), fixture_bytes=len(raw),
                   redacted_fixture_sha256=sha(redacted.read_bytes()),
                   source_file_sha256={name: sha(path.read_bytes()) if path.exists() else "" for name, path in source_files.items()},
                   command=command, cwd=str(root / "game"), environment=environment,
                   environment_sha256=sha(json.dumps(environment, sort_keys=True, separators=(",", ":")).encode()),
                   environment_hash_encoding="UTF-8 JSON, sorted keys, compact separators, ensure_ascii=True",
                   purchase_values_absent_from_environment_and_argv=True,
                   strict_minimal_restart_config=phase != "send" and set(config) == RETRY_CONFIG_KEYS)
    write_json(directory / (phase + ".launch-inputs.json"), evidence.redact(binding))
    evidence.event("native_inputs_prepared", **binding)
    return binding


def verify_native_read(events, binding):
    reads = [event for event in events if event["event"] == "fixture_read"]
    expected_sources = {key: value for key, value in binding["source_file_sha256"].items() if key != "driver"}
    if len(reads) != 1 or any(reads[0].get(key) != expected for key, expected in {
        "keys": binding["keys"], "sha256": binding["fixture_sha256"], "bytes": binding["fixture_bytes"],
        "mode": "send" if binding["phase"] == "send" else "retry", "source_file_sha256": expected_sources,
    }.items()):
        raise RuntimeError("Native fixture/source read does not match the captured prelaunch binding")
    return dict(phase=binding["phase"], native_pid=reads[0]["pid"], matched=True,
                strict_minimal_restart_config=binding["strict_minimal_restart_config"], native_read=reads[0])


def run_case(args, root, private, seeded, fee_basis_points, database, backend_port, directory):
    directory.mkdir()
    evidence = Evidence(directory)
    buyer, seller, item, price = (seeded[key] for key in ["buyer", "seller", "item", "price"])
    evidence.secrets.update([buyer["password"], buyer["token"], seller["password"], seller["token"]])
    listing = request(f"http://127.0.0.1:{backend_port}", "/market/list", dict(item_id=item, price=price), seller["token"])
    path = f'/market/{listing["id"]}/buy'
    proxy = HoldProxy(backend_port, path, evidence)
    journal = private / (directory.name + "-pending.json")
    config = dict(url=proxy.url, journal=str(journal), mode="send", path=path,
                  payload=dict(expected_price=price, idempotency_key=str(uuid.uuid4())),
                  owner=buyer["owner"], username=buyer["username"], password=buyer["password"],
                  seller=seller["owner"], item=item, listing=listing["id"])
    fixture = private / (directory.name + "-fixture.json")
    write_json(directory / "fixture.redacted.json", evidence.redact(config))
    environment = {key: value for key, value in os.environ.items() if key.upper() in NATIVE_ENV_KEYS}
    environment["SIGHTBREAK_RECEIPT_FIXTURE"] = str(fixture)
    command = [str(args.godot), "--headless", "--verbose", "--path", str(root / "game"), "--script", str(PROBE)]
    process = None
    try:
        before = snapshot(database, directory, "01-before", evidence)
        binding = capture_launch_inputs(config, config, fixture, environment, command, root, directory, "send", evidence)
        process = launch(command, environment, evidence, "send", cwd=root / "game")
        if not proxy.reached.wait(25):
            raise RuntimeError("Native request did not reach upstream response barrier")
        committed = snapshot(database, directory, "02-committed-before-kill", evidence)
        checks = verify_commit(before, committed, config, proxy.held, price * fee_basis_points // 10000)
        before_kill = journal_snapshot(journal, directory, "journal-before-kill", evidence)
        if not all(checks.values()):
            write_json(directory / "commit-checks.json", checks)
            raise RuntimeError("PostgreSQL commit invariants failed")
        if process.poll() is not None or time.monotonic_ns() - proxy.held["barrier"]["monotonic_ns"] > 6_000_000_000:
            raise RuntimeError("Kill barrier missed; client must still await its 12-second HTTP timeout")
        evidence.event("kill_requested", pid=process.pid, upstream_committed=True, client_response_bytes=0)
        process.kill()
        stdout, stderr, killed_events = collect(process, directory, "killed-client", evidence, timeout=10)
        if any(event["event"] == "completed" for event in killed_events) or "SCRIPT ERROR" in stderr:
            raise RuntimeError("Client completed or script failed before the intended kill")
        input_reads = [verify_native_read(killed_events, binding)]
        evidence.event("kill_confirmed", pid=process.pid, returncode=process.returncode)
        process = None
        after_kill_journal = journal_snapshot(journal, directory, "journal-after-kill", evidence)
        after_kill = snapshot(database, directory, "03-after-kill", evidence)
        proxy.release.set()
        if not proxy.finished.wait(5):
            raise RuntimeError("Held connection was not discarded")

        recovered = {}
        phases = []
        for phase in ["recovery", "second-restart"]:
            proxy.phase = phase
            retry_config = {key: config[key] for key in RETRY_CONFIG_KEYS}
            retry_config["mode"] = "retry"
            binding = capture_launch_inputs(retry_config, config, fixture, environment, command, root, directory, phase, evidence)
            process = launch(command, environment, evidence, phase, cwd=root / "game")
            stdout, stderr, events = collect(process, directory, phase, evidence)
            if process.returncode or "ERROR:" in stderr:
                raise RuntimeError(f"Native {phase} failed")
            input_reads.append(verify_native_read(events, binding))
            process = None
            completed = [event for event in events if event["event"] == "completed"]
            if len(completed) != 1:
                raise RuntimeError("Native completion marker missing")
            current = snapshot(database, directory, "04-after-recovery" if phase == "recovery" else "05-after-second-restart", evidence)
            saved = journal_snapshot(journal, directory, "journal-after-" + phase, evidence)
            phases.append(dict(phase=phase, completed=completed[0], journal=saved,
                               economic_state_unchanged=current == committed))
            if phase == "recovery":
                recovered = completed[0]
        logins = proxy.logins
        with psycopg.connect(**CONNECT, dbname=database) as db:
            sessions = dict(db.execute("SELECT token_hash, player_id FROM sessions").fetchall())
        recovery_requests = [row for row in proxy.purchases if row["phase"] == "recovery"]
        recovered_exactly = recovered["result"] == proxy.held["response"]
        checks.update(
            native_input_read_bindings=len(input_reads) == 3 and all(row["matched"] for row in input_reads),
            strict_minimal_restart_inputs=all(row["strict_minimal_restart_config"] for row in input_reads[1:]),
            state_unchanged_at_kill=after_kill == committed,
            stable_journal_at_kill=before_kill == after_kill_journal,
            three_fresh_native_logins=len(logins) == 3 and len({row["token_sha256"] for row in logins}) == 3
                and all(row["player_id"] == buyer["owner"] and sessions.get(row["token_sha256"]) == buyer["owner"] for row in logins),
            economic_state_unchanged=all(phase["economic_state_unchanged"] for phase in phases),
            no_second_restart_request=not any(row["phase"] == "second-restart" for row in proxy.purchases),
            no_pending_after_recovery=all(not phase["journal"]["exists"] and not phase["completed"]["pending_after"] for phase in phases),
            second_restart_no_pending=not phases[1]["completed"]["pending_on_start"] and phases[1]["completed"]["result"] == {},
        )
        recovery_checks = dict(
            journal_survived=before_kill["exists"] and after_kill_journal["exists"],
            pending_restored=bool(recovered["pending_on_start"]), exact_receipt=recovered_exactly,
            original_request_replayed=len(recovery_requests) == 1 and recovery_requests[0]["body"] == config["payload"]
                and type(recovery_requests[0]["body"].get("expected_price")) is int and recovery_requests[0]["response"] == proxy.held["response"],
        )
        result = dict(price=price, checks=checks, recovery_checks=recovery_checks,
                       authoritative_pass=all(checks.values()), recovered=all(recovery_checks.values()),
                       logins=logins, purchases=proxy.purchases, phases=phases, input_reads=input_reads)
        write_json(directory / "result.json", result)
        return result
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            collect(process, directory, "aborted-client", evidence, timeout=10)
        proxy.close()
        fixture.unlink(missing_ok=True)


def native_economy(args, root, private, seeded, backend_port, directory, calibrated):
    directory.mkdir()
    evidence = Evidence(directory)
    a, b, items = (seeded[key] for key in ["a", "b", "items"])
    evidence.secrets.update([a["password"], a["token"], b["password"], b["token"]])
    config = dict(a=a["owner"], b=b["owner"], token_a=a["token"], token_b=b["token"], **items,
                  api_url=f"http://127.0.0.1:{backend_port}")
    fixture = private / (directory.name + ".json")
    write_json(fixture, config)
    write_json(directory / "fixture.redacted.json", evidence.redact(config))
    original = (root / "game/tests/native_economy_test.gd").read_bytes()
    source = original
    probe = root / "game/tests/native_economy_test.gd"
    if calibrated:
        old, new = b'"http://127.0.0.1:9"', b'"http://native-receipt-oracle.invalid"'
        if source.count(old) != 1:
            raise RuntimeError("Unexpected native economy test calibration site")
        source = source.replace(old, new)
        probe = private / "native_economy_dns_calibration.gd"
        probe.write_bytes(source)
    (directory / "executed-probe.gd").write_bytes(source)
    environment = dict(os.environ, SIGHTBREAK_NATIVE_FIXTURE=str(fixture))
    process = launch([str(args.godot), "--headless", "--path", str(root / "game"), "--script", str(probe)], environment, evidence, "native-economy")
    stdout, stderr, _ = collect(process, directory, "native-economy", evidence, timeout=90)
    tally = re.search(r"NATIVE_REAL_ECONOMY_QA (\d+)/(\d+) passed", stdout)
    result = dict(returncode=process.returncode, tally=tally.group(0) if tally else None,
                  original_sha256=sha(original), executed_sha256=sha(source), calibrated=calibrated,
                  calibration='Only port-9 URL replaced by reserved .invalid DNS name' if calibrated else None,
                  passed=process.returncode == 0 and "ERROR:" not in stderr and bool(tally) and tally[1] == tally[2])
    write_json(directory / "result.json", result)
    fixture.unlink(missing_ok=True)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--cache-source", type=Path, required=True, help="Imported game/.godot from the same revision")
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3, choices=range(1, 4))
    parser.add_argument("--expect-recovered", type=int, choices=[0, 1], required=True)
    parser.add_argument("--native-economy", action="store_true", help="Also retain original and one-line DNS-calibrated native regression")
    args = parser.parse_args()
    args.out = args.out.resolve()
    args.out.mkdir(parents=True, exist_ok=False)
    source = identity(args.source, args.revision)
    harness_identity = identity(HARNESS.parents[1], "HEAD")
    if source["status"] or harness_identity["status"]:
        raise RuntimeError("Freeze a clean harness/source checkout before measurement")
    cache_identity = identity(args.cache_source.parents[1], "HEAD")
    if cache_identity["status"] or cache_identity["game_tree"] != source["game_tree"]:
        raise RuntimeError("Import cache must come from a clean checkout of the same game tree")
    if native_pids(args.godot):
        raise RuntimeError("Native slot occupied; no concurrent Godot/import processes allowed")
    database = "sightbreak_receipt_" + secrets.token_hex(8) + "_test"
    assert re.fullmatch(r"sightbreak_receipt_[0-9a-f]+_test", database)
    summary = dict(platform=platform.platform(), python=sys.version, source=source, harness_checkout=harness_identity,
                   cache_source=cache_identity, harness_sha256=sha(HARNESS.read_bytes()), probe_sha256=sha(PROBE.read_bytes()),
                   godot_sha256=sha(args.godot.read_bytes()), database=database, runs=[])
    (args.out / HARNESS.name).write_bytes(HARNESS.read_bytes())
    (args.out / PROBE.name).write_bytes(PROBE.read_bytes())
    created = False
    process = None
    try:
        with tempfile.TemporaryDirectory(prefix="sightbreak-receipt-", dir=Path(os.environ["LOCALAPPDATA"]) / "Temp/opencode") as folder:
            private = Path(folder)
            root = private / "source"
            archive = subprocess.check_output(["git", "-C", str(args.source), "archive", "--format=zip", source["measured_commit"], "game", "backend"])
            summary["archive_sha256"] = sha(archive)
            with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
                zipped.extractall(root)
            source_manifest = manifest(root, exclude_cache=True)
            write_json(args.out / "source-manifest.json", source_manifest)
            shutil.copytree(args.cache_source, root / "game/.godot")
            write_json(args.out / "cache-manifest.json", manifest(root / "game/.godot"))
            summary["godot_version"] = subprocess.check_output([str(args.godot), "--version"], text=True).strip()
            with psycopg.connect(**CONNECT, dbname="postgres", autocommit=True) as db:
                db.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
            created = True
            os.environ["DATABASE_URL"] = f'postgresql+psycopg://{CONNECT["user"]}:{CONNECT["password"]}@127.0.0.1:{CONNECT["port"]}/{database}'
            setup_file = private / "seeded-private.json"
            setup_command = [sys.executable, str(HARNESS), "--prepare", str(root), database,
                             str(setup_file), str(args.repetitions), str(int(args.native_economy))]
            setup = subprocess.Popen(setup_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            setup_stdout, setup_stderr = setup.communicate(timeout=90)
            summary["setup"] = dict(pid=setup.pid, command=setup_command, returncode=setup.returncode)
            (args.out / "setup.stdout.txt").write_text(setup_stdout, encoding="utf-8")
            (args.out / "setup.stderr.txt").write_text(setup_stderr, encoding="utf-8")
            if setup.returncode:
                raise RuntimeError("PostgreSQL setup subprocess failed")
            seeded = json.loads(setup_file.read_text(encoding="utf-8"))
            setup_file.unlink()
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", 0))
                port = listener.getsockname()[1]
            with (args.out / "service.stdout.txt").open("w", encoding="utf-8") as log:
                command = [sys.executable, "-m", "uvicorn", "app:app", "--app-dir", str(root / "backend"), "--host", "127.0.0.1", "--port", str(port)]
                process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=os.environ.copy())
                summary["service"] = dict(pid=process.pid, command=command, started_wall_ns=time.time_ns())
                for _ in range(100):
                    if process.poll() is not None:
                        raise RuntimeError("Real API exited during startup")
                    try:
                        summary["health"] = request(f"http://127.0.0.1:{port}", "/health")
                        break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError("Real PostgreSQL API did not become healthy")
                for index, case in enumerate(seeded["cases"]):
                    result = run_case(args, root, private, case, seeded["fee_basis_points"], database, port, args.out / f"run-{index + 1}")
                    summary["runs"].append(result)
                    print(f'run-{index + 1} recovered={result["recovered"]} authoritative_pass={result["authoritative_pass"]}', flush=True)
                if args.native_economy:
                    summary["native_economy"] = [native_economy(args, root, private, seeded["native"][index], port, args.out / name, calibrated)
                        for index, (name, calibrated) in enumerate([("native-economy-original", False), ("native-economy-dns-calibrated", True)])]
                summary["archived_source_unchanged"] = source_manifest == manifest(root, exclude_cache=True)
                process.terminate()
                process.wait(timeout=10)
                summary["service"]["stopped_wall_ns"] = time.time_ns()
                process = None
        summary["source_after"] = identity(args.source, args.revision)
        summary["harness_after"] = identity(HARNESS.parents[1], "HEAD")
        summary["core_pass"] = (all(run["authoritative_pass"] and run["recovered"] == bool(args.expect_recovered) for run in summary["runs"])
                                and summary["archived_source_unchanged"] and source == summary["source_after"]
                                and harness_identity == summary["harness_after"])
    except Exception as error:
        summary["error"] = f"{type(error).__name__}: {error}"
        summary["core_pass"] = False
        raise
    finally:
        if process is not None:
            process.terminate()
            process.wait(timeout=10)
        if created:
            with psycopg.connect(**CONNECT, dbname="postgres", autocommit=True) as db:
                db.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(database)))
                summary["database_dropped"] = db.execute("SELECT NOT EXISTS (SELECT 1 FROM pg_database WHERE datname=%s)", (database,)).fetchone()[0]
        write_json(args.out / "summary.json", summary)
        write_json(args.out / "evidence-manifest.json", manifest(args.out))
    raise SystemExit(0 if summary["core_pass"] else 1)


if __name__ == "__main__":
    if len(sys.argv) == 7 and sys.argv[1] == "--prepare":
        prepare_database(Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4]), int(sys.argv[5]), bool(int(sys.argv[6])))
    else:
        main()
