"""Create-only post-restart byte revalidation/qualification, not a test runner."""
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import sys

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 13):
    raise SystemExit("Approved CPython 3.13 required.")

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT.parent / "source-review"
checks = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check(name, condition, **details):
    checks.append({"check": name, "passed": bool(condition), **details})


def write_new(path, data):
    with path.open("xb") as stream:
        stream.write((json.dumps(data, indent=2) + "\n").encode())


key = json.loads((ROOT / "released-key/mapping.json").read_bytes())
initial = json.loads((ROOT / "binding/BINDING_VALIDATION.json").read_bytes())
qualification = json.loads((ROOT / "binding/LINE_ENDING_QUALIFICATION.json").read_bytes())
anchors = initial["original_anchors"]
for path, anchor in [(ROOT / "verdict/NEUTRAL_VERDICT.md", "verdict"),
                     (ROOT / "verdict/FROZEN.json", "freeze"),
                     (ROOT / "packet/SHA256SUMS.txt", "packet_manifest"),
                     (ROOT / "released-key/mapping.json", "released_key"),
                     (SOURCE / "original/SOURCE_REVIEW.md", "source_review"),
                     (SOURCE / "original/isolated_assurance_controls.py", "unexecuted_controls")]:
    check(f"post-restart supplied anchor {anchor}", sha(path.read_bytes()) == anchors[anchor])

copied = []
for root in [ROOT, SOURCE]:
    ledger = json.loads((root / "COPY_LEDGER.json").read_bytes())
    for entry in ledger["files"]:
        data = (root / entry["published"]).read_bytes()
        check(f"retained copy stable {root.name}/{entry['published']}",
              sha(data) == entry["sha256"] and len(data) == entry["bytes"])
        origin = Path(entry["origin"])
        # Only origins explicitly recorded in our completed bounded copy ledger.
        exists = origin.is_file()
        exact = exists and origin.read_bytes() == data
        check(f"original still available and exact {root.name}/{entry['published']}", exact,
              original_available=exists)
        copied.append({"published_group": root.name, "path": entry["published"],
                       "original_available": exists, "exact_bytes_reverified": exact})

commands = json.loads((ROOT / "raw/collect-commands.json").read_bytes())
for command in commands:
    for kind in ("stdout", "stderr"):
        data = (ROOT / command[f"{kind}_path"]).read_bytes()
        check(f"raw command {kind} retained {command[f'{kind}_path']}",
              sha(data) == command[f"{kind}_sha256"] and len(data) == command[f"{kind}_bytes"])
    check(f"explicit successful nonempty Git result {command['stdout_path']}",
          command["returncode"] == 0 and command["stdout_bytes"] > 0)

original_manifest = (ROOT / "original-measurements/source-SHA256SUMS.txt").read_bytes()
check("source evidence manifest remains key-bound", sha(original_manifest) == key["source_manifest_sha256"])
manifest_entries = {}
for line in original_manifest.decode().splitlines():
    match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
    if match is None:
        raise ValueError("Invalid retained original manifest line")
    digest, path = match.groups()
    if path in manifest_entries:
        raise ValueError("Duplicate retained original manifest path")
    manifest_entries[path] = digest

for label in ("K", "R"):
    mapping = key["variants"][label]
    original_raw = (ROOT / f"original-measurements/{label}-measurement.json").read_bytes()
    neutral_raw = (ROOT / "packet" / mapping["neutral_file"]).read_bytes()
    original = json.loads(original_raw, parse_float=Decimal)
    neutral = json.loads(neutral_raw, parse_float=Decimal)
    manifest_path = mapping["original_git_path"].removeprefix("docs/reports/backend-trade-read-v3/")
    check(f"{label} original manifest entry binds measurement bytes",
          manifest_entries[manifest_path] == sha(original_raw) == mapping["original_sha256"])
    check(f"{label} neutral rows remain exact numeric/string objects after restart",
          len(original["rows"]) == len(neutral["rows"]) == 7 and original["rows"] == neutral["rows"])
    check(f"{label} neutral bytes remain key-bound", sha(neutral_raw) == mapping["neutral_sha256"])

check("initial candidate fingerprint failure remains explicitly retained",
      len(initial["failed_checks"]) == 1 and initial["failed_checks"][0]["passed"] is False
      and "K recorded app fingerprint" in initial["failed_checks"][0]["check"]
      and initial["all_recorded_checks_passed"] is False)
check("line-ending attempts do not claim a match", qualification["matching_constructions"] == []
      and all(not item["matches_K_recorded_fingerprint"] for item in qualification["constructions"]))

copied_originals = {key["variants"][label]["original_git_path"].removeprefix("docs/reports/backend-trade-read-v3/")
                    for label in ("K", "R")}
omitted = [{"path": path, "manifest_sha256": digest,
            "git_reference": f"{key['source_evidence_commit']}:docs/reports/backend-trade-read-v3/{path}",
            "status": "Listed original manifest only; payload not inspected, verified, or copied"}
           for path, digest in manifest_entries.items() if path not in copied_originals]
write_new(ROOT / "OMISSIONS_AND_REFERENCES.json", {
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "copied_in_full": ["All 7 first verdict/freeze files", "All 8 first neutral packet files",
                       "Released first mapping.json only", "All 17 completed source-review files"],
    "original_local_references": {"verdict": str(Path(initial['checks'][0].get('origin', r'C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-blind-verdict-20261019T194014Z'))),
                                  "packet": key["packet_path"], "source_manifest": key["source_manifest_path"],
                                  "original_K_measurement": key["variants"]["K"]["original_file_path"],
                                  "original_R_measurement": key["variants"]["R"]["original_file_path"],
                                  "source_review": str(Path(r'C:\Users\blith\AppData\Local\Temp\opencode\sol-backend-source-critic-20261019T194154Z'))},
    "original_evidence_git_commit": key["source_evidence_commit"],
    "omitted_owner_payloads": omitted,
    "never_retained_in_first_packet_not_a_publication_omission": ["Actual response bodies and independent actual-response digests",
                                                               "Authoritative before/after snapshots and their digests",
                                                               "Original measured app.py byte snapshot in this bounded publication"],
    "uninspected_and_not_published": ["Second-round packet/key and verdict", "Current working-tree runtime/tests",
                                     "Other reports/agents' files; no owner tests or services rerun"],
    "no_checksum_claim_for_unpublished_payloads": True})

receipt = {
    "schema": "append-only-qualified-first-round-publication-v1",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "post_restart_revalidation": checks,
    "publication_integrity_revalidation_passed": all(item["passed"] for item in checks),
    "failed_revalidation_checks": [item for item in checks if not item["passed"]],
    "original_binding_check_history": {"passed": len(initial["checks"]) - len(initial["failed_checks"]),
                                       "failed": len(initial["failed_checks"]), "all_passed": False},
    "complete_measured_app_byte_binding": "NOT_ESTABLISHED_K_APP_FINGERPRINT",
    "K_reported_app_sha256": qualification["K_recorded_app_sha256"],
    "K_git_app_sha256": qualification["constructions"][0]["sha256"],
    "source_identity_binding": "Released first key and original headers bind reported K/R commits and Git trees; not execution authentication.",
    "permitted_acceptance": "Frozen retained SQL statement-count preference only; no new independent performance verdict.",
    "response_and_state_acceptance": "NOT_ESTABLISHED; actual response/state payloads not retained in first round",
    "source_safety": "INSPECTION_ONLY; no current shipping runtime/test certification",
    "controls": "UNEXECUTED; no retained scripts rerun",
    "second_round": "NOT_INSPECTED",
    "supersedes": [],
    "preservation": "All original artifacts and failed checks remain exact and authoritative for what they recorded; this receipt only adds qualification.",
    "copied_original_revalidation": copied,
    "original_anchors": anchors}
write_new(ROOT / "binding/QUALIFIED_RECEIPT.json", receipt)
write_new(SOURCE / "PUBLICATION_STATUS.json", {
    "created_utc": receipt["created_utc"], "scope": "Completed pinned source review exact-byte publication",
    "source_review_sha256": anchors["source_review"], "controls_sha256": anchors["unexecuted_controls"],
    "controls": "UNEXECUTED", "all_original_source_files": 17,
    "source_safety": "INSPECTION_ONLY", "original_files_superseded": [],
    "publication_integrity_revalidation_passed": receipt["publication_integrity_revalidation_passed"]})
print(json.dumps({"checks": len(checks), "failed_revalidation_checks": receipt["failed_revalidation_checks"],
                  "complete_measured_app_byte_binding": receipt["complete_measured_app_byte_binding"],
                  "original_failure_retained": True, "controls": "UNEXECUTED"}, indent=2))
