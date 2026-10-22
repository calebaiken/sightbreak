"""Recompute retained campaign and directly verify exact owned cleanup."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import time

CAMPAIGN = Path("/workspace/sightbreak-postgres-receipt-market-r1")
CANDIDATE = Path("/workspace/sightbreak-postgres-receipt-recovery")
OUT = Path(__file__).parent / "runtime-r1"
SOURCE = "882931dd7024c2b200a72b2a52017dd98b95ee6a"
sys.path.insert(0, str(CANDIDATE / "scripts"))
from postgres_receipt_oracle import verify_market, verify_sql_witness, verify_unchanged


def main():
    report = json.loads((CAMPAIGN / "report.json").read_text())
    spec = json.loads((CAMPAIGN / "business-spec.json").read_text())
    events = [json.loads(line) for line in (CAMPAIGN / "timeline.jsonl").read_text().splitlines()]
    def one(phase):
        rows = [r for r in events if r["phase"] == phase]
        assert len(rows) == 1, phase
        return rows[0]
    def ordered(phases):
        rows = [one(p) for p in phases]
        assert all(a["monotonic_ns"] < b["monotonic_ns"] and a["wall_ns"] < b["wall_ns"] for a, b in zip(rows, rows[1:])), phases
    def observation(phase):
        lines = (CAMPAIGN / (phase + ".log")).read_text().splitlines()
        result = [json.loads(s.removeprefix("PG_RECEIPT_RESULT ")) for s in lines if s.startswith("PG_RECEIPT_RESULT ")]
        logout = [json.loads(s.removeprefix("PG_RECEIPT_LOGOUT ")) for s in lines if s.startswith("PG_RECEIPT_LOGOUT ")]
        assert len(result) == len(logout) == 1 and logout[0]["account_cleared"] and logout[0]["token_cleared"]
        return result[0]
    assert report["status"] == "focused_checks_passed" and report["cleanup"]["pass"] and not report["credential_redaction_events"]
    assert report["source_before"] == report["source_after"] and report["source_before"]["commit"] == SOURCE and not report["source_before"]["status"]
    before = json.loads((CAMPAIGN / "sql-before_original.json").read_text())
    settled = json.loads((CAMPAIGN / "sql-settled.json").read_text())
    original = one("market_1_backend_200")["response"]
    verify_market(before, settled, spec, original)
    sql_rows = [json.loads(p.read_text()) for p in sorted(CAMPAIGN.glob("sql-*.json"))]
    assert len(sql_rows) == len({r["query_id"] for r in sql_rows}) == 9
    for row in sql_rows:
        verify_sql_witness(row, row["phase"])
        if row["phase"] != "before_original": verify_unchanged(settled, row)
    final_sql = next(r for r in sql_rows if r["phase"] == "after_final_refresh")
    verify_sql_witness(final_sql, "after_final_refresh", one("final_recovery_response_and_refresh_complete"))
    independent_before = json.loads((OUT / "pre_original-witness.json").read_text())["snapshot"]
    independent_final = json.loads((OUT / "post_final_refresh-witness.json").read_text())["snapshot"]
    assert independent_before["business"] == before["business"]
    verify_market(independent_before, independent_final, spec, original)
    verify_unchanged(settled, independent_final)
    attempts = [e for e in events if e["phase"] == "mutation_attempt"]
    requests = [e for e in events if e["phase"] == "market_request"]
    expected_payload = {"idempotency_key": spec["key"], "expected_price": 400}
    assert len(attempts) == len(requests) == 3
    assert [r["native_phase"] for r in attempts] == ["original", "first_recovery", "final_recovery"]
    assert len({r["raw_body_hex"] for r in attempts}) == 1
    for row in attempts:
        assert row["method"] == "POST" and row["path"] == spec["path"] and row["origin"] == "origin1"
        assert row["body_complete"] and row["authorization_present"] and not row["credential_redacted"]
        assert row["payload"] == json.loads(bytes.fromhex(row["raw_body_hex"])) == expected_payload
    native_logins = [e for e in events if e["phase"] == "auth_response" and e["path"] == "/auth/login"]
    assert len(native_logins) == 6 and all(e["status"] == 200 and e["body_and_headers_redacted"] for e in native_logins)
    assert {r["native_phase"] for r in native_logins} == {"original", "wrong_account", "wrong_origin", "first_recovery", "final_recovery", "post_clear_restart"}
    kill_gaps = {}
    for index, phase, sql_phase in ((1, "original", "settled"), (2, "first_recovery", "replay_held")):
        ordered(["market_" + str(index) + "_backend_200", sql_phase + "_sql_retained", phase + "_alive_before_kill", phase + "_kill_requested", phase + "_kill_ack", "market_" + str(index) + "_response_dropped"])
        assert one("market_" + str(index) + "_backend_200")["status"] == 200
        assert one(phase + "_kill_ack")["returncode"] == -9
        assert one("market_" + str(index) + "_response_dropped")["header_bytes_sent"] == 0
        assert one(phase + "_old_session_revoked")["logout_status"] == 200 and one(phase + "_old_session_revoked")["old_me_status"] == 401
        alive, started, owned = one(phase + "_alive_before_kill")["process"], one(phase + "_started")["process"], one(phase + "_journal_listener_owned")
        assert alive["state"] in ("R", "S") and alive["pid"] == started["pid"] == owned["process"]["pid"]
        assert alive["start_ticks"] == started["start_ticks"] == owned["process"]["start_ticks"]
        assert owned["address"] == "127.0.0.1" and owned["inode"] and owned["port"] == 64049
        assert one("market_" + str(index) + "_backend_200")["response"] == original
        kill_gaps[phase] = (one(phase + "_kill_ack")["monotonic_ns"] - one("market_" + str(index) + "_backend_200")["monotonic_ns"]) / 1e6
    raw = (CAMPAIGN / "original-journal.json").read_bytes()
    assert raw == (CAMPAIGN / "first_recovery-journal.json").read_bytes() and len(raw) <= 8192
    journal = json.loads(raw)
    intent = journal["transaction"]
    assert journal["schema"] == 1 and set(intent) == {"path", "payload", "method", "message", "owner", "server"}
    assert intent["owner"] == spec["buyer"] and intent["path"] == spec["path"] and intent["payload"] == expected_payload and intent["method"] == 2
    for phase in ("wrong_account", "wrong_origin"):
        result = observation(phase)
        assert result["pending_before"] and result["pending_after"] and result["journal_exists"] and result["result"].get("_error")
        assert not any(a["native_phase"] == phase for a in attempts)
    final = observation("final_recovery")
    assert final["result"] == original == one("market_3_backend_200")["response"]
    assert final["pending_before"] and not final["pending_after"] and not final["journal_exists"]
    fresh_reads = [r for r in events if r["phase"] == "business_read" and r["native_phase"] == "final_recovery" and r["monotonic_ns"] > one("market_3_response_forwarded")["monotonic_ns"]]
    assert len(fresh_reads) == 2
    fresh = {r["path"]: r["response"] for r in fresh_reads}
    assert final["account"] == fresh["/me"] and final["inventory"] == fresh["/inventory"]["items"]
    assert final["account"]["credits"] == 600 and final["account"]["xp"] == 0 and final["inventory"] == [original["item"]]
    cleared = observation("post_clear_restart")
    assert not cleared["pending_before"] and not cleared["pending_after"] and not cleared["journal_exists"] and cleared["result"] == {}
    assert not (CAMPAIGN / "client/pending.json").exists()
    assert one("changed_price_refused")["status"] == one("outsider_api_refused")["status"] == 409
    assert one("changed_price_refused")["payload"] == dict(expected_payload, expected_price=401)
    assert "item" not in one("outsider_api_refused")["response"]
    assert not [e for e in events if e["phase"] == "proxy_failure"]
    for path in CAMPAIGN.rglob("*"):
        if not path.is_file(): continue
        data = path.read_bytes()
        assert not any(marker in data for marker in (b"SCRIPT ERROR", b"Parse Error", b"ObjectDB instances leaked", b"resources still in use")), path.name
        if path.suffix in (".log", ".json", ".jsonl"):
            assert not re.search(rb'Bearer\s+[A-Za-z0-9._-]{8,}|"(?:password|token|authorization)"\s*:', data, re.I), "credential field/value in " + path.name
    env = dict(os.environ)
    for key in ("DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"): env.pop(key, None)
    cleanup = dict(requested_monotonic_ns=time.monotonic_ns(), requested_wall_ns=time.time_ns(), commands=[], processes=[], ports={})
    container = json.loads((OUT / "post_final_refresh-witness.json").read_text())["container"]
    for label, argv in (("container-absent", ["docker", "--host=unix:///var/run/docker.sock", "inspect", "--format", "{{.Id}}", container["id"]]),
                        ("volume-absent", ["docker", "--host=unix:///var/run/docker.sock", "volume", "inspect", "--format", "{{.Name}}", report["run"] + "-data"])):
        result = subprocess.run(argv, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        cleanup["commands"].append(dict(label=label, argv=argv, exit=result.returncode, stdout=result.stdout, stderr=result.stderr))
        assert result.returncode == 1 and not result.stdout.strip(), label
    identities = [p["identity"] for p in report["processes"]] + [s["process"] for s in report["steps"]] + [{"pid": 149153}, {"pid": container["pid"]}]
    for row in identities:
        stat = Path("/proc") / str(row["pid"]) / "stat"
        observed = None
        if stat.exists():
            tail = stat.read_text().rsplit(")", 1)[1].split()
            observed = dict(state=tail[0], start_ticks=int(tail[19]))
        cleanup["processes"].append(dict(pid=row["pid"], expected_start_ticks=row.get("start_ticks"), observed=observed))
        assert observed is None or (row.get("start_ticks") is not None and observed["start_ticks"] != row["start_ticks"]), "owned process remains"
    for port in report["cleanup"]["ports"]:
        with socket.socket() as sock:
            sock.settimeout(.3)
            cleanup["ports"][port] = sock.connect_ex(("127.0.0.1", int(port)))
        assert cleanup["ports"][port] != 0, "owned listener remains"
    cleanup.update(completed_monotonic_ns=time.monotonic_ns(), completed_wall_ns=time.time_ns(), pass_=True)
    (OUT / "independent-cleanup.json").write_text(json.dumps(cleanup, indent=2) + "\n")
    archive = OUT / "campaign"
    assert not archive.exists()
    shutil.copytree(CAMPAIGN, archive)
    manifest = {str(p.relative_to(CAMPAIGN)): dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(CAMPAIGN.rglob("*")) if p.is_file()}
    (OUT / "campaign-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    verdict = dict(source=SOURCE, status="independently_passed_bounded_market_recovery", campaign_files=len(manifest), native_processes=6,
                   original_and_replay_kill_ack_ms_after_backend_200=kill_gaps, independent_live_witnesses=2, sql_snapshots=9,
                   exact_mutation_attempts=3, original_journal_bytes=len(raw), original_journal_sha256=hashlib.sha256(raw).hexdigest(),
                   buyer=600, seller=488, outsider=0, fee=12, no_xp_or_rewards=True, cleanup_independently_verified=True,
                   credential_scope="structural independent audit plus frozen driver private-value scan; no credential values read or retained")
    (OUT / "independent-verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
    print(json.dumps(verdict, indent=2))


if __name__ == "__main__": main()
