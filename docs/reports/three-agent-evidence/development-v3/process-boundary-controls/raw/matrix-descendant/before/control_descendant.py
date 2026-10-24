"""Real CPython subprocess control of run_check; no native programs are launched."""
from pathlib import Path
import json
import os
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
sys.path[:0] = [str(OUT / "source/scripts"), str(ROOT / "scripts")]
import validate_matrix as matrix
from native_log import failed

case = OUT / "descendant-control"
case.mkdir()
started = case / "child-started.json"
finished = case / "child-finished.json"
child = (
    "from pathlib import Path; import json, os, time; "
    f"Path({str(started)!r}).write_text(json.dumps({{'pid': os.getpid()}})); "
    "time.sleep(1.5); print('ERROR: escaped CPython descendant failed', flush=True); "
    f"Path({str(finished)!r}).write_text(json.dumps({{'exit_requested': 7}})); "
    "raise SystemExit(7)"
)
parent = (
    "from pathlib import Path; import subprocess, sys, time; "
    f"p=subprocess.Popen([sys.executable, '-B', '-c', {child!r}]); "
    f"marker=Path({str(started)!r}); "
    "\nwhile not marker.exists(): time.sleep(.005)\n"
    "print('parent exiting zero; child PID', p.pid, flush=True)"
)
(case / "child-program.txt").write_text(child)
(case / "parent-program.txt").write_text(parent)
record = matrix.run_check("control", [sys.executable, "-B", "-c", parent],
                          case, os.environ.copy(), "SYNTHETIC-CONTROL-NOT-A-SOURCE-CLAIM", timeout=10)
early = {"record": record, "child_started": started.exists(),
         "child_finished_at_return": finished.exists(),
         "raw_log_at_return": (case / "control.log").read_text()}
(case / "at-return.json").write_text(json.dumps(early, indent=2))
deadline = time.monotonic() + 8
while not finished.exists() and time.monotonic() < deadline:
    time.sleep(.05)
time.sleep(.1)
late = (case / "control.log").read_text()
result = {**early, "child_finished": finished.exists(), "raw_log_after_child": late,
          "late_log_fails_existing_native_log_gate": failed(late),
          "bug_reproduced": record["passed"] and not early["child_finished_at_return"] and failed(late)}
(case / "reproduction.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2), flush=True)
