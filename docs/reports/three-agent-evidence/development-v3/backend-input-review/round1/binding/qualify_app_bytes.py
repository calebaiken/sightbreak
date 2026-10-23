"""Byte arithmetic on retained publication inputs only; no code/tests executed.

Keep the failed initial raw/uniform-CRLF check. This separate append-only receipt
tries explicitly named line-ending constructions, never current runtime files.
"""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import sys

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 13):
    raise SystemExit("Approved CPython 3.13 required.")

ROOT = Path(__file__).resolve().parents[1]
key = json.loads((ROOT / "released-key/mapping.json").read_bytes())
commands = json.loads((ROOT / "raw/collect-commands.json").read_bytes())


def app_data(object_id):
    command = next(item for item in commands if item["argv"][-3:] == ["cat-file", "blob", object_id])
    data = (ROOT / command["stdout_path"]).read_bytes()
    if command["returncode"] != 0 or hashlib.sha256(data).hexdigest() != command["stdout_sha256"]:
        raise ValueError("Captured Git object does not match its successful raw command record.")
    return data


candidate = app_data("16f33c94da490c77a8ab930b88d8fc0662f3fa4c")
baseline = app_data("bb15f054d622fc4f6164248a2f4453d20a3e7fff")
before = baseline.replace(b"\r\n", b"\n").splitlines(keepends=True)
after = candidate.replace(b"\r\n", b"\n").splitlines(keepends=True)
matching = difflib.SequenceMatcher(a=before, b=after, autojunk=False)
inherited_crlf_new_lf = bytearray()
inherited_lf_new_crlf = bytearray()
regions = []
for kind, a0, a1, b0, b1 in matching.get_opcodes():
    lines = b"".join(after[b0:b1])
    inherited_crlf_new_lf.extend(lines.replace(b"\n", b"\r\n") if kind == "equal" else lines)
    inherited_lf_new_crlf.extend(lines if kind == "equal" else lines.replace(b"\n", b"\r\n"))
    regions.append({"opcode": kind, "baseline_lines_0based_halfopen": [a0, a1],
                    "candidate_lines_0based_halfopen": [b0, b1]})

expected = key["variants"]["K"]["withheld_original_header"]["source"]["backend_files"]["backend/app.py"]
variants = {
    "raw_candidate_git_bytes": candidate,
    "all_LF": candidate.replace(b"\r\n", b"\n"),
    "all_CRLF": candidate.replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"),
    "unchanged_lines_CRLF_added_or_replaced_lines_LF": bytes(inherited_crlf_new_lf),
    "unchanged_lines_LF_added_or_replaced_lines_CRLF": bytes(inherited_lf_new_crlf),
}
results = []
for name, data in variants.items():
    digest = hashlib.sha256(data).hexdigest()
    results.append({"construction": name, "bytes": len(data), "sha256": digest,
                    "matches_K_recorded_fingerprint": digest == expected,
                    "CRLF_count": data.count(b"\r\n"),
                    "bare_LF_count": data.count(b"\n") - data.count(b"\r\n"),
                    "same_content_after_CRLF_to_LF_only": data.replace(b"\r\n", b"\n") == candidate.replace(b"\r\n", b"\n")})

receipt = {
    "schema": "post-freeze-explicit-line-ending-qualification-v1",
    "created_utc": datetime.now(timezone.utc).isoformat(),
    "original_failed_check_retained": "BINDING_VALIDATION.json: K raw exact/uniform LF-to-CRLF binding false",
    "original_verdict_and_freeze_unchanged": True,
    "no_prior_file_superseded": True,
    "K_recorded_app_sha256": expected,
    "candidate_app_blob": "16f33c94da490c77a8ab930b88d8fc0662f3fa4c",
    "baseline_app_blob": "bb15f054d622fc4f6164248a2f4453d20a3e7fff",
    "constructions": results,
    "diff_regions": regions,
    "matching_constructions": [item["construction"] for item in results if item["matches_K_recorded_fingerprint"]],
    "scope": "Explicit reproducible line-ending hash arithmetic only, not recovered original worktree bytes, code execution authentication, or a new source safety test.",
    "remaining_limits": ["Raw candidate Git bytes do not equal the recorded worktree fingerprint.",
                         "No original measured app.py byte snapshot is claimed retained here.",
                         "Current shipping source safety remains inspection-only; retained controls remain UNEXECUTED."]
}
with (ROOT / "binding/LINE_ENDING_QUALIFICATION.json").open("xb") as output:
    output.write((json.dumps(receipt, indent=2) + "\n").encode())
print(json.dumps(receipt, indent=2))
