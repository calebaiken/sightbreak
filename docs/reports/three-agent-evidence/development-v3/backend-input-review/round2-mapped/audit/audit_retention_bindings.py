"""Independent retained-byte/body/state audit; serial offline; no retained code run."""
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from auditlib import ROOT, SOURCES, check, digest, finish, git_bytes, load, local, save_json

prekey = load((ROOT / "PRE_KEY_FREEZE_VERIFIED.json").read_bytes())
if not prekey["all_checks_passed"]:
    raise SystemExit("Freeze first")
key = load((ROOT / "second-key-verified.json").read_bytes())
archive = "866e2e1f38461fa245557c9015b6c1a1a97ad745"
raw_root = key["raw_git_path"]
packet_root = Path(key["packet_path"])
_, tree_raw = git_bytes(["ls-tree", "-r", "-z", archive, "--", raw_root])
tree = {}
for record in tree_raw.split(b"\0"):
    if not record:
        continue
    header, path = record.split(b"\t", 1)
    mode, kind, oid = header.decode().split()
    if kind != "blob":
        raise ValueError("Expected blob only")
    tree[path.decode().removeprefix(raw_root + "/")] = oid
check("raw archive inventory exactly matches released key", set(tree) == set(key["raw_files"]))

# Reuse already captured immutable blobs, then fetch only unique remaining IDs.
cache = {}
for line in (ROOT / "commands.jsonl").read_text().splitlines():
    command = load(line)
    args = command["argv"]
    if command["exit"] == 0 and len(args) >= 3 and args[-3:-1] == ["cat-file", "blob"]:
        cache[args[-1]] = ROOT / command["stdout"]


def raw_file(path):
    oid = tree[path]
    if oid not in cache:
        entry, data = git_bytes(["cat-file", "blob", oid])
        cache[oid] = ROOT / entry["stdout"]
    data = cache[oid].read_bytes()
    actual_oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if actual_oid != oid:
        raise ValueError("Git blob identity mismatch")
    return data


for path, expected in key["raw_files"].items():
    data = raw_file(path)
    check(f"released raw Git file hash {path}", digest(data) == expected)
    SOURCES.append({"kind": "git", "commit": archive, "path": raw_root + "/" + path, "blob": tree[path],
                    "bytes": len(data), "sha256": digest(data), "capture": cache[tree[path]].relative_to(ROOT).as_posix()})
check("r2 original raw manifest key anchor", digest(raw_file("SHA256SUMS.txt")) == key["raw_manifest_sha256"])

for path, expected in key["packet_files"].items():
    data = local(packet_root / path)
    check(f"frozen neutral file hash {path}", digest(data) == expected)
check("frozen neutral manifest anchor", digest(local(packet_root / "SHA256SUMS.txt")) == prekey["packet_manifest_sha256"])
actual_packet = {path.relative_to(packet_root).as_posix() for path in packet_root.rglob("*") if path.is_file()}
check("neutral packet inventory exact", actual_packet == set(key["packet_files"]))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def artifact(role, label, reference):
    relative, expected = reference["file"], reference["sha256"]
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Unsafe artifact reference")
    original = raw_file(role + "/" + relative)
    neutral = (packet_root / label / relative).read_bytes()
    check(f"raw-neutral artifact exact bytes {label}/{relative}", original == neutral and digest(original) == expected)
    return original


totals = {"workloads": 0, "received_responses": 0, "timed": 0, "warmups": 0,
          "state_arrays": 0, "state_aggregate_hashes": 0, "row_instances": 0,
          "empty_state_arrays": 0}
records = []
bodies_by_pair = {}
monetary_tables = {"audit", "game_tickets", "ledger", "listings", "loadouts", "operations", "rate_buckets", "rewards"}
source_records = []
for label in ("M", "V"):
    mapping = key["variants"][label]
    role = mapping["original_role"]
    original_raw = raw_file(role + "/measurement.json")
    neutral_raw = (packet_root / label / "measurement.json").read_bytes()
    original, neutral = load(original_raw), load(neutral_raw)
    check(f"{label} original measurement binds key", digest(original_raw) == mapping["original_measurement_sha256"])
    check(f"{label} neutral measurement binds key", digest(neutral_raw) == mapping["neutral_measurement_sha256"])
    check(f"{label} full withheld header matches original", {name: value for name, value in original.items() if name != "rows"} == mapping["original_header"])
    check(f"{label} raw-neutral all rows precise-number equality",
          json.loads(original_raw, parse_float=Decimal)["rows"] == json.loads(neutral_raw, parse_float=Decimal)["rows"])
    check(f"{label} initial/final reported source identical", original["source"] == original["final_source"])
    check(f"{label} recorded source clean (not a byte derivation)", original["source"]["backend_dirty"] == "")
    check(f"{label} reported completion and DB cleanup", original["completed"] is True and original["database_dropped"] is True)
    expected_executed = "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd" if label == "M" else "8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf"
    expected_runtime = "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd" if label == "M" else "4a8e9ea73aa8b286d9f1751b0a6b485479737294"
    check(f"{label} exact executed/runtime/harness identities", original["source"]["commit"] == expected_executed
          and original["runtime_reference"]["commit"] == expected_runtime
          and original["harness_commit"] == "8070436f53dd98e9529e8c21ea7b0f7e3ecb6daf")
    source_records.append({"label": label, "executed": expected_executed, "runtime": expected_runtime,
                           "recorded_app_sha256": original["source"]["backend_files"]["backend/app.py"],
                           "original_imported_fixture_captured": "imported_fixture" in original,
                           "app_snapshot_present_in_r2_raw_files": any(path.endswith("/app.py") or path.endswith("/app.py.txt") for path in key["raw_files"])})
    for index, row in enumerate(original["rows"]):
        totals["workloads"] += 1
        expected_bytes = artifact(role, label, row["expected_response"])
        expected = load(expected_bytes)
        check(f"{label} row {index} expected canonical JSON bytes", canonical(expected) == expected_bytes)
        responses = row["warmups"] + [sample["response"] for sample in row["samples"]]
        check(f"{label} row {index} 2 warmup/10 timed records", len(row["warmups"]) == 2 and len(row["samples"]) == 10)
        observed_hashes = set()
        for response_index, response in enumerate(responses):
            totals["received_responses"] += 1
            totals["warmups" if response_index < 2 else "timed"] += 1
            received = artifact(role, label, response["raw"])
            received_value = load(received)
            check(f"{label} row {index} response {response_index} no dropped top-level fields", set(received_value) == {"trades"})
            canonical_value = {"trades": sorted(received_value["trades"], key=lambda trade: trade["id"])}
            actual_canonical = canonical(canonical_value)
            retained_canonical = artifact(role, label, response["canonical"])
            check(f"{label} row {index} response {response_index} received bytes canonical hash/content",
                  actual_canonical == retained_canonical and digest(actual_canonical) == response["canonical"]["sha256"]
                  and canonical_value == expected and response["matches_expected"] is True and response["status"] == 200)
            observed_hashes.add(digest(actual_canonical))
        check(f"{label} row {index} retained actual response hash set", sorted(observed_hashes) == row["actual_response_sha256s"])
        bodies_by_pair[(label, index)] = digest(expected_bytes)
        states = {}
        for phase in ("before", "after"):
            state = row["state_" + phase]
            table_rows = {}
            for name, reference in state["tables"].items():
                raw_array = artifact(role, label, reference)
                values = load(raw_array)
                check(f"{label} row {index} {phase}/{name} full array/hash/count",
                      isinstance(values, list) and all(isinstance(value, dict) for value in values)
                      and len(values) == reference["row_count"] and reference["representation"] == "full_rows"
                      and canonical(values) == raw_array and sorted(values, key=canonical) == values)
                table_rows[name] = values
                totals["state_arrays"] += 1
                totals["row_instances"] += len(values)
                totals["empty_state_arrays"] += not values
            check(f"{label} row {index} {phase} all 12 tables", set(table_rows) == monetary_tables | {"players", "sessions", "items", "trades"})
            aggregate = digest(canonical(table_rows))
            check(f"{label} row {index} {phase} independent aggregate state hash", aggregate == state["sha256"])
            totals["state_aggregate_hashes"] += 1
            check(f"{label} row {index} {phase} monetary/history tables not exercised", all(not table_rows[name] for name in monetary_tables)
                  and all(player["credits"] == 0 for player in table_rows["players"]))
            states[phase] = aggregate
        check(f"{label} row {index} retained interval net row equality", states["before"] == states["after"] and row["read_only"] is True)
        records.append({"label": label, "index": index, "trades": row["trades"], "per_side": row["items_per_side"],
                        "response_records": len(responses), "canonical_actual_sha256s": sorted(observed_hashes),
                        "state_before_sha256": states["before"], "state_after_sha256": states["after"],
                        "recorded_query_counts": row["query_counts"]})

for index in range(7):
    check(f"pair {index} independently received canonical bodies match", bodies_by_pair[("M", index)] == bodies_by_pair[("V", index)])
for name, expected in [("scripts/benchmark_trade_reads.py", "harness_sha256"),
                       ("scripts/verify_trade_read_artifacts.py", "artifact_verifier_sha256"),
                       ("backend/tests/test_trade_reads.py", "fixture_sha256")]:
    data = (ROOT / "objects/r2-executed" / name).read_bytes()
    check(f"recorded common {expected} matches exact 807 Git bytes",
          all(digest(data) == key["variants"][label]["original_header"][expected] for label in ("M", "V")))
check("r2 has not retained imported fixture __file__ capture", all(not item["original_imported_fixture_captured"] for item in source_records))
check("r2 has not retained original app working bytes snapshot", all(not item["app_snapshot_present_in_r2_raw_files"] for item in source_records))
save_json("RETENTION_WORKLOAD_LEDGER.json", {"totals": totals, "sources": source_records, "records": records,
          "cross_variant_state_hash_equality_not_assumed": True, "monetary_tables_empty": sorted(monetary_tables)})
finish("RETENTION_BINDING_AUDIT.json", {"totals": totals, "source_binding_limit": "R2 records app fingerprint/clean label but no app byte snapshot/derivation or actual imported fixture identity. R3 posthoc evidence is separate.",
                                      "original_first_app_failure_retained": True})
