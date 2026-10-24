"""Read-only source receipts and serial pure/synthetic unit runner.

Every write is beneath this new external evidence directory. No native client,
engine, OCR binary, database, server, or network endpoint is launched.
"""
import datetime
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
OUT = Path(__file__).resolve().parent
FILES = [
    "scripts/test_validate_matrix.py", "scripts/verify_integration_export.py",
    "scripts/verify_offline_export.py", "scripts/offline_hud.py",
    "scripts/test_export_ui.py", "scripts/test_offline_hud.py",
    "scripts/validate_matrix.py", "scripts/export_flow.py", "scripts/test_export_flow.py",
    "scripts/build_manifest.py", "scripts/godot_process.py", "scripts/matrix_process.py",
    "scripts/native_log.py", "scripts/ocr_process.py", "scripts/fixtures/export_integration.gd",
    "game/scripts/main.gd", "game/tests/ux_contract_test.gd",
    "game/scripts/gameplay/actor.gd", "game/scripts/gameplay/match.gd",
    "game/scripts/gameplay/weapons.gd", "game/scripts/ui/design_tokens.gd",
    ".github/workflows/v3-development.yml",
]


def git(*args):
    result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                            text=True, encoding="utf-8", errors="replace", check=True)
    return result.stdout


def snapshot(label):
    data = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "head": git("rev-parse", "HEAD").strip(),
            "status": git("status", "--porcelain=v1", "--untracked-files=all"),
            "python": sys.version, "executable": sys.executable,
            "scope": "Read-only critic; local pure/synthetic controls only", "files": {}}
    for relative in FILES:
        path = ROOT / relative
        if path.is_file():
            raw = path.read_bytes()
            data["files"][relative] = {"sha256": hashlib.sha256(raw).hexdigest(),
                                      "bytes": len(raw), "mtime_ns": path.stat().st_mtime_ns}
        else:
            data["files"][relative] = {"missing": True}
    with (OUT / f"source-{label}.json").open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2)
        stream.write("\n")
    return data


def run_units():
    os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
    scratch = OUT / "scratch"
    scratch.mkdir()
    os.environ["TEMP"] = os.environ["TMP"] = str(scratch)
    tempfile.tempdir = str(scratch)
    original = tempfile.TemporaryDirectory
    current = None

    class RetainedTemporaryDirectory(original):
        def __init__(self, *args, **kwargs):
            kwargs.setdefault("dir", str(current))
            super().__init__(*args, **kwargs)
            self._finalizer.detach()

        def cleanup(self):
            pass  # Keep raw synthetic controls, including expected failures.

    tempfile.TemporaryDirectory = RetainedTemporaryDirectory
    sys.path.insert(0, str(ROOT / "scripts"))
    rows = []
    try:
        for name in ("test_validate_matrix", "test_export_ui", "test_offline_hud", "test_export_flow"):
            current = OUT / "units" / name
            current.mkdir(parents=True)
            snapshot(name + "-before")
            module = importlib.import_module(name)
            suite = unittest.defaultTestLoader.loadTestsFromModule(module)
            with (current / "unittest.log").open("x", encoding="utf-8") as log:
                result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
            rows.append({"module": name, "tests_run": result.testsRun,
                         "failures": len(result.failures), "errors": len(result.errors),
                         "skipped": len(result.skipped), "passed": result.wasSuccessful()})
            snapshot(name + "-after")
            print(json.dumps(rows[-1]), flush=True)
    finally:
        tempfile.TemporaryDirectory = original
    with (OUT / "units.json").open("x", encoding="utf-8") as stream:
        json.dump(rows, stream, indent=2)
        stream.write("\n")
    return all(row["passed"] for row in rows)


if __name__ == "__main__":
    if sys.argv[1:] == ["baseline"]:
        data = snapshot("before")
        with (OUT / "scoped-working-diff.patch").open("x", encoding="utf-8") as stream:
            stream.write(git("diff", "--", *FILES[:6]))
        print(json.dumps({"head": data["head"], "files": len(data["files"])}))
    elif sys.argv[1:] == ["units"]:
        raise SystemExit(0 if run_units() else 1)
    elif sys.argv[1:] == ["final"]:
        data = snapshot("after")
        original = json.loads((OUT / "source-before.json").read_text(encoding="utf-8"))
        changed = {key: {"before": value, "after": data["files"].get(key)}
                   for key, value in original["files"].items() if value != data["files"].get(key)}
        result = {"head_changed": original["head"] != data["head"],
                  "status_changed": original["status"] != data["status"],
                  "selected_file_drift": changed,
                  "evidence_bytes_at_check": sum(path.stat().st_size for path in OUT.rglob("*") if path.is_file()),
                  "bound_bytes": 2 * 1024 * 1024}
        with (OUT / "drift.json").open("x", encoding="utf-8") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
        print(json.dumps(result, indent=2))
    else:
        raise SystemExit("usage: audit.py baseline|units|final")
