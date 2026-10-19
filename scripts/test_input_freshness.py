#!/usr/bin/env python3
"""Source-bound, portable native workload for stale input liveness.

Runs the SAME external GDScript fixture against either frozen source tree. Godot
is always awaited/captured, including Windows GUI-subsystem executables. Evidence
must live outside the source checkout. No campaign/matrix tooling is modified.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import socket
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "game/tests/input_freshness_probe.gd"
ERROR = re.compile(r"SCRIPT ERROR|ERROR:|ObjectDB instances leaked|resources still in use", re.I)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def identity(source):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=source, text=True).strip()
    return {"commit": git("rev-parse", "HEAD"), "game_tree": git("rev-parse", "HEAD:game"),
            "status": git("status", "--porcelain"),
            "input_stream_sha256": sha(source / "game/scripts/network/input_stream.gd")}


def command(godot, source, script):
    return [str(godot), "--headless", "--path", str(source / "game"), "--max-fps", "60", "--script", str(script)]


def capture(cmd, cwd, output, timeout=180):
    start = time.monotonic()
    result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    output.write_bytes(result.stdout)
    return {"command": cmd, "exit": result.returncode, "seconds": time.monotonic() - start,
            "log": output.name, "log_sha256": sha(output), "logged_errors": bool(ERROR.search(result.stdout.decode("utf-8", "replace")))}


def trial(godot, source, out, scenario, prediction):
    out.mkdir()
    barrier = out / "barrier"
    barrier.mkdir()
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    duration = 34 if scenario == "stale-replay" else 8
    children, logs, commands = {}, {}, {}
    env = os.environ.copy()
    for key in ("SIGHTBREAK_SERVER_KEY", "SIGHTBREAK_JOIN_TICKET", "SIGHTBREAK_RESULT_SPOOL"):
        env.pop(key, None)
    try:
        for role in ("server", "client"):
            cmd = command(godot, source, PROBE) + ["--", f"--role={role}", f"--scenario={scenario}",
                  f"--port={port}", f"--seconds={duration}", f"--output={out / (role + '.json')}", f"--barrier={barrier}"]
            if prediction:
                cmd.append("--prediction")
            commands[role] = cmd
            logs[role] = (out / (role + ".log")).open("wb")
            children[role] = subprocess.Popen(cmd, cwd=source, env=env, stdout=logs[role], stderr=subprocess.STDOUT)
            deadline = time.monotonic() + 45
            while not (out / (role + ".json.ready")).exists():
                if children[role].poll() is not None or time.monotonic() > deadline:
                    raise RuntimeError(f"{role} readiness failed; inspect {out}")
                time.sleep(.02)
        (barrier / "start.tmp").write_text(json.dumps({"epoch": time.time() + .5}), encoding="utf-8")
        os.replace(barrier / "start.tmp", barrier / "start.json")
        deadline = time.monotonic() + duration + 15
        while not all((out / (role + ".json")).exists() for role in children):
            if any(p.poll() is not None for p in children.values()) or time.monotonic() > deadline:
                raise RuntimeError(f"reports incomplete; inspect {out}")
            time.sleep(.02)
        (barrier / "stop").write_text("reports latched; release peers", encoding="utf-8")
        exits = {role: process.wait(timeout=15) for role, process in children.items()}
    finally:
        for process in children.values():
            if process.poll() is None:
                process.kill()
                process.wait()
        for log in logs.values():
            log.close()
    server = json.loads((out / "server.json").read_text(encoding="utf-8"))
    client = json.loads((out / "client.json").read_text(encoding="utf-8"))
    rows = server["rows"]
    # Independent authority measurements, not client-predicted displacement.
    held = [r for r in rows if 3.8 <= r["t"] <= 4.8]
    recovered = [r for r in rows if 7.0 <= r["t"] <= 7.8]
    cap_rows = [r for r in client["rows"] if r["pending"] == 120 and r["t"] < 5]
    fresh = [r for r in rows if 2.0 <= r["t"] < 4.8]
    ack_changes = [row for i, row in enumerate(fresh) if i == 0 or row["ack"] != fresh[i - 1]["ack"]]
    last_ack_time = ack_changes[-1]["t"] if ack_changes else None
    stopped = [r for r in rows if last_ack_time is not None and last_ack_time <= r["t"] < 5 and abs(r["vx"]) < .001 and abs(r["move_x"]) < .001]
    result = {"scenario": scenario, "prediction": prediction, "commands": commands, "exits": exits,
              "native_errors": {role: bool(ERROR.search((out / (role + '.log')).read_text(encoding="utf-8", errors="replace"))) for role in children},
              "protocol": server["protocol"], "privacy_violations": client["privacy_violations"],
              "hit_history_frames": server["hit_history_frames"], "max_pending": client["max_pending"],
              "client_prediction": client["prediction"], "dropped_snapshots": client["dropped_snapshots"],
              "first_history_cap_seconds": cap_rows[0]["t"] if cap_rows else None,
              "stale_window_displacement_m": abs(held[-1]["x"] - held[0]["x"]) if held else None,
              "stale_window_max_speed_mps": max((abs(r["vx"]) for r in held), default=None),
              "last_ack_before_resume_seconds": last_ack_time,
              "stop_after_last_ack_seconds": stopped[0]["t"] - last_ack_time if stopped else None,
              "recovery_min_speed_mps": min((abs(r["vx"]) for r in recovered), default=None),
              "shots_at_end": rows[-1]["shots"], "ammo_at_end": rows[-1]["ammo"],
              "rejected_packets": rows[-1]["rejected"], "disconnected_at_seconds": server["disconnected_at"],
              "final_peer_count": server["final_peer_count"], "lifecycle_entries": server["lifecycle_entries"],
              "input_queues": server["input_queues"], "pending_joins": server["pending_joins"]}
    result["transport_authority_privacy_pass"] = (all(code == 0 for code in exits.values()) and not any(result["native_errors"].values())
        and result["protocol"] == 6 and result["privacy_violations"] == 0 and result["hit_history_frames"] == 0
        and result["client_prediction"] == prediction and client["max_pending"] <= 120)
    if scenario == "stale-replay":
        result["improvement_gate"] = (31.5 <= server["disconnected_at"] <= 32.5 and all(server[k] == 0 for k in ("final_peer_count", "lifecycle_entries", "input_queues", "pending_joins")))
    else:
        result["recovery_and_edges_pass"] = (result["shots_at_end"] == 2 and result["ammo_at_end"] == 13
            and result["recovery_min_speed_mps"] > .9 and server["final_peer_count"] == 1)
        result["improvement_gate"] = (result["stale_window_displacement_m"] < .001 and result["stale_window_max_speed_mps"] < .001
            and result["stop_after_last_ack_seconds"] is not None and result["stop_after_last_ack_seconds"] <= .35) if scenario == "snapshot-gap" else True
    (out / "metrics.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--godot", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--scenarios", nargs="+", choices=["steady", "input-gap", "snapshot-gap", "stale-replay"], default=["steady", "input-gap", "snapshot-gap", "stale-replay"])
    parser.add_argument("--prediction", nargs="+", choices=["off", "on"], default=["off", "on"])
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--checks", action="store_true")
    parser.add_argument("--expect-fixed", action="store_true", help="also fail the run when a declared improvement gate fails")
    parser.add_argument("--skip-import", action="store_true", help="use a previously imported class/resource cache; permits clean frozen-source runs after restoring platform-generated .import metadata")
    parser.add_argument("--allow-dirty", action="store_true", help="preflight only; final source-bound runs must be clean")
    args = parser.parse_args()
    args.source, args.out, args.godot = args.source.resolve(), args.out.resolve(), args.godot.resolve()
    if args.out == args.source or args.source in args.out.parents:
        parser.error("evidence must be outside the measured source")
    args.out.mkdir(parents=True, exist_ok=False)
    before = identity(args.source)
    if before["status"] and not args.allow_dirty:
        parser.error("source is dirty")
    manifest = {"source_before": before, "platform": platform.platform(), "python": platform.python_version(),
                "harness_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                "harness_status": subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip(),
                "expect_fixed": args.expect_fixed,
                "godot_sha256": sha(args.godot), "driver_sha256": sha(Path(__file__)), "probe_sha256": sha(PROBE),
                "scope": "real headless native Godot ENet pair; application snapshot omission and hostile replay; isolated static platform; no rendered/device/WAN claim", "trials": [], "checks": []}
    def save():
        (args.out / "summary.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    save()
    try:
        if args.skip_import:
            if not (args.source / "game/.godot/global_script_class_cache.cfg").is_file():
                raise RuntimeError("import script classes first")
            manifest["import"] = {"scope": "previously prepared native import cache; --skip-import"}
        else:
            manifest["import"] = capture([str(args.godot), "--headless", "--path", str(args.source / "game"), "--editor", "--import"], args.source, args.out / "import.log", 240)
            if manifest["import"]["exit"] or manifest["import"]["logged_errors"]:
                raise RuntimeError("native import failed")
        if args.checks:
            for name in ("input_stream_test", "input_lifecycle_test", "peer_lifecycle_test", "reconnect_policy_test", "snapshot_buffer_test", "movement_prediction_test", "state_privacy_test", "integration_actor_lifecycle_test", "hit_history_test"):
                manifest["checks"].append(capture(command(args.godot, args.source, "res://tests/" + name + ".gd"), args.source, args.out / (name + ".log")))
                save()
        for repeat in range(args.repeats):
            for scenario in args.scenarios:
                for prediction in args.prediction:
                    name = f"{repeat + 1}-{scenario}-prediction-{prediction}"
                    metrics = trial(args.godot, args.source, args.out / name, scenario, prediction == "on")
                    manifest["trials"].append({"directory": name, "metrics": metrics})
                    print(json.dumps({"trial": name, "gate": metrics["improvement_gate"], "authority_privacy": metrics["transport_authority_privacy_pass"], "stale_displacement_m": metrics["stale_window_displacement_m"]}), flush=True)
                    save()
    finally:
        manifest["source_after"] = identity(args.source)
        manifest["source_unchanged"] = manifest["source_before"] == manifest["source_after"]
        save()
    invalid = (not manifest["source_unchanged"] or any(row["exit"] or row["logged_errors"] for row in manifest["checks"])
        or any(not row["metrics"]["transport_authority_privacy_pass"] or not row["metrics"].get("recovery_and_edges_pass", True)
               or (args.expect_fixed and not row["metrics"]["improvement_gate"]) for row in manifest["trials"]))
    # Baseline's failed improvement gate is an observed defect, not process failure.
    return int(invalid)


if __name__ == "__main__":
    raise SystemExit(main())
