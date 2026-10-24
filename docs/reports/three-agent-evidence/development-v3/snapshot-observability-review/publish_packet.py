"""Docs-only archival copying/hashing. No Git, game, reviewed script, or test execution."""
import datetime
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

assert sys.version_info[:3] == (3, 13, 15), sys.version
BASE = Path(r"C:\Users\blith\AppData\Local\Temp\opencode")
OUT = Path(__file__).resolve().parent
EXPECTED_OUT = BASE / "sightbreak-v3/docs/reports/three-agent-evidence/development-v3/snapshot-observability-review"
assert OUT == EXPECTED_OUT.resolve()
LIMIT = 4 * 1024 * 1024
ROOTS = {
    "outcome_only": BASE / "sol-snapshot-neutral-verdict-20261023T005224059323Z",
    "post_freeze_binding": BASE / "sol-snapshot-bound-source-review-20261023T010608524006Z",
}
PINS = {
    "outcome_only": {
        "report.md": "30fe9a84632e559dbd9316e399df6c643285a3c38b4b363d7d912bfaf055484f",
        "machine-judgments.json": "bb61be5f52133d425d7f4f8b6f086e57398d736f133db65c3c87189834140888",
        "SHA256-LEDGER.json": "f19a450468b91fffd6260eadd9ecdd48026cc62bad961607c442607f0b646fb5",
        "FREEZE-RECEIPT.json": "d6011331986f18e348345be31b324a05254dc4c48b61ef09131a794afbd40025",
        "FROZENUTC.txt": "53e66e8be8dd4dc533e69bdd711b239bee4fa1a7957aca2e7311d04513891dfb",
    },
    "post_freeze_binding": {
        "report.md": "7a69ccfda7d2c3c9042d14285ebb6d0a520009fefb551f90f28d6dc27174d1c1",
        "machine-judgments.json": "a2957db88e9c2e0a178be07412317c1ea5b8d84399aeefb9f030ad00d9d79f6d",
        "shipping-source-hashes.json": "2d4c0b58af41a3de1be5d41eb16e26b316161fbf360f8bd4a114b585cf39ce12",
        "command-index.json": "002da2fd17881e3b3c1a1cae3c3d01c7fa26f7c9cf70b04f1997f44b4ed93a83",
        "SHA256-LEDGER.json": "f394dc7565936cd496a8feb64f643bc25339479c533ec174506ed9d0017081de",
        "FINAL-RECEIPT.json": "5f61b1b398c71e3d9a0b594ccb3a9f552406683e18768545b3ae5a24793c5b1e",
        "REVIEWUTC.txt": "f3d3058bd76104096828f2804b4dd43919a125b7276aae92ce5b5c239231d299",
    },
}
ZIP_INPUT = BASE / "ack-cache-boundary-neutral-r1/blind-traces.zip"
ZIP_SHA = "70a15c1f330c7e9e51bf50fc52673243dd3cbe62dd030acdc60081eba6443517"
COMMANDS = list(range(1, 17)) + [19, 22, 25, 26, 27, 28, 29, 30, 31, 33, 34, 35, 36, 38, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 152, 185, 186, 187]
assert len(COMMANDS) == len(set(COMMANDS)) == 45
initial_authored = {"REPORT.md", ".gitattributes", ".gitignore", "publish_packet.py"}
assert {p.relative_to(OUT).as_posix() for p in OUT.rglob("*") if p.is_file()} == initial_authored, "Destination is not a new packet; do not overwrite existing work"
copied = []
utc = datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_new(relative, data):
    relative_path = Path(relative)
    assert not relative_path.is_absolute() and ".." not in relative_path.parts
    path = OUT / relative_path
    assert path.resolve().is_relative_to(OUT)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)
    assert path.read_bytes() == data, relative


def write_json(relative, value):
    write_new(relative, (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def verify_external(root_key):
    root = ROOTS[root_key]
    pins = PINS[root_key]
    for name, expected in pins.items():
        assert sha((root / name).read_bytes()) == expected, (root_key, name, "frozen pin mismatch")
    ledger = json.loads((root / "SHA256-LEDGER.json").read_bytes())
    expected = {row["path"]: {"sha256": row["sha256"], "bytes": row["bytes"]} for row in ledger["files"]}
    for name, digest in pins.items():
        data = (root / name).read_bytes()
        if name in expected:
            assert expected[name]["sha256"] == digest
        else:
            expected[name] = {"sha256": digest, "bytes": len(data)}
    actual_names = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    assert actual_names == set(expected), (root_key, "unexpected/missing external artifacts", sorted(actual_names ^ set(expected)))
    for name, entry in expected.items():
        data = (root / name).read_bytes()
        assert len(data) == entry["bytes"] and sha(data) == entry["sha256"], (root_key, name)
    return expected


external = {key: verify_external(key) for key in ROOTS}
assert len(external["outcome_only"]) == 22
assert len(external["post_freeze_binding"]) == 937
assert sha(ZIP_INPUT.read_bytes()) == ZIP_SHA


def copy_frozen(root_key, source_relative, destination):
    entry = external[root_key][source_relative]
    data = (ROOTS[root_key] / source_relative).read_bytes()
    assert len(data) == entry["bytes"] and sha(data) == entry["sha256"]
    write_new(destination, data)
    copied.append({"path": destination, "external_root": root_key, "source_relative_path": source_relative, **entry})


# The whole original freeze is retained, including all raw rows/checks and original ledgers.
memory = io.BytesIO()
archive_members = []
with zipfile.ZipFile(memory, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
    for name, entry in sorted(external["outcome_only"].items()):
        data = (ROOTS["outcome_only"] / name).read_bytes()
        assert sha(data) == entry["sha256"]
        info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 3
        info.external_attr = 0o100644 << 16
        archive.writestr(info, data, compresslevel=9)
        archive_members.append({"path": name, **entry})
archive_bytes = memory.getvalue()
write_new("outcome-only/frozen-original.zip", archive_bytes)
with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
    assert archive.namelist() == [entry["path"] for entry in archive_members]
    for entry in archive_members:
        data = archive.read(entry["path"])
        assert len(data) == entry["bytes"] and sha(data) == entry["sha256"]
for name in ("report.md", "machine-judgments.json", "FROZENUTC.txt", "SHA256-LEDGER.json", "FREEZE-RECEIPT.json"):
    copy_frozen("outcome_only", name, "outcome-only/" + name)
zip_bytes = ZIP_INPUT.read_bytes()
write_new("outcome-only/blind-traces.zip", zip_bytes)
copied.append({"path": "outcome-only/blind-traces.zip", "external_root": "original_zip_input", "source_absolute_path": str(ZIP_INPUT), "bytes": len(zip_bytes), "sha256": sha(zip_bytes)})

post_root_files = ["report.md", "machine-judgments.json", "shipping-source-hashes.json", "command-index.json", "SHA256-LEDGER.json", "FINAL-RECEIPT.json", "REVIEWUTC.txt", "verify_binding.py", "git_object_audit.py", "finalize_review.py"]
post_structured = [name for name in external["post_freeze_binding"] if name.startswith("auditraw/") and "/" not in name[len("auditraw/"):] and not Path(name).name[:3].isdigit()]
post_selected = post_root_files + sorted(post_structured) + [f"auditraw/{number:03d}.{suffix}" for number in COMMANDS for suffix in ("command.json", "stdout.bin", "stderr.bin", "exit.txt")]
assert len(post_selected) == len(set(post_selected)) == 207
for name in post_selected:
    copy_frozen("post_freeze_binding", name, "binding/" + name)
released = {
    "released/controller/mapping.json": "objects/docs/closure/controller/mapping.json",
    "released/controller/capture.json": "objects/docs/closure/controller/capture.json",
    "released/controller/release-receipt.json": "objects/docs/closure/controller/release-receipt.json",
    "released/original-publication-audit.json": "objects/docs/original/publication-audit.json",
    "released/original-checksums.json": "objects/docs/original/checksums.json",
    "released/closure-checksums.json": "objects/docs/closure/checksums.json",
}
for destination, name in released.items():
    copy_frozen("post_freeze_binding", name, destination)
assert sha((OUT / "released/controller/mapping.json").read_bytes()) == "bb9e66d695b9d079fc5b55c99ba985aee4133052e55245b1de0315aeca7483b5"
assert sha((OUT / "released/controller/capture.json").read_bytes()) == "68aefbc9a5b3f0d397078b144f5e40993fdbe2e183a8154dcb1eecb488e393b2"

index = json.loads((ROOTS["post_freeze_binding"] / "command-index.json").read_bytes())
indexed = {row["number"]: row for row in index["commands"]}
roles = {
    1: "Released documentation tree", 2: "Original commitment/evidence tree",
    3: "Exact released mapping", 4: "Exact released capture", 5: "Released receipt",
    15: "Original committed controller commitments", 16: "Original Git ZIP bytes",
    19: "Measured harness production script tree", 22: "Shipping production script tree",
    25: "V2 production script tree", 26: "V2-to-shipping game path delta",
    27: "Shipping-to-measured-harness path delta", 28: "Measured production-API probe",
    29: "Measured exporter", 30: "Measured imported support driver",
    31: "Shipping movement predictor", 33: "Snapshot buffer", 34: "Snapshot schema",
    35: "Movement step", 36: "Production actor", 38: "V2 movement predictor",
    45: "Production ACK diagnostic helper", 46: "Exact predictor diagnostic additions",
    47: "Match defaults/protocol/reconciliation/coalescing", 48: "Input stream / pending seed sanitization",
    49: "Input gate", 50: "Hit-history helper", 51: "Shipping server tree", 52: "V2 server tree",
    53: "Full V2 game tree", 54: "Full measured harness game tree", 55: "Full shipping game tree",
    152: "Privacy snapshot source / move_ack origin", 185: "Closure production script tree",
    186: "Empty harness-to-closure source delta", 187: "Original-to-closure scoped docs delta",
}
selected_commands = []
for number in COMMANDS:
    entry = indexed[number]
    prefix = f"binding/auditraw/{number:03d}"
    assert sha((OUT / (prefix + ".stdout.bin")).read_bytes()) == entry["stdout_sha256"]
    assert sha((OUT / (prefix + ".stderr.bin")).read_bytes()) == entry["stderr_sha256"]
    selected_commands.append({"historical_number": number, "role": roles.get(number, "Historical requested documentation/checksum or expected-absence evidence"), "argv": entry["argv"], "exit_code": entry["exit_code"], "stdout": prefix + ".stdout.bin", "stdout_sha256": entry["stdout_sha256"], "stderr": prefix + ".stderr.bin", "stderr_sha256": entry["stderr_sha256"], "command_record": prefix + ".command.json", "exit_receipt": prefix + ".exit.txt"})
write_json("SOURCE-EVIDENCE.json", {"schema": "archived-source-evidence-selection-v1", "new_git_commands_executed": 0, "selected_historical_commands": len(COMMANDS), "full_historical_command_count": len(indexed), "full_original_index": "binding/command-index.json", "source_line_references": "Line numbers in binding/report.md apply to these exact raw stdout bodies or the full external object captures; no source body was rewritten", "selected": selected_commands})

aliases = {}
for entry in copied:
    aliases.setdefault(entry["sha256"], []).append(entry["path"])
for entry in archive_members:
    aliases.setdefault(entry["sha256"], []).append("outcome-only/frozen-original.zip!" + entry["path"])
selected_external_post = {entry["source_relative_path"] for entry in copied if entry["external_root"] == "post_freeze_binding"}
omitted = []
for name, entry in sorted(external["post_freeze_binding"].items()):
    if name in selected_external_post:
        continue
    equivalent = sorted(set(aliases.get(entry["sha256"], [])))
    if equivalent:
        reason = "File occurrence omitted; identical bytes are published at the listed alternate location(s)"
    elif name.startswith("__pycache__/"):
        reason = "Interpreter cache; original hash retained in the full external ledger"
    elif name.startswith("objects/"):
        reason = "Unselected bulk asset/source/object capture; all source hash records and the necessary production/harness bodies are retained"
    else:
        reason = "Raw record for an unselected historical Git retrieval; full original index and full external ledger retained"
    omitted.append({"source_relative_path": name, **entry, "reason": reason, "equivalent_published_byte_locations": equivalent})
write_json("OMISSIONS.json", {
    "schema": "compact-publication-precise-omissions-v1",
    "outcome_only": {"external_files": 22, "all_members_preserved_in": "outcome-only/frozen-original.zip", "omitted_members": []},
    "post_freeze_binding": {"external_root": str(ROOTS["post_freeze_binding"]), "external_files": len(external["post_freeze_binding"]), "selected_external_file_occurrences": len(selected_external_post), "omitted_external_file_occurrences": len(omitted), "selected_historical_command_numbers": COMMANDS, "unselected_historical_command_numbers": sorted(set(indexed) - set(COMMANDS)), "full_external_ledger": "binding/SHA256-LEDGER.json", "full_external_ledger_sha256": PINS["post_freeze_binding"]["SHA256-LEDGER.json"], "omitted": omitted},
    "not_added_or_authenticated": ["Engine executable or a native rerun", "Godot UID generation/registration and import/cache correctness", "Historical actual loaded-script identity or authenticated filesystem/process attestation", "Combined integration CI result", "Source/UID/CI-repair edits at the reported integration cherry-pick"],
})

write_json("EXTERNAL-LEDGERS.json", {
    "schema": "full-external-review-ledger-references-v1",
    "outcome_only": {"external_root": str(ROOTS["outcome_only"]), "external_ledger": str(ROOTS["outcome_only"] / "SHA256-LEDGER.json"), "copied_full_ledger": "outcome-only/SHA256-LEDGER.json", "complete_archival_copy": "outcome-only/frozen-original.zip", "ledger_covered_files": 20, "total_files_including_ledger_and_receipt": 22, "recorded_freeze_utc": "2026-10-23T00:58:57.663009+00:00", "pins": PINS["outcome_only"]},
    "post_freeze_binding": {"external_root": str(ROOTS["post_freeze_binding"]), "external_ledger": str(ROOTS["post_freeze_binding"] / "SHA256-LEDGER.json"), "copied_full_ledger": "binding/SHA256-LEDGER.json", "copied_full_command_index": "binding/command-index.json", "ledger_covered_files": 935, "total_files_including_ledger_and_receipt": 937, "recorded_finalization_utc": "2026-10-23T01:20:10.637759+00:00", "pins": PINS["post_freeze_binding"], "local_mirror_is_partial": True, "precise_omissions": "OMISSIONS.json"},
    "original_zip": {"external_path": str(ZIP_INPUT), "published_path": "outcome-only/blind-traces.zip", "sha256": ZIP_SHA},
    "original_external_artifacts_modified": False,
})

# Hash-only preservation recheck, not a rerun of any review, test, or workload.
for key in ROOTS:
    assert verify_external(key) == external[key], key
assert sha(ZIP_INPUT.read_bytes()) == ZIP_SHA
write_json("PUBLICATION.json", {
    "schema": "snapshot-observability-docs-publication-v1",
    "publication_utc": utc,
    "python_executable": sys.executable,
    "python_version": sys.version,
    "activity": "Copying, lossless archival packaging, recorded-metadata indexing, and byte/SHA-256 verification only",
    "tests_or_reviews_rerun": False,
    "git_commands_executed": 0,
    "native_engine_db_network_services_github": False,
    "repository_writes_scope": str(OUT),
    "game_source_other_reports_index_stage_commit_branch_edits": False,
    "original_freezes_rechecked_unchanged": True,
    "copy_byte_mismatches": 0,
    "archive_member_byte_mismatches": 0,
    "selected_historical_git_commands": 45,
    "main_reported_integration": {"cherry_pick": "456d9be", "shipping_source": "0fbce120d8c17db58596d280f7d8401ab2aa0937", "independently_inspected_in_this_publication": False, "acceptance_scope_as_reported": "ADDITIVE OBSERVABILITY ONLY", "combined_ci_at_handoff": "not run; no combined result asserted here", "uid_metadata_owner": "Main; not generated, imported, or authenticated here"},
    "new_approval_release_or_runtime_assurance_claim": False,
    "size_limit_bytes": LIMIT,
    "checksum_rule": "SHA256SUMS covers all published files except itself, including PACKET-LEDGER.json; both manifest digests returned out of band",
})

def inventory():
    return [{"path": p.relative_to(OUT).as_posix(), "bytes": p.stat().st_size, "sha256": sha(p.read_bytes())} for p in sorted(OUT.rglob("*")) if p.is_file()]


before_ledger = inventory()
write_json("PACKET-LEDGER.json", {
    "schema": "snapshot-observability-compact-packet-sha256-ledger-v1",
    "publication_utc": utc,
    "size_limit_bytes": LIMIT,
    "files": before_ledger,
    "copy_origins": copied,
    "outcome_complete_archive": {"path": "outcome-only/frozen-original.zip", "sha256": sha(archive_bytes), "container_metadata_is_not_historical_execution_evidence": True, "member_count": 22, "members": archive_members},
    "external_pins": PINS,
    "omissions": "OMISSIONS.json",
    "excluded_from_this_ledger_for_hash_self_reference": ["PACKET-LEDGER.json", "SHA256SUMS"],
    "complete_final_coverage": "SHA256SUMS covers this ledger and every other published regular file except SHA256SUMS itself",
})
sums_entries = inventory()
write_new("SHA256SUMS", "".join(entry["sha256"] + "  " + entry["path"] + "\n" for entry in sums_entries).encode("utf-8"))

# Final readback is byte/hash validation only. Nothing is written after SHA256SUMS.
final = inventory()
expected_paths = {entry["path"] for entry in sums_entries} | {"SHA256SUMS"}
assert {entry["path"] for entry in final} == expected_paths
for entry in sums_entries:
    assert sha((OUT / entry["path"]).read_bytes()) == entry["sha256"], entry["path"]
for entry in copied:
    assert sha((OUT / entry["path"]).read_bytes()) == entry["sha256"], entry["path"]
with zipfile.ZipFile(OUT / "outcome-only/frozen-original.zip") as archive:
    for entry in archive_members:
        assert sha(archive.read(entry["path"])) == entry["sha256"], entry["path"]
for key in ROOTS:
    assert verify_external(key) == external[key]
assert sha(ZIP_INPUT.read_bytes()) == ZIP_SHA
total_bytes = sum(entry["bytes"] for entry in final)
assert total_bytes <= LIMIT, (total_bytes, LIMIT)
print(json.dumps({"published_directory": str(OUT), "main_report": str(OUT / "REPORT.md"), "published_file_count": len(final), "published_bytes": total_bytes, "limit_bytes": LIMIT, "packet_ledger_sha256": sha((OUT / "PACKET-LEDGER.json").read_bytes()), "sha256sums_sha256": sha((OUT / "SHA256SUMS").read_bytes()), "report_sha256": sha((OUT / "REPORT.md").read_bytes()), "outcome_full_archive_members": 22, "copied_historical_git_commands": 45, "post_freeze_omitted_external_file_occurrences": len(omitted), "mismatches": 0, "original_freezes_unchanged": True, "tests_native_or_git_rerun": False, "exit_code": 0}, indent=2))
