#!/usr/bin/env python3
"""Source-only audit. These numbers are predictions, never native measurements."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
BASE = "317410aff6f1a85b4f8c1b5b344c7ec50dd363d2"
REVIEWED = "68587d006a2f96d9586e5f133c91f23d9cce02d0"
DT = 1 / 60
TICKS = 1800


def git(*args: str) -> str:
    return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()


def original_predicate(times: list[int], spec: dict) -> bool:
    """The actual cadence checks at probe lines 116-121, assuming matching ammo."""
    if not times or times[0] != 0:
        return False
    if spec["automatic"]:
        return max(abs(t * DT - i * spec["interval"]) for i, t in enumerate(times)) <= DT + 1e-6
    gaps = [(b - a) * DT for a, b in zip(times, times[1:])]
    return bool(gaps) and min(gaps) + 1e-6 >= spec["interval"] and max(gaps) < spec["interval"] + 2 * DT


def predicted_ticks(spec: dict) -> list[int]:
    # Automatic sub-tick carry should track the interval's absolute phase. The
    # semi-auto fixture presses only on even ticks and starts a fresh interval.
    if spec["automatic"]:
        shots = []
        index = 0
        while (at := math.ceil(index * spec["interval"] / DT - 1e-8)) < TICKS:
            shots.append(at)
            index += 1
        return shots
    gap = 2 * math.ceil(spec["interval"] / (2 * DT) - 1e-8)
    return list(range(0, TICKS, gap))


def original_damage_predicate(spec: dict, sample: dict) -> bool:
    """Positive body damage checks, with snapshot/expiry checks assumed valid."""
    expected = spec["damage"] * (1 + (spec["falloff"] - 1) * sample["distance"] / spec["range"])
    return (
        sample["shots"] == 1
        and sample["ammo_after"] == spec["magazine"] - 1
        and len(sample["damage_events"]) == 1
        and sample["impact_events"] == 1
        and not sample["last_hit_headshot"]
        and abs(sample["damage_events"][0] - min(100, expected)) < 1e-5
        and sample["confirmations"] == [{"head": False, "lethal": expected >= 100}]
    )


def main() -> None:
    weapons = git("show", f"{REVIEWED}:game/scripts/gameplay/weapons.gd")
    specs = {}
    for weapon, raw in re.findall(r'^\s*"(sidearm|smg|rifle|marksman)": \{(.*)\}', weapons, re.M):
        spec = {key: float(re.search(rf'"{key}": ([0-9.]+)', raw).group(1)) for key in ("interval", "reload", "damage", "head", "range", "falloff", "magazine", "reserve")}
        spec["automatic"] = '"automatic": true' in raw
        specs[weapon] = spec
    assert len(specs) == 4
    controls = {}
    for weapon, spec in specs.items():
        expected = predicted_ticks(spec)
        truncated = expected[:1 if spec["automatic"] else 2]
        assert original_predicate(expected, spec)
        assert original_predicate(truncated, spec), weapon
        assert len(truncated) != len(expected)
        remaining = spec["reload"]
        reload_ticks = 0
        while remaining > 0:
            remaining = max(0.0, remaining - DT)
            reload_ticks += 1
        event_only = {
            "distance": 1.7,
            "shots": 1,
            "ammo_after": int(spec["magazine"]) - 1,
            "damage_events": [spec["damage"] * (1 + (spec["falloff"] - 1) * 1.7 / spec["range"])],
            "impact_events": 1,
            "last_hit_headshot": False,
            "confirmations": [{"head": False, "lethal": False}],
            "health_before": 100,
            "health_after": 100,
        }
        assert original_damage_predicate(spec, event_only)
        assert event_only["health_before"] - event_only["health_after"] != event_only["damage_events"][0]
        controls[weapon] = {
            "stock_source": spec,
            "predicted_shot_count": len(expected),
            "predicted_first_ticks": expected[:8],
            "predicted_last_tick": expected[-1],
            "predicted_semi_gap_ticks": expected[1] if not spec["automatic"] else None,
            "predicted_reload_float64_ticks": reload_ticks,
            "false_accept_control": {
                "truncated_shot_ticks": truncated,
                "matching_ammo": 10000 - len(truncated),
                "original_cadence_predicates_pass": original_predicate(truncated, spec),
                "expected_count_predicate_pass": len(truncated) == len(expected),
                "silence_after_tick": truncated[-1],
            },
            "damage_event_only_control": {
                "sample": event_only,
                "original_damage_predicates_pass": original_damage_predicate(spec, event_only),
                "actual_health_delta_matches_emitted_damage": False,
                "reason": "probe reads damage signal but never target health after a positive hit",
            },
        }
    files = ["game/scripts/gameplay/actor.gd", "game/scripts/gameplay/weapons.gd", "game/scripts/gameplay/match.gd", "game/tests/gunplay_rules_probe.gd", "docs/reports/gauntlet/m4-gunplay-invariants/README.md"]
    identities = {}
    for file in files:
        data = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{REVIEWED}:{file}"])
        identities[file] = {"git_blob": git("rev-parse", f"{REVIEWED}:{file}"), "sha256": hashlib.sha256(data).hexdigest()}
    result = {
        "mode": "source-only; no engine or native measurements",
        "reviewed_commit": REVIEWED,
        "reviewed_game_tree": git("rev-parse", f"{REVIEWED}:game"),
        "baseline_commit": BASE,
        "changed_game_or_runtime_paths": git("diff", "--name-only", BASE, REVIEWED, "--", "game", "scripts", "backend", "server").splitlines(),
        "files": identities,
        "pure_controls": controls,
        "control_verdict": "all four truncated runs falsely pass original cadence predicates",
    }
    (OUT / "source-controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"weapons": len(controls), "false_accept_controls": len(controls), "expected_counts": {k: v["predicted_shot_count"] for k, v in controls.items()}, "native_measurements": False}))


if __name__ == "__main__":
    main()
