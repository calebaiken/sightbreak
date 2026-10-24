"""Offline reconstruction of retained observations; does not launch a test/client or access SQL."""
from pathlib import Path
import hashlib
import io
import json
import subprocess
import sys
import zipfile

ROOT = Path(subprocess.check_output(["git", "-C", str(Path(__file__).resolve().parent), "rev-parse", "--show-toplevel"], text=True).strip())
OUT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / ".runtime/native-journal-only-r2"
STAGES = ["01-before", "02-committed-before-kill", "03-after-kill", "04-after-recovery", "05-after-second-restart"]
MINIMAL = ["journal", "mode", "owner", "password", "url", "username"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def main():
    result = dict(kind="Offline reconstruction from retained raw observations, not a new execution or critic verdict", arms={})
    for arm, revision, recovery in [("baseline-701", "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd", False),
                                   ("candidate-7b6f379", "7b6f379a3f8c809d0985a64e883cbadfdd78d135", True)]:
        directory = OUT / arm
        summary = read(directory / "summary.json")
        assert summary["source"]["measured_commit"] == revision
        assert summary["core_pass"] and summary["database_dropped"] and len(summary["runs"]) == 1
        assert "native_economy" not in summary and summary["archived_source_unchanged"]
        freeze = summary["harness_checkout"]["measured_commit"]
        assert freeze == "7be70f73ec6a065849d902e7075d2b76e78bdd21"
        for name, field in [("validate_native_transaction_restart.py", "harness_sha256"), ("native_transaction_restart_probe.gd", "probe_sha256")]:
            source = subprocess.check_output(["git", "show", freeze + ":scripts/" + name], cwd=ROOT)
            assert source == (directory / name).read_bytes() and sha(source) == summary[field]
        archive = subprocess.check_output(["git", "archive", "--format=zip", revision, "game", "backend"], cwd=ROOT)
        assert sha(archive) == summary["archive_sha256"]
        with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
            source_hashes = {name: sha(zipped.read(name)) for name in zipped.namelist() if not name.endswith("/")}
        assert source_hashes == read(directory / "source-manifest.json")
        for name, expected in read(directory / "evidence-manifest.json").items():
            assert sha((directory / name).read_bytes()) == expected, name
        case = directory / "run-1"
        fixture = read(case / "fixture.redacted.json")
        assert fixture["payload"]["expected_price"] == 400
        snapshots = [read(case / (stage + ".json")) for stage in STAGES]
        before, committed = [snapshot["economic_state"] for snapshot in snapshots[:2]]
        assert all(snapshot["economic_state"] == committed for snapshot in snapshots[2:])
        changes = {}
        for table in before:
            left, right = ({row.get("id", (row.get("player_id"), row.get("slot"))): row for row in state[table]} for state in [before, committed])
            assert len(left) == len(before[table]) and len(right) == len(committed[table])
            changes[table] = dict(added=[right[key] for key in right if key not in left],
                                  removed=[left[key] for key in left if key not in right],
                                  changed=[dict(before=left[key], after=right[key]) for key in left if key in right and left[key] != right[key]])
        assert len(changes["operations"]["added"]) == 1 and len(changes["ledger"]["added"]) == 2 and len(changes["audit"]["added"]) == 1
        assert all(not value["removed"] for value in changes.values())
        players_before, players_after = ({row["id"]: row for row in state["players"]} for state in [before, committed])
        buyer, seller = fixture["owner"], fixture["seller"]
        assert players_before[buyer]["credits"] - players_after[buyer]["credits"] == 400
        assert players_after[seller]["credits"] - players_before[seller]["credits"] == 388
        assert sum(row["credits"] for row in before["players"]) - sum(row["credits"] for row in committed["players"]) == 12
        events = [json.loads(line) for line in (case / "timeline.jsonl").read_bytes().splitlines()]
        requests = [event for event in events if event["event"] == "proxy_request" and event["path"] == fixture["path"]]
        assert [event["phase"] for event in requests] == (["send", "recovery"] if recovery else ["send"])
        assert all(event["body"] == fixture["payload"] and type(event["body"]["expected_price"]) is int for event in requests)
        operation = changes["operations"]["added"][0]
        assert operation["id"] == f'{buyer}:buy:{fixture["listing"]}:{fixture["payload"]["idempotency_key"]}'
        assert all(sha(event["raw_utf8"].encode()) == operation["request_hash"] for event in requests)
        upstream = [event for event in events if event["event"] == "proxy_upstream_response" and event["path"] == fixture["path"]]
        assert all(event["status"] == 200 and event["response"] == operation["response"] for event in upstream)
        assert not any(event["event"] == "proxy_response_delivered" and event["phase"] == "send" and event["path"] == fixture["path"] for event in events)
        ordered_names = ["response_held_before_any_client_headers", "postgresql_snapshot", "kill_requested", "kill_confirmed", "held_response_discarded", "native_started"]
        order = []
        for name in ordered_names:
            matches = [(i, row) for i, row in enumerate(events) if row["event"] == name
                       and (name != "postgresql_snapshot" or row["name"] == "02-committed-before-kill")
                       and (name != "native_started" or row["phase"] == "recovery")]
            assert len(matches) == 1
            order.append(matches[0])
        assert [index for index, _ in order] == sorted(index for index, _ in order)
        assert [row["monotonic_ns"] for _, row in order] == sorted(row["monotonic_ns"] for _, row in order)
        purchase_values = [fixture[name] for name in ["path", "item", "listing", "seller"]] + [fixture["payload"]["idempotency_key"]]
        inputs, logins, completed = [], [], {}
        for phase, stdout_name, stage_index in [("send", "killed-client", 1), ("recovery", "recovery", 3), ("second-restart", "second-restart", 4)]:
            config = read(case / (phase + ".fixture.redacted.json"))
            binding = read(case / (phase + ".launch-inputs.json"))
            assert binding["redacted_fixture_sha256"] == sha((case / (phase + ".fixture.redacted.json")).read_bytes())
            assert binding["environment_sha256"] == sha(json.dumps(binding["environment"], sort_keys=True, separators=(",", ":")).encode())
            assert len(binding["command"]) == 7 and binding["command"][1:4] == ["--headless", "--verbose", "--path"] and binding["command"][5] == "--script"
            assert binding["cwd"] == binding["command"][4]
            assert [name for name in binding["environment"] if name.startswith("SIGHTBREAK_")] == ["SIGHTBREAK_RECEIPT_FIXTURE"]
            assert "DATABASE_URL" not in binding["environment"]
            assert not any(value in json.dumps(dict(environment=binding["environment"], command=binding["command"])) for value in purchase_values)
            native = [json.loads(line.removeprefix("NATIVE_RECEIPT_EVENT ")) for line in (case / (stdout_name + ".stdout.txt")).read_text().splitlines() if line.startswith("NATIVE_RECEIPT_EVENT ")]
            reads = [row for row in native if row["event"] == "fixture_read"]
            assert len(reads) == 1
            read_event = reads[0]
            assert read_event["keys"] == binding["keys"] == sorted(config)
            assert read_event["sha256"] == binding["fixture_sha256"] and read_event["bytes"] == binding["fixture_bytes"]
            expected = {name: value for name, value in binding["source_file_sha256"].items() if name != "driver"}
            assert read_event["source_file_sha256"] == expected
            assert expected["probe"] == summary["probe_sha256"] and binding["source_file_sha256"]["driver"] == summary["harness_sha256"]
            for name in ["economy_ui", "economy_api", "transaction_journal"]:
                assert expected[name] == source_hashes.get("game/scripts/ui/" + name + ".gd", "")
            launch = next(row for row in events if row["event"] == "native_started" and row["phase"] == phase)
            prepared = next(row for row in events if row["event"] == "native_inputs_prepared" and row["phase"] == phase)
            assert launch["pid"] == read_event["pid"] and launch["command"] == binding["command"]
            assert prepared["monotonic_ns"] <= launch["monotonic_ns"]
            if phase != "send":
                assert sorted(config) == MINIMAL and config["mode"] == "retry"
                assert not any(value in json.dumps(config) for value in purchase_values)
                assert all(config[name] == fixture[name] for name in ["url", "journal", "username", "password", "owner"])
                completed[phase] = next(row for row in native if row["event"] == "completed")
            auth = next(row for row in native if row["event"] == "authenticated")
            assert auth["ok"] and auth["owner"] == buyer and auth["pid"] == launch["pid"]
            sessions = [row for row in snapshots[stage_index]["sessions"] if row["token_hash"] == auth["token_sha256"]]
            assert len(sessions) == 1 and sessions[0]["player_id"] == buyer
            logins.append(auth["token_sha256"])
            inputs.append(dict(phase=phase, pid=launch["pid"], keys=read_event["keys"], fixture_sha256=read_event["sha256"],
                               bytes=read_event["bytes"], native_read_matches_prelaunch=True,
                               source_file_hashes_match_exact_git=True, original_purchase_absent=phase != "send"))
            assert not (case / (stdout_name + ".stderr.txt")).read_bytes()
        assert len(set(logins)) == 3
        assert completed["recovery"]["result"] == (operation["response"] if recovery else {})
        assert completed["second-restart"]["result"] == {} and not completed["second-restart"]["pending_on_start"]
        assert all(not row["pending_after"] for row in completed.values())
        journals = [read(case / (name + ".json")) for name in ["journal-before-kill", "journal-after-kill", "journal-after-recovery", "journal-after-second-restart"]]
        assert journals[0] == journals[1] and journals[0]["exists"] == recovery
        assert not journals[2]["exists"] and not journals[3]["exists"]
        if recovery:
            raw_journal = (case / "journal-before-kill.raw.json").read_bytes()
            assert raw_journal == (case / "journal-after-kill.raw.json").read_bytes()
            assert sha(raw_journal) == journals[0]["sha256"] and len(raw_journal) == journals[0]["bytes"]
        result["arms"][arm] = dict(revision=revision, harness_commit=freeze, recovered=recovery, price=400,
            actual_inputs=inputs, actual_purchase_count_by_phase={phase: sum(row["phase"] == phase for row in requests) for phase in ["send", "recovery", "second-restart"]},
            database=summary["database"], database_dropped=True, actual_row_changes=changes,
            complete_economic_state_equal_after_commit=True, session_digests=logins,
            ordering_events=[row for _, row in order], journal_survived=recovery,
            original_request_bytes_equal_on_recovery=requests[0]["raw_utf8"] == requests[-1]["raw_utf8"] if recovery else None)
    destination = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ROOT / ".runtime/journal-only-evidence-verification.json"
    destination.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({arm: {key: value for key, value in row.items() if key in ["revision", "harness_commit", "recovered", "price", "database", "database_dropped", "actual_inputs", "actual_purchase_count_by_phase"]} for arm, row in result["arms"].items()}, indent=2))
    print("Verification artifact", destination, "SHA256", sha(destination.read_bytes()))


if __name__ == "__main__":
    main()
