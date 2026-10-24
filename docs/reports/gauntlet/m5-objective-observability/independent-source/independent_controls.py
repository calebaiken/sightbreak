#!/usr/bin/env python3
"""Independent receipt falsifiers. Does not run or emulate Godot."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

FIXTURE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(FIXTURE / "scripts"))
import test_bot_objective_observation as maintained
import verify_bot_objective_observation as oracle

results = []
def run(name, mutate, expect_reject=True):
    rows = copy.deepcopy(maintained.synthetic_records())
    mutate(rows)
    terminal = rows[-1][1]
    terminal["decisions"] = sum(tag == "DECISION" for tag, _ in rows)
    terminal["interactions"] = sum(tag == "INTERACTION" for tag, _ in rows)
    try:
        result = oracle.verify(maintained.log(rows))
    except (ValueError, KeyError, TypeError) as error:
        outcome = {"name": name, "expected_rejection": expect_reject, "rejected": True,
                   "error": type(error).__name__ + ": " + str(error), "met_expectation": expect_reject}
    else:
        outcome = {"name": name, "expected_rejection": expect_reject, "rejected": False,
                   "accepted_scope": result["scope"], "met_expectation": not expect_reject}
    results.append(outcome)

run("valid_maintained_synthetic_receipt", lambda rows: None, False)
run("forward_rows_have_no_dt_pose_command_objective_or_progress", lambda rows: None)

def tagrow(rows, kind, label=None):
    return next(row for tag, row in rows if tag == kind and (label is None or row.get("label") == label))

def corrupt_forward(rows):
    for tag, row in rows:
        if tag == "INTERACTION" and row["label"] == "forward_live_122":
            row.update(dt=-100, objective_before="defused", objective_after="invented",
                       actors_before={}, progress_after={})
run("forward_negative_dt_and_impossible_objective_accepted", corrupt_forward)
run("forward_decision_not_bound_to_actor_or_tick_state", lambda rows:
    tagrow(rows, "DECISION", "forward_live_122").update(tick=-50, position=[900,900,900]))

def incomplete_command(rows):
    for tag, row in rows:
        if tag == "DECISION":
            row["observation"]["decision"]["command"] = {"move": [0,0], "look": [0,0], "interact": False}
        if tag == "PAIR":
            for key in ("before_off", "before_on", "after_off", "after_on"):
                row[key]["actors"]["6"]["input"] = {"move": [0,0], "look": [0,0], "interact": False}
run("missing_fire_reload_weapon_utility_command_fields", incomplete_command)

def discontinuous(rows):
    row = tagrow(rows, "INTERACTION", "control_plant")
    row["actors_before"]["6"]["progress"] = 1.5
    row["progress_after"]["6"] = 1.5 + row["dt"]
run("plant_progress_jumps_then_resets_between_rows", discontinuous)
run("last_plant_row_keeps_impossible_negative_progress", lambda rows:
    [row for tag,row in rows if tag == "INTERACTION" and row["label"] == "control_plant"][-1]["progress_after"].update({"6": -100}))

def outcome_mismatch(rows):
    for tag,row in rows:
        if tag == "INTERACTION" and row["label"].startswith("control_"):
            row.update(objective_before="defused", objective_after="planted", carrier_after=99)
run("authority_rows_contradict_control_summary", outcome_mismatch)

def impossible_time(rows):
    row = tagrow(rows, "INTERACTION", "control_plant")
    row["dt"] = -1
    row["progress_after"]["6"] = row["actors_before"]["6"]["progress"] - 1
    others = [row for tag,row in rows if tag == "INTERACTION" and row["label"] == "control_plant"]
    others[1]["dt"] += 1 + 1/60
    others[1]["progress_after"]["6"] = others[1]["actors_before"]["6"]["progress"] + others[1]["dt"]
run("negative_dt_in_plant_with_same_total_duration", impossible_time)

def two_step(rows):
    steps = [row for tag,row in rows if tag == "INTERACTION" and row["label"] == "control_plant"]
    for index,row in enumerate(steps[:2]):
        row["dt"] = 1.5
        row["actors_before"]["6"]["progress"] = index * 1.5
        row["progress_after"] = {"6": 1.5} if index == 0 else {}
    rows[:] = [(tag,row) for tag,row in rows if not (tag == "INTERACTION" and row["label"] == "control_plant" and row not in steps[:2])]
    next(row for tag,row in rows if tag == "CONTROL" and row["name"] == "plant")["ticks"] = 2
run("plant_uses_two_1p5_second_steps_instead_of_stock_60hz", two_step)

def unrelated_trace(rows):
    row = tagrow(rows, "DECISION", "pose_120")
    row["position"] = [100,100,100]
    row["tick"] = -50
    row["observation"]["plan"]["destination"] = [8,8,8]
    row["observation"]["decision"]["destination"] = [-8,-8,-8]
run("paired_decision_pose_tick_plan_disagree_with_protected_state", unrelated_trace)

def wrong_profile(rows):
    rows[0][1]["profiles"] = {"normal": {"vision_range": -1}}
run("wrong_profile_not_bound_to_source", wrong_profile)

run("wrong_protocol_is_rejected", lambda rows: rows[0][1].update(protocol=5))
run("missing_terminal_is_rejected", lambda rows: rows.pop())
run("changed_paired_ammo_is_rejected", lambda rows:
    tagrow(rows,"PAIR")["after_on"]["actors"]["6"].update(ammo=31))
run("wrong_duration_is_rejected", lambda rows:
    tagrow(rows,"INTERACTION","control_plant").update(dt=0.2))
run("negative_control_retained_progress_is_rejected", lambda rows:
    tagrow(rows,"INTERACTION","control_moving")["progress_after"].update({"6": .26}))


def boolean_actor(rows):
    row = tagrow(rows, "DECISION", "forward_live_122")
    row["actor_id"] = True
    row["observation"]["decision"]["actor_id"] = True
run("boolean_actor_id_is_not_a_typed_integer", boolean_actor)
run("boolean_time_scale_is_not_a_typed_number", lambda rows: rows[0][1].update(time_scale=True))
run("float_protocol_is_not_a_typed_integer", lambda rows: rows[0][1].update(protocol=6.0))

output = {"candidate": "c91d9b98a293ef8605d99ae6e83402d3af983519", "fixture": str(FIXTURE),
          "native_executed": False, "total": len(results),
          "met_expectation": sum(row["met_expectation"] for row in results),
          "unexpected_acceptances": sum(row["expected_rejection"] and not row["rejected"] for row in results),
          "results": results}
print(json.dumps(output, indent=2))
sys.exit(0 if all(row["met_expectation"] for row in results) else 1)
