#!/usr/bin/env python3
"""Two-process journal-only stage ownership regression; no UI, HTTP or imports.

Copies exact journal bytes from --revision (or the working file) into a tiny
project. The same external probe runs against either source, with at most two
native children at once. All raw logs, state, source and executable hashes stay
outside git. Injected file corruption/deletion is not evidence of real disk full.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "game/scripts/ui/transaction_journal.gd"
PROBE = ROOT / "game/tests/journal_stage_ownership_probe.gd"
DEFAULT_GODOT = Path(os.environ.get("LOCALAPPDATA", "")) / "Temp/opencode/godot/Godot_v4.7.2-stable_win64.exe"
# name: (fresh guard must release, canonical file remains after owner's stage)
CASES = {
    "invalid": (True, False),
    "oversized": (True, False),
    "open_missing_parent": (True, False),
    "temp_truncated": (True, False),
    "temp_missing": (True, False),
    "rename_locked": (True, False),
    "rename_missing_source": (False, False),
    # Windows rename removes the existing destination before failing on a missing
    # source. The probe records the earlier publication; final absence is unsafe.
    "rename_published": (False, False),
    "temp_canonical": (False, True),
    "postpublish_truncated": (False, True),
    "postpublish_missing": (False, False),
    "existing_pending": (False, True),
    "existing_damaged": (False, True),
    "already_owned_invalid": (False, False),
    "already_owned_open_missing_parent": (False, False),
    "already_owned_temp_truncated": (False, False),
    "successful_stage": (False, True),
}
FAULTS = {"temp_truncated", "temp_missing", "rename_locked", "rename_missing_source",
          "rename_published", "temp_canonical", "postpublish_truncated", "postpublish_missing"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_digest(path: Path) -> str:
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


class Native:
    def __init__(self, godot: Path, project: Path, config: Path, prefix: Path):
        self.logs = [prefix.with_suffix(".stdout.txt").open("wb"),
                     prefix.with_suffix(".stderr.txt").open("wb")]
        self.command = [str(godot), "--headless", "--path", str(project), "--script",
                        "res://tests/journal_stage_ownership_probe.gd", "--", str(config)]
        try:
            self.process = subprocess.Popen(self.command, stdout=self.logs[0], stderr=self.logs[1])
        except BaseException:
            for log in self.logs:
                log.close()
            raise
        self.pid = self.process.pid
        self.closed = False

    def wait(self, timeout=10) -> int:
        return self.process.wait(timeout=timeout)

    def close(self) -> None:
        if self.closed:
            return
        try:
            if self.process.poll() is None:
                self.process.kill()  # Only this driver's own Popen child.
            self.process.wait(timeout=10)
        finally:
            for log in self.logs:
                log.close()
            self.closed = True


def wait_file(path: Path, child: Native, timeout=12) -> None:
    deadline = time.monotonic() + timeout
    while not path.exists():
        if child.process.poll() is not None:
            raise RuntimeError(f"PID {child.pid} exited {child.process.returncode} before {path.name}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"PID {child.pid} did not publish {path.name}")
        time.sleep(0.02)


class RenameBlock:
    """Real Windows sharing violation: readable source, rename/delete denied."""
    def __init__(self, path: Path):
        if os.name != "nt":
            raise RuntimeError("rename_locked requires a Windows no-delete sharing handle")
        from ctypes import wintypes
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.kernel.CreateFileW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                                           ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
        self.kernel.CreateFileW.restype = wintypes.HANDLE
        self.kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        self.kernel.CloseHandle.restype = wintypes.BOOL
        # GENERIC_READ, FILE_SHARE_READ|WRITE (no DELETE), OPEN_EXISTING.
        self.handle = self.kernel.CreateFileW(str(path), 0x80000000, 3, None, 3, 0x80, None)
        if self.handle == ctypes.c_void_p(-1).value:
            raise ctypes.WinError(ctypes.get_last_error())

    def close(self) -> None:
        if self.handle is not None:
            self.kernel.CloseHandle(self.handle)
            self.handle = None


def snapshot_bytes(journal: Path, directory: Path, name: str) -> dict:
    files = {}
    for suffix, label in [("", "canonical"), (".tmp", "temporary")]:
        path = Path(str(journal) + suffix)
        raw = path.read_bytes() if path.is_file() else None
        files[label] = {"exists": raw is not None, "sha256": digest(raw) if raw is not None else ""}
        if raw is not None:
            (directory / f"{name}.{label}.raw").write_bytes(raw)
    write_json(directory / f"{name}.files.json", files)
    return files


def run_case(name: str, godot: Path, project: Path, output: Path, source_hash: str) -> dict:
    release, canonical = CASES[name]
    directory = output / name
    directory.mkdir()
    journal = directory / "receipt.json"
    if name.endswith("open_missing_parent"):
        journal = directory / "missing" / "receipt.json"
    pending = {"path": "/store/buy", "method": 2, "payload": {"idempotency_key": "owner", "definition_id": "key"},
               "owner": "fixture-account", "server": "http://127.0.0.1:8080", "message": "Saved"}
    fault = name.removeprefix("already_owned_")
    fault = fault if fault in FAULTS else ""
    config = dict(case=name, role="owner", journal=journal.as_posix(), control=directory.as_posix(),
                  pending=pending, fault=fault)
    write_json(directory / "owner-config.json", config)
    children = []
    rename_block = None
    report = dict(case=name, expect_release=release, checks={}, processes=[])
    started = time.monotonic()
    try:
        owner = Native(godot, project, directory / "owner-config.json", directory / "owner")
        children.append(owner)
        report["processes"].append(dict(role="owner", pid=owner.pid, command=owner.command))
        if name == "rename_locked":
            wait_file(directory / "rename_ready", owner)
            rename_block = RenameBlock(Path(str(journal) + ".tmp"))
            (directory / "rename_go").touch()
        wait_file(directory / "owner.json", owner)
        if rename_block:
            rename_block.close()
        a = json.loads((directory / "owner.json").read_text(encoding="utf-8"))
        before = snapshot_bytes(journal, directory, "after_owner")
        # Repair the actual open failure while A still lives. B uses the same path.
        journal.parent.mkdir(exist_ok=True)
        contender_pending = {**pending, "payload": {"idempotency_key": "contender", "definition_id": "key"}}
        write_json(directory / "contender-config.json", {**config, "role": "contender", "pending": contender_pending})
        alive_before = owner.process.poll() is None
        contender = Native(godot, project, directory / "contender-config.json", directory / "contender")
        children.append(contender)
        report["processes"].append(dict(role="contender", pid=contender.pid, command=contender.command))
        wait_file(directory / "contender_first.json", contender)
        alive_after = owner.process.poll() is None
        b = json.loads((directory / "contender_first.json").read_text(encoding="utf-8"))
        after = snapshot_bytes(journal, directory, "after_contender_first")
        report["owner_alive_before_and_after_contender"] = [alive_before, alive_after]
        (directory / "owner_exit").touch()
        owner_exit = owner.wait()
        # Same contender instance, same input, after confirmed owner process exit.
        (directory / "retry_go").touch()
        wait_file(directory / "contender_retry.json", contender)
        contender_exit = contender.wait()
        retry = json.loads((directory / "contender_retry.json").read_text(encoding="utf-8"))
        snapshot_bytes(journal, directory, "after_contender_retry")
        native_states = []
        for role in ["owner", "contender"]:
            for line in (directory / f"{role}.stdout.txt").read_text(encoding="utf-8").splitlines():
                if line.startswith("JOURNAL_STAGE_STATE "):
                    native_states.append(json.loads(line.removeprefix("JOURNAL_STAGE_STATE ")))
        checks = report["checks"]
        checks.update(
            raw_logs_match_states=native_states == [a, b, retry],
            source_bound=all(state["source_sha256"] == source_hash for state in [a, b, retry]),
            distinct_live_processes=owner.pid != contender.pid and alive_before and alive_after,
            reported_pids=a["pid"] == owner.pid and b["pid"] == retry["pid"] == contender.pid,
            setup_succeeded=a["setup_result"] == 0 and a["injection_ok"] and a["injected"] == bool(fault),
            owner_stage_result=(a["result"] == 0) if name == "successful_stage" else (a["result"] != 0),
            owner_canonical=a["canonical_exists"] == canonical,
            owner_guard=a["guard"] == (not release),
            active_path_cannot_retarget=a["retarget_blocked"] == a["guard"],
            contender_stage_while_owner_alive=b["result"] == (0 if release else 22),
            contender_guard=b["guard"] == release,
            contender_input=b["input"] == retry["input"] == contender_pending,
            contender_effect=(b["loaded_exact_input"] and after["canonical"]["exists"]) if release else (before == after),
            post_exit_retry=retry["guard"] and retry["result"] == (22 if canonical or b["result"] == 0 else 0),
            post_exit_exact_body=retry["loaded_exact_input"] if not canonical else (retry["canonical_sha256"] == a["canonical_sha256"]),
            clean_exit=owner_exit == contender_exit == 0,
        )
        if name in {"invalid", "oversized", "already_owned_invalid"}:
            checks["invalid_data_error"] = a["result"] == 30
        if name in {"temp_truncated", "temp_missing", "already_owned_temp_truncated", "temp_canonical",
                    "postpublish_truncated", "postpublish_missing"}:
            checks["readback_write_error"] = a["result"] == 13
        if name in {"existing_pending", "existing_damaged"}:
            checks["existing_bytes_preserved"] = a["canonical_sha256"] == a["before"]["canonical_sha256"] and a["result"] == 22
        if name == "rename_locked":
            checks["failed_rename_retained_exact_source"] = bool(a["verified_temporary_sha256"]) and before["temporary"]["sha256"] == a["verified_temporary_sha256"] and not before["canonical"]["exists"]
        if name in {"rename_published", "postpublish_truncated", "postpublish_missing"}:
            checks["publication_preceded_failure"] = bool(a["published_sha256"])
        if name == "rename_published":
            checks["published_verified_bytes"] = a["published_sha256"] == a["verified_temporary_sha256"]
        report["results"] = {"owner": a["result"], "contender_first": b["result"], "contender_retry": retry["result"]}
    except Exception as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        if rename_block:
            rename_block.close()
        for child in children:
            child.close()
        for child, process_record in zip(children, report["processes"]):
            process_record["returncode"] = child.process.returncode
        report["elapsed_seconds"] = round(time.monotonic() - started, 3)
        report["passed"] = "error" not in report and bool(report["checks"]) and all(report["checks"].values())
        write_json(directory / "result.json", report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, default=DEFAULT_GODOT)
    parser.add_argument("--revision", default="working", help="Git revision or 'working'; source is copied verbatim")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--cases", nargs="+", choices=list(CASES), default=list(CASES))
    args = parser.parse_args()
    temporary = Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir())) / "Temp/opencode"
    temporary.mkdir(parents=True, exist_ok=True)
    output = args.output.resolve() if args.output else Path(tempfile.mkdtemp(prefix="journal-stage-ownership-", dir=temporary))
    if output.is_relative_to(ROOT):
        parser.error("Evidence output must be outside the repository")
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        parser.error("Evidence output must be empty")
    source = (ROOT / SOURCE).read_bytes() if args.revision == "working" else subprocess.check_output(
        ["git", "-C", str(ROOT), "show", f"{args.revision}:{SOURCE}"])
    project = output / "project"
    (project / "scripts/ui").mkdir(parents=True)
    (project / "tests").mkdir()
    (project / "scripts/ui/transaction_journal.gd").write_bytes(source)
    (project / "tests/journal_stage_ownership_probe.gd").write_bytes(PROBE.read_bytes())
    (output / Path(__file__).name).write_bytes(Path(__file__).read_bytes())
    (project / "project.godot").write_text(
        'config_version=5\n[application]\nconfig/name="Journal stage ownership probe"\n'
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
        '[threading]\nworker_pool/max_threads=1\n', encoding="utf-8")
    version = subprocess.run([str(args.godot), "--headless", "--version"], capture_output=True, timeout=10, check=True)
    (output / "engine-version.stdout.txt").write_bytes(version.stdout)
    (output / "engine-version.stderr.txt").write_bytes(version.stderr)
    manifest = dict(scope="journal-only native component; no UI/HTTP, no real disk-full claim",
                    harness_pid=os.getpid(), checkout_head=git("rev-parse", "HEAD"),
                    checkout_status=git("status", "--porcelain", "--untracked-files=all"),
                    revision=args.revision, measured_commit=None if args.revision == "working" else git("rev-parse", args.revision),
                    source_sha256=digest(source), source_git_blob=subprocess.check_output(
                        ["git", "hash-object", "--stdin"], input=source, cwd=ROOT).decode().strip(),
                    probe_sha256=file_digest(PROBE), driver_sha256=file_digest(Path(__file__)),
                    godot=str(args.godot.resolve()), godot_sha256=file_digest(args.godot),
                    godot_version=version.stdout.decode().strip(), cases=args.cases,
                    project_files={path.relative_to(project).as_posix(): file_digest(path) for path in project.rglob("*") if path.is_file()})
    write_json(output / "manifest.json", manifest)
    reports = []
    print(f"Evidence: {output}", flush=True)
    for name in args.cases:
        report = run_case(name, args.godot, project, output, digest(source))
        reports.append(report)
        failed = [key for key, ok in report["checks"].items() if not ok]
        print(f"{'PASS' if report['passed'] else 'FAIL'} {name}: {report.get('results', report.get('error'))} {failed}", flush=True)
    summary = dict(passed=all(row["passed"] for row in reports), cases_passed=sum(row["passed"] for row in reports),
                   cases_total=len(reports), checks_passed=sum(sum(row["checks"].values()) for row in reports),
                   checks_total=sum(len(row["checks"]) for row in reports), reports=reports)
    write_json(output / "summary.json", summary)
    print(f"{summary['cases_passed']}/{summary['cases_total']} cases; {summary['checks_passed']}/{summary['checks_total']} checks")
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
