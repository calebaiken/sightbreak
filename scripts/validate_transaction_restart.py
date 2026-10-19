#!/usr/bin/env python3
"""Matched native UI process-kill workload; a durable HTTP fixture supplies receipts.

This is a client crash oracle, not a substitute for PostgreSQL authority tests.
Run the identical probe against a clean baseline and candidate checkout.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import platform
import queue
import sqlite3
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "game/tests/transaction_crash_probe.gd"


def identity(root: Path) -> dict:
    def git(*args: str) -> str:
        return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()
    return {"commit": git("rev-parse", "HEAD"), "game_tree": git("rev-parse", "HEAD:game"),
            "status": git("status", "--porcelain", "--untracked-files=all")}


def run_case(exe: Path, root: Path, directory: Path, kind: str, boundary: str) -> dict:
    directory.mkdir(parents=True)
    database = directory / "authority.sqlite3"
    with sqlite3.connect(database) as db:
        db.executescript("CREATE TABLE receipts (key TEXT PRIMARY KEY, payload TEXT, response TEXT);"
                         "CREATE TABLE mutations (id INTEGER PRIMARY KEY, cost INTEGER);"
                         "CREATE TABLE requests (body TEXT);")
    reached = threading.Event()
    release = threading.Event()
    committed = threading.Event()
    barrier_failed = threading.Event()
    event_lock = threading.Lock()
    hold = True
    late = boundary in ("late_commit", "recovery_kill")
    token = "fixture-memory-only-credential"
    price = 10000000 if kind == "market" else 100

    def event(name, **fields):
        with event_lock, (directory / "timeline.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(dict(event=name, wall_ns=time.time_ns(), monotonic_ns=time.monotonic_ns(), **fields)) + "\n")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            with (directory / "http.log").open("a", encoding="utf-8") as log:
                log.write(fmt % args + "\n")

        def respond(self, value, status=200):
            data = json.dumps(value).encode()
            try:
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
                pass  # Expected: the first client is deliberately terminated.

        def do_GET(self):
            self.respond({"items": [{"id": "one-authoritative-instance"}], "slots": {}, "credits": 10000000 - price})

        def do_POST(self):
            nonlocal hold
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            event("request_received", body=body)
            if self.headers.get("Authorization") != "Bearer " + token:
                self.respond({"detail": "invalid credential"}, 401)
                return
            if kind == "market" and type(body.get("expected_price")) is not int:
                self.respond({"detail": "expected_price must be an integer"}, 422)
                return
            first = hold
            if not first and late and not release.is_set():
                event("retry_rejected_before_original_commit", status=409)
                self.respond({"detail": "insufficient credits at retry time"}, 409)
                return
            if first and (boundary == "before_commit" or late):
                event("before_commit_barrier")
                reached.set()
                if not release.wait(30):
                    event("barrier_timeout", phase="before_commit")
                    barrier_failed.set()
                    return
                # Connection was killed before authority committed. Retry must still use
                # the persisted intent; the killed first request is deliberately dropped.
                if boundary == "before_commit":
                    return
            canonical = json.dumps(body, sort_keys=True)
            with sqlite3.connect(database) as db:
                db.execute("INSERT INTO requests(body) VALUES (?)", (canonical,))
                old = db.execute("SELECT payload,response FROM receipts WHERE key=?", (body["idempotency_key"],)).fetchone()
                if old:
                    if old[0] != canonical:
                        self.respond({"detail": "receipt payload changed"}, 409)
                        return
                    response = json.loads(old[1])
                else:
                    response = {"item": {"id": "one-authoritative-instance"}, "credits": 10000000 - price}
                    if kind == "case":
                        response.update(roll=0, table_version="1")
                    elif kind == "market":
                        response["fee"] = price * 300 // 10000
                    db.execute("INSERT INTO mutations(cost) VALUES (?)", (price,))
                    db.execute("INSERT INTO receipts VALUES (?,?,?)", (body["idempotency_key"], canonical, json.dumps(response)))
            event("transaction_committed_or_replayed", first=first)
            committed.set()
            if first:
                reached.set()
                if not release.wait(30):
                    event("barrier_timeout", phase="before_response")
                    barrier_failed.set()
                    return
            self.respond(response)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    payload = {"idempotency_key": str(uuid.uuid5(uuid.NAMESPACE_URL, directory.name))}
    path = "/store/buy"
    if kind == "store":
        payload["definition_id"] = "key"
    elif kind == "case":
        path = "/cases/open"
        payload.update(case_id="case-instance", key_id="key-instance")
    else:
        path = "/market/listing-instance/buy"
        payload["expected_price"] = price
    config = {"url": f"http://127.0.0.1:{server.server_port}", "owner": "fixture-account", "token": token,
              "journal": str(directory / "pending.json"), "mode": "send", "path": path, "payload": payload}
    fixture = directory / "fixture.json"
    fixture.write_text(json.dumps(config), encoding="utf-8")
    env = dict(os.environ, SIGHTBREAK_RECEIPT_FIXTURE=str(fixture))
    command = [str(exe), "--headless", "--path", str(root / "game"), "--script", str(PROBE)]
    try:
        with (directory / "killed-client.log").open("w", encoding="utf-8") as log:
            proc = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT)
            event("client_started", pid=proc.pid)
            try:
                if not reached.wait(25):
                    raise RuntimeError(f"Client did not reach {boundary}: {directory}")
            finally:
                event("kill_requested", pid=proc.pid)
                proc.kill()
                proc.wait(timeout=10)
                event("kill_confirmed", pid=proc.pid, returncode=proc.returncode)
        saved = Path(config["journal"])
        def capture_journal(name):
            raw = saved.read_bytes() if saved.exists() else None
            observation = {"wall_ns": time.time_ns(), "monotonic_ns": time.monotonic_ns(),
                           "exists": raw is not None,
                           "sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
                           "bytes_base64": base64.b64encode(raw).decode() if raw is not None else None}
            (directory / f"{name}.json").write_text(json.dumps(observation, indent=2), encoding="utf-8")
            return observation

        journal = saved.read_text(encoding="utf-8") if saved.exists() else ""
        capture_journal("journal-first-kill-state")
        if journal:
            (directory / "journal-at-kill.json").write_text(journal, encoding="utf-8")
        hold = False
        if not late:
            release.set()
        config["mode"] = "retry_hold" if boundary == "recovery_kill" else "retry"
        fixture.write_text(json.dumps(config), encoding="utf-8")
        def restart(name, kill_after_observation=False):
            process = subprocess.Popen(command, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            event("recovery_started", pid=process.pid, phase=name)
            if kill_after_observation:
                observed = queue.Queue()
                lines = []

                def read_until_observation():
                    for line in process.stdout:
                        lines.append(line)
                        if line.startswith("RECEIPT_PROBE "):
                            observed.put(json.loads(line.removeprefix("RECEIPT_PROBE ")))
                            return

                reader = threading.Thread(target=read_until_observation, daemon=True)
                reader.start()
                try:
                    value = observed.get(timeout=25)
                    event("recovery_observation_before_kill", pid=process.pid, phase=name, observation=value)
                    if process.poll() is not None:
                        raise RuntimeError("Recovery exited before the required forced kill")
                finally:
                    event("recovery_kill_requested", pid=process.pid, phase=name)
                    process.kill()
                    process.wait(timeout=10)
                    event("recovery_kill_confirmed", pid=process.pid, phase=name, returncode=process.returncode)
                reader.join(timeout=5)
                stdout = "".join(lines) + process.stdout.read()
                stderr = process.stderr.read()
                if process.returncode == 0:
                    raise RuntimeError("Recovery unexpectedly exited normally")
            else:
                try:
                    stdout, stderr = process.communicate(timeout=35)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                    raise
            event("recovery_finished", pid=process.pid, returncode=process.returncode, phase=name)
            (directory / f"{name}.log").write_text(stdout + stderr, encoding="utf-8")
            lines = [line.removeprefix("RECEIPT_PROBE ") for line in stdout.splitlines() if line.startswith("RECEIPT_PROBE ")]
            if (process.returncode and not kill_after_observation) or len(lines) != 1 or "SCRIPT ERROR" in stderr or "ERROR:" in stderr:
                raise RuntimeError(f"Restart probe failed: {directory}")
            return json.loads(lines[0])

        probe = restart("restarted-client", boundary == "recovery_kill")
        retained_rejection = None
        late_order_verified = None
        release_before_commit = None
        if late:
            # V2 has no saved intent and sends no recovery request. When a receipt
            # exists, prove the client really observed the rejection before release.
            if journal and probe.get("result", {}).get("_status") != 409:
                raise RuntimeError("Late-commit recovery did not observe the required 409")
            retained_rejection = bool(probe.get("pending")) and saved.exists() and saved.read_text(encoding="utf-8") == journal
            capture_journal("journal-after-rejected-recovery")
            event("original_commit_released_after_retry", retained_rejection=retained_rejection)
            release.set()
            if not committed.wait(10):
                raise RuntimeError("Original request did not finish its delayed commit")
            config["mode"] = "retry"
            fixture.write_text(json.dumps(config), encoding="utf-8")
            probe = restart("after-late-commit")
            events = [json.loads(line) for line in (directory / "timeline.jsonl").read_text(encoding="utf-8").splitlines()]
            released = next(row["monotonic_ns"] for row in events if row["event"] == "original_commit_released_after_retry")
            original_commit = next(row["monotonic_ns"] for row in events if row["event"] == "transaction_committed_or_replayed" and row["first"])
            rejected = [row["monotonic_ns"] for row in events if row["event"] == "retry_rejected_before_original_commit" and row["status"] == 409]
            release_before_commit = released < original_commit
            late_order_verified = len(rejected) == 1 and rejected[0] < released < original_commit if journal else None
            if not release_before_commit or (journal and not late_order_verified):
                raise RuntimeError("Late-commit rejection/release/commit ordering was not enforced")
        if barrier_failed.is_set():
            raise RuntimeError("Fixture barrier timed out; this trial cannot qualify")
        with sqlite3.connect(database) as db:
            costs = [row[0] for row in db.execute("SELECT cost FROM mutations")]
            requests = [json.loads(row[0]) for row in db.execute("SELECT body FROM requests")]
        recovered = probe.get("recovered", False)
        final_journal = capture_journal("journal-after-recovery")
        return {"kind": kind, "boundary": boundary, "recovered": recovered, "mutation_count": len(costs),
                "total_debit": sum(costs), "receipt_reused": recovered and all(body == payload for body in requests),
                "credential_persisted": token in journal, "journal_before_kill": bool(journal),
                "journal_after_recovery": final_journal["exists"], "requests": requests, "probe": probe,
                "retained_rejection": retained_rejection,
                "late_order_verified": late_order_verified,
                "release_before_commit": release_before_commit,
                "command": command}
    finally:
        release.set()
        server.shutdown()
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--boundaries", nargs="+", choices=["before_commit", "after_commit", "late_commit", "recovery_kill"],
                        default=["before_commit", "after_commit", "late_commit"])
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    result = {"platform": platform.platform(), "python": platform.python_version(),
              "godot": subprocess.check_output([str(args.godot), "--version"], text=True).strip(),
              "probe_sha256": hashlib.sha256(PROBE.read_bytes()).hexdigest(),
              "harness_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "runs": {}}
    for label, root in [("baseline", args.baseline), ("candidate", args.candidate)]:
        root = root.resolve()
        source = identity(root)
        if source["status"]:
            raise RuntimeError(f"Dirty source tree: {label}: {source['status']}")
        imported = subprocess.run([str(args.godot), "--headless", "--path", str(root / "game"), "--editor", "--import", "--quit"], capture_output=True, text=True, timeout=120)
        (args.out / f"{label}-import.log").write_text(imported.stdout + imported.stderr, encoding="utf-8")
        if imported.returncode or "SCRIPT ERROR" in imported.stderr:
            raise RuntimeError(f"Import failed: {label}")
        cases = []
        for repeat in range(args.repetitions):
            for kind in ["store", "case", "market"]:
                for boundary in args.boundaries:
                    case = run_case(args.godot, root, args.out / label / f"{repeat}-{kind}-{boundary}", kind, boundary)
                    cases.append(case)
                    print(label, repeat, kind, boundary, "recovered", case["recovered"], flush=True)
        source["status_after"] = identity(root)["status"]
        result["runs"][label] = {"source": source, "cases": cases, "recovered": sum(case["recovered"] for case in cases), "total": len(cases)}
    candidate = result["runs"]["candidate"]
    result["pass"] = (candidate["recovered"] == candidate["total"]
                      and all(case["mutation_count"] == 1 and case["receipt_reused"]
                              and not case["credential_persisted"] and not case["journal_after_recovery"]
                              and case["retained_rejection"] is not False for case in candidate["cases"])
                      and all(not row["source"]["status_after"] for row in result["runs"].values()))
    (args.out / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({label: {key: row[key] for key in ["recovered", "total"]} for label, row in result["runs"].items()}, indent=2))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
