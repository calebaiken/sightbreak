"""Two tiny immutable-source component invocations, not a network campaign."""
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\sightbreak-v3")
ENGINE = Path(r"C:\Users\blith\AppData\Local\Temp\opencode\godot\Godot_v4.7.2-stable_win64.exe")
sys.path.insert(0, str(ROOT / "scripts"))
from matrix_process import run_process
from native_log import failed


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args])


def main():
    out = HERE / "attempt-r2"
    out.mkdir()  # Never overwrite prior raw evidence.
    (out / "private").mkdir()
    (out / "neutral").mkdir()
    sources = ["701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd", "f3ceaad98e089aa393c7f5fa650a52695094d979"]
    secrets.SystemRandom().shuffle(sources)
    probe = (HERE / "probe.gd").read_bytes()
    source_paths = ["game/scripts/network/input_stream.gd", "game/scripts/network/input_gate.gd"]
    frozen = {"scope": "isolated native component control, not campaign", "probe_sha256": sha(probe), "driver_sha256": sha(Path(__file__).read_bytes()), "engine_sha256": file_sha(ENGINE), "engine_version": subprocess.check_output([str(ENGINE), "--version"], text=True).strip(), "samples": {}}
    projects = []
    for commit in sources:
        label = "sample-" + secrets.token_hex(3)
        project = out / "private" / label
        project.mkdir()
        config = b'config_version=5\n\n[application]\nconfig/name="SIGHTBREAK native input component control"\n\n[rendering]\nrenderer/rendering_method="gl_compatibility"\n'
        (project / "project.godot").write_bytes(config)
        (project / "probe.gd").write_bytes(probe)
        files = {}
        for path in source_paths:
            data = git("show", f"{commit}:{path}")
            (project / Path(path).name).write_bytes(data)
            files[path] = {"blob": git("rev-parse", f"{commit}:{path}").decode().strip(), "sha256": sha(data)}
        frozen["samples"][label] = {"source_commit": commit, "files": files, "config_sha256": sha(config)}
        projects.append((label, project))
    # Record all exact production/probe/driver bytes before either import/run.
    (out / "private" / "SOURCE_FROZEN_BEFORE_EXECUTION.json").write_text(json.dumps(frozen, indent=2) + "\n", encoding="utf-8")
    results = []
    for label, project in projects:
        raw = out / "neutral" / label
        raw.mkdir()
        env = os.environ.copy()
        state = project / ".state"
        for name in ("APPDATA", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
            env[name] = str(state / name)
        for phase, args in (("import", ["--headless", "--editor", "--import", "--quit"]), ("probe", ["--headless", "--script", "res://probe.gd"])):
            command = [str(ENGINE), "--path", str(project), *args]
            log = raw / f"{phase}.log"
            with log.open("x", encoding="utf-8") as output:
                code = run_process(command, cwd=project, env=env, log=output, result_path=raw / f"{phase}.process.json", timeout=35)
            text = log.read_text(encoding="utf-8", errors="replace")
            if code != 0 or failed(text) or "HARNESS_ERROR" in text:
                raise RuntimeError(f"{label} {phase} failed, actual exit {code}; original log retained")
            if phase == "probe":
                lines = [line.removeprefix("INPUT_BOUNDARY_RESULT ") for line in text.splitlines() if line.startswith("INPUT_BOUNDARY_RESULT ")]
                if len(lines) != 1:
                    raise RuntimeError("missing/ambiguous component summary")
                result = json.loads(lines[0])
                if result["failures"] != 0 or result["checks"] < 20:
                    raise RuntimeError("component assertions did not complete cleanly")
                result["label"] = label
                result["actual_exit"] = code
                (raw / "result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
                results.append(result)
        for path, receipt in frozen["samples"][label]["files"].items():
            if sha((project / Path(path).name).read_bytes()) != receipt["sha256"]:
                raise RuntimeError("production module bytes changed during component invocation")
        if sha((project / "probe.gd").read_bytes()) != frozen["probe_sha256"]:
            raise RuntimeError("probe bytes changed during component invocation")
    (out / "neutral" / "RESULTS.json").write_text(json.dumps({"passed": True, "samples": results, "scope": frozen["scope"], "source_key_withheld": True}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"passed": True, "neutral": str(out / "neutral"), "private_key": str(out / "private" / "SOURCE_FROZEN_BEFORE_EXECUTION.json"), "samples": [{"label": r["label"], "checks": r["checks"], "exit": r["actual_exit"]} for r in results]}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        if (HERE / "attempt-r2").is_dir():
            (HERE / "attempt-r2" / "FAILED.json").write_text(json.dumps({"passed": False, "error": str(error), "when_ns": time.time_ns()}, indent=2) + "\n", encoding="utf-8")
        raise
