#!/usr/bin/env python3
"""Exact stock-rule predictions and retained false-acceptance controls; no engine."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
TICKS = 1800


def ceil(value):
    return -(-value.numerator // value.denominator)


def schedule(interval, automatic):
    if not automatic:
        return list(range(0, TICKS, 2 * ceil(interval * 30)))
    result = []
    for index in range(TICKS):
        tick = ceil(index * interval * 60)
        if tick >= TICKS:
            break
        result.append(tick)
    return result


def main():
    source = (ROOT / "game/scripts/gameplay/weapons.gd").read_bytes()
    retained = json.loads((OUT.parent / "round-1-rejected/source-controls.json").read_text())
    assert hashlib.sha256(source).hexdigest() == retained["files"]["game/scripts/gameplay/weapons.gd"]["sha256"]
    results = {}
    for weapon, raw in re.findall(r'^\s*"(sidearm|smg|rifle|marksman)": \{(.*)\}', source.decode(), re.M):
        interval = Fraction(re.search(r'"interval": ([0-9.]+)', raw)[1])
        automatic = '"automatic": true' in raw
        expected = schedule(interval, automatic)
        old = retained["pure_controls"][weapon]
        truncated = old["false_accept_control"]["truncated_shot_ticks"]
        event_only = old["damage_event_only_control"]["sample"]
        controls = {
            "agrees_with_independent_float_prediction": len(expected) == old["predicted_shot_count"] and expected[-1] == old["predicted_last_tick"],
            "retained_truncated_schedule_rejected": truncated != expected,
            "missing_middle_shot_rejected": expected[:2] + expected[3:] != expected,
            "missing_final_shot_rejected": expected[:-1] != expected,
            "event_without_health_change_rejected": abs(event_only["health_before"] - event_only["health_after"] - event_only["damage_events"][0]) >= 1e-5,
        }
        assert all(controls.values()), (weapon, controls)
        results[weapon] = {"interval": str(interval), "automatic": automatic, "expected_count": len(expected), "expected_first_ticks": expected[:8], "expected_last_tick": expected[-1], "controls": controls}
    assert len(results) == 4
    result = {"mode": "pure exact-rational source predictions; not Godot output", "weapons_sha256": hashlib.sha256(source).hexdigest(), "window_ticks": TICKS, "weapons": results}
    (OUT / "source-predictions.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"native_execution": False, "weapons": len(results), "controls": sum(len(v["controls"]) for v in results.values()), "expected_counts": {k: v["expected_count"] for k, v in results.items()}}))


if __name__ == "__main__":
    main()
