"""Serial, source-bound tooling checks; no native or delivery qualification."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
HERE = Path(__file__).resolve().parent
TESTS = [
    "test_build_manifest.py", "test_source_identity.py", "test_matrix_process.py",
    "test_validate_matrix.py", "test_godot_process.py", "test_export_flow.py",
    "test_export_ui.py", "test_offline_hud.py", "test_reload_negative_controls.py",
    "test_verify_builds.py",
]


def hashes():
    paths = sorted((ROOT / "scripts").glob("*.py"))
    return {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths}


def main():
    output = HERE / datetime.now(timezone.utc).strftime("attempt-%Y%m%dT%H%M%S%fZ")
    output.mkdir()
    before = hashes()
    report = {
        "scope": "Pre-freeze pure/synthetic tooling checks, not native validation or export evidence",
        "python": sys.version,
        "python_executable": sys.executable,
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_before": before,
        "checks": [],
    }
    for name, optimized in [(name, False) for name in TESTS] + [("test_verify_builds.py", True)]:
        command = [sys.executable, "-X", "faulthandler"]
        if optimized:
            command += ["-O"]
        command += [str(ROOT / "scripts" / name), "-v"]
        label = name.removesuffix(".py") + ("-optimized" if optimized else "")
        start = time.monotonic()
        with (output / (label + ".log")).open("x", encoding="utf-8") as raw:
            completed = subprocess.run(command, cwd=ROOT, stdout=raw, stderr=subprocess.STDOUT, timeout=180)
        row = {"test": name, "optimized": optimized, "command": command,
               "exit": completed.returncode, "seconds": round(time.monotonic() - start, 3),
               "log": label + ".log"}
        report["checks"].append(row)
        print(json.dumps(row), flush=True)
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    report["source_after"] = hashes()
    report["source_unchanged"] = report["source_after"] == before
    report["passed"] = report["source_unchanged"] and all(row["exit"] == 0 for row in report["checks"])
    (output / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "passed": report["passed"]}), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
