"""Package immutable observations only. Does not launch clients/services or access SQL."""
from pathlib import Path
import hashlib
import json
import re
import secrets
import shutil
import subprocess
import zipfile

REPO = Path(__file__).resolve().parents[1]
EVIDENCE = "49268b8702c44a6a19adfc743727f5aad2a10e8b"
HARNESS = "31438cbcea6ef08a131ae312c65b94f7e3e882c3"
PREFIX = "docs/reports/native-pg-restart-evidence/"
ARMS = [
    ("r9/baseline", "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd"),
    ("r10/candidate-7b6f379", "7b6f379a3f8c809d0985a64e883cbadfdd78d135"),
]
STAGES = ["01-before.json", "02-committed-before-kill.json", "03-after-kill.json",
          "04-after-recovery.json", "05-after-second-restart.json"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def git(*args, data=None):
    return subprocess.check_output(["git", "-C", str(REPO), *args], input=data)


def load_objects():
    tree = git("ls-tree", "-rz", EVIDENCE, "--", PREFIX,
               "scripts/validate_native_transaction_restart.py", "scripts/native_transaction_restart_probe.gd")
    blobs = {}
    for entry in tree.split(b"\0"):
        if not entry:
            continue
        meta, name = entry.split(b"\t", 1)
        mode, kind, oid = meta.decode().split()
        if kind == "blob":
            blobs[name.decode()] = oid
    names = sorted(blobs)
    output = git("cat-file", "--batch", data="".join(blobs[name] + "\n" for name in names).encode())
    offset = 0
    contents = {}
    for name in names:
        end = output.index(b"\n", offset)
        oid, kind, size = output[offset:end].decode().split()
        assert oid == blobs[name] and kind == "blob"
        size = int(size)
        contents[name] = output[end + 1:end + 1 + size]
        offset = end + size + 2
    assert offset == len(output)
    return blobs, contents


def neutralize(data, aliases):
    operations = []
    replacements = {}
    for category, original, neutral in aliases:
        for spelling in {original, original.replace("\\", "/"), original.replace("/", "\\")}:
            for text, form in [(spelling, "literal"), (json.dumps(spelling)[1:-1], "JSON-escaped")]:
                replacements[text.encode()] = (neutral.encode(), category, form)
    for old, (new, category, form) in sorted(replacements.items(), key=lambda row: -len(row[0])):
        count = data.count(old)
        if count:
            data = data.replace(old, new)
            operations.append(dict(category=category, original_text=old.decode(), replacement_text=new.decode(),
                                   representation=form, occurrences=count))
    return data, operations


def differences(before, after):
    result = {}
    for table in before:
        def key(row):
            return row.get("id", (row.get("player_id"), row.get("slot")))
        left, right = ({key(row): row for row in data[table]} for data in (before, after))
        result[table] = {
            "added_rows": [right[k] for k in right if k not in left],
            "removed_rows": [left[k] for k in left if k not in right],
            "changed_rows": [{"before": left[k], "after": right[k]} for k in left if k in right and left[k] != right[k]],
        }
    return result


def semantics(files):
    snapshots = [json.loads(files[name]) for name in STAGES]
    context, result = (json.loads(files[name]) for name in ["fixture.redacted.json", "result.json"])
    timeline = [json.loads(line) for line in files["timeline.jsonl"].splitlines()]
    requests = [row for row in timeline if row["event"] == "proxy_request" and row["path"] == context["path"]]
    operation_id = f'{context["owner"]}:buy:{context["listing"]}:{context["payload"]["idempotency_key"]}'
    operation = next(row for row in snapshots[1]["economic_state"]["operations"] if row["id"] == operation_id)
    first = result["purchases"][0]
    recovery = [row for row in requests if row["phase"] == "recovery"]
    phase_index = {"send": 1, "recovery": 3, "second-restart": 4}
    sessions = []
    for login in result["logins"]:
        matched = [row for row in snapshots[phase_index[login["phase"]]]["sessions"] if row["token_hash"] == login["token_sha256"]]
        sessions.append(dict(observed_login=login, matching_postgresql_session_rows=matched,
                             matches_original_owner=bool(matched) and all(row["player_id"] == context["owner"] for row in matched)))
    return {
        "status": "Derived comparison aid; independently check the supplied observations. Not a critic verdict.",
        "actors_and_request": {key: context[key] for key in ["owner", "seller", "item", "listing", "path", "payload"]},
        "actual_economic_table_row_counts": {name: {table: len(rows) for table, rows in snapshot["economic_state"].items()} for name, snapshot in zip(STAGES, snapshots)},
        "actual_row_deltas": {name: differences(snapshots[0 if i == 1 else 1]["economic_state"], snapshots[i]["economic_state"])
                              for i, name in enumerate(STAGES) if i > 0},
        "complete_economic_state_equal_to_commit": {STAGES[i]: snapshots[i]["economic_state"] == snapshots[1]["economic_state"] for i in [2, 3, 4]},
        "actual_persisted_operation": operation,
        "initial_committed_http_result": first["response"],
        "native_recovery_result": result["phases"][0]["completed"]["result"],
        "initial_http_result_equals_stored_operation": first["response"] == operation["response"],
        "native_recovery_result_equals_initial_http_result": result["phases"][0]["completed"]["result"] == first["response"],
        "observed_purchase_requests": requests,
        "recovery_body_bytes_equal_initial": recovery[0]["raw_utf8"] == requests[0]["raw_utf8"] if len(recovery) == 1 else None,
        "strict_integer_expected_prices": all(type(row["body"]["expected_price"]) is int for row in requests),
        "same_account_fresh_sessions": sessions,
        "distinct_login_digest_count": len({row["token_sha256"] for row in result["logins"]}),
        "second_restart_purchase_request_count": sum(row["phase"] == "second-restart" for row in requests),
        "ordering_events": [row for row in timeline if row["event"] in {
            "native_started", "response_held_before_any_client_headers", "postgresql_snapshot", "kill_requested",
            "native_finished", "kill_confirmed", "held_response_discarded"}],
    }


def main():
    blobs, originals = load_objects()
    nonce = secrets.token_hex(8)
    base = Path("C:/Users/blith/AppData/Local/Temp/opencode") / ("receipt-review-" + nonce)
    packet, controller = base / "critic", base / "CONTROLLER"
    packet.mkdir(parents=True)
    controller.mkdir()
    labels = ["Set-" + secrets.token_hex(4).upper() for _ in ARMS]
    assert len(set(labels)) == 2
    secrets.SystemRandom().shuffle(labels)
    key = dict(evidence_commit=EVIDENCE, frozen_measured_harness_commit=HARNESS, labels={}, files=[],
               transformations_policy={
                   "replacements": "Only exact absolute executable, project, external-probe, and private journal path strings; literal and JSON-escaped slash variants. Each occurrence is logged per file.",
                   "no_row_pruning": "All five SQL snapshots per case are retained byte-for-byte from immutable published artifacts, including all economic rows, all session rows and PostgreSQL metadata.",
                   "untouched": "All original timestamps, nanosecond integers, process IDs, database identifiers, entity UUIDs, economic values, request/response strings, session digests and journal captures remain unchanged unless an explicitly logged absolute path occurs.",
                   "source_identity_withheld": "Original arm/folder labels, source commits/trees, original path/hash bindings, reports, top-level arm summaries, source/cache manifests, executable and harness/probe hashes are controller-only.",
                   "original_redactions": "The immutable inputs already redact plaintext passwords and bearer credentials. Those redactions are retained; no secret is reintroduced.",
                   "byte_claim": "Only files with byte_identical=true equal the immutable original artifact bytes. Path-neutralized files are transformed copies, never described as raw-byte-identical.",
               }, ancillary=[])
    packet_manifest = {}
    overview = {"groups": {}, "comparison_kind": "Observation-derived aids only; no preferred implementation label or critic verdict."}

    def binding(path):
        data = originals[path]
        return dict(commit=EVIDENCE, path=path, git_blob=blobs[path], sha256=digest(data), bytes=len(data))

    def emit(relative, data, kind, source=None, changes=None, derived_from=None):
        destination = packet / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        packet_manifest[relative] = dict(sha256=digest(data), bytes=len(data), kind=kind)
        if source:
            key["files"].append(dict(packet_path=relative, packet_sha256=digest(data), packet_bytes=len(data),
                                     original=binding(source), byte_identical=data == originals[source],
                                     transformations=changes or []))
        elif derived_from:
            key["files"].append(dict(packet_path=relative, packet_sha256=digest(data), generated=True,
                                     derivation=kind, original_inputs=[binding(path) for path in derived_from]))

    for label, (arm, revision) in zip(labels, ARMS):
        summary_path = PREFIX + arm + "/summary.json"
        summary = json.loads(originals[summary_path])
        key["labels"][label] = dict(original_arm=arm, measured_source_commit=revision,
                                    source_identity=summary["source"], harness_sha256=summary["harness_sha256"],
                                    probe_sha256=summary["probe_sha256"], executable_sha256=summary["godot_sha256"],
                                    original_summary=binding(summary_path), cases={})
        overview["groups"][label] = []
        for index in range(1, 4):
            prefix = PREFIX + arm + f"/run-{index}/"
            source_paths = sorted(path for path in originals if path.startswith(prefix))
            context = json.loads(originals[prefix + "fixture.redacted.json"])
            timeline = [json.loads(line) for line in originals[prefix + "timeline.jsonl"].splitlines()]
            command = next(row["command"] for row in timeline if row["event"] == "native_started")
            aliases = [("executable_path", command[0], "[EXECUTABLE]/native-client"),
                       ("project_path", command[command.index("--path") + 1], "[PROJECT_ROOT]"),
                       ("external_probe_path", command[command.index("--script") + 1], "[EXTERNAL_PROBE]/driver.gd"),
                       ("private_journal_path", context["journal"], "[ISOLATED_STATE]/pending.json")]
            case = f"{label}/case-{index:02d}"
            files = {}
            for source in source_paths:
                name = source[len(prefix):]
                data, operations = neutralize(originals[source], aliases)
                files[name] = data
                kind = "identity-neutralized observation copy" if operations else "unchanged published observation bytes"
                emit(case + "/" + name, data, kind, source=source, changes=operations)
            for stage in STAGES:
                assert files[stage] == originals[prefix + stage]
            comparison = semantics(files)
            emit(case + "/semantic-comparison.json", encoded(comparison), "derived from full supplied records; no expected-fixture substitution", derived_from=source_paths)
            key["labels"][label]["cases"][f"case-{index:02d}"] = dict(original_prefix=prefix, aliases=aliases)
            overview["groups"][label].append(dict(case=f"case-{index:02d}", expected_price=context["payload"]["expected_price"],
                                                  before_economic_row_counts=comparison["actual_economic_table_row_counts"][STAGES[0]],
                                                  before_session_row_count=len(json.loads(files[STAGES[0]])["sessions"])))

    all_case_paths = [path for path in originals if any(path.startswith(PREFIX + arm + "/run-") for arm, _ in ARMS)]
    emit("OBSERVED_COMPARISON.json", encoded(overview), "observed prices and unfiltered initial row counts", derived_from=all_case_paths)
    readme = (REPO / ".runtime/neutral_receipt_review_readme.md").read_bytes()
    emit("README.md", readme, "fixed reviewer quality bar, method and limitations")

    for source in sorted(originals):
        if "/native-economy-original/" in source or "/native-economy-dns-calibrated/" in source:
            part = source.split("/candidate-7b6f379/", 1)[1]
            destination = controller / "ancillary" / part
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(originals[source])
            key["ancillary"].append(dict(controller_relative_path="ancillary/" + part, original=binding(source), byte_identical=True))
    for source in ["scripts/validate_native_transaction_restart.py", "scripts/native_transaction_restart_probe.gd"]:
        destination = controller / "frozen-source" / Path(source).name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(originals[source])
        key.setdefault("withheld_sources", []).append(binding(source))

    # Packaging integrity only: no application, database, native process or test is run.
    forbidden = [revision.encode() for _, revision in ARMS] + [EVIDENCE.encode(), HARNESS.encode(),
                 b"candidate", b"baseline", b"cda6372", b"1fa754b", b"sightbreak-pr18", b"C:\\Users", b"C:/Users"]
    for path in packet.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            assert not any(term.lower() in data.lower() for term in forbidden), path
            assert not re.search(rb"receipt-oracle-[0-9a-f]{32}|Bearer [A-Za-z0-9_-]{20,}", data), path
    for row in key["files"]:
        if "original" not in row:
            continue
        source = row["original"]["path"]
        result = originals[source]
        for operation in row["transformations"]:
            old, new = operation["original_text"].encode(), operation["replacement_text"].encode()
            assert result.count(old) == operation["occurrences"]
            result = result.replace(old, new)
        assert result == (packet / row["packet_path"]).read_bytes()
    manifest = dict(schema=1, hash_algorithm="SHA-256", scope="Every ZIP payload except MANIFEST.json itself.",
                    source_mapping="withheld by controller outside this packet", files=packet_manifest)
    manifest_bytes = encoded(manifest)
    (packet / "MANIFEST.json").write_bytes(manifest_bytes)
    zip_path = base / ("receipt-review-" + nonce + ".zip")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(packet.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(packet).as_posix(), date_time=(2000, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(zip_path) as archive:
        assert set(archive.namelist()) == set(packet_manifest) | {"MANIFEST.json"}
        for name, record in packet_manifest.items():
            assert digest(archive.read(name)) == record["sha256"]
        assert archive.read("MANIFEST.json") == manifest_bytes
    zip_bytes = zip_path.read_bytes()
    key["packet"] = dict(zip_path=str(zip_path), zip_sha256=digest(zip_bytes), zip_bytes=len(zip_bytes),
                         manifest_sha256=digest(manifest_bytes), payload_files=len(packet_manifest),
                         zip_container="sorted entries; fixed 2000-01-01 metadata time; 0644; DEFLATE level 9; no comment",
                         git_blob_object_id_computed_uncommitted=git("hash-object", "--stdin", data=zip_bytes).decode().strip())
    key["packaging_verification"] = dict(full_economic_stage_files_byte_identical=30, case_count=6,
        source_label_and_absolute_path_scan="passed", exact_transformation_replay="passed", zip_manifest_verification="passed",
        application_database_native_test_executions=0,
        changed_observation_files=sum(not row["byte_identical"] for row in key["files"] if "byte_identical" in row),
        unchanged_observation_files=sum(row["byte_identical"] for row in key["files"] if "byte_identical" in row))
    key_path = controller / "mapping.json"
    key_bytes = encoded(key)
    key_path.write_bytes(key_bytes)
    shutil.copyfile(__file__, controller / "packaging.py")
    pins = dict(packet=key["packet"], controller_key_path=str(key_path), controller_key_sha256=digest(key_bytes),
                critic_directory=str(packet), controller_directory=str(controller), verification=key["packaging_verification"])
    (controller / "pins.json").write_bytes(encoded(pins))
    print(json.dumps(pins, indent=2))


if __name__ == "__main__":
    main()
