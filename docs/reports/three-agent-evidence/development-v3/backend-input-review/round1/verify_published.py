"""Read-only final publication verifier; does not import retained evidence code."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 13):
    raise SystemExit("Approved CPython 3.13 required.")

ROUND = Path(__file__).resolve().parent
SOURCE = ROUND.parent / "source-review"
REPO = ROUND.parents[5]
checks = []


def require(name, value):
    checks.append({"check": name, "passed": bool(value)})
    if not value:
        raise ValueError(name)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git(args, data=None):
    result = subprocess.run(["git", "--no-pager", *args], cwd=REPO, input=data,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), capture_output=True, check=False)
    require(f"explicit Git success {args[0]}", result.returncode == 0)
    return result.stdout


summaries, all_files = [], []
for root in [ROUND, SOURCE]:
    manifest = root / "PUBLISHED_SHA256SUMS.txt"
    raw_manifest = manifest.read_bytes()
    expected = {}
    for line in raw_manifest.decode("utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        require(f"valid checksum entry {root.name}", match is not None)
        digest, path = match.groups()
        require(f"safe unique checksum path {root.name}/{path}",
                not Path(path).is_absolute() and ".." not in Path(path).parts and path not in expected)
        expected[path] = digest
    files = sorted(file for file in root.rglob("*") if file.is_file())
    require(f"no symlinks in {root.name}", all(not file.is_symlink() for file in files))
    actual_paths = {file.relative_to(root).as_posix() for file in files if file != manifest}
    require(f"complete manifest coverage {root.name}", actual_paths == set(expected))
    for path, digest in expected.items():
        require(f"payload hash {root.name}/{path}", sha((root / path).read_bytes()) == digest)
    summaries.append({"directory": root.relative_to(REPO).as_posix(),
                      "payload_files": len(expected), "total_files_including_manifest": len(files),
                      "total_bytes_including_manifest": sum(file.stat().st_size for file in files),
                      "manifest_sha256": sha(raw_manifest)})
    all_files.extend(files)

total_bytes = sum(summary["total_bytes_including_manifest"] for summary in summaries)
require("combined publication at most 3 MiB", total_bytes <= 3 * 1024 * 1024)
stdin = b"".join(file.relative_to(REPO).as_posix().encode() + b"\0" for file in all_files)
attributes = ["text", "filter", "ident", "working-tree-encoding"]
raw = git(["check-attr", "-z", *attributes, "--stdin"], stdin)
parts = raw.split(b"\0")[:-1]
require("complete exact-byte attribute records", len(parts) == len(all_files) * 4 * 3)
require("all nested byte transformations disabled", all(parts[index] == b"unset" for index in range(2, len(parts), 3)))
args = ["-z", "--", ROUND.relative_to(REPO).as_posix(), SOURCE.relative_to(REPO).as_posix()]
untracked = git(["ls-files", "--others", "--exclude-standard", *args])
tracked = git(["ls-files", "--cached", *args])
visible = set((untracked + tracked).decode().split("\0")) - {""}
require("all final payloads/raw logs/manifests are Git-visible", all(file.relative_to(REPO).as_posix() in visible for file in all_files))

initial = json.loads((ROUND / "binding/BINDING_VALIDATION.json").read_bytes())
qualified = json.loads((ROUND / "binding/QUALIFIED_RECEIPT.json").read_bytes())
receipt = json.loads((ROUND / "PUBLICATION_RECEIPT.json").read_bytes())
require("packaging receipt is a pass", receipt["packaging_checks_passed"] is True)
require("post-restart byte revalidation passed", qualified["publication_integrity_revalidation_passed"] is True)
require("initial failed source binding preserved, not converted to pass", len(initial["failed_checks"]) == 1
        and initial["all_recorded_checks_passed"] is False and receipt["all_collected_binding_checks_passed"] is False)
require("qualified receipt does not supersede originals", qualified["supersedes"] == [])
require("unexecuted controls and source-only safety kept explicit", qualified["controls"].startswith("UNEXECUTED")
        and qualified["source_safety"].startswith("INSPECTION_ONLY"))
anchors = initial["original_anchors"]
for file, key in [(ROUND / "verdict/NEUTRAL_VERDICT.md", "verdict"), (ROUND / "verdict/FROZEN.json", "freeze"),
                  (ROUND / "packet/SHA256SUMS.txt", "packet_manifest"), (ROUND / "released-key/mapping.json", "released_key"),
                  (SOURCE / "original/SOURCE_REVIEW.md", "source_review"),
                  (SOURCE / "original/isolated_assurance_controls.py", "unexecuted_controls")]:
    require(f"final preserved anchor {key}", sha(file.read_bytes()) == anchors[key])

print(json.dumps({"verified_utc": datetime.now(timezone.utc).isoformat(),
                  "publication_verified": True, "directories": summaries,
                  "combined_bytes": total_bytes, "checks_passed": len(checks),
                  "original_binding_checks_passed": len(initial["checks"]) - len(initial["failed_checks"]),
                  "original_binding_checks_failed_and_retained": len(initial["failed_checks"]),
                  "post_restart_byte_checks_passed": len(qualified["post_restart_revalidation"]),
                  "missing_binding": qualified["complete_measured_app_byte_binding"],
                  "controls": "UNEXECUTED", "source_safety": "INSPECTION_ONLY",
                  "second_round": "NOT_INSPECTED", "original_anchors": anchors,
                  "no_originals_superseded": True}, indent=2))
