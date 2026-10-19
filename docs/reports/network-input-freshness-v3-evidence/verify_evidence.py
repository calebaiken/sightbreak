"""Recompute the matched-run verdict from retained raw native timelines.

This post-run verifier is separate from the frozen native driver. It accepts the
evidence directory as its optional first argument and writes only a derived
verification.json there. It never edits or reruns either measured source tree.
"""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent
EXPECTED = {"baseline-r3": "701ce2c4d7f8b2872cf1fefa64cb6edd0cd1a3fd",
            "candidate-r2": "77f204083ab5bea4dc9149d3179daf540a994de4"}
ERROR = re.compile(r"SCRIPT ERROR|ERROR:|ObjectDB instances leaked|resources still in use", re.I)


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def verify():
    result = {"pass": True, "failures": [], "sources": {}, "raw_sha256": {}}
    def require(condition, label):
        if not condition:
            result["failures"].append(label)
    for name, commit in EXPECTED.items():
        folder = ROOT / name
        summary = load(folder / "summary.json")
        require(summary["source_before"]["commit"] == commit, name + ": wrong source")
        require(summary["source_before"] == summary["source_after"] and not summary["source_before"]["status"], name + ": source changed or dirty")
        require(summary["harness_commit"] == EXPECTED["candidate-r2"] and not summary["harness_status"], name + ": harness not frozen/clean")
        require(len(summary["checks"]) == 9, name + ": missing maintained groups")
        require(len(summary["trials"]) == 16, name + ": missing scenario repetitions")
        for check in summary["checks"]:
            require(check["exit"] == 0 and not check["logged_errors"], name + ": " + check["log"])
            require(not ERROR.search((folder / check["log"]).read_text(encoding="utf-8", errors="replace")), name + ": raw maintained log error")
        metrics = []
        for trial in summary["trials"]:
            trial_dir = folder / trial["directory"]
            server, client = load(trial_dir / "server.json"), load(trial_dir / "client.json")
            row = load(trial_dir / "metrics.json")
            require(row == trial["metrics"], name + ": embedded/raw metrics mismatch")
            require(row["transport_authority_privacy_pass"], str(trial_dir) + ": authority/privacy")
            for role in ("server", "client"):
                require(not ERROR.search((trial_dir / (role + ".log")).read_text(encoding="utf-8", errors="replace")), str(trial_dir) + ": raw native error")
            require(server["protocol"] == client["protocol"] == 6 and server["hit_history_frames"] == client["hit_history_frames"] == 0, str(trial_dir) + ": protocol/history")
            require(client["privacy_violations"] == 0 and client["max_pending"] <= 120, str(trial_dir) + ": privacy/bound")
            require(row["barrier_control"] and server["barrier_read_retries"] > 0 and client["barrier_read_retries"] > 0, str(trial_dir) + ": missing barrier negative control")
            sample = [r for r in server["rows"] if 3.8 <= r["t"] <= 4.8]
            distance = abs(sample[-1]["x"] - sample[0]["x"])
            require(distance == row["stale_window_displacement_m"], str(trial_dir) + ": displacement mismatch")
            metric = {"trial": trial["directory"], "stale_displacement_m": distance,
                      "stop_seconds": row["stop_after_last_ack_seconds"], "disconnected_seconds": server["disconnected_at"]}
            if row["scenario"] == "stale-replay":
                fixed = name == "candidate-r2"
                require((31.5 <= server["disconnected_at"] <= 32.5) if fixed else server["disconnected_at"] == -1, str(trial_dir) + ": replay attribution")
                require(server["final_peer_count"] == (0 if fixed else 1), str(trial_dir) + ": replay ownership")
                require(server["rows"][-1]["shots"] == 1 and server["rows"][-1]["ammo"] == 14, str(trial_dir) + ": replay invented semi-auto edge")
            else:
                require(row["recovery_and_edges_pass"], str(trial_dir) + ": recovery/edges")
                recovery = [r for r in server["rows"] if 7.0 <= r["t"] <= 7.8]
                # Signed velocity also verifies that the later LEFT command won;
                # the frozen driver's speed gate alone uses absolute velocity.
                metric["largest_recovery_vx_mps"] = max(r["vx"] for r in recovery)
                require(metric["largest_recovery_vx_mps"] < -.9, str(trial_dir) + ": wrong recovery direction")
                if row["scenario"] == "snapshot-gap":
                    require(client["max_pending"] == 120 and client["dropped_snapshots"] >= 60, str(trial_dir) + ": gap did not exercise cap")
                    require(distance < .001 if name == "candidate-r2" else distance > .9, str(trial_dir) + ": gap attribution")
            require(row["improvement_gate"] == (name == "candidate-r2" or row["scenario"] in ("steady", "input-gap")), str(trial_dir) + ": unexpected gate result")
            metrics.append(metric)
        result["sources"][name] = {"commit": commit, "maintained_groups": len(summary["checks"]), "native_pairs": len(summary["trials"]), "metrics": metrics}
        for path in sorted(folder.rglob("*")):
            if path.is_file():
                result["raw_sha256"][path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    left, right = (load(ROOT / name / "summary.json") for name in EXPECTED)
    for key in ("godot_sha256", "driver_sha256", "probe_sha256", "python", "platform"):
        require(left[key] == right[key], "matched environment/harness mismatch: " + key)
    result["pass"] = not result["failures"]
    (ROOT / "verification.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"pass": result["pass"], "failures": result["failures"], "sources": result["sources"]}, indent=2))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(verify())
