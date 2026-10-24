"""Read-only comparison of sealed packet ledgers against physical and staged bytes."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
from datetime import datetime, timezone

ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
PREFIX = Path("docs/reports/three-agent-evidence/development-v3")
PACKETS = {
    "backend-input-review/round2-mapped": "PUBLISHED_SHA256SUMS.txt",
    "input-boundary-review": "SHA256SUMS.txt",
}


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to replace an earlier audit")
    expected = {}
    counts = {}
    for packet, ledger_name in PACKETS.items():
        base = PREFIX / packet
        ledger = ROOT / base / ledger_name
        rows = ledger.read_text(encoding="utf-8").splitlines()
        counts[packet] = len(rows)
        for row in rows:
            digest, name = row.split("  ", 1)
            relative = PurePosixPath(name)
            if (not re.fullmatch(r"[0-9a-f]{64}", digest) or relative.is_absolute()
                    or ".." in relative.parts or "\\" in name or ":" in name):
                raise ValueError(f"Noncanonical ledger row: {row}")
            path = (base / Path(*relative.parts)).as_posix()
            if path in expected:
                raise ValueError(f"Repeated ledger path: {path}")
            expected[path] = digest
    paths = list(expected)
    batch = subprocess.run(
        ["git", "cat-file", "--batch"], cwd=ROOT,
        input="".join(f":{path}\n" for path in paths).encode(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    )
    offset = 0
    failures = []
    for path in paths:
        physical = ROOT / path
        if physical.is_symlink() or not physical.is_file():
            failures.append({"path": path, "failure": "missing/nonregular physical file"})
        elif hashlib.sha256(physical.read_bytes()).hexdigest() != expected[path]:
            failures.append({"path": path, "failure": "physical byte mismatch"})
        end = batch.stdout.index(b"\n", offset)
        header = batch.stdout[offset:end].decode()
        offset = end + 1
        if header.endswith(" missing"):
            failures.append({"path": path, "failure": "missing from Git index"})
            continue
        _, kind, length = header.split()
        length = int(length)
        data = batch.stdout[offset:offset + length]
        offset += length + 1
        if kind != "blob" or len(data) != length or hashlib.sha256(data).hexdigest() != expected[path]:
            failures.append({"path": path, "failure": "Git index byte mismatch"})
    if offset != len(batch.stdout):
        raise ValueError("Unconsumed batch output")
    staged = git("diff", "--cached", "--name-only").decode().splitlines()
    result = {
        "utc": datetime.now(timezone.utc).isoformat(),
        "head": git("rev-parse", "HEAD").decode().strip(),
        "scope": "Sealed evidence bytes only; no tests, native work or acceptance",
        "ledger_counts": counts,
        "payloads_checked": len(expected),
        "staged_files": len(staged),
        "failures": failures,
        "passed": not failures,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2))
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
