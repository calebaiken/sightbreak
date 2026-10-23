#!/usr/bin/env python3
"""Independent frozen-revision source checks; no Godot or runtime processes."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[5]
OUT = Path(__file__).resolve().parent
REVISED = "d1e89edfbd474a04d6759300141880566b1559e3"
ORIGINAL = "68587d006a2f96d9586e5f133c91f23d9cce02d0"
CRITIC = "5606f1ec0c229be6712e51ecc5ce56a0e88e6bf6"
PREFIX = "docs/reports/gauntlet/m4-gunplay-invariants/"
DT = 1 / 60


def blob(commit, path):
    return subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{path}"])


def ceil(value):
    return -(-value.numerator // value.denominator)


def rational_schedule(interval, automatic):
    if not automatic:
        return list(range(0, 1800, 2 * ceil(interval * 30)))
    return [tick for index in range(1800) if (tick := ceil(index * interval * 60)) < 1800]


def action_clock_schedule(interval, automatic):
    # A separate float64 transcription of the current actor decrement/carry
    # rules, cross-checked against the rational absolute-time reference.
    cooldown = 0.0
    previous = False
    result = []
    for tick in range(1800):
        cooldown -= DT
        firing = automatic or tick % 2 == 0
        if firing and (automatic or not previous) and cooldown <= 1e-6:
            result.append(tick)
            carry = cooldown if previous and -DT * .999 < cooldown <= 0 else 0
            cooldown = carry + float(interval)
        else:
            cooldown = max(0.0, cooldown)
        previous = firing
    return result


def damage_checks(spec, sample):
    expected = spec["damage"] * (1 + (spec["falloff"] - 1) * sample["distance"] / spec["range"])
    expected_health = max(0, sample["before"] - expected)
    lethal = expected_health == 0
    return (
        abs(sample["after"] - expected_health) < 1e-5
        and abs(sample["before"] - sample["after"] - sample["event"]) < 1e-5
        and sample["alive"] == (not lethal)
        and sample["lethal"] == lethal
        and abs(sample["feedback_remaining"] - .18) < 1e-6
    )


def main():
    revised_probe = blob(REVISED, "game/tests/gunplay_rules_probe.gd").decode()
    weapon_source = blob(REVISED, "game/scripts/gameplay/weapons.gd").decode()
    retained = json.loads(blob(CRITIC, PREFIX + "independent-review/source-controls.json"))
    builder = json.loads(blob(REVISED, PREFIX + "round-2/source-predictions.json"))
    original_hash = hashlib.sha256(blob(ORIGINAL, "game/tests/gunplay_rules_probe.gd")).hexdigest()
    assert original_hash == hashlib.sha256(blob(REVISED, PREFIX + "round-1-rejected/probe.gd.txt")).hexdigest()
    assert blob(CRITIC, PREFIX + "independent-review/source-controls.json") == blob(REVISED, PREFIX + "round-1-rejected/source-controls.json")
    unchanged = {}
    for path in ["game/scripts/gameplay/actor.gd", "game/scripts/gameplay/weapons.gd", "game/scripts/gameplay/match.gd"]:
        assert blob(ORIGINAL, path) == blob(REVISED, path)
        unchanged[path] = hashlib.sha256(blob(REVISED, path)).hexdigest()
    anchors = {
        "complete_cadence_schedule": "check(times == expected_times,",
        "cadence_count": "check(times.size() == expected_times.size(),",
        "cadence_final_shot": "times[-1] == expected_times[-1]",
        "initial_deploy_shot_check": "check(shots.size() == initial_shots and shooter.ammo == alternate_store.x",
        "forbidden_deploy_window": "step * DT < Actor.DEPLOY_SECONDS - Actor.READY_EPSILON",
        "partial_reload_raw_series": '"timeline": reload_timeline',
        "cancel_deploy_raw_series": '"timeline": cancel_timeline',
        "actual_health_delta": "float(target_before.health) - float(target_after.health) - damages[0]",
        "actual_alive_state": "bool(target_after.alive) == not lethal",
        "feedback_starts": "absf(float(feedback_initial.remaining) - 0.18)",
        "all_four_lethal_fixture": '"name": "lethal_body", "head": false, "health": 5.0',
        "friendly_and_enemy_intersections": "not front_entry.is_empty() and not behind_entry.is_empty()",
        "friendly_contact_distance": "absf(actual_distance - float(front_entry.distance)) < 0.00001",
        "both_visual_authority_states": "shooter.snapshot() == shooter_after and target.snapshot() == target_after",
    }
    for name, anchor in anchors.items():
        assert anchor in revised_probe, name
    deploy_section = revised_probe.split("var start_tick := tick", 1)[1].split("func switch_cycle", 1)[0]
    assert "shots.clear()" not in deploy_section
    results = {}
    for weapon, raw in re.findall(r'^\s*"(sidearm|smg|rifle|marksman)": \{(.*)\}', weapon_source, re.M):
        interval = Fraction(re.search(r'"interval": ([0-9.]+)', raw)[1])
        automatic = '"automatic": true' in raw
        spec = {key: float(re.search(rf'"{key}": ([0-9.]+)', raw)[1]) for key in ["damage", "falloff", "range"]}
        expected = rational_schedule(interval, automatic)
        actor_model = action_clock_schedule(interval, automatic)
        old = retained["pure_controls"][weapon]
        event = old["damage_event_only_control"]["sample"]
        positive = {"distance": event["distance"], "before": 100, "after": 100 - event["damage_events"][0], "event": event["damage_events"][0], "alive": True, "lethal": False, "feedback_remaining": .18}
        event_only = dict(positive, after=100)
        lethal = dict(positive, before=5, after=0, event=5, alive=False, lethal=True)
        controls = {
            "absolute_rational_schedule_matches_actor_float_model": expected == actor_model,
            "builder_exact_schedule_prediction_matches": (len(expected), expected[-1]) == (builder["weapons"][weapon]["expected_count"], builder["weapons"][weapon]["expected_last_tick"]),
            "original_truncated_control_rejected": old["false_accept_control"]["truncated_shot_ticks"] != expected,
            "missing_middle_shot_rejected": expected[:2] + expected[3:] != expected,
            "missing_last_shot_rejected": expected[:-1] != expected,
            "event_without_health_delta_rejected": not damage_checks(spec, event_only),
            "correct_body_health_delta_accepted": damage_checks(spec, positive),
            "correct_actual_lethal_accepted": damage_checks(spec, lethal),
            "incorrect_alive_state_rejected": not damage_checks(spec, dict(lethal, alive=True)),
            "missing_feedback_start_rejected": not damage_checks(spec, dict(positive, feedback_remaining=0)),
        }
        assert all(controls.values()), (weapon, controls)
        results[weapon] = {"checks": controls, "expected_count": len(expected), "expected_last_tick": expected[-1]}
    assert len(results) == 4
    result = {
        "mode": "independent source-only controls; no engine execution or compile assertion",
        "reviewed_revision": REVISED,
        "game_tree": subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", f"{REVISED}:game"], text=True).strip(),
        "unchanged_shipping_source_sha256": unchanged,
        "original_rejection_artifacts_identical": True,
        "source_anchors_present": list(anchors),
        "initial_deploy_events_preserved": True,
        "controls": results,
    }
    (OUT / "revision-source-controls.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"weapons": 4, "independent_pure_controls": sum(len(v["checks"]) for v in results.values()), "source_anchors": len(anchors), "native_execution": False}))


if __name__ == "__main__":
    main()
