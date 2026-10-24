"""Exactly one serial price-400 invocation per arm; no ancillary regression."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

repo = Path(__file__).resolve().parents[1]
base = Path("C:/Users/blith/AppData/Local/Temp/opencode")
output = repo / ".runtime/native-journal-only-r1"
output.mkdir(exist_ok=False)
freeze = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
assert not subprocess.check_output(["git", "status", "--porcelain"], cwd=repo, text=True)
bindings = {}
for name in ["validate_native_transaction_restart.py", "native_transaction_restart_probe.gd"]:
    path = "scripts/" + name
    data = (repo / path).read_bytes()
    assert data == subprocess.check_output(["git", "show", freeze + ":" + path], cwd=repo)
    bindings[name] = hashlib.sha256(data).hexdigest()
meta = dict(harness_commit=freeze, file_sha256=bindings, python=sys.version,
            wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), arms=[])
for label, folder, revision, expected in [
    ("baseline-701", "sightbreak-v2-baseline", "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd", 0),
    ("candidate-7b6f379", "sightbreak-native-pg-7b6f379", "7b6f379a3f8c809d0985a64e883cbadfdd78d135", 1),
]:
    command = [sys.executable, str(repo / "scripts/validate_native_transaction_restart.py"),
               "--source", str(base / folder), "--revision", revision,
               "--cache-source", str(base / folder / "game/.godot"),
               "--godot", str(base / "godot/Godot_v4.7.2-stable_win64.exe"),
               "--out", str(output / label), "--repetitions", "1", "--expect-recovered", str(expected)]
    (output / (label + ".command.json")).write_text(json.dumps(command, indent=2) + "\n", encoding="utf-8")
    launch = dict(label=label, command=command, started_wall_ns=time.time_ns())
    with (output / (label + ".stdout.txt")).open("wb") as stdout, (output / (label + ".stderr.txt")).open("wb") as stderr:
        process = subprocess.Popen(command, cwd=repo, stdout=stdout, stderr=stderr)
        launch["pid"] = process.pid
        launch["returncode"] = process.wait()
    launch["finished_wall_ns"] = time.time_ns()
    meta["arms"].append(launch)
    (output / "launch.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(label, "exit", launch["returncode"], flush=True)
    if launch["returncode"]:
        raise SystemExit(launch["returncode"])
print("Completed the two requested single-case invocations at frozen harness", freeze, flush=True)
