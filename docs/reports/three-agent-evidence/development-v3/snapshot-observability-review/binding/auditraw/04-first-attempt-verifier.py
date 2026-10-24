"""Read-only, offline binding checks. Never executes source under review."""
import datetime
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import zipfile

_spec = importlib.util.spec_from_file_location("git_object_audit", Path(__file__).resolve().parent / "git_object_audit.py")
_audit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_audit)
OUT, git, sha, write_json = _audit.OUT, _audit.git, _audit.sha, _audit.write_json

assert sys.version_info[:3] == (3, 13, 15)
CLOSURE = "37924d1531029b7429ee9289a266a497388001b4"
ORIGINAL = "d5c738d367f3ba80f3cfc679e104a009d0a72183"
HARNESS = "b4b3db044fc762fbb5c9eb69da8713b316fdb496"
SHIPPING = "0fbce120d8c17db58596d280f7d8401ab2aa0937"
V2 = "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd"
SCRIPT_TREE = "3111af5423d229b9b04b958de9588c4ab537c1ee"
ZIP_SHA = "70a15c1f330c7e9e51bf50fc52673243dd3cbe62dd030acdc60081eba6443517"
MAP_SHA = "bb9e66d695b9d079fc5b55c99ba985aee4133052e55245b1de0315aeca7483b5"
CAPTURE_SHA = "68aefbc9a5b3f0d397078b144f5e40993fdbe2e183a8154dcb1eecb488e393b2"
checks = []


def check(label, actual, expected):
    passed = type(actual) is type(expected) and actual == expected
    checks.append({"check": label, "pass": passed, "actual": actual, "expected": expected})
    return passed


def read(relative):
    return (OUT / "objects" / relative).read_bytes()


def load(relative):
    return json.loads(read(relative))


def tree(commit):
    raw = git(["ls-tree", "-r", "-l", commit, "--", "game"])
    result = {}
    for line in raw.decode("utf-8").splitlines():
        metadata, name = line.split("\t", 1)
        mode, kind, oid, size = metadata.split()
        if name.startswith("game/tests/"):
            continue
        assert kind == "blob" and mode in ("100644", "100755"), (kind, mode, name)
        result[name.removeprefix("game/")] = {"git_blob_oid": oid, "git_blob_bytes": int(size), "mode": mode}
    return result


started = datetime.datetime.now(datetime.timezone.utc).isoformat()
mapping_bytes = read("docs/closure/controller/mapping.json")
capture_bytes = read("docs/closure/controller/capture.json")
mapping = json.loads(mapping_bytes)
capture = json.loads(capture_bytes)
receipt = load("docs/closure/controller/release-receipt.json")
publication_bytes = read("docs/original/publication-audit.json")
publication = json.loads(publication_bytes)
old_sums = load("docs/original/checksums.json")
new_sums = load("docs/closure/checksums.json")
check("mapping.requested_sha256", sha(mapping_bytes), MAP_SHA)
check("capture.requested_sha256", sha(capture_bytes), CAPTURE_SHA)
check("original_commitment.mapping", publication["controller_only_commitments"]["mapping.json"], MAP_SHA)
check("original_commitment.capture", publication["controller_only_commitments"]["capture.json"], CAPTURE_SHA)
check("original_commitment.bytes_unchanged_at_closure", read("docs/closure/publication-audit.json"), publication_bytes)
check("original_commitment.blob_sha256", sha(publication_bytes), "590976fd2abe89cd12e14572e94d5183c4f91fd26aab2239590e4e2a975926ce")
check("release.original_commit", receipt["parent_evidence_commit"], ORIGINAL)
check("release.original_commitment_sha256", receipt["existing_commitment_blob_sha256"], sha(publication_bytes))
check("mapping.identity", mapping, {"sample-M": "baseline", "sample-T": "candidate"})
for name, data in (("mapping.json", mapping_bytes), ("capture.json", capture_bytes)):
    check("release." + name + ".sha256", receipt["released_files"][name]["sha256"], sha(data))
    check("release." + name + ".bytes", receipt["released_files"][name]["bytes"], len(data))
for n in (7, 8, 9):
    check(f"withheld_controller.original_absence_exit[{n}]", int((OUT / "auditraw" / f"{n:03d}.exit.txt").read_text()), 128)

zip_bytes = (OUT.parent / "ack-cache-boundary-neutral-r1" / "blind-traces.zip").read_bytes()
check("frozen_zip.sha256", sha(zip_bytes), ZIP_SHA)
check("original_git.zip_identical", read("docs/original/blind-traces.zip"), zip_bytes)
check("closure_git.zip_identical", read("docs/closure/blind-traces.zip"), zip_bytes)
check("release.zip_sha256", receipt["original_packet_sha256_unchanged"]["docs/reports/ack-cache-boundary-v3/blind-traces.zip"], ZIP_SHA)
zip_members = {}
with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
    check("frozen_zip.crc", archive.testzip(), None)
    for name in archive.namelist():
        zip_members[name] = archive.read(name)

known_old = {"README.md": read("docs/original/README.md"), "blind-traces.zip": zip_bytes, "publication-audit.json": publication_bytes, **{n: b for n, b in zip_members.items() if n.endswith(".json")}}
known_new = {"README.md": read("docs/closure/README.md"), "blind-traces.zip": zip_bytes, "publication-audit.json": publication_bytes, "controller/mapping.json": mapping_bytes, "controller/capture.json": capture_bytes, "controller/release-receipt.json": read("docs/closure/controller/release-receipt.json"), **{n: b for n, b in zip_members.items() if n.endswith(".json")}}
for label, sums, data in (("original", old_sums, known_old), ("closure", new_sums, known_new)):
    for name, value in data.items():
        check(f"checksums.{label}.{name}", sha(value), sums[name])

summary = json.loads((OUT / "auditraw" / "01-docs-trees-freeze.json").read_bytes())
doc_trees = {}
for label, number in (("closure", 1), ("original", 2)):
    entries = {}
    for line in (OUT / "auditraw" / f"{number:03d}.stdout.bin").read_text().splitlines():
        metadata, path = line.split("\t", 1)
        entries[path.rsplit("/", 1)[-1] if "/controller/" not in path else "controller/" + path.rsplit("/", 1)[-1]] = metadata.split()[2]
    doc_trees[label] = entries
for name, data in zip_members.items():
    if not name.endswith(".json"):
        continue
    oid = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
    for label in ("closure", "original"):
        check(f"zip_payload.git_blob_oid.{label}.{name}", oid, doc_trees[label][name])

check("capture.harness_commit", capture["harness_commit"], HARNESS)
check("capture.baseline_commit", capture["baseline_commit"], V2)
check("capture.runtime_commit", capture["runtime_commit"], SHIPPING)
for label in ("harness", "shipping"):
    check("script_tree." + label, summary["trees"][label]["scripts_tree"], SCRIPT_TREE)
source_bindings = [("probe_sha256", "game/tests/ack_cache_boundary_probe.gd"), ("driver_sha256", "scripts/measure_ack_cache_boundary.py"), ("support_driver_sha256", "scripts/measure_prediction_timeline.py")]
for key, path in source_bindings:
    actual = sha(read("harness/" + path))
    check("harness." + key + ".capture", actual, capture[key])
    check("harness." + key + ".original_publication", actual, publication["frozen_git_blob_hashes"][path])
for label, role in mapping.items():
    run = capture["runs"][label]
    check(label + ".role", run["role"], role)
    check(label + ".source_commit", run["source_commit"], V2 if role == "baseline" else HARNESS)
    check(label + ".trace_sha256", run["trace_sha256"], sha(zip_members[label + ".json"]))
    check(label + ".recorded_exit", run["exit"], 0)
    check(label + ".recorded_logged_error", run["logged_error"], False)
    check(label + ".recorded_shipping_unchanged", run["shipping_after_identical"], True)
    check(label + ".recorded_probe_command", run["command"][5], "res://tests/ack_cache_boundary_probe.gd")
    check(label + ".log_sha_matches_committed_checksum", run["log_sha256"], new_sums[label + ".log"])

trees = {"baseline": tree(V2), "candidate": tree(HARNESS), "shipping": tree(SHIPPING)}
check("candidate_and_shipping.complete_nontest_game_blob_map", trees["candidate"], trees["shipping"])
for role in ("baseline", "candidate"):
    check(role + ".reported_shipping_path_set", sorted(capture["shipping_sha256_by_source"][role]), sorted(trees[role]))

blob_cache = {}
files = []
for role in ("baseline", "candidate"):
    for path, meta in sorted(trees[role].items()):
        oid = meta["git_blob_oid"]
        if oid not in blob_cache:
            blob_cache[oid] = git(["cat-file", "blob", oid], save="by-oid/" + oid + ".bin")
        raw = blob_cache[oid]
        actual_oid = hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()
        check(role + "." + path + ".raw_oid", actual_oid, oid)
        check(role + "." + path + ".raw_size", len(raw), meta["git_blob_bytes"])
        expected = capture["shipping_sha256_by_source"][role][path]
        raw_sha = sha(raw)
        matched = "raw_git_blob" if raw_sha == expected else None
        crlf_sha = None
        if matched is None and b"\r" not in raw and b"\0" not in raw:
            try:
                raw.decode("utf-8", errors="strict")
                crlf_sha = sha(raw.replace(b"\n", b"\r\n"))
                if crlf_sha == expected:
                    matched = "pure_lf_to_crlf_only"
            except UnicodeDecodeError:
                pass
        check(role + "." + path + ".reported_hash_exact_or_demonstrated_eol_only", matched is not None, True)
        files.append({"role": role, "source_commit": V2 if role == "baseline" else HARNESS, "shipping_path": path, **meta, "git_blob_sha256": raw_sha, "reported_measured_sha256": expected, "match_kind": matched, "lf_to_crlf_sha256": crlf_sha, "lf_count": raw.count(b"\n"), "cr_count": raw.count(b"\r"), "source_object_capture": "objects/by-oid/" + oid + ".bin", "historical_filesystem_measurement_authenticated": False})

prediction = read("shipping/game/scripts/network/movement_prediction.gd")
v2_prediction = read("v2/game/scripts/network/movement_prediction.gd")
additions = [
    b'const AckSnapshotDiagnostics := preload("res://scripts/network/ack_snapshot_diagnostics.gd")\n',
    b'var snapshot_diagnostics := AckSnapshotDiagnostics.new()\n',
    b'\tsnapshot_diagnostics.clear()\n',
    b'\t\tsnapshot_diagnostics.begin_epoch(current_epoch)\n',
    b'\tsnapshot_diagnostics.observe(state, current_epoch, enabled)\n',
]
projected = prediction
for line in additions:
    check("prediction.exact_added_line_occurs_once." + line.decode().strip(), projected.count(line), 1)
    projected = projected.replace(line, b"", 1)
check("prediction.remove_only_five_diagnostic_lines_restores_v2_exact_bytes", projected, v2_prediction)
changed = sorted(path for path in set(trees["baseline"]) | set(trees["candidate"]) if trees["baseline"].get(path) != trees["candidate"].get(path))
check("shipping.runtime_changed_paths", changed, ["scripts/network/ack_snapshot_diagnostics.gd", "scripts/network/movement_prediction.gd"])
server = json.loads((OUT / "auditraw" / "03-server-trees.json").read_bytes())
check("server.tree_identical", server["shipping"], server["v2"])
match = read("shipping/game/scripts/gameplay/match.gd")
check("match.protocol6", b"const PROTOCOL_VERSION := 6\n" in match, True)
check("match.prediction_default_false", b"var _prediction_enabled := false\n" in match, True)
check("match.prediction_config_still_opt_in", b'_prediction_enabled = bool(options.get("prediction", OS.get_cmdline_user_args().has("--network-prediction")))' in match, True)
check("match.hit_history_recording_default_false", b'bool(options.get("record_hit_history", false))' in match, True)
check("match.hit_history_only_two_references", match.count(b"_hit_history"), 2)
helper = read("shipping/game/scripts/network/ack_snapshot_diagnostics.gd")
check("helper.capacity120", b"const MAX_SAMPLES := 120\n" in helper, True)
check("helper.anchor_kind", b'const ANCHOR_KIND := "first_observed_snapshot_not_consumption"\n' in helper, True)

# Byte values in check logs are represented by their content hashes, never coerced into text.
for item in checks:
    for key in ("actual", "expected"):
        if isinstance(item[key], bytes):
            item[key] = {"bytes": len(item[key]), "sha256": sha(item[key])}
counts = {role: {"files": sum(f["role"] == role for f in files), "raw_git_blob": sum(f["role"] == role and f["match_kind"] == "raw_git_blob" for f in files), "pure_lf_to_crlf_only": sum(f["role"] == role and f["match_kind"] == "pure_lf_to_crlf_only" for f in files), "unexplained": sum(f["role"] == role and f["match_kind"] is None for f in files)} for role in ("baseline", "candidate")}
result = {
    "started_utc": started,
    "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "status": "pass" if all(c["pass"] for c in checks) else "fail",
    "checks": len(checks), "passed": sum(c["pass"] for c in checks), "failed": sum(not c["pass"] for c in checks),
    "shipping_hash_match_counts": counts,
    "unique_git_blobs_read": len(blob_cache),
    "unique_git_blob_bytes": sum(len(b) for b in blob_cache.values()),
    "runtime_changed_paths": changed,
    "mapping": mapping,
    "verified_git_sources": {"closure": CLOSURE, "original_commitments": ORIGINAL, "harness": HARNESS, "shipping": SHIPPING, "v2": V2, "candidate_and_shipping_scripts_tree": SCRIPT_TREE},
    "checksums_scope": {"original_checked": sorted(known_old), "closure_checked": sorted(known_new), "original_not_content_read": sorted(set(old_sums) - set(known_old)), "closure_not_content_read": sorted(set(new_sums) - set(known_new))},
    "historical_execution_status": "Hash-bound author-run attestation; not authenticated process attestation; no rerun, engine/cache inspection or native execution",
}
write_json("shipping-source-hashes.json", {"schema": "post-freeze-shipping-hash-comparison-v1", "counts": counts, "files": files})
write_json("auditraw/04-binding-checks.json", checks)
write_json("auditraw/04-binding-result.json", result)
exit_code = 0 if result["status"] == "pass" else 1
(OUT / "auditraw" / "04-binding.exit.txt").write_text(str(exit_code) + "\n", encoding="ascii")
print(json.dumps(result, indent=2))
sys.exit(exit_code)
