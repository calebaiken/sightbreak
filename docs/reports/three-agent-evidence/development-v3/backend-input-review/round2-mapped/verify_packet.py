"""Read-only compact publication verifier; never imports/runs copied evidence."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 13):
    raise SystemExit("Approved CPython 3.13 required")
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[5]
checks = 0


def require(condition, message):
    global checks
    checks += 1
    if not condition:
        raise ValueError(message)


def filehash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def git(args, stdin=None):
    result = subprocess.run(["git", "--no-pager", *args], cwd=REPO, input=stdin,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_PAGER="cat"), capture_output=True, check=False)
    require(result.returncode == 0, "Explicit Git exit required: " + repr(args))
    return result.stdout


manifest = ROOT / "PUBLISHED_SHA256SUMS.txt"
entries = {}
for line in manifest.read_text(encoding="utf-8").splitlines():
    match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
    require(match is not None, "Invalid manifest line")
    expected, name = match.groups()
    require(name not in entries and not Path(name).is_absolute() and ".." not in Path(name).parts, "Unsafe/duplicate manifest path")
    require(filehash(ROOT / name) == expected, "Published checksum mismatch: " + name)
    entries[name] = expected
files = sorted(p for p in ROOT.rglob("*") if p.is_file())
require({p.relative_to(ROOT).as_posix() for p in files if p != manifest} == set(entries), "Incomplete published checksum coverage")
require(all(not p.is_symlink() for p in files), "Symlink in packet")
total_bytes = sum(p.stat().st_size for p in files)
require(total_bytes <= 6 * 1024 * 1024, "Packet exceeds 6 MiB")

copies = load(ROOT / "COPY_LEDGER.json")["copies"]
require(len(copies) == 537 and len({item["published"] for item in copies}) == 537, "Unexpected exact-copy ledger count")
for item in copies:
    path = ROOT / item["published"]
    require(path.stat().st_size == item["bytes"] and filehash(path) == item["sha256"], "Copied evidence mismatch: " + item["published"])
require(filehash(ROOT / "audit/SHA256SUMS.txt") == "048276d1fcb0fe2dc52485b9d730e109669e5902ffca5f79c38cb089d7068750", "External full manifest anchor")
original_entries = {}
for line in (ROOT / "audit/SHA256SUMS.txt").read_text().splitlines():
    expected, name = line.split("  ", 1)
    require(name not in original_entries, "Duplicate full external manifest entry")
    original_entries[name] = expected
require(len(original_entries) == 611, "Full external index must contain 611 entries")
omissions = load(ROOT / "OMISSIONS.json")
require(omissions["omitted_external_files"] == len(omissions["omissions"]) == 85, "Omission count")
require(sum(item["bytes"] for item in omissions["omissions"]) == omissions["omitted_external_bytes"] == 3262041, "Omission byte count")
selected = {item["path"] for item in load(ROOT / "COMPACT_COLLECTION_PLAN.json")["inventory"] if item["selected"]}
omitted = {item["path"] for item in omissions["omissions"]}
require(len(selected) == 526 and not selected & omitted and selected | omitted == set(original_entries), "Exact external selection/omission partition")
for name in selected:
    require(filehash(ROOT / "audit" / name) == original_entries[name], "Selected original bytes changed")

for index_name, key, path_key, hash_key in [
    ("publication-raw/BULK_INTERRUPTED_COPY_RECOVERY.json", "damaged_copies", "path", "damaged_sha256"),
    ("publication-raw/PUBLICATION_HISTORY_INDEX.json", "entries", "original_publication_path", "sha256"),
]:
    index = load(ROOT / index_name)
    archive = ROOT / index["archive"]
    require(filehash(archive) == index["archive_sha256"], "Publication failure archive hash")
    with zipfile.ZipFile(archive) as bundle:
        require(set(bundle.namelist()) == {item[path_key] for item in index[key]}, "Failure archive coverage")
        for item in index[key]:
            data = bundle.read(item[path_key])
            require(len(data) == item["bytes"] and hashlib.sha256(data).hexdigest() == item[hash_key], "Failure/history decoded bytes changed")

bindings = load(ROOT / "GIT_BINDINGS.json")
grouped = {}
for item in bindings["bindings"]:
    grouped.setdefault(item["commit"], []).append(item)
require(len(bindings["bindings"]) == 470 and all(item["verified"] for item in bindings["bindings"]), "Expected verified source bindings")
for commit, items in grouped.items():
    if commit == "866e2e1f38461fa245557c9015b6c1a1a97ad745":
        paths = ["docs/reports/backend-trade-read-v3/retention-r2", "docs/reports/backend-trade-read-v3/identity-release-r2"]
    elif commit == "172c900795c04f9b8706c4e80d72f55927f40da1":
        paths = ["docs/reports/backend-trade-read-v3/assurance-r3"]
    else:
        paths = sorted({item["path"] for item in items})
    tree_raw = git(["ls-tree", "-r", "-z", commit, "--", *paths])
    require(bool(tree_raw), "Nonempty exact source tree required")
    tree = {}
    for row in tree_raw.split(b"\0"):
        if row:
            header, path = row.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            tree[path.decode()] = (mode, kind, oid)
    for item in items:
        require(tree.get(item["path"]) == (item["git_mode"], "blob", item["blob"]), "Fresh Git source tree binding failed")
integration = bindings["local_integration_commit"]
require(git(["ls-tree", integration, "--", "backend/app.py"]).decode().strip() == "100644 blob 16f33c94da490c77a8ab930b88d8fc0662f3fa4c\tbackend/app.py", "Local integration app binding")

attrs = git(["-C", str(ROOT), "check-attr", "-z", "text", "filter", "ident", "working-tree-encoding", "--stdin"],
            b"".join(p.relative_to(ROOT).as_posix().encode() + b"\0" for p in files)).split(b"\0")[:-1]
require(len(attrs) == len(files) * 4 * 3 and all(attrs[i] == b"unset" for i in range(2, len(attrs), 3)), "Copied bytes not protected by attributes")
visible = set((git(["-C", str(ROOT), "ls-files", "--others", "--exclude-standard", "-z", "--", "."]) + git(["-C", str(ROOT), "ls-files", "--cached", "-z", "--", "."])).decode().split("\0")) - {""}
require(all(p.relative_to(ROOT).as_posix() in visible for p in files), "Ignored publication payload or raw log")
require(load(ROOT / "PUBLICATION_VALIDATION.json")["all_publication_checks_passed"] is True, "Collection publication integrity failed")
require(load(ROOT / "PUBLICATION_RECEIPT.json")["all_packaging_checks_passed"] is True, "Seal integrity failed")
require(len(load(ROOT / "audit/objects/first-round/BINDING_VALIDATION.json")["failed_checks"]) == 1, "First 165/1 failure must remain")
require(len(load(ROOT / "audit/ASSURANCE_AUDIT.json")["failed_checks"]) == 2, "Archived negative/partial failures must remain")
print(json.dumps({"verified": True, "payload_files": len(entries), "files_including_ledger": len(files), "bytes_including_ledger": total_bytes,
                  "ledger_sha256": filehash(manifest), "exact_copies": len(copies), "omitted_external_files": 85,
                  "fresh_git_source_bindings": len(bindings["bindings"]), "checks_passed": checks,
                  "original_source_controls": "UNEXECUTED", "target_test_PG_native_executions": 0,
                  "locked_archives_or_builder_sources_modified": False}, indent=2))
