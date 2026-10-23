"""Retain completed OR failed aggregate originals; verify before any cleanup.

Adapted from aggregate-recovered-20261023/independent-critic/archive_originals.py.
Never deletes an original. Run after the outer launch/terminal receipts are saved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
from run_aggregate import STRICT


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive(run, repo, output):
    run, repo, output = run.resolve(), repo.resolve(), output.resolve()
    if output.is_relative_to(run) or output.is_relative_to(repo / ".local"):
        raise RuntimeError("Archive output must be outside originals")
    output.mkdir(parents=True, exist_ok=False)
    originals = {}
    for path in sorted(run.rglob("*")):
        if path.is_file():
            originals["supervisor/" + path.relative_to(run).as_posix()] = path
    for directory in (repo / ".local/validation", repo / ".local/aggregate-state-r1"):
        for path in sorted(directory.rglob("*.log")):
            originals["private-logs/" + path.relative_to(repo / ".local").as_posix()] = path
    audit_path = run / "log-audit.json"
    if audit_path.is_file():
        audit = json.loads(audit_path.read_text())
        for index, raw in enumerate(audit["network_dirs"]):
            for path in sorted(Path(raw).glob("*.log")):
                originals["network-smoke/" + str(index) + "/" + path.name] = path
        # The terminal audit's log bytes must still be the originals archived.
        for row in audit["files"]:
            data = Path(row["path"]).read_bytes()
            if len(data) != row["bytes"] or sha(data) != row["sha256"]:
                raise RuntimeError("Late log mutation: " + row["path"])
    if not originals:
        raise RuntimeError("No original evidence")
    manifest = []
    bundle_path = output / "raw-logs.tar.gz"
    with tarfile.open(bundle_path, "w:gz") as bundle:
        for name, path in sorted(originals.items()):
            if path.is_symlink():
                raise RuntimeError("Symlink in original evidence: " + str(path))
            data = path.read_bytes()
            bundle.add(path, arcname=name, recursive=False)
            manifest.append({"path": name, "original_path": str(path), "bytes": len(data), "sha256": sha(data)})
    expected = {row["path"]: row for row in manifest}
    log_scan = []
    with tarfile.open(bundle_path, "r:gz") as bundle:
        members = bundle.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise RuntimeError("Archive inventory mismatch")
        for member in members:
            data = bundle.extractfile(member).read()
            row = expected[member.name]
            origin = Path(row["original_path"]).read_bytes()
            if len(data) != row["bytes"] or sha(data) != row["sha256"] or origin != data:
                raise RuntimeError("Archive/original byte mismatch: " + member.name)
            if member.name.endswith(".log"):
                match = STRICT.search(data.decode(errors="replace"))
                log_scan.append({"path": member.name, "bytes": len(data), "sha256": sha(data),
                                 "strict_clean": match is None, "failure": match[0] if match else None})
    (output / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    checksum = sha(bundle_path.read_bytes())
    (output / "archive-sha256.txt").write_text(checksum + "  raw-logs.tar.gz\n")
    (output / "archive-log-scan.json").write_text(json.dumps(log_scan, indent=2) + "\n")
    receipt = {"verified": True, "original_files": len(manifest), "original_bytes": sum(r["bytes"] for r in manifest),
               "archive_sha256": checksum, "originals_deleted": False,
               "strict_clean": all(row["strict_clean"] for row in log_scan), "scanned_logs": len(log_scan),
               "scope": "all supervisor/outer receipt files; all validation/private userdata logs; all original ENet smoke logs; ordinary non-log state/cache remains at original path"}
    (output / "archive-verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(archive(args.run, args.repo, args.output)))
