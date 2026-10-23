#!/usr/bin/env python3
"""Synthetic receipt falsifiers and source preservation; no native execution."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import verify_bot_objective_observation as oracle

ROOT = Path(__file__).resolve().parents[1]


def command():
    return {"move": [0, 0], "look": [0, 0], "interact": False, "fire": False,
            "reload": False, "jump": False, "crouch": False, "weapon": "", "smoke": False, "grenade": False}


def protected():
    actors = {}
    for i in range(1, 11):
        actors[str(i)] = {"team": 0, "position": [0, 0, 0], "velocity": [0, 0, 0],
                          "yaw": 0, "pitch": 0, "alive": True, "health": 100,
                          "weapon": "smg", "ammo": 30, "reserve": 0, "reload": 0,
                          "deploy": 0, "ammo_store": {}, "inventory": ["smg"],
                          "credits": 800, "grenades": 1, "smokes": 1, "recoil": [0, 0],
                          "rng": "-9215223372036854755", "input": command()}
    return {"actors": actors, "rng": "9223372036854775801", "bots": {}, "teams": {},
            "heard": {}, "objective": "carried", "carrier": 6, "interactions": {},
            "time_left": 90, "tick": 13415, "elapsed": 223.58, "phase": "live"}


def decision(label, tick=1):
    return {"label": label, "tick": tick, "actor_id": 6, "position": [0, 0, 0],
            "observation": {"enabled": True, "candidates": [], "rng_before": "9223372036854775801",
                            "plan": {"destination": [15, 0, 10]}, "movement_mode": "navigate",
                            "navigation_waypoint": [0, 0, 3],
                            "decision": {"actor_id": 6, "target_id": 0, "role": "carrier",
                                         "destination": [15, 0, 10], "interact": False,
                                         "command": command(), "rng_after": "9223372036854775801"}}}


def synthetic_records():
    rows = [("HEADER", {"schema": 1, "engine": {"major": 4, "minor": 7, "patch": 2},
                        "scope": "component_reconstruction_not_historical_replay", "time_scale": 1,
                        "protocol": 6, "source_events": oracle.POSES, "controls": oracle.CONTROLS,
                        "forward_source_event": 122, "forward_ticks": 120,
                        "rules": {"buy_seconds": 15, "round_seconds": 100, "device_seconds": 35,
                                  "plant_seconds": 3, "defuse_seconds": 5, "win_score": 7},
                        "seed_policy": "original_initial_seeds_not_original_later_rng_state",
                        "missing_state_reset": ["bot_memory", "team_contacts", "heard", "recoil", "holstered_ammo", "utility", "rng_state"]})]
    for index in oracle.POSES:
        state = protected()
        rows.append(("PAIR", {"event_index": index, "equal": True, **{k: copy.deepcopy(state) for k in ("before_off", "before_on", "after_off", "after_on")}}))
        rows.append(("DECISION", decision("pose_" + str(index))))
    rows.append(("DECISION", decision("forward_live_122", 13416)))
    for tick in range(13416, 13536):
        rows.append(("INTERACTION", {"label": "forward_live_122", "tick": tick}))
    for name in oracle.CONTROLS:
        count = 180 if name == "plant" else (300 if name == "defuse" else 1)
        positive = name in ("plant", "defuse")
        for tick in range(count):
            actor = {"alive": True, "team": 1 if name == "defuse" else 0,
                     "interact": name != "no_interact", "move": [0, 1] if name == "moving" else [0, 0],
                     "site": -1 if name == "wrong_site" else 0, "objective_distance": 0,
                     "progress": tick / 60 if positive else .25}
            rows.append(("INTERACTION", {"label": "control_" + name, "tick": tick, "dt": 1 / 60,
                                         "actors_before": {"6": actor}, "carrier_before": 6,
                                         "progress_after": {"6": (tick + 1) / 60} if positive and tick < count - 1 else {}}))
        rows.append(("CONTROL", {"name": name, "valid": True, "ticks": count,
                                 "objective": "planted" if name == "plant" else ("defused" if name == "defuse" else "carried"),
                                 "contributions": {"6": 1} if positive else {}}))
    rows.append(("RESULT", {"checks": 20, "failures": [], "pairs": 3, "controls": 5,
                            "decisions": 4, "interactions": 603,
                            "scope": "diagnostic_only_no_objective_quality_acceptance"}))
    return rows


def log(rows):
    return "\n".join(oracle.PREFIX + kind + " " + json.dumps(value) for kind, value in rows) + "\n"


class ObjectiveOracleTests(unittest.TestCase):
    def setUp(self):
        self.rows = synthetic_records()

    def reject(self, rows):
        with self.assertRaises((ValueError, KeyError, TypeError)):
            oracle.verify(log(rows))

    def test_synthetic_complete_contract(self):
        self.assertTrue(oracle.verify(log(self.rows))["observable_contract_passed"])

    def test_truncation_duplicate_and_unknown_records(self):
        for rows in [self.rows[:-1], self.rows[1:], self.rows + [self.rows[-1]], self.rows[:1] + self.rows]:
            with self.subTest(case=len(rows)):
                self.reject(rows)
        with self.assertRaises(ValueError): oracle.verify(log(self.rows) + "BOT_OBJECTIVE_FUTURE {}\n")

    def test_native_warnings_and_errors_stay_failures(self):
        for warning in ["WARNING: leak", "SCRIPT ERROR: bad type", "ObjectDB instances leaked", "Orphan StringName: Master"]:
            with self.subTest(warning=warning), self.assertRaises(ValueError):
                oracle.verify(warning + "\n" + log(self.rows))

    def test_parity_rejects_resource_memory_rng_and_command_mutations(self):
        mutations = [
            lambda p: p["after_on"]["actors"]["6"].update(ammo=31),
            lambda p: p["after_on"]["actors"]["6"]["input"].update(fire=True),
            lambda p: p["after_on"]["bots"].update(target=4),
            lambda p: p["after_on"].update(rng="9223372036854775800"),
            lambda p: p["before_on"].update(time_left=91),
            lambda p: p["after_on"]["actors"]["6"].pop("ammo_store"),
        ]
        for mutate in mutations:
            rows = copy.deepcopy(self.rows)
            mutate(rows[1][1])
            self.reject(rows)

    def test_trace_must_bind_actual_command_and_rng(self):
        for mutate in [lambda o: o["decision"]["command"].update(fire=True),
                       lambda o: o.update(rng_before="7"), lambda o: o["decision"].update(rng_after="8")]:
            rows = copy.deepcopy(self.rows)
            mutate(rows[2][1]["observation"])
            self.reject(rows)

    def test_perception_cannot_omit_or_invent_target(self):
        rows = copy.deepcopy(self.rows)
        for key in ("before_off", "before_on", "after_off", "after_on"):
            rows[1][1][key]["actors"]["4"]["team"] = 1
        self.reject(rows)
        rows = copy.deepcopy(self.rows)
        rows[2][1]["observation"]["decision"]["target_id"] = 4
        self.reject(rows)

    def test_forward_ticks_and_controls_are_mandatory(self):
        for kind, predicate in [("INTERACTION", lambda r: r.get("label") == "forward_live_122"),
                                ("CONTROL", lambda r: r["name"] == "defuse"),
                                ("DECISION", lambda r: r["label"] == "pose_127")]:
            rows = copy.deepcopy(self.rows)
            index = next(i for i, (tag, row) in enumerate(rows) if tag == kind and predicate(row))
            del rows[index]
            self.reject(rows)

    def test_positive_and_negative_authority_falsifiers(self):
        for label, mutate in [
            ("control_plant", lambda r: r["actors_before"]["6"].update(interact=False)),
            ("control_defuse", lambda r: r["actors_before"]["6"].update(objective_distance=3)),
            ("control_plant", lambda r: r["progress_after"].update({"6": 1})),
            ("control_wrong_site", lambda r: r["progress_after"].update({"6": .26})),
            ("control_moving", lambda r: r["actors_before"]["6"].update(move=[0, 0])),
            ("control_no_interact", lambda r: r["actors_before"]["6"].update(interact=True)),
        ]:
            rows = copy.deepcopy(self.rows)
            row = next(row for tag, row in rows if tag == "INTERACTION" and row.get("label") == label)
            mutate(row)
            self.reject(rows)

    def test_original_source_erasure_and_bytes(self):
        result = oracle.source_audit(ROOT)
        self.assertTrue(result["source_erasure_passed"])
        self.assertFalse(result["native_executed"])

    def test_source_audit_rejects_policy_map_and_fixture_mutations(self):
        identity = json.loads((ROOT / oracle.REPORT / "benchmark-identity.json").read_text())
        paths = list(identity["source"]) + [oracle.REPORT + "/benchmark-identity.json",
                                          oracle.REPORT + "/original-timeout-slice.jsonl",
                                          "game/tests/fixtures/bot_objective_timeout.jsonl"]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for path in paths:
                (root / path).parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(ROOT / path, root / path)
            for path in ["game/scripts/gameplay/bot_ai.gd", "game/scripts/gameplay/arena.gd", "game/tests/fixtures/bot_objective_timeout.jsonl"]:
                with self.subTest(path=path):
                    original = (root / path).read_bytes()
                    (root / path).write_bytes(original + b"# deliberate falsifier\n")
                    with self.assertRaises(ValueError): oracle.source_audit(root)
                    (root / path).write_bytes(original)


if __name__ == "__main__":
    unittest.main()
