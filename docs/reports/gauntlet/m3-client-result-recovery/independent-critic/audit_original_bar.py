#!/usr/bin/env python3
"""Read original PR18 Git objects; never launch an engine, socket or server."""
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess

ROOT = Path(__file__).resolve().parents[5]
BAR = "ccd0955a2cf5d8bcad4e9e9e2fba8ad399591f5e"
PREFIX = "docs/reports/systems-v3-evidence/client-recovery"


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def blob(path):
    return git("show", f"{BAR}:{path}")


def record(path):
    return json.loads(blob(path))


def audit():
    result = {"bar": BAR, "method": "Git blob/SQLite in-memory read-only audit; no new native execution", "campaigns": {}}
    for campaign, expected in [("campaign-r6", 27), ("campaign-r7", 9)]:
        prefix = f"{PREFIX}/{campaign}"
        files = git("ls-tree", "-r", "--name-only", BAR, prefix).decode().splitlines()
        fixtures = sorted(path for path in files if path.endswith("/fixture.json"))
        assert len(fixtures) == expected * 2
        rows = []
        for fixture_path in fixtures:
            directory = fixture_path.rsplit("/", 1)[0]
            config = record(fixture_path)
            label = directory.split("/")[-2]
            kind = directory.split("/")[-1].split("-")[1]
            boundary = directory.split("/")[-1].split("-")[2]
            candidate = label == "candidate"
            events = [json.loads(line) for line in blob(directory + "/timeline.jsonl").splitlines()]
            by_name = lambda name: [row for row in events if row["event"] == name]
            assert not by_name("barrier_timeout")
            for clock in ["wall_ns", "monotonic_ns"]:
                assert all(a[clock] <= b[clock] for a, b in zip(events, events[1:]))
            assert len(by_name("client_started")) == len(by_name("kill_confirmed")) == 1
            assert by_name("client_started")[0]["pid"] == by_name("kill_confirmed")[0]["pid"]
            assert by_name("kill_confirmed")[0]["returncode"] != 0
            observed_requests = by_name("request_received")
            assert observed_requests and all(row["body"] == config["payload"] for row in observed_requests)
            db = sqlite3.connect(":memory:")
            db.deserialize(blob(directory + "/authority.sqlite3"))
            assert db.execute("PRAGMA integrity_check").fetchone() == ("ok",)
            costs = [row[0] for row in db.execute("SELECT cost FROM mutations")]
            receipts = db.execute("SELECT key,payload,response FROM receipts").fetchall()
            requests = [json.loads(row[0]) for row in db.execute("SELECT body FROM requests")]
            db.close()
            committed = candidate or boundary != "before_commit"
            price = 10000000 if kind == "market" else 100
            assert costs == ([price] if committed else [])
            assert len(receipts) == int(committed)
            assert all(body == config["payload"] for body in requests)
            if receipts:
                key, payload, response = receipts[0]
                assert key == config["payload"]["idempotency_key"] and json.loads(payload) == config["payload"]
                stored_response = json.loads(response)
            first = None
            if campaign == "campaign-r7":
                first = record(directory + "/journal-first-kill-state.json")
                final = record(directory + "/journal-after-recovery.json")
                assert first["exists"] == candidate and not final["exists"]
                assert final["bytes_base64"] is None and final["sha256"] is None
            if candidate:
                raw = base64.b64decode(first["bytes_base64"], validate=True) if first else blob(directory + "/journal-at-kill.json")
                if first:
                    assert hashlib.sha256(raw).hexdigest() == first["sha256"]
                saved = json.loads(raw)["transaction"]
                assert saved["payload"] == config["payload"] and saved["path"] == config["path"]
                assert saved["server"] == config["url"] and saved["owner"] == config["owner"] and saved["method"] == 2
                assert config["token"].encode() not in raw and b"Bearer" not in raw and b"password" not in raw
                assert set(saved) == {"path", "payload", "server", "owner", "method", "message"}
            if boundary in ("late_commit", "recovery_kill"):
                released = by_name("original_commit_released_after_retry")[0]
                original = [row for row in by_name("transaction_committed_or_replayed") if row["first"]][0]
                for clock in ["wall_ns", "monotonic_ns"]:
                    assert released[clock] < original[clock]
                if candidate:
                    rejected = by_name("retry_rejected_before_original_commit")
                    assert len(rejected) == 1 and rejected[0]["status"] == 409
                    for clock in ["wall_ns", "monotonic_ns"]:
                        assert rejected[0][clock] < released[clock] < original[clock]
                    if boundary == "recovery_kill":
                        rejected_disk = record(directory + "/journal-after-rejected-recovery.json")
                        assert rejected_disk["bytes_base64"] == first["bytes_base64"] and rejected_disk["sha256"] == first["sha256"]
                        observed = by_name("recovery_observation_before_kill")[0]
                        killed = by_name("recovery_kill_confirmed")[0]
                        assert observed["observation"]["pending"] and observed["observation"]["result"]["_status"] == 409
                        assert observed["pid"] == killed["pid"] and killed["returncode"] != 0
                        for clock in ["wall_ns", "monotonic_ns"]:
                            assert rejected[0][clock] < observed[clock] < killed[clock] < rejected_disk[clock] < released[clock]
            log = "after-late-commit" if boundary in ("late_commit", "recovery_kill") else "restarted-client"
            native = blob(directory + f"/{log}.log").decode()
            assert "SCRIPT ERROR" not in native and "ERROR:" not in native
            observations = [json.loads(line.removeprefix("RECEIPT_PROBE ")) for line in native.splitlines() if line.startswith("RECEIPT_PROBE ")]
            assert len(observations) == 1 and observations[0]["recovered"] == candidate
            if candidate:
                assert observations[0]["result"] == stored_response and not observations[0]["pending"]
            rows.append({"case": directory.split("/")[-1], "label": label, "recovered": observations[0]["recovered"], "mutations": len(costs), "debit": sum(costs), "request_count": len(observed_requests)})
        result["campaigns"][campaign] = {"cases": len(rows), "candidate_recovered": sum(row["recovered"] for row in rows if row["label"] == "candidate"), "baseline_recovered": sum(row["recovered"] for row in rows if row["label"] == "baseline"), "rows": rows}
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2))
