#!/usr/bin/env python3
"""Archive bounded original aggregate/ENet evidence after execution completes."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main(args):
    run, out = args.run.resolve(), args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    if (out / "raw-logs.tar.gz").exists():
        raise RuntimeError("Use a fresh archive output; preserve prior evidence")
    stdout = (run / "aggregate.log").read_text()
    completed_dirs = re.findall(r"^Validation completed\. Logs: (.+)$", stdout, re.M)
    if args.logs:
        logs = args.logs.resolve()
        if completed_dirs and completed_dirs != [str(logs)]:
            raise RuntimeError("Explicit logs do not equal original completion receipt")
    elif len(completed_dirs) == 1:
        logs = Path(completed_dirs[0])
    else:
        raise RuntimeError("Incomplete run needs explicit --logs selector; do not guess an evidence directory")
    smoke_dirs = re.findall(r"^NETWORK_LOG_DIR=(.+)$", stdout, re.M)
    if len(smoke_dirs) > 1:
        raise RuntimeError("Multiple original smoke directories need separate retained attempts")
    smoke = Path(smoke_dirs[0]) if smoke_dirs else None
    originals = {}
    for p in sorted(run.rglob("*")):
        if p.is_file():
            originals["root-outputs/" + p.relative_to(run).as_posix()] = (p, "original coordinator/supervisor output")
    for p in sorted(logs.rglob("*.log")):
        originals["aggregate-logs/" + p.relative_to(logs).as_posix()] = (p, "original maintained aggregate native/Python contact/lifecycle log")
    if smoke:
        for p in sorted(smoke.glob("*.log")):
            originals["network-smoke/" + p.name] = (p, "original maintained ENet smoke/cleanup log")
    manifest = []
    with tarfile.open(out / "raw-logs.tar.gz", "w:gz") as archive:
        for name, (p, origin) in sorted(originals.items()):
            data = p.read_bytes()
            if p.is_symlink():
                raise RuntimeError("Original evidence unexpectedly symlinked: " + str(p))
            archive.add(p, arcname=name, recursive=False)
            manifest.append({"path": name, "original_path": str(p), "bytes": len(data), "sha256": sha(data), "origin": origin})
    (out / "MANIFEST.json").write_text(json.dumps(manifest, indent=2) + "\n")
    expected = {r["path"]: r for r in manifest}
    with tarfile.open(out / "raw-logs.tar.gz", "r:gz") as archive:
        members = archive.getmembers()
        if len(members) != len(expected) or {m.name for m in members} != set(expected):
            raise RuntimeError("Archive inventory mismatch")
        for member in members:
            data = archive.extractfile(member).read()
            if len(data) != expected[member.name]["bytes"] or sha(data) != expected[member.name]["sha256"]:
                raise RuntimeError("Archive byte mismatch: " + member.name)
    digest = sha((out / "raw-logs.tar.gz").read_bytes())
    (out / "archive-sha256.txt").write_text(digest + "  raw-logs.tar.gz\n")
    result = {"verified": True, "original_files": len(manifest), "original_bytes": sum(r["bytes"] for r in manifest), "archive_sha256": digest,
              "logs": str(logs), "smoke": str(smoke) if smoke else None, "completion_marker_present": bool(completed_dirs),
              "selection": "Every original supervisor-output file, all mandatory/contact/lifecycle logs, all original ENet smoke logs. Ordinary test state/cache outside those selected logs is not archived."}
    (out / "archive-verification.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--logs", type=Path)
    main(parser.parse_args())
