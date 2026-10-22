#!/usr/bin/env python3
"""Recompute retained native timing evidence. Does not launch Godot or mutate inputs."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[4]
GUIDANCE = ROOT / "docs/reports/gauntlet/m1-postplant-guidance"
WINDOWS = ROOT / "docs/reports/gauntlet/m1-native-ci-39735001567/archives/windows-qa-receipts-12407696223.zip"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rows(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.splitlines() if line]


def find(actions: list[dict], event: str, key: str, value: str) -> dict:
    matches = [row for row in actions if row["event"] == event and row.get(key) == value]
    assert len(matches) == 1, (event, key, value, len(matches))
    return matches[0]


def interval(start: dict, end: dict) -> dict:
    a, b = start["observed"], end["observed"]
    wall = end["seconds"] - start["seconds"]
    ticks = b["simulation_tick"] - a["simulation_tick"]
    frames = b["drawn_frames"] - a["drawn_frames"]
    simulation = b["elapsed"] - a["elapsed"]
    assert wall > 0 and frames > 0 and ticks > 0
    assert abs(simulation - ticks / 60) < 1e-9
    return {
        "start_driver_seconds": start["seconds"], "end_driver_seconds": end["seconds"],
        "driver_wall_seconds": wall,
        "start_observation": a, "end_observation": b,
        "observed_tick_delta": ticks, "observed_simulation_seconds": simulation,
        "observed_drawn_frame_delta": frames,
        "observed_ticks_per_drawn_frame": ticks / frames,
        "observed_drawn_frames_per_driver_wall_second": frames / wall,
        "observed_simulation_seconds_per_driver_wall_second": simulation / wall,
        "clock_scope": "Driver-clock action bracket; engine observations may precede actions. No clock domains equated.",
    }


def inspect_native(actions: list[dict], result: dict, log: str, terminal: dict) -> dict:
    initial = find(actions, "capture_end", "capture", "02-offline-initial-conditions")
    resolved = find(actions, "capture_end", "capture", "07-objective-round-resolved")
    return {
        "source": result["source"], "passed": result["passed"],
        "error": result.get("error"), "partial_checks": result["partial_checks"],
        "initial_settings": result["initial"]["initial_profile"]["settings"],
        "capture_dimensions": sorted({tuple(capture["dimensions"]) for capture in result["captures"]}),
        "renderer_lines": [line for line in log.splitlines() if "Using Device:" in line],
        "initial_capture_to_terminal": interval(initial, terminal),
        "resolution_capture_to_terminal": interval(resolved, terminal),
    }


report = {"scope": "CPU-free recomputation of archived observations; no new native result", "linux": []}
for number in (3, 4):
    directory = GUIDANCE / f"round-{number}/native-plant"
    data = {name: (directory / name).read_bytes() for name in ("actions.jsonl", "results.json", "client.log", "trace/status.json")}
    actions = rows(data["actions.jsonl"])
    failures = [row for row in actions if row["event"] == "failure"]
    assert len(failures) == 1
    result = json.loads(data["results.json"])
    native = inspect_native(actions, result, data["client.log"].decode(), failures[0])
    status = json.loads(data["trace/status.json"])
    assert not result["passed"] and result["error"] == "Natural next round after objective resolution"
    assert status["phase"] == "post" and status["round_number"] == 1
    assert status["simulation_tick"] == 2625 and abs(status["time_left"] - 0.65) < 1e-9
    assert native["initial_capture_to_terminal"]["observed_tick_delta"] == 2600
    assert native["initial_capture_to_terminal"]["observed_drawn_frame_delta"] == 325
    assert native["resolution_capture_to_terminal"]["observed_tick_delta"] == 247
    assert native["resolution_capture_to_terminal"]["observed_drawn_frame_delta"] == 31
    native.update(round=number, input_sha256={name: digest(value) for name, value in data.items()},
                  final_time_left=status["time_left"], final_window_size=status["ui"]["window_size"])
    report["linux"].append(native)

with zipfile.ZipFile(WINDOWS) as outer:
    inner = outer.read("qa-receipts.zip")
with zipfile.ZipFile(io.BytesIO(inner)) as archive:
    data = {name: archive.read("evidence/offline-plant/" + name) for name in ("actions.jsonl", "results.json", "client.log", "trace/status.json")}
actions = rows(data["actions.jsonl"])
result = json.loads(data["results.json"])
terminal = find(actions, "observed", "label", "Natural next round after objective resolution")
assert result["passed"] and terminal["observed"]["phase"] == "buy" and terminal["observed"]["round_number"] == 2
native = inspect_native(actions, result, data["client.log"].decode(), terminal)
native.update(run_id=39735001567, archive_sha256=digest(WINDOWS.read_bytes()),
              inner_archive_sha256=digest(inner),
              input_sha256={name: digest(value) for name, value in data.items()},
              final_window_size=json.loads(data["trace/status.json"])["ui"]["window_size"],
              client_commands=[row["command"] for row in result["commands"] if row["name"] == "client"])
report["windows"] = native
assert all(row["source"]["source_content_sha256"] == native["source"]["source_content_sha256"] for row in report["linux"])
assert all(row["initial_settings"] == native["initial_settings"] for row in report["linux"])
report["same_shipping_content_and_initial_settings"] = True

legacy = []
for name in ("before", "standard", "low"):
    path = f"docs/reports/evidence-v03/render-profile/{name}-summary.json"
    data = subprocess.check_output(["git", "show", f"ba5013d:{path}"], cwd=ROOT)
    summary = json.loads(data)
    legacy.append({"path": path, "source_blob_sha256": digest(data), "context": summary["context"],
                   "quality": summary["quality"], "cpus": summary["cpus"], "mesa_workers": summary["mesa_workers"],
                   "runs": summary["runs"], "frames_per_view_per_run": summary["frames_per_view_per_run"],
                   "views": summary["views"]})
report["legacy_fixed_work_profiles"] = legacy
print(json.dumps(report, indent=2) + "\n", end="")
