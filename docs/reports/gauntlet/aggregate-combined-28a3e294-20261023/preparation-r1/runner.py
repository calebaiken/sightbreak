"""Adapt the accepted recovered aggregate supervisor; preserve the validator bytes.

--prepare only inventories source/toolchain/commands. The ordinary invocation
launches ONE unmodified validate.sh; it requires external source approval/release.
"""
import argparse
import ast
import ctypes
import datetime
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
import zipfile

EXPECTED = "28a3e294c850482475b7ab74067c08538ae6310d"
ENGINE = Path("/workspace/tools/godot-4.7.2/Godot_v4.7.2-stable_linux.x86_64")
ENGINE_SHA256 = "8d106cbe6144c2dc7e881d61d2429c1a8a76e6b22ef48bd5e48dcf934953f71e"
BACKEND = Path("/workspace/sightbreak/.venv/bin/python")
WHOLE_SECONDS = 1200
PHASE_SECONDS = 540
SCOPES = ["game", "scripts", ".github", "backend", "server",
          "docs/reports/media/art-v9/hands/logs", "docs/reports/gauntlet/native-layout-ocr"]
FIXED_PORTS = {27991, 29900, 29901, 29902}
STRICT = re.compile(
    r"^(?:SCRIPT ERROR|ERROR:)|Parse Error|ObjectDB.*leaked|Leaked instance"
    r"|^Orphan StringName: [^\r\n]+ \(static: [0-9]+, total: [0-9]+\)\r?$"
    r"|^StringName: [1-9][0-9]* unclaimed string names at exit\.\r?$"
    r"|[Rr]esources? still in use|Traceback \(most recent call last\)"
    r"|^FAILED(?:[ (]|$)|^FAIL:|(?:failures|errors)=[1-9][0-9]*", re.M)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def digest(path, algorithm="sha256"):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, algorithm).hexdigest()


def write(out, name, value):
    (out / name).write_text(json.dumps(value, indent=2) + "\n")


def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo)


def load(repo, name):
    spec = importlib.util.spec_from_file_location(name, repo / "scripts" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_inventory(repo):
    source = load(repo, "build_manifest").source()
    if source["source_commit"] != EXPECTED or source["source_dirty"] or source["source_game_dirty"]:
        raise RuntimeError("Expected exact clean committed 28a3e294 source")
    rows = {}
    for raw in git(repo, "ls-files", "-z", *SCOPES).split(b"\0"):
        if not raw:
            continue
        relative = os.fsdecode(raw)
        path = repo / relative
        if not path.is_file() or path.is_symlink():
            raise RuntimeError("Missing/symlinked sparse input: " + relative)
        data = path.read_bytes()
        committed = git(repo, "show", EXPECTED + ":" + relative)
        if data != committed:
            raise RuntimeError("Tracked input differs from exact Git blob: " + relative)
        rows[relative] = {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    uids = {p: v for p, v in rows.items() if p.startswith("game/") and p.endswith(".uid")}
    return {"source": source, "inputs": rows, "uids": uids}


def contract(repo):
    text = (repo / "scripts/validate.sh").read_text()
    mandatory, conditional, python = [], [], []
    display = False
    for line in text.splitlines():
        if line.startswith('if [[ -n "${DISPLAY:-}" ]]'):
            display = True
        match = re.search(r"\brun_godot ([\w-]+)", line)
        if match:
            (conditional if display else mandatory).append({"label": match[1], "source_command": line})
        if line.startswith("python3 "):
            target = "server/tests" if "-m unittest discover" in line else line.split()[1]
            paths = sorted((repo / target).glob("test*.py")) if target == "server/tests" else [repo / target]
            count = sum(sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test")
                            for n in ast.walk(ast.parse(p.read_text()))) for p in paths)
            python.append({"command": line, "target": target, "source_test_methods": count})
        if line == "fi":
            display = False
    return {"validate_sha256": digest(repo / "scripts/validate.sh"), "command": ["./scripts/validate.sh"],
            "mandatory_godot": mandatory, "display_only_godot": conditional, "python": python,
            "whole_seconds": WHOLE_SECONDS, "per_godot_seconds": PHASE_SECONDS,
            "phase_limits_origin": "unchanged timeout ${SIGHTBREAK_TEST_TIMEOUT:-540}; connection lifecycle 45-second waits, readiness 100*0.05s, owned cleanup 5s; smoke readiness 80*0.1s and owned cleanup 5s; other helpers bounded by whole supervisor",
            "strict_pattern": STRICT.pattern}


def engine_receipt(repo):
    toolchain = load(repo, "toolchain")
    if ENGINE.resolve() != ENGINE or digest(ENGINE) != ENGINE_SHA256:
        raise RuntimeError("Pinned engine path/hash mismatch")
    archive = ENGINE.parent / "godot.zip"
    if digest(archive, "sha512") != toolchain.EDITORS["linux"][2]:
        raise RuntimeError("Pinned engine archive mismatch")
    with zipfile.ZipFile(archive) as bundle:
        member = bundle.read(ENGINE.name)
    if hashlib.sha256(member).hexdigest() != ENGINE_SHA256:
        raise RuntimeError("Installed engine differs from pinned archive member")
    if not BACKEND.is_file() or not os.access(BACKEND, os.X_OK):
        raise RuntimeError("Required backend catalog interpreter unavailable")
    return {"path": str(ENGINE), "sha256": ENGINE_SHA256, "expected_version": toolchain.ENGINE,
            "archive": str(archive), "archive_sha512": digest(archive, "sha512"),
            "backend_python": str(BACKEND), "backend_resolved": str(BACKEND.resolve()),
            "backend_sha256": digest(BACKEND)}


def process_table():
    rows = {}
    for path in Path("/proc").iterdir():
        if not path.name.isdigit():
            continue
        try:
            data = (path / "stat").read_text()
            values = data[data.rindex(")") + 2:].split()
            argv = (path / "cmdline").read_bytes()
            rows[int(path.name)] = {"pid": int(path.name), "ppid": int(values[1]), "pgid": int(values[2]),
                "sid": int(values[3]), "start_ticks": int(values[19]), "state": values[0],
                "comm": (path / "comm").read_text().strip(), "argv": os.fsdecode(argv).replace("\0", " ").strip(),
                "argv_sha256": hashlib.sha256(argv).hexdigest()}
        except (OSError, ValueError, IndexError):
            continue
    return rows


def identify_owned(table, repo, supervisor, session, seen):
    chosen = {}
    known = {(r["pid"], r["start_ticks"]) for r in seen.values()}
    for pid, row in table.items():
        if pid == supervisor:
            continue
        reasons = []
        if session is not None and row["sid"] == session:
            reasons.append("original-session")
        if str(repo) in row["argv"] and ("godot" in row["comm"].lower() or "scripts/" in row["argv"]):
            reasons.append("checkout-argv")
        if (pid, row["start_ticks"]) in known:
            reasons.append("previously-observed-identity")
        if reasons:
            chosen[pid] = dict(row, ownership=reasons)
    while True:
        extra = {pid: dict(row, ownership=["descendant-or-subreaper-adoptee"])
                 for pid, row in table.items() if pid != supervisor and pid not in chosen
                 and (row["ppid"] == supervisor or row["ppid"] in chosen)}
        if not extra:
            return chosen
        chosen.update(extra)


def listeners(ports):
    found = []
    for kind in ("udp", "udp6", "tcp", "tcp6"):
        for line in (Path("/proc/net") / kind).read_text().splitlines()[1:]:
            fields = line.split()
            port = int(fields[1].rsplit(":", 1)[1], 16)
            if port in ports and (kind.startswith("udp") or fields[3] == "0A"):
                found.append({"kind": kind, "port": port, "state": fields[3], "inode": fields[9]})
    return found


def required_logs(repo, out, new_dirs, specification):
    text = (out / "aggregate.log").read_text(errors="replace")
    completed = re.findall(r"^Validation completed\. Logs: (.+)$", text, re.M)
    smoke = re.findall(r"^NETWORK_LOG_DIR=(.+)$", text, re.M)
    files = [out / "aggregate.log"]
    failures = []
    if len(new_dirs) != 1 or completed != [str(new_dirs[0])]:
        failures.append("exact one new validation directory and matching completion marker required")
    for directory in new_dirs:
        expected = {r["label"] + ".log" for r in specification["mandatory_godot"]} | {"reload-contact.log"}
        actual = {p.name for p in directory.glob("*.log")}
        if actual != expected:
            failures.append("mandatory top-level log ledger mismatch")
        for label in expected:
            p = directory / label
            if not p.is_file() or p.stat().st_size == 0:
                failures.append("missing/empty log " + str(p))
        files += sorted(directory.rglob("*.log"))
        for scenario in ("silent", "idle", "reject"):
            for role in ("server", "client"):
                p = directory / "connection-lifecycle" / (scenario + "-" + role + ".log")
                if not p.is_file() or '"ok":true' not in p.read_text():
                    failures.append("missing/failing lifecycle " + str(p))
    if len(smoke) != 1:
        failures.append("one original ENet smoke directory required")
    for raw in smoke:
        directory = Path(raw)
        for name in ("server.log", "client-a.log", "client-b.log", "cleanup.log"):
            p = directory / name
            if not p.is_file() or not p.stat().st_size:
                failures.append("missing/empty ENet " + str(p))
            else:
                files.append(p)
        for name in ("client-a.log", "client-b.log"):
            p = directory / name
            if not p.is_file() or "NETWORK_CLIENT_PASS" not in p.read_text():
                failures.append("missing ENet client pass " + str(p))
    files += sorted((repo / ".local/aggregate-state-r1").rglob("*.log"))
    for path in sorted(set(files)):
        if path.is_file():
            match = STRICT.search(path.read_text(errors="replace"))
            if match:
                failures.append("strict native/Python log failure " + str(path) + ": " + match[0])
    if "SKIPPED catalog fixture" in text or "backend_world.json matches the backend (29 definitions)" not in text:
        failures.append("mandatory 29-definition backend catalog marker absent or skipped")
    return {"failures": failures, "validation_dirs": [str(p) for p in new_dirs], "network_dirs": smoke,
            "files": [{"path": str(p), "bytes": p.stat().st_size, "sha256": digest(p)} for p in sorted(set(files)) if p.is_file()]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("expected")
    parser.add_argument("out", type=Path)
    parser.add_argument("--prepare", action="store_true")
    args = parser.parse_args()
    if args.expected != EXPECTED:
        raise RuntimeError("This preregistration is pinned to 28a3e294")
    repo, out = args.repo.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, out / "runner.py")
    try:
        before = source_inventory(repo)
        specification = contract(repo)
        write(out, "source-before.json", before)
        write(out, "command-contract.json", specification)
        write(out, "engine.json", engine_receipt(repo))
    except BaseException as error:
        write(out, "setup-failure.json", {"utc": now(), "type": type(error).__name__, "message": str(error), "engine_executed": False})
        raise
    if args.prepare:
        write(out, "preparation.json", {"prepared_utc": now(), "engine_executed": False,
              "source_input_count": len(before["inputs"]), "uid_count": len(before["uids"]),
              "runner_sha256": digest(Path(__file__))})
        return
    # Linux subreaper observes children that leave their original session and
    # are later orphaned. Sampling still cannot prove unseen escaped descendants.
    if ctypes.CDLL(None, use_errno=True).prctl(36, 1, 0, 0, 0):
        raise OSError(ctypes.get_errno(), "Unable to establish owned child subreaper")
    supervisor = os.getpid()
    own = process_table()[supervisor]
    write(out, "supervisor-launch.json", dict(own, observed_utc=now(), cwd=str(Path.cwd()),
          executable=sys.executable, argv=sys.argv, runner_sha256=digest(Path(__file__)), subreaper=True))
    initial = identify_owned(process_table(), repo, supervisor, None, {})
    ports = listeners(FIXED_PORTS)
    write(out, "preflight-resources.json", {"processes": list(initial.values()), "listeners": ports})
    state = repo / ".local/aggregate-state-r1"
    if initial or ports or state.exists() or (repo / "game/.godot").exists():
        raise RuntimeError("Frozen checkout requires unused ports, fresh private state/import cache, no owned engine")
    original_dirs = set((repo / ".local/validation").glob("run-*"))
    if original_dirs:
        raise RuntimeError("Fresh frozen checkout must have no prior aggregate directories")
    env = dict(os.environ)
    for key in ("DISPLAY", "SIGHTBREAK_TEST_TIMEOUT", "SIGHTBREAK_BUILDS_DIR"):
        env.pop(key, None)
    env.update(SIGHTBREAK_TOOLS_DIR="/workspace/tools", GODOT_BIN=str(ENGINE),
        SIGHTBREAK_STATE_DIR=str(state), SIGHTBREAK_BACKEND_PYTHON=str(BACKEND),
        DATABASE_URL="postgresql+psycopg://fixture:fixture@127.0.0.1:1/fixture")
    selectors = ("DISPLAY", "SIGHTBREAK_TOOLS_DIR", "SIGHTBREAK_STATE_DIR", "SIGHTBREAK_BACKEND_PYTHON",
                 "GODOT_BIN", "SIGHTBREAK_TEST_TIMEOUT", "LP_NUM_THREADS", "LIBGL_ALWAYS_SOFTWARE", "DATABASE_URL")
    command = ["./scripts/validate.sh"]
    record = {"command": command, "cwd": str(repo), "started_utc": now(), "timeout_seconds": WHOLE_SECONDS,
        "per_godot_timeout_seconds": PHASE_SECONDS, "environment": {k: env.get(k) for k in selectors},
        "runner_sha256": digest(Path(__file__)), "stdout_stderr": "combined losslessly in aggregate.log"}
    write(out, "command.json", record)
    process, failure, seen, events, phase_events = None, None, {}, [], []
    started = time.monotonic()
    latest_phase = None
    try:
        with (out / "aggregate.log").open("wb") as log:
            process = subprocess.Popen(command, cwd=repo, env=env, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            record.update(pid=process.pid, pgid=os.getpgid(process.pid), sid=os.getsid(process.pid))
            write(out, "command.json", record)
            while process.poll() is None:
                table = process_table()
                for row in identify_owned(table, repo, supervisor, process.pid, seen).values():
                    key = (row["pid"], row["start_ticks"])
                    seen[key] = row
                logs = sorted((repo / ".local/validation").glob("run-*/*.log"), key=lambda p: p.stat().st_mtime_ns)
                phase = str(logs[-1]) if logs else None
                if phase != latest_phase:
                    latest_phase = phase
                    phase_events.append({"phase_log": phase, "observed_utc": now(), "seconds": time.monotonic() - started})
                if time.monotonic() - started >= WHOLE_SECONDS:
                    raise subprocess.TimeoutExpired(command, WHOLE_SECONDS)
                time.sleep(.1)
            record["exit_code"] = process.wait()
            if record["exit_code"]:
                raise RuntimeError("Maintained aggregate exited nonzero")
    except BaseException as error:
        failure = {"type": type(error).__name__, "message": str(error)}
    finally:
        # Signal only revalidated PID/start identities. On a failed run use TERM
        # then bounded KILL; every forced action remains a failing acquisition.
        sid = process.pid if process is not None else None
        if process is not None and process.poll() is not None:
            process.wait()
            while True:
                try:
                    pid, status = os.waitpid(-1, os.WNOHANG)
                    if not pid:
                        break
                    events.append({"naturally_reaped_pid": pid, "wait_status": status, "utc": now()})
                except ChildProcessError:
                    break
        remaining = identify_owned(process_table(), repo, supervisor, sid, seen)
        if remaining:
            failure = failure or {"type": "CleanupFailure", "message": "Owned descendants remain after validator exit"}
            for sig in (signal.SIGTERM, signal.SIGKILL):
                for pid, row in remaining.items():
                    current = process_table().get(pid)
                    if current and current["start_ticks"] == row["start_ticks"] and current["state"] != "Z":
                        try:
                            os.kill(pid, sig)
                            events.append({"pid": pid, "start_ticks": row["start_ticks"], "signal": sig.name, "utc": now()})
                        except ProcessLookupError:
                            pass
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    if process is not None and process.poll() is not None:
                        process.wait()
                    if process is None or process.poll() is not None:
                        while True:
                            try:
                                pid, status = os.waitpid(-1, os.WNOHANG)
                                if not pid:
                                    break
                                events.append({"reaped_pid": pid, "wait_status": status, "utc": now()})
                            except ChildProcessError:
                                break
                    remaining = identify_owned(process_table(), repo, supervisor, sid, seen)
                    if not remaining:
                        break
                    time.sleep(.1)
                if not remaining:
                    break
        after = None
        try:
            after = source_inventory(repo)
        except BaseException as error:
            failure = failure or {"type": type(error).__name__, "message": str(error)}
        write(out, "source-after.json", after)
        new_dirs = sorted(set((repo / ".local/validation").glob("run-*")) - original_dirs)
        audit = required_logs(repo, out, new_dirs, specification)
        write(out, "log-audit.json", audit)
        # Readiness receipts also declare ephemeral journal ports. Scan all
        # printed port fields, retaining the exact registered fixed ports too.
        all_text = "\n".join(Path(r["path"]).read_text(errors="replace") for r in audit["files"])
        readiness_ports = {int(p) for p in re.findall(r'\b(?:port["\s:=]+)([0-9]{2,5})\b', all_text) if 0 < int(p) < 65536}
        terminal_ports = listeners(FIXED_PORTS | readiness_ports)
        terminal = identify_owned(process_table(), repo, supervisor, sid, seen)
        write(out, "observed-processes.json", list(seen.values()))
        write(out, "phase-observations.json", phase_events)
        write(out, "cleanup.json", {"observed_utc": now(), "remaining": list(terminal.values()),
            "ports_checked": sorted(FIXED_PORTS | readiness_ports), "listeners": terminal_ports, "signal_and_reap_events": events,
            "scope": "sampled ancestry, subreaper-adopted children, original session, observed PID/start identities and checkout-bound argv; unseen arbitrary escaped descendants remain unqualified"})
        record.update(completed_utc=now(), seconds=time.monotonic() - started, source_unchanged=before == after,
            failure=failure, log_failures=audit["failures"], forced_cleanup=any("signal" in event for event in events))
        passed = failure is None and before == after and not terminal and not terminal_ports and not audit["failures"] and record.get("exit_code") == 0
        write(out, "result.json", dict(record, passed=passed))
        print(json.dumps({"passed": passed, "exit_code": record.get("exit_code"), "failure": failure,
            "log_failures": audit["failures"], "seconds": record["seconds"], "source_unchanged": before == after,
            "remaining": len(terminal), "listeners": len(terminal_ports)}), flush=True)
    if not passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
