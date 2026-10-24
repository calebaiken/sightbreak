"""Read-only native/source re-audit plus new summary files; no native launches."""
from ctypes import WinDLL, POINTER, byref, get_last_error
from ctypes import wintypes as w
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent
OLD = ROOT.parent / "sol-recovery-contract-controls-20261024T0857266917001Z"
REPO = ROOT.parent / "sightbreak-v3"
COMMIT = "7b6f379a3f8c809d0985a64e883cbadfdd78d135"
ENGINE_SHA256 = "ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424"
PYTHON = ROOT.parent / "sightbreak-tools/python/cpython-3.13.15-windows-x86_64-none/python.exe"


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def file_record(path):
    return {"path": str(path), "size": path.stat().st_size, "sha256": sha(path)}


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def process_alive(pid):
    api = WinDLL("kernel32", use_last_error=True)
    api.OpenProcess.argtypes = [w.DWORD, w.BOOL, w.DWORD]
    api.OpenProcess.restype = w.HANDLE
    api.GetExitCodeProcess.argtypes = [w.HANDLE, POINTER(w.DWORD)]
    api.GetExitCodeProcess.restype = w.BOOL
    api.CloseHandle.argtypes = [w.HANDLE]
    api.CloseHandle.restype = w.BOOL
    handle = api.OpenProcess(0x1000, False, pid)
    if not handle:
        require(get_last_error() in (87, 1168), "Cannot establish process exit")
        return False
    try:
        code = w.DWORD()
        require(api.GetExitCodeProcess(handle, byref(code)), "Cannot query process")
        return code.value == 259
    finally:
        api.CloseHandle(handle)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def run():
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.version_info[:3] == (3, 13, 15),
            "Not approved CPython 3.13.15")
    result = load(ROOT / "results.json")
    require(result["complete"] is True and result["claims_verified"] is True and not result["failures"],
            "Original driver did not complete successfully")
    manifest = load(ROOT / "pre-import-manifest.json")
    require(manifest["commit"] == COMMIT and manifest["native_imports_started"] is False, "Wrong pre-import provenance")
    for record in manifest["inputs"] + [manifest["engine"], manifest["python"]]:
        require(file_record(Path(record["path"])) == {key: record[key] for key in ("path", "size", "sha256")},
                "Changed frozen input: " + record["path"])
    require(manifest["engine"]["sha256"] == ENGINE_SHA256, "Wrong actual engine hash")
    sources = []
    for record in manifest["source"]:
        source = subprocess.run(["git", "show", COMMIT + ":" + record["source_path"]], cwd=REPO,
                                check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=15).stdout
        require(source == Path(record["path"]).read_bytes(), "Source differs from exact Git blob")
        oid = hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest()
        require(oid == record["git_blob_oid"], "Source Git OID mismatch")
        sources.append({**record, "byte_equal_to_exact_git": True})
    ui = (ROOT / "source/economy_ui.gd").read_bytes().splitlines(keepends=True)
    require((ROOT / "project/receipt_predicates.gd").read_bytes() == b"extends RefCounted\n\n" + b"".join(ui[596:608]),
            "Predicate component not exact complete production region")
    require(sha(OLD / "blocked-final-sha256.json") == "698aa56f757a68deeba0092bbff810b4e75bf1ec38bbe127d7324c00a76367b4",
            "Prior blocked index changed")
    for record in load(OLD / "blocked-final-sha256.json"):
        require(file_record(Path(record["path"])) == record, "Prior blocked file changed")
    for name in ("project/probe.gd", "project/project.godot"):
        require((ROOT / name).read_bytes() == (OLD / name).read_bytes(), "Prepared probe/config changed")
    for record in load(ROOT / "evidence-sha256.json"):
        require(file_record(Path(record["path"])) == record, "Original successful evidence changed")

    native = {}
    exact_log_checks = []
    for filename, role, check_count in (
        ("native-A-ready.json", "A", 33), ("native-A.json", "A", 36),
        ("native-B-blocked.json", "B", 6), ("native-B.json", "B", 13),
    ):
        raw = (ROOT / "raw" / filename).read_text(encoding="utf-8")
        require(raw.endswith("\n"), "Incomplete persisted native JSON")
        event = json.loads(raw)
        log = (ROOT / "raw" / ("engine-" + role + ".log")).read_text(encoding="utf-8")
        literal = "NATIVE_JSON " + filename + " " + raw[:-1]
        require(log.splitlines().count(literal) == 1, "Not exactly equal to one actual engine-log line")
        require(event["complete"] is True and event["checks_passed"] is True and event["role"] == role,
                "Missing native completion")
        require(len(event["checks"]) == check_count, "Unexpected native control count")
        for check in event["checks"]:
            require(check["passed"] is True and canonical(check["actual"]) == canonical(check["expected"]),
                    "Control mismatch: " + check["name"])
        require(not any(term in log for term in ("ERROR:", "SCRIPT ERROR", "Parse Error", "HARNESS_ERROR")),
                "Unexpected engine diagnostics")
        native[filename] = event
        exact_log_checks.append({"file": filename, "role": role, "pid": event["pid"],
                                 "complete": True, "exact_persisted_json_to_engine_log": True,
                                 "assertion_count": check_count})
    stdout_sizes = {}
    for role in ("A", "B"):
        require(load(ROOT / "raw" / ("supervisor-" + role + ".json")) == {"complete": True, "exit": 0, "errors": []},
                "Missing/unclean process receipt")
        stdout_path = ROOT / "raw" / ("stdout-" + role + ".log")
        stdout_sizes[role] = stdout_path.stat().st_size
        require("HARNESS_ERROR" not in stdout_path.read_text(encoding="utf-8"), "Process harness error in stdout")

    a = native["native-A.json"]
    b = native["native-B.json"]
    blocked = native["native-B-blocked.json"]
    require(a["pid"] == native["native-A-ready.json"]["pid"] and b["pid"] == blocked["pid"]
            and a["pid"] != b["pid"], "Cross-process/same-B identity mismatch")
    require(not process_alive(a["pid"]) and not process_alive(b["pid"]), "Owned native PID is still alive")
    require(a["stage_result"] == 30 and blocked["stage_result"] == 22 and b["positive_result"] == 0,
            "S2 numeric stage results mismatch")
    require(a["storage_path"] == blocked["storage_path"] == b["storage_path"]
            and Path(a["storage_path"]).resolve() == (ROOT / "state/pending_transaction.json").resolve(),
            "Not the same new canonical owned journal path")
    require(blocked["pending"] == b["pending"], "B positive pending differs from blocked valid input")
    positive = load(ROOT / "state/pending_transaction.json")
    require(positive == {"schema": 1, "transaction": b["pending"]}, "Published valid receipt mismatch")
    require(sha(ROOT / "state/pending_transaction.json") == b["published_sha256"], "Positive receipt changed")
    require(not (ROOT / "state/pending_transaction.json.tmp").exists(), "Unexpected temporary receipt remains")
    timeline = load(ROOT / "raw/timeline.json")
    require([event["action"] for event in timeline] == ["launch-A", "launch-B", "B-blocked-observed", "A-exit-observed-before-B-retry"],
            "Unexpected native launch/exit sequence")
    require(timeline[2]["both_alive"] is True and timeline[2]["pending_file_exists"] is False
            and timeline[3]["A_alive"] is False and timeline[3]["B_alive"] is True,
            "Missing actual alive/absent/exit observations")

    s1 = a["s1_cases"]
    require(len(s1) == 22 and all(case["actual"] is case["expected"] for case in s1), "S1 fixture mismatch")
    by_name = {case["name"]: case for case in s1}
    require(by_name["market_minimal_unrelated_body"]["body"] == {"item": {"id": "unrelated"}, "credits": 0, "fee": 0},
            "Market finding body changed")
    require(by_name["case_minimal_partial_body"]["body"] == {"item": {"id": "partial"}, "roll": 0, "table_version": "anything"},
            "Case finding body changed")
    counts = {kind: sum(case["kind"] == kind for case in s1) for kind in ("finding", "positive", "negative")}
    require(counts == {"finding": 2, "positive": 3, "negative": 17}, "S1 classification count mismatch")
    preflights = [load(ROOT / "raw" / name) for name in ("preflight-before-A.json", "preflight-before-B-while-A-alive.json")]
    require(all(entry["safe_to_launch"] is True and all(entry[key] >= value for key, value in entry["minimums"].items())
                for entry in preflights), "Unsafe preflight")
    require((ROOT / "raw/owner-status-before.txt").read_bytes() == (ROOT / "raw/owner-status-after.txt").read_bytes(),
            "Owner status changed during native control")

    audit = {
        "utc": datetime.now(timezone.utc).isoformat(), "passed": True, "commit": COMMIT,
        "scope": "Bounded source-PR reproduction: native exact predicate component + complete unfiltered journal",
        "native_process_count_total": 2, "native_pids": {"A": a["pid"], "B": b["pid"]},
        "same_B_used_before_and_after_A_exit": True, "owned_native_processes_still_alive": False,
        "source": sources, "exact_native_json_log_checks": exact_log_checks,
        "S1": {"finding_acceptances": [by_name[name] for name in ("market_minimal_unrelated_body", "case_minimal_partial_body")],
               "shape_counts": counts, "integer_helper_controls": 3, "total_predicate_controls": 25,
               "all_controls_passed": True, "http_status_tested": False},
        "S2": {"A_invalid_stage": {"code": 30, "name": "ERR_INVALID_DATA", "new_guard_retained": True,
                                   "no_published_or_tmp_file": True},
               "B_valid_stage_while_A_alive": {"code": 22, "name": "ERR_ALREADY_IN_USE", "both_native_pids_alive": True},
               "B_same_valid_stage_after_A_exit": {"code": 0, "name": "OK", "exact_load_pending_equality": True},
               "published_positive_receipt_preserved": file_record(ROOT / "state/pending_transaction.json"),
               "oversize_unwritable_runtime_tested": False},
        "preflights": preflights, "original_driver_results_preserved": file_record(ROOT / "results.json"),
        "previous_blocked_bundle_unchanged": True, "probe_and_config_unchanged": True,
        "engine_sha256": ENGINE_SHA256, "stdout_sizes_bytes": stdout_sizes,
        "engine_logs_and_json_required_even_if_stdout_empty": True,
        "source_inference_only": result["source_inference_only"], "limitations": result["limitations"],
    }
    save(ROOT / "post-run-audit.json", audit)
    print(json.dumps({"passed": True, "native_pids": audit["native_pids"], "S1_counts": counts,
                      "S1_total": 25, "S2_codes": [30, 22, 0], "preflights": preflights,
                      "audit": file_record(ROOT / "post-run-audit.json")}, indent=2))


if __name__ == "__main__":
    try:
        run()
    except BaseException as error:
        save(ROOT / "post-run-audit-failure.json", {"passed": False, "error": repr(error), "traceback": traceback.format_exc()})
        raise
