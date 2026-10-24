"""Seal the separate post-freeze review; never write to the original freeze/repo."""
import datetime
import hashlib
import json
from pathlib import Path
import sys

assert sys.version_info[:3] == (3, 13, 15)
OUT = Path(__file__).resolve().parent
OLD = OUT.parent / "sol-snapshot-neutral-verdict-20261023T005224059323Z"
ZIP = OUT.parent / "ack-cache-boundary-neutral-r1" / "blind-traces.zip"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_new(name, data):
    with (OUT / name).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


result = json.loads((OUT / "auditraw/04-binding-result.json").read_bytes())
judgments = json.loads((OUT / "machine-judgments.json").read_bytes())
closure = json.loads((OUT / "auditraw/05-closure-source-and-reference-scan.json").read_bytes())
assert result["status"] == "pass" and result["checks"] == result["passed"] == 830 and result["failed"] == 0
assert judgments["verification"]["passed"] == 830
assert judgments["release_approval"] is False
assert judgments["probe_and_exporter"]["historical_process_authenticated"] is False
assert closure["harness_to_closure_source_delta"] == ""
assert closure["closure_scripts_tree"] == "3111af5423d229b9b04b958de9588c4ab537c1ee"
assert (OUT / "auditraw/04-binding.exit.txt").read_text().strip() == "0"
old_expected = {
    "report.md": "30fe9a84632e559dbd9316e399df6c643285a3c38b4b363d7d912bfaf055484f",
    "machine-judgments.json": "bb61be5f52133d425d7f4f8b6f086e57398d736f133db65c3c87189834140888",
    "SHA256-LEDGER.json": "f19a450468b91fffd6260eadd9ecdd48026cc62bad961607c442607f0b646fb5",
    "FREEZE-RECEIPT.json": "d6011331986f18e348345be31b324a05254dc4c48b61ef09131a794afbd40025",
}
for name, expected in old_expected.items():
    assert sha(OLD / name) == expected, "Original freeze changed: " + name
old_ledger = json.loads((OLD / "SHA256-LEDGER.json").read_bytes())
assert len(old_ledger["files"]) == 20
for item in old_ledger["files"]:
    assert sha(OLD / item["path"]) == item["sha256"], "Original artifact changed: " + item["path"]
assert sha(ZIP) == "70a15c1f330c7e9e51bf50fc52673243dd3cbe62dd030acdc60081eba6443517"

commands = []
for path in sorted((OUT / "auditraw").glob("[0-9][0-9][0-9].command.json")):
    record = json.loads(path.read_bytes())
    number = record["number"]
    stem = f"auditraw/{number:03d}"
    assert sha(OUT / (stem + ".stdout.bin")) == record["stdout_sha256"]
    assert sha(OUT / (stem + ".stderr.bin")) == record["stderr_sha256"]
    assert int((OUT / (stem + ".exit.txt")).read_text()) == record["exit_code"]
    assert record["argv"][5] in ("cat-file", "ls-tree", "rev-parse", "diff-tree", "diff")
    assert record["exit_code"] == (128 if number in (7, 8, 9) else 0)
    commands.append({**record, "raw_stdout": stem + ".stdout.bin", "raw_stderr": stem + ".stderr.bin", "raw_exit": stem + ".exit.txt"})
assert [c["number"] for c in commands] == list(range(1, len(commands) + 1))
utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
write_new("command-index.json", {"schema": "read-only-git-object-command-index-v1", "git_command_count": len(commands), "expected_absence_exits_128": [7, 8, 9], "all_other_exits_zero": True, "commands": commands})
write_new("auditraw/06-prior-freeze-preservation.json", {"verified_utc": utc, "old_directory": str(OLD), "expected_hashes_verified": old_expected, "old_ledger_files_rechecked": 20, "unchanged": True, "old_directory_writes": 0, "external_zip_sha256": sha(ZIP)})
write_new("auditraw/06-finalization.json", {"review_finalized_utc": utc, "python_executable": sys.executable, "python_version": sys.version, "final_binding_checks_passed": 830, "git_commands_verified": len(commands), "old_freeze_unchanged": True, "source_or_runtime_edits": False, "native_workload_executed": False, "network_or_services": False, "exit_code": 0})
with (OUT / "auditraw/06-finalization.exit.txt").open("x", encoding="ascii", newline="\n") as stream:
    stream.write("0\n")
with (OUT / "REVIEWUTC.txt").open("x", encoding="ascii", newline="\n") as stream:
    stream.write(utc + "\n")
excluded = {"SHA256-LEDGER.json", "FINAL-RECEIPT.json"}
files = []
for path in sorted(OUT.rglob("*")):
    if path.is_file() and path.relative_to(OUT).as_posix() not in excluded:
        files.append({"path": path.relative_to(OUT).as_posix(), "bytes": path.stat().st_size, "sha256": sha(path)})
ledger = {
    "schema": "sol-post-freeze-source-review-sha256-ledger-v1",
    "review_finalized_utc": utc,
    "git_pins": judgments["git_pins"],
    "source_hash_comparison": "shipping-source-hashes.json",
    "raw_git_command_index": "command-index.json",
    "external_input": {"path": str(ZIP), "sha256": sha(ZIP)},
    "prior_freeze_preservation": {"path": str(OLD), "hashes": old_expected, "ledger_files_verified": 20},
    "files": files,
    "excluded_for_hash_self_reference": sorted(excluded),
}
write_new("SHA256-LEDGER.json", ledger)
receipt = {
    "schema": "sol-post-freeze-source-review-final-receipt-v1",
    "review_finalized_utc": utc,
    "report_sha256": sha(OUT / "report.md"),
    "machine_judgments_sha256": sha(OUT / "machine-judgments.json"),
    "shipping_source_hashes_sha256": sha(OUT / "shipping-source-hashes.json"),
    "command_index_sha256": sha(OUT / "command-index.json"),
    "ledger_sha256": sha(OUT / "SHA256-LEDGER.json"),
    "utc_marker_sha256": sha(OUT / "REVIEWUTC.txt"),
    "ledger_included_files": len(files),
    "git_commands_with_exact_raw_outputs": len(commands),
    "prior_outcome_freeze_unchanged": True,
    "prior_outcome_freeze_receipt_sha256": old_expected["FREEZE-RECEIPT.json"],
    "mapping_sha256": judgments["commitment_binding"]["mapping_sha256"],
    "capture_sha256": judgments["commitment_binding"]["capture_sha256"],
    "zip_sha256": judgments["commitment_binding"]["zip_sha256"],
    "judgment": judgments["judgment"],
    "historical_execution_authenticated": False,
    "release_approval": False,
    "content_hash_snapshot_not_filesystem_write_lock": True,
}
write_new("FINAL-RECEIPT.json", receipt)
# Read-back only from here onward; no file is modified after the ledger/receipt.
for item in files:
    assert sha(OUT / item["path"]) == item["sha256"], item["path"]
assert sha(OUT / "SHA256-LEDGER.json") == receipt["ledger_sha256"]
for name, expected in old_expected.items():
    assert sha(OLD / name) == expected
for item in old_ledger["files"]:
    assert sha(OLD / item["path"]) == item["sha256"]
print(json.dumps({"output_directory": str(OUT), **receipt, "final_receipt_sha256": sha(OUT / "FINAL-RECEIPT.json"), "all_ledger_hashes_and_original_freeze_reverified": True, "exit_code": 0}, indent=2))
