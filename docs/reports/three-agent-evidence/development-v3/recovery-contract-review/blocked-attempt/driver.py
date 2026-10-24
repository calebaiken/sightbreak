"""Bounded independent controls. Never imports the owner project or contacts HTTP."""
from concurrent.futures import ThreadPoolExecutor
import ctypes
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parent
REPO = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
COMMIT = "7b6f379a3f8c809d0985a64e883cbadfdd78d135"
ENGINE = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe")
PYTHON = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-tools\python\cpython-3.13.15-windows-x86_64-none\python.exe")
RAW = ROOT / "raw"
PROJECT = ROOT / "project"
LAUNCH_TIMEOUT = 15
THRESHOLDS = {"physical_free_bytes": 768 * 1024**2,
              "commit_free_bytes": 1536 * 1024**2,
              "disk_free_bytes": 512 * 1024**2}


def utc():
    return datetime.now(timezone.utc).isoformat()


def save(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return {"path": str(path), "size": path.stat().st_size, "sha256": hasher.hexdigest()}


def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15).stdout


def preflight(label):
    class PerformanceInfo(ctypes.Structure):
        _fields_ = [("cb", w.DWORD), ("CommitTotal", ctypes.c_size_t),
                    ("CommitLimit", ctypes.c_size_t), ("CommitPeak", ctypes.c_size_t),
                    ("PhysicalTotal", ctypes.c_size_t), ("PhysicalAvailable", ctypes.c_size_t),
                    ("SystemCache", ctypes.c_size_t), ("KernelTotal", ctypes.c_size_t),
                    ("KernelPaged", ctypes.c_size_t), ("KernelNonpaged", ctypes.c_size_t),
                    ("PageSize", ctypes.c_size_t), ("HandleCount", w.DWORD),
                    ("ProcessCount", w.DWORD), ("ThreadCount", w.DWORD)]

    api = ctypes.WinDLL("psapi", use_last_error=True)
    api.GetPerformanceInfo.argtypes = [ctypes.POINTER(PerformanceInfo), w.DWORD]
    api.GetPerformanceInfo.restype = w.BOOL
    info = PerformanceInfo()
    info.cb = ctypes.sizeof(info)
    if not api.GetPerformanceInfo(ctypes.byref(info), info.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    result = {"utc": utc(), "label": label,
              "physical_free_bytes": info.PhysicalAvailable * info.PageSize,
              "physical_total_bytes": info.PhysicalTotal * info.PageSize,
              "commit_free_bytes": (info.CommitLimit - info.CommitTotal) * info.PageSize,
              "commit_limit_bytes": info.CommitLimit * info.PageSize,
              "committed_bytes": info.CommitTotal * info.PageSize,
              "disk_free_bytes": shutil.disk_usage(ROOT).free,
              "minimums": THRESHOLDS,
              "policy": "tiny headless scripts only; at most two Godot processes, 15s each"}
    result["safe_to_launch"] = all(result[key] >= value for key, value in THRESHOLDS.items())
    save(RAW / ("preflight-" + label + ".json"), result)
    if not result["safe_to_launch"]:
        raise RuntimeError("Preflight unsafe: " + label)
    return result


def freeze():
    for directory in (RAW, ROOT / "source", ROOT / "state", ROOT / "signals", ROOT / "harness"):
        directory.mkdir(exist_ok=False)
    if Path(sys.executable).resolve() != PYTHON.resolve():
        raise RuntimeError("Wrong Python executable")
    if git("rev-parse", COMMIT + "^{commit}").decode().strip() != COMMIT:
        raise RuntimeError("Wrong source commit")
    before = git("status", "--porcelain=v1")
    (RAW / "owner-status-before.txt").write_bytes(before)
    records = []
    for source_path, destination in [
        ("game/scripts/ui/economy_ui.gd", ROOT / "source/economy_ui.gd"),
        ("game/scripts/ui/transaction_journal.gd", PROJECT / "transaction_journal.gd"),
    ]:
        spec = COMMIT + ":" + source_path
        blob = git("show", spec)
        with destination.open("xb") as stream:
            stream.write(blob)
        oid = git("rev-parse", spec).decode().strip()
        calculated = hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest()
        if calculated != oid:
            raise RuntimeError("Git blob mismatch")
        records.append({"source_path": source_path, "git_blob_oid": oid, **digest(destination)})
    ui = (ROOT / "source/economy_ui.gd").read_bytes().splitlines(keepends=True)
    fragment = b"".join(ui[596:608])
    if (not ui[596].startswith(b"func _valid_receipt_result(")
            or not ui[606].startswith(b"func _receipt_integer(")
            or ui[608].strip()):
        raise RuntimeError("Unexpected predicate boundaries")
    prefix = b"extends RefCounted\n\n"
    with (PROJECT / "receipt_predicates.gd").open("xb") as stream:
        stream.write(prefix + fragment)
    save(ROOT / "source/predicate-provenance.json", {
        "commit": COMMIT, "source_path": "game/scripts/ui/economy_ui.gd",
        "source_lines_inclusive": [597, 608], "functions": ["_valid_receipt_result", "_receipt_integer"],
        "extraction": "Complete function region copied byte-for-byte; only extends RefCounted + blank line prefixed.",
        "fragment_sha256": hashlib.sha256(fragment).hexdigest(),
        "scope": "native predicate-component test, NOT full EconomyUI/_send_transaction/client/backend",
        "full_ui_not_imported": "UI preloads inspector/reveal/design components; intentionally outside tiny test.",
        "positive_fixtures": "synthetic legitimate shapes, not backend-produced receipts",
        "native_journal": "Exact complete unfiltered Git blob; no private API aliases or release calls."})
    shared = REPO / "scripts/matrix_process.py"
    with (ROOT / "harness/matrix_process.py").open("xb") as stream:
        stream.write(shared.read_bytes())
    env = dict(os.environ)
    overrides = {"APPDATA": str(ROOT / "sandbox/roaming"),
                 "LOCALAPPDATA": str(ROOT / "sandbox/local"),
                 "PYTHONDONTWRITEBYTECODE": "1"}
    for key in ("APPDATA", "LOCALAPPDATA"):
        Path(overrides[key]).mkdir(parents=True, exist_ok=False)
    env.update(overrides)
    commands = {
        role: [str(ENGINE), "--headless", "--audio-driver", "Dummy", "--path", str(PROJECT),
               "--log-file", str(RAW / ("engine-" + role + ".log")), "--max-fps", "30",
               "--script", "res://probe.gd", "--", "--role=" + role, "--evidence-root=" + str(ROOT)]
        for role in ("A", "B")}
    save(ROOT / "commands.json", {"commands": commands, "env_overrides": overrides,
                                   "native_timeout_seconds_each": LAUNCH_TIMEOUT,
                                   "native_launch_limit_total": 2,
                                   "max_simultaneous_native_processes": 2})
    manifest = {
        "utc": utc(), "commit": COMMIT, "native_imports_started": False, "source": records,
        "engine": digest(ENGINE), "python": {**digest(PYTHON), "version": sys.version},
        "shared_supervisor_origin": digest(shared),
        "inputs": [digest(ROOT / name) for name in (
            "driver.py", "project/probe.gd", "project/project.godot", "project/receipt_predicates.gd",
            "project/transaction_journal.gd", "source/economy_ui.gd", "source/predicate-provenance.json",
            "harness/matrix_process.py", "commands.json")],
        "excluded": ["full game assets", "Match", "export", "campaign", "HTTP/backend/DB", "GitHub", "source edits", "commits"]}
    save(ROOT / "pre-import-manifest.json", manifest)
    return commands, env, manifest


def wait_json(name, future, limit=7):
    path = RAW / name
    deadline = time.monotonic() + limit
    while time.monotonic() < deadline:
        if path.exists():
            try:
                result = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                time.sleep(0.025)
                continue
            if result.get("complete") is not True or result.get("checks_passed") is not True:
                raise RuntimeError("Native assertions failed in " + name)
            return result
        if future.done():
            raise RuntimeError("Native process ended before " + name + ": " + str(future.result()))
        time.sleep(0.025)
    raise TimeoutError("No native evidence: " + name)


def signal(name):
    with (ROOT / "signals" / name).open("x", encoding="utf-8") as stream:
        stream.write(utc() + "\n")


def alive(pid):
    api = ctypes.WinDLL("kernel32", use_last_error=True)
    api.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    api.OpenProcess.restype = w.HANDLE
    api.GetExitCodeProcess.argtypes = [w.HANDLE, ctypes.POINTER(w.DWORD)]
    api.GetExitCodeProcess.restype = w.BOOL
    api.CloseHandle.argtypes = [w.HANDLE]
    api.CloseHandle.restype = w.BOOL
    handle = api.OpenProcess(0x1000, False, pid)
    if not handle:
        if ctypes.get_last_error() in (87, 1168):
            return False
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        exit_code = w.DWORD()
        if not api.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            raise ctypes.WinError(ctypes.get_last_error())
        return exit_code.value == 259
    finally:
        api.CloseHandle(handle)


def attest_native(name, role):
    raw = (RAW / name).read_text(encoding="utf-8")
    if not raw.endswith("\n"):
        raise RuntimeError("Incomplete persisted native JSON")
    payload = json.loads(raw)
    log = (RAW / ("engine-" + role + ".log")).read_text(encoding="utf-8")
    exact_line = "NATIVE_JSON " + name + " " + raw[:-1]
    if log.splitlines().count(exact_line) != 1:
        raise RuntimeError("Native JSON not exactly present once in engine log: " + name)
    if (payload.get("complete") is not True or payload.get("checks_passed") is not True
            or payload.get("role") != role or not payload.get("checks")
            or any(check.get("passed") is not True or check.get("actual") != check.get("expected")
                   for check in payload["checks"])):
        raise RuntimeError("Native completion/assertion failure: " + name)
    engine = payload["engine"]
    if any(engine.get(key) != value for key, value in
           {"major": 4, "minor": 7, "patch": 2, "status": "stable", "build": "official"}.items()):
        raise RuntimeError("Unexpected native Godot version")
    return {"name": name, "exact_json_to_engine_log": True,
            "check_count": len(payload["checks"]), "pid": payload["pid"], "engine": engine}


def run():
    futures = {}
    pool = None
    timeline = []
    outcome = {"commit": COMMIT, "complete": False, "claims_verified": False,
               "failures": [], "scope": "S1 native predicates; S2 complete journal cross-process control"}
    try:
        commands, env, manifest = freeze()
        preflight("before-A")
        spec = importlib.util.spec_from_file_location("frozen_matrix_process", ROOT / "harness/matrix_process.py")
        supervisor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(supervisor)

        def run_native(role):
            # run_process requires the open log HANDLE, not a Path.
            with (RAW / ("stdout-" + role + ".log")).open("x", encoding="utf-8") as log:
                return supervisor.run_process(commands[role], cwd=PROJECT, env=env, log=log,
                                              result_path=RAW / ("supervisor-" + role + ".json"),
                                              timeout=LAUNCH_TIMEOUT)

        pool = ThreadPoolExecutor(max_workers=2)
        timeline.append({"utc": utc(), "action": "launch-A"})
        futures["A"] = pool.submit(run_native, "A")
        ready = wait_json("native-A-ready.json", futures["A"])
        if not alive(ready["pid"]) or futures["A"].done():
            raise RuntimeError("A not alive after invalid stage")
        preflight("before-B-while-A-alive")
        timeline.append({"utc": utc(), "action": "launch-B", "A_pid": ready["pid"], "A_alive": True})
        futures["B"] = pool.submit(run_native, "B")
        blocked = wait_json("native-B-blocked.json", futures["B"])
        if ready["pid"] == blocked["pid"] or not alive(ready["pid"]) or not alive(blocked["pid"]):
            raise RuntimeError("Distinct A and B not both alive at blocked stage")
        if (ROOT / "state/pending_transaction.json").exists():
            raise RuntimeError("Unexpected published receipt before positive control")
        timeline.append({"utc": utc(), "action": "B-blocked-observed", "A_pid": ready["pid"],
                         "B_pid": blocked["pid"], "both_alive": True, "pending_file_exists": False})
        signal("release-A.signal")
        exit_a = futures["A"].result(timeout=18)
        if exit_a != 0 or alive(ready["pid"]):
            raise RuntimeError("A did not complete and exit")
        timeline.append({"utc": utc(), "action": "A-exit-observed-before-B-retry", "A_alive": False,
                         "B_alive": alive(blocked["pid"])})
        if not timeline[-1]["B_alive"]:
            raise RuntimeError("B not alive before retry")
        signal("retry-B.signal")
        exit_b = futures["B"].result(timeout=18)
        if exit_b != 0 or alive(blocked["pid"]):
            raise RuntimeError("B did not complete and exit")
        attestations = [attest_native(name, role) for name, role in (
            ("native-A-ready.json", "A"), ("native-A.json", "A"),
            ("native-B-blocked.json", "B"), ("native-B.json", "B"))]
        for role in ("A", "B"):
            receipt = json.loads((RAW / ("supervisor-" + role + ".json")).read_text(encoding="utf-8"))
            stdout = (RAW / ("stdout-" + role + ".log")).read_text(encoding="utf-8")
            if receipt != {"complete": True, "exit": 0, "errors": []} or "HARNESS_ERROR" in stdout:
                raise RuntimeError("Containment/completion failure: " + role)
        for record in manifest["inputs"]:
            if digest(Path(record["path"])) != record:
                raise RuntimeError("Frozen input changed: " + record["path"])
        published = ROOT / "state/pending_transaction.json"
        final_b = json.loads((RAW / "native-B.json").read_text(encoding="utf-8"))
        if digest(published)["sha256"] != final_b["published_sha256"]:
            raise RuntimeError("Published receipt hash differs from native observation")
        outcome.update({"complete": True, "claims_verified": True, "attestations": attestations,
                        "native_process_count": 2, "native_processes_alive_after_run": False,
                        "published_positive_receipt": digest(published),
                        "source_inference_only": [
                            "EconomyUI 559-563 and 584-586 permit clear after accepted success body, conditional on clear succeeding; not invoked.",
                            "EconomyUI 543-550 returns before _send_transaction on stage failure; network count is not independently measured."],
                        "limitations": [
                            "No full UI/_send_transaction/client/backend test; no forged backend-response claim or authority contract.",
                            "Invalid-empty stage only; oversize/unwritable early returns are source review, not independently executed.",
                            "No HTTP or backend; do not report measured network count 0.",
                            "Positive fixtures are synthetic legitimate shapes, not live/backend receipts.",
                            "Published positive-control receipt left intact; no private release or clear call.",
                            "No broad recovery-safety or performance conclusion."]})
    except BaseException as error:
        outcome["failures"].append({"utc": utc(), "error": repr(error), "traceback": traceback.format_exc()})
    finally:
        # Only signal our own waiting probes. Contained supervisors enforce 15s caps.
        for name in ("release-A.signal", "retry-B.signal"):
            if (ROOT / "signals").is_dir() and not (ROOT / "signals" / name).exists():
                signal(name)
        for role, future in futures.items():
            try:
                code = future.result(timeout=35)
                outcome.setdefault("native_exit_codes", {})[role] = code
            except BaseException as error:
                outcome["failures"].append({"role": role, "cleanup_error": repr(error)})
                outcome["claims_verified"] = False
        if pool:
            pool.shutdown(wait=True)
        if RAW.is_dir():
            save(RAW / "timeline.json", timeline)
            after = git("status", "--porcelain=v1")
            (RAW / "owner-status-after.txt").write_bytes(after)
            outcome["owner_status_unchanged"] = ((RAW / "owner-status-before.txt").read_bytes() == after)
        outcome["finished_utc"] = utc()
        save(ROOT / "results.json", outcome)
        save(ROOT / "evidence-sha256.json", [digest(path) for path in sorted(ROOT.rglob("*")) if path.is_file()])
    print(json.dumps({"root": str(ROOT), "complete": outcome["complete"],
                      "claims_verified": outcome["claims_verified"], "failures": outcome["failures"]}, indent=2))
    return 0 if outcome["claims_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(run())
