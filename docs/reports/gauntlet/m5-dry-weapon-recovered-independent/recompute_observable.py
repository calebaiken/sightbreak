#!/usr/bin/env python3
"""Recompute logged dry-weapon outputs; unlogged authority snapshots are excluded."""
import argparse
import collections
import json
import math
from pathlib import Path

PROFILES = ("easy", "normal", "hard")
PRIMARIES = ("rifle", "marksman", "smg")


def expectations(mode):
    result = {}
    for difficulty in PROFILES:
        def add(name, weapon="", active="sidearm", ammo=15, reserve=60,
                reload=False, interact=False, target=0):
            result[difficulty, name] = dict(
                difficulty=difficulty, name=name, active=active, ammo=ammo,
                reserve=reserve, requested=weapon, reload=reload,
                interact=interact, target=target)

        for primary in PRIMARIES:
            for state in ("dry", "clip", "reserve", "unknown"):
                add(f"{primary}_{state}", primary if state != "dry" else "")
        add("unowned_usable")
        add("skip_dry_first", "marksman")
        add("unknown_keeps_priority", "rifle")
        add("all_dry")
        add("stale_active_dry_cache")
        add("stale_active_loaded_cache", ammo=0, reserve=0, reload=True)
        add("active_primary_loaded", active="rifle", ammo=30, reserve=0)
        add("active_primary_empty_reserve", active="rifle", ammo=0, reserve=30, reload=True)
        add("active_primary_fully_dry", active="rifle", ammo=0, reserve=0, reload=True)
        add("interacting_return_unchanged", "rifle", interact=True)
        for reserve in (0, 30):
            add(f"close_empty_clip_reserve_{reserve}",
                "" if difficulty == "easy" else "sidearm", active="rifle", ammo=0,
                reserve=reserve, reload=difficulty == "easy", target=1)
        add("distance_boundary", active="rifle", ammo=0, reserve=30, reload=True, target=1)
        add("loaded_clip", active="rifle", ammo=1, reserve=30, target=1)
        add("unowned_sidearm", active="rifle", ammo=0, reserve=30, reload=True, target=1)
        add("interacting_fallback_unchanged", active="rifle", ammo=0, reserve=30,
            interact=True, target=1)

    candidate = {key: value.copy() for key, value in result.items()}
    if mode == "baseline":
        for (difficulty, name), value in result.items():
            if name in {f"{p}_dry" for p in PRIMARIES} | {
                "skip_dry_first", "all_dry", "stale_active_dry_cache", "stale_active_loaded_cache"
            }:
                value["requested"] = "rifle" if name not in {"marksman_dry", "smg_dry"} else name[:-4]
                value["reload"] = False
    return result, candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", required=True, choices=("baseline", "candidate"))
    parser.add_argument("log", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    raw = args.log.read_text()
    rows = collections.defaultdict(list)
    errors = []
    for line in raw.splitlines():
        for kind in ("ENGINE", "CASE", "STEP", "SEQUENCE", "RESULT", "FAILURE"):
            prefix = f"BOT_DRY_WEAPON_{kind} "
            if line.startswith(prefix):
                payload = line[len(prefix):]
                if kind == "FAILURE":
                    rows[kind].append(payload)
                else:
                    try:
                        rows[kind].append(json.loads(payload))
                    except (ValueError, TypeError) as error:
                        errors.append(f"Malformed {kind}: {error}")
                break

    predicates = 0

    def check(value, label):
        nonlocal predicates
        predicates += 1
        if not value:
            errors.append(label)

    def fields(actual, expected, label):
        for key, value in expected.items():
            actual_value = actual.get(key)
            equal = (isinstance(actual_value, (float, int)) and not isinstance(actual_value, bool)
                     and math.isclose(actual_value, value, abs_tol=0.000001)) if isinstance(value, float) else (
                         type(actual_value) is type(value) and actual_value == value)
            check(equal, f"{label}: {key} expected {value!r}, got {actual_value!r}")

    check(len(rows["ENGINE"]) == 1, "Exactly one engine marker")
    if rows["ENGINE"]:
        fields(rows["ENGINE"][0], {"major": 4, "minor": 7, "patch": 2}, "Pinned engine")

    expected_cases, candidate_cases = expectations(args.mode)
    check(len(expected_cases) == 84, "Oracle has 84 expected cases")
    check(len(rows["CASE"]) == 84, "Raw has 84 cases")
    seen = set()
    expected_failures = []
    for row in rows["CASE"]:
        key = row.get("difficulty"), row.get("name")
        check(key not in seen, f"Duplicate case {key}")
        seen.add(key)
        check(key in expected_cases, f"Unexpected case {key}")
        if key not in expected_cases:
            continue
        expected = expected_cases[key]
        fields(row, expected, f"Case {key}")
        candidate = candidate_cases[key]
        fields(row, {"expected_weapon": candidate["requested"], "expected_reload": candidate["reload"]}, f"Declared case {key}")
        if expected["requested"] != candidate["requested"]:
            expected_failures.append(f"{key[0]}/{key[1]} expected weapon {candidate['requested']}")
        if expected["reload"] != candidate["reload"]:
            expected_failures.append(f"{key[0]}/{key[1]} expected reload")
    check(seen == set(expected_cases), "All expected cases observed")

    check(len(rows["STEP"]) == 48, "Raw has 48 sequence steps")
    seen_steps = set()
    expected_sequences = {}
    for difficulty in PROFILES:
        for sequence in ("idle", "alternating"):
            baseline = args.mode == "baseline"
            cycling = baseline and sequence == "alternating" and difficulty != "easy"
            switches = 8 if cycling else (1 if baseline else 0)
            dry_equips = 4 if cycling else (1 if baseline else 0)
            empty_reloads = 0 if cycling or not baseline else 7
            expected_sequences[difficulty, sequence] = dict(
                difficulty=difficulty, sequence=sequence, switches=switches,
                dry_equips=dry_equips, empty_reloads=empty_reloads, shots=0)
            for value, message in ((switches, "avoids switches to or from a dry primary"),
                                   (dry_equips, "avoids dry equips"),
                                   (empty_reloads, "avoids repeated dry reload requests")):
                if value:
                    expected_failures.append(f"{difficulty}/{sequence} {message}")

    for row in rows["STEP"]:
        key = row.get("difficulty"), row.get("sequence"), row.get("step")
        check(key not in seen_steps, f"Duplicate sequence step {key}")
        seen_steps.add(key)
        difficulty, sequence, step = key
        valid = (difficulty, sequence) in expected_sequences and isinstance(step, int) and 0 <= step < 8
        check(valid, f"Unexpected sequence step {key}")
        if not valid:
            continue
        baseline = args.mode == "baseline"
        cycling = baseline and sequence == "alternating" and difficulty != "easy"
        active = "sidearm" if not baseline or cycling and step % 2 == 1 else "rifle"
        prior = "sidearm" if step == 0 or not baseline or cycling and step % 2 == 0 else "rifle"
        requested = active if baseline and (step == 0 or cycling) else ""
        deploy = 0.3 if baseline and (step == 0 or cycling) else max(0.0, 0.3 - 0.12 * step) if baseline else 0.0
        fields(row, dict(difficulty=difficulty, sequence=sequence, step=step,
                         visible=sequence == "alternating" and step % 2 == 1,
                         prior_weapon=prior, requested=requested,
                         reload=baseline and not cycling and step > 0, fire=False,
                         active=active, ammo=15 if active == "sidearm" else 0,
                         reserve=60 if active == "sidearm" else 0,
                         reload_remaining=0.0, deploy_remaining=deploy, total_ammo=75, shots=0),
               f"Step {key}")
    check(seen_steps == {(d, s, i) for d in PROFILES for s in ("idle", "alternating") for i in range(8)},
          "All expected sequence steps observed")

    check(len(rows["SEQUENCE"]) == 6, "Raw has six sequence summaries")
    seen_sequences = set()
    for row in rows["SEQUENCE"]:
        key = row.get("difficulty"), row.get("sequence")
        check(key not in seen_sequences, f"Duplicate sequence summary {key}")
        seen_sequences.add(key)
        check(key in expected_sequences, f"Unexpected sequence summary {key}")
        if key in expected_sequences:
            fields(row, expected_sequences[key], f"Sequence {key}")
    check(seen_sequences == set(expected_sequences), "All expected sequence summaries observed")
    check(collections.Counter(rows["FAILURE"]) == collections.Counter(expected_failures),
          "Exact expected in-engine assertion failure labels")
    check(len(rows["RESULT"]) == 1, "Exactly one result marker")
    if rows["RESULT"]:
        fields(rows["RESULT"][0], dict(cases=84, sequence_steps=48, checks=590,
                                       failures=len(expected_failures), passed=not expected_failures), "Result")
    result = dict(mode=args.mode, input=str(args.log), predicates=predicates,
                  observed_records={key: len(value) for key, value in rows.items()},
                  expected_fixture_failures=len(expected_failures), errors=errors,
                  observable_comparison_passed=not errors,
                  excluded="Unlogged full protected authority snapshots; supervisor/source/cleanup evidence")
    output = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(output)
    print(output, end="")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
