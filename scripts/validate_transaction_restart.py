#!/usr/bin/env python3
"""Matched native UI process-kill workload; a durable HTTP fixture supplies receipts.

This is a client crash oracle, not a substitute for PostgreSQL authority tests.
Run the identical probe against a clean baseline and candidate checkout.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import sqlite3
import subprocess
import threading
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
    hold = True
    token = "fixture-memory-only-credential"
    price = 10000000 if kind == "market" else 100

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
            if self.headers.get("Authorization") != "Bearer " + token:
                self.respond({"detail": "invalid credential"}, 401)
                return
            if kind == "market" and type(body.get("expected_price")) is not int:
                self.respond({"detail": "expected_price must be an integer"}, 422)
                return
            first = hold
            if first and boundary == "before_commit":
                reached.set()
                release.wait(30)
                # Connection was killed before authority committed. Retry must still use
                # the persisted intent; the killed first request is deliberately dropped.
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
                    db.execute("INSERT INTO mutations(cost) VALUES (?)", (price,))
                    db.execute("INSERT INTO receipts VALUES (?,?,?)", (body["idempotency_key"], canonical, json.dumps(response)))
            if first:
                reached.set()
                release.wait(30)
            self.respond(response)

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    payload = {"idempotency_key": "same-immutable-receipt"}
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
            try:
                if not reached.wait(25):
                    raise RuntimeError(f"Client did not reach {boundary}: {directory}")
            finally:
                proc.kill()
                proc.wait(timeout=10)
        saved = Path(config["journal"])
        journal = saved.read_text(encoding="utf-8") if saved.exists() else ""
        if journal:
            (directory / "journal-at-kill.json").write_text(journal, encoding="utf-8")
        hold = False
        release.set()
        config["mode"] = "retry"
        fixture.write_text(json.dumps(config), encoding="utf-8")
        p = subprocess.run(command, env=env, capture_output=True, text=True, timeout=35)
        (directory / "restarted-client.log").write_text(p.stdout + p.stderr, encoding="utf-8")
        lines = [line.removeprefix("RECEIPT_PROBE ") for line in p.stdout.splitlines() if line.startswith("RECEIPT_PROBE ")]
        if p.returncode or len(lines) != 1 or "SCRIPT ERROR" in p.stderr or "ERROR:" in p.stderr:
            raise RuntimeError(f"Restart probe failed: {directory}")
        probe = json.loads(lines[0])
        with sqlite3.connect(database) as db:
            costs = [row[0] for row in db.execute("SELECT cost FROM mutations")]
            requests = [json.loads(row[0]) for row in db.execute("SELECT body FROM requests")]
        recovered = probe.get("recovered", False)
        return {"kind": kind, "boundary": boundary, "recovered": recovered, "mutation_count": len(costs),
                "total_debit": sum(costs), "receipt_reused": recovered and all(body == payload for body in requests),
                "credential_persisted": token in journal, "journal_before_kill": bool(journal),
                "journal_after_recovery": saved.exists(), "requests": requests, "probe": probe,
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
                for boundary in ["before_commit", "after_commit"]:
                    case = run_case(args.godot, root, args.out / label / f"{repeat}-{kind}-{boundary}", kind, boundary)
                    cases.append(case)
                    print(label, repeat, kind, boundary, "recovered", case["recovered"], flush=True)
        source["status_after"] = identity(root)["status"]
        result["runs"][label] = {"source": source, "cases": cases, "recovered": sum(case["recovered"] for case in cases), "total": len(cases)}
    candidate = result["runs"]["candidate"]
    result["pass"] = (candidate["recovered"] == candidate["total"]
                      and all(case["mutation_count"] == 1 and case["receipt_reused"]
                              and not case["credential_persisted"] and not case["journal_after_recovery"] for case in candidate["cases"])
                      and all(not row["source"]["status_after"] for row in result["runs"].values()))
    (args.out / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({label: {key: row[key] for key in ["recovered", "total"]} for label, row in result["runs"].items()}, indent=2))
    raise SystemExit(0 if result["pass"] else 1)


if __name__ == "__main__":
    main()
