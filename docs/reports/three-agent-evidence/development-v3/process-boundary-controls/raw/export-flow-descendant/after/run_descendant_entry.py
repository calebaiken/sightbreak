"""Independent end-to-end entry/supervisor/worker control, only CPython children."""
from pathlib import Path
import json
import os
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
case = HERE / "entry-descendant-control"
case.mkdir()
out = case / "evidence"
command = [sys.executable, "-B", str(HERE / "synthetic_descendant_entry.py"), "--output", str(out), "--timeout", "5"]
with (case / "entry.stdout.txt").open("xb") as stdout, (case / "entry.stderr.txt").open("xb") as stderr:
    process = subprocess.Popen(command, stdout=stdout, stderr=stderr, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    code = process.wait(timeout=15)
result = json.loads((out / "results.json").read_text())
early = {"synthetic_control_not_native_evidence": True, "entry_exit": code,
         "result_at_return": result, "child_finished_at_return": (case / "child-finished.txt").exists(),
         "log_at_return": (out / "watchdog.log").read_text()}
(case / "at-return.json").write_text(json.dumps(early, indent=2) + "\n")
time.sleep(2)
late = (out / "watchdog.log").read_text()
observation = {**early, "child_finished_later": (case / "child-finished.txt").exists(),
               "log_after_child": late, "persisted_result_passed": json.loads((out / "results.json").read_text()).get("passed"),
               "false_pass_reproduced": code == 0 and result.get("passed") is True and "ERROR:" in late}
(case / "after-observation.json").write_text(json.dumps(observation, indent=2) + "\n")
print(json.dumps(observation, indent=2), flush=True)
