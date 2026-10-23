#!/usr/bin/env python3
"""Strict reader for the opt-in objective component probe; never launches Godot."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re

PREFIX = "BOT_OBJECTIVE_"
KINDS = {"HEADER", "PAIR", "DECISION", "INTERACTION", "CONTROL", "RESULT"}
POSES = [120, 122, 127]
CONTROLS = ["plant", "defuse", "wrong_site", "moving", "no_interact"]
REPORT = "docs/reports/gauntlet/m5-objective-observability"
ACTOR_FIELDS = {"team", "position", "velocity", "yaw", "pitch", "alive", "health",
                "weapon", "ammo", "reserve", "reload", "deploy", "ammo_store", "inventory",
                "credits", "grenades", "smokes", "recoil", "rng", "input"}
STATE_FIELDS = {"actors", "rng", "bots", "teams", "heard", "objective", "carrier",
                "interactions", "time_left", "tick", "elapsed", "phase"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def source_audit(root):
    root = Path(root)
    identity = json.loads((root / REPORT / "benchmark-identity.json").read_text())
    ai_path = "game/scripts/gameplay/bot_ai.gd"
    ai = (root / ai_path).read_text()
    # These blocks only write caller-owned observations. Erasure establishes that
    # the original gameplay statements remain byte-identical, not runtime parity.
    erased = re.sub(r"^[\t ]*# OBJECTIVE_OBSERVATION_BEGIN\n.*?^[\t ]*# OBJECTIVE_OBSERVATION_END\n", "", ai, flags=re.M | re.S)
    for name in ("acquire_target", "compute_bot_input"):
        erased = re.sub(rf"(static func {name}\([^\n]*), observation: Dictionary = \{{\}}(\) ->)", r"\1\2", erased)
    erased = erased.replace("acquire_target(match_node, actor, state, profile, observation if observing else {})", "acquire_target(match_node, actor, state, profile)")
    require(digest(erased.encode()) == identity["source"][ai_path], "observation erasure does not recover inspected AI bytes")
    for path, expected in identity["source"].items():
        if path != ai_path:
            require(digest((root / path).read_bytes()) == expected, "changed gameplay: " + path)
    raw = (root / REPORT / "original-timeout-slice.jsonl").read_bytes()
    require(digest(raw) == identity["selected_bytes_sha256"], "changed original slice")
    require(raw == (root / "game/tests/fixtures/bot_objective_timeout.jsonl").read_bytes(), "fixture differs from original bytes")
    rows = [json.loads(line) for line in raw.splitlines()]
    require([r["event_index"] for r in rows] == [0, 120, 122, 126, 127], "original event identities")
    final = rows[-1]
    carrier = next(a for a in final["actors"] if a["id"] == final["objective_carrier"])
    require(rows[-2]["message"] == "Defenders win • Time expired", "original timeout missing")
    require(final["phase"] == "post" and carrier["id"] == 6 and carrier["alive"] and carrier["health"] == 100 and carrier["ammo"] == 30 and carrier["reserve"] == 0, "original carrier facts changed")
    return {"source_erasure_passed": True, "unchanged_gameplay_files": 4,
            "original_slice_sha256": digest(raw), "source_base": identity["base_commit"],
            "native_executed": False, "compilation_verified": False}


def records(text):
    result = []
    for line in text.splitlines():
        require(not re.search(r"SCRIPT ERROR|Parse Error|ERROR:|WARNING:|Orphan StringName|ObjectDB instances leaked", line), "native log is not strict-clean")
        if not line.startswith(PREFIX):
            continue
        kind, sep, body = line[len(PREFIX):].partition(" ")
        require(sep and kind in KINDS, "unknown or malformed record")
        value = json.loads(body, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
        require(isinstance(value, dict), "record is not an object")
        result.append((kind, value))
    return result


def vector(value, size):
    return isinstance(value, list) and len(value) == size and all(type(x) in (int, float) and math.isfinite(x) for x in value)


def verify(text):
    rows = records(text)
    require(rows and rows[0][0] == "HEADER" and rows[-1][0] == "RESULT", "missing header or terminal result")
    groups = {kind: [value for tag, value in rows if tag == kind] for kind in KINDS}
    require(len(groups["HEADER"]) == len(groups["RESULT"]) == 1, "duplicate boundary records")
    header, result = groups["HEADER"][0], groups["RESULT"][0]
    require(header["schema"] == 1 and header["scope"] == "component_reconstruction_not_historical_replay", "wrong scope")
    require(header["time_scale"] == 1 and header["protocol"] == 6, "changed time scale or protocol")
    require(tuple(header["engine"][key] for key in ("major", "minor", "patch")) == (4, 7, 2), "wrong engine")
    require(header["source_events"] == POSES and header["controls"] == CONTROLS and header["forward_source_event"] == 122 and header["forward_ticks"] == 120, "changed registered fixture")
    require(header["rules"] == {"buy_seconds": 15, "round_seconds": 100, "device_seconds": 35, "plant_seconds": 3, "defuse_seconds": 5, "win_score": 7}, "changed stock rules")
    require(header["seed_policy"] == "original_initial_seeds_not_original_later_rng_state", "seed assumption missing")
    require(set(header["missing_state_reset"]) == {"bot_memory", "team_contacts", "heard", "recoil", "holstered_ammo", "utility", "rng_state"}, "reset assumptions missing")
    require([p["event_index"] for p in groups["PAIR"]] == POSES, "missing or duplicate paired pose")
    decisions = groups["DECISION"]
    modes, rejections = Counter(), Counter()
    seen = set()
    for row in decisions:
        key = (row["label"], row["tick"], row["actor_id"])
        require(key not in seen, "duplicate decision")
        seen.add(key)
        require(1 <= row["actor_id"] <= 10 and vector(row["position"], 3), "malformed actor decision")
        obs = row["observation"]
        dec = obs["decision"]
        require(obs["enabled"] is True and dec["actor_id"] == row["actor_id"], "trace actor mismatch")
        require(vector(obs["plan"]["destination"], 3) and vector(dec["destination"], 3) and vector(obs["navigation_waypoint"], 3), "missing goal/waypoint")
        require(obs["movement_mode"] in {"interact", "idle", "combat_cover", "combat_brake", "combat_strafe", "navigate", "scan"}, "unknown movement branch")
        command = dec["command"]
        require(vector(command["move"], 2) and vector(command["look"], 2), "malformed final command")
        require(command["interact"] == dec["interact"], "lost interaction intent")
        candidates = obs["candidates"]
        require(len({c["id"] for c in candidates}) == len(candidates), "duplicate candidate")
        require(all(c["reason"] in {"range", "fov", "visibility", "eligible"} and math.isfinite(c["distance"]) and c["distance"] >= 0 for c in candidates), "malformed perception result")
        eligible = [c["id"] for c in candidates if c["reason"] == "eligible"]
        require(dec["target_id"] == 0 or dec["target_id"] in eligible, "selected an unperceived target")
        require(isinstance(obs["rng_before"], str) and isinstance(dec["rng_after"], str), "RNG state must retain 64-bit string precision")
        modes[obs["movement_mode"]] += 1
        rejections.update(c["reason"] for c in candidates)
    for pair in groups["PAIR"]:
        for key in ("before_off", "before_on", "after_off", "after_on"):
            state = pair[key]
            require(STATE_FIELDS <= state.keys() and set(state["actors"]) == {str(i) for i in range(1, 11)}, "incomplete protected state")
            require(all(ACTOR_FIELDS <= a.keys() for a in state["actors"].values()), "incomplete actor protection")
        require(pair["equal"] is True and pair["before_off"] == pair["before_on"] and pair["after_off"] == pair["after_on"], "trace changed protected state")
        matched = [r for r in decisions if r["label"] == "pose_" + str(pair["event_index"])]
        require(len(matched) == 1 and matched[0]["actor_id"] == 6, "paired actual decision missing")
        obs = matched[0]["observation"]
        require(obs["rng_before"] == pair["before_on"]["rng"] and obs["decision"]["rng_after"] == pair["after_on"]["rng"], "trace RNG does not bind pair")
        require(obs["decision"]["command"] == pair["after_on"]["actors"]["6"]["input"], "trace command does not bind actual command")
        actor = pair["before_on"]["actors"]["6"]
        enemies = {int(i) for i, a in pair["before_on"]["actors"].items() if a["alive"] and a["team"] != actor["team"]}
        require({c["id"] for c in obs["candidates"]} == enemies, "perception omitted a living enemy")
    interactions = groups["INTERACTION"]
    forward = [r for r in interactions if r["label"] == "forward_live_122"]
    require(len(forward) == 120 and [r["tick"] for r in forward] == list(range(13416, 13536)), "forward authority ticks incomplete")
    require(any(r["label"] == "forward_live_122" for r in decisions), "forward AI never observed")
    require([c["name"] for c in groups["CONTROL"]] == CONTROLS, "missing or duplicate authority control")
    for control in groups["CONTROL"]:
        name = control["name"]
        require(control["valid"] is True, "failed authority control")
        steps = [r for r in interactions if r["label"] == "control_" + name]
        require(len(steps) == control["ticks"] and steps, "control authority stream missing")
        if name in ("plant", "defuse"):
            seconds = 3 if name == "plant" else 5
            require(seconds <= sum(r["dt"] for r in steps) + 1e-10 < seconds + 1 / 60 + 1e-10, "objective hold duration changed")
            require(control["objective"] == ("planted" if name == "plant" else "defused") and control["contributions"].get("6") == 1, "positive control did not complete")
            for row in steps:
                actor = row["actors_before"]["6"]
                require(actor["alive"] and actor["interact"] and math.hypot(*actor["move"]) < .2, "positive control input ineligible")
                require((name == "plant" and actor["team"] == 0 and actor["site"] >= 0 and row["carrier_before"] == 6) or (name == "defuse" and actor["team"] == 1 and actor["objective_distance"] <= 2.8), "positive control objective ineligible")
                if row is not steps[-1]:
                    require(math.isclose(row["progress_after"]["6"], actor["progress"] + row["dt"], abs_tol=1e-9), "authority progress discontinuity")
            require(steps[-1]["actors_before"]["6"]["progress"] + steps[-1]["dt"] >= seconds - 1e-10, "early objective completion")
        else:
            require(len(steps) == 1 and control["objective"] == "carried" and control["contributions"].get("6", 0) == 0, "negative control changed objective")
            actor = steps[0]["actors_before"]["6"]
            require(actor["progress"] == .25 and "6" not in steps[0]["progress_after"], "invalid interaction did not reset")
            require((name == "wrong_site" and actor["site"] == -1) or (name == "moving" and math.hypot(*actor["move"]) >= .2) or (name == "no_interact" and not actor["interact"]), "negative control not exercised")
    expected_labels = {"pose_" + str(i) for i in POSES} | {"forward_live_122"} | {"control_" + name for name in CONTROLS}
    require(all(r["label"] in expected_labels for r in decisions + interactions), "unexpected fixture label")
    require(result["failures"] == [] and result["checks"] >= 10 and result["pairs"] == 3 and result["controls"] == 5 and result["decisions"] == len(decisions) and result["interactions"] == len(interactions), "failed or incomplete terminal result")
    require(result["scope"] == "diagnostic_only_no_objective_quality_acceptance", "result overclaims scope")
    return {"observable_contract_passed": True, "decision_rows": len(decisions), "interaction_rows": len(interactions),
            "movement_modes": dict(modes), "perception_results": dict(rejections),
            "scope": "component_reconstruction_not_historical_cause_or_G2_acceptance"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    report = {"source": source_audit(args.root)}
    if args.log:
        report["observations"] = verify(args.log.read_text())
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
