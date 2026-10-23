"""Run bounded CPU4 source checks and record each attempt without overwrite."""
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
for stem in ("checks",):
    for suffix in (".log", "-command.json"):
        path = HERE / (stem + suffix)
        if path.exists(): path.rename(HERE / ("initial-19" + suffix))
commands = [
    ("final-20", ["timeout", "60s", "taskset", "-c", "4", "env", "PYTHONPATH=scripts",
                  "python3", str(HERE / "checks.py")]),
    ("unchanged-60", ["timeout", "60s", "taskset", "-c", "4", "env", "PYTHONPATH=scripts",
                      "python3", "-m", "unittest", "-v", "test_touch_geometry_r4b",
                      "test_touch_method_r4b", "test_touch_receipts_r4b_r2", "test_touch_declaration_r4b_r3"]),
]
for stem, command in commands:
    output, receipt = HERE / (stem + ".log"), HERE / (stem + "-command.json")
    if output.exists() or receipt.exists(): raise SystemExit("refusing to overwrite attempt " + stem)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    sources = {str(path.relative_to(REPO)): hashlib.sha256(path.read_bytes()).hexdigest()
               for path in (HERE / "prototype.py", HERE / "checks.py", HERE / "retained-inputs.json")}
    begin = time.monotonic()
    result = subprocess.run(command, capture_output=True, text=True, cwd=REPO)
    output.write_text(result.stdout + result.stderr)
    record = {"command": command, "started_utc": started, "exit_code": result.returncode,
              "elapsed_seconds": time.monotonic() - begin, "engine_invocations": 0,
              "source_only": True, "sources_before": sources,
              "source_hashes_unchanged_after": all(hashlib.sha256((REPO / p).read_bytes()).hexdigest() == h for p, h in sources.items()),
              "log_sha256": hashlib.sha256(output.read_bytes()).hexdigest()}
    receipt.write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record), flush=True)
    if result.returncode: raise SystemExit(result.returncode)
