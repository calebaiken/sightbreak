"""Read-only, serial Git/file audit helpers. No retained code is imported/run."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 13):
    raise SystemExit("Approved CPython 3.13 required")

ROOT = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
COMMAND_LOG = ROOT / "commands.jsonl"
CHECKS = []
SOURCES = []


def utc():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def filehash(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_new(path, data):
    if not path.is_relative_to(ROOT):
        raise ValueError("External audit writes only")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data.encode("utf-8") if isinstance(data, str) else data)


def save_json(name, value):
    write_new(ROOT / name, json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def check(name, condition, **details):
    CHECKS.append({"check": name, "passed": bool(condition), **details})
    return bool(condition)


def pairs_unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key {key}")
        result[key] = value
    return result


def load(data):
    return json.loads(data, object_pairs_hook=pairs_unique,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def local(path, max_bytes=8 * 1024 * 1024):
    if path.stat().st_size > max_bytes:
        raise ValueError(f"Bounded individual read exceeded: {path}")
    data = path.read_bytes()
    SOURCES.append({"kind": "local", "path": str(path), "bytes": len(data), "sha256": digest(data)})
    return data


def command(args, stdin=None):
    identifier = sum(1 for _ in COMMAND_LOG.open(encoding="utf-8")) + 1 if COMMAND_LOG.exists() else 1
    out = ROOT / f"raw/{identifier:04d}.stdout.bin"
    err = ROOT / f"raw/{identifier:04d}.stderr.log"
    out.parent.mkdir(exist_ok=True)
    argv = ["git", "--no-pager", *args]
    with out.open("xb") as stdout, err.open("xb") as stderr:
        result = subprocess.run(argv, cwd=REPO, input=stdin, stdout=stdout, stderr=stderr,
                                env=dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_PAGER="cat"), check=False)
    entry = {"utc": utc(), "argv": argv, "cwd": str(REPO), "exit": result.returncode,
             "stdin_sha256": digest(stdin) if stdin is not None else None,
             "stdout": out.relative_to(ROOT).as_posix(), "stdout_bytes": out.stat().st_size,
             "stdout_sha256": filehash(out), "stderr": err.relative_to(ROOT).as_posix(),
             "stderr_bytes": err.stat().st_size, "stderr_sha256": filehash(err)}
    with COMMAND_LOG.open("a", encoding="utf-8", newline="\n") as log:
        log.write(json.dumps(entry) + "\n")
    return entry, out


def git_bytes(args, max_bytes=8 * 1024 * 1024, allow_failure=False):
    entry, out = command(args)
    if entry["exit"] != 0 and not allow_failure:
        raise RuntimeError(f"Git exit {entry['exit']}: {args}; see {entry['stderr']}")
    if out.stat().st_size > max_bytes:
        raise ValueError(f"Bounded Git read exceeded: {args}")
    return entry, out.read_bytes()


def git_blob(commit, path):
    entry, raw_oid = git_bytes(["rev-parse", "--verify", f"{commit}:{path}"])
    oid = raw_oid.decode("ascii").strip()
    if entry["exit"] != 0 or re.fullmatch(r"[0-9a-f]{40}", oid) is None:
        raise ValueError("Nonempty exact Git object ID required")
    entry, data = git_bytes(["cat-file", "blob", oid])
    actual_oid = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    check(f"Git blob identity {commit}:{path}", actual_oid == oid)
    SOURCES.append({"kind": "git", "commit": commit, "path": path, "blob": oid,
                    "bytes": len(data), "sha256": digest(data), "capture": entry["stdout"]})
    return data


def finish(name, extra=None):
    value = {"created_utc": utc(), "python": sys.version, "executable": sys.executable,
             "checks": CHECKS, "failed_checks": [c for c in CHECKS if not c["passed"]],
             "all_checks_passed": all(c["passed"] for c in CHECKS), "sources": SOURCES,
             "execution_scope": "Our stdlib file/JSON/hash/AST audit and read-only Git only; no retained runner/control, DB, pytest, app/native/service/network/index execution",
             **(extra or {})}
    save_json(name, value)
    print(json.dumps({"receipt": name, "checks": len(CHECKS), "failed_checks": value["failed_checks"]}, indent=2))
    return value
