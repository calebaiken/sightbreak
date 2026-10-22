#!/usr/bin/env python3
"""Turn game/tests/gunplay_metrics.gd output into markdown tables.

    scripts/summarize_gunplay.py LOG [--weapons game/scripts/gameplay/weapons.gd]

LOG is the captured output of the harness (lines starting GUNPLAY_). Weapon data are read from weapons.gd, so the
derived columns (shots to kill, one-shot headshot range, damage per second) always use the file under test.
Observation only: reads files, changes nothing.
"""
import argparse
import json
import math
import re
from collections import defaultdict

HEALTH = 100.0
ORDER = ["sidearm", "smg", "rifle", "marksman"]


def read_weapons(path):
    text = open(path).read()
    weapons = {}
    for match in re.finditer(r'"(\w+)":\s*\{([^}]*)\}', text):
        name, body = match.group(1), match.group(2)
        fields = {}
        for key, value in re.findall(r'"(\w+)":\s*("[^"]*"|Color\("[^"]*"\)|[\w.\-]+)', body):
            if value.startswith('"') or value.startswith("Color"):
                fields[key] = value
            elif value in ("true", "false"):
                fields[key] = value == "true"
            else:
                fields[key] = float(value)
        if "damage" in fields:
            weapons[name] = fields
    return weapons


def damage_at(spec, distance, head=False):
    ratio = min(max(distance / spec["range"], 0.0), 1.0)
    amount = spec["damage"] * (1.0 + (spec["falloff"] - 1.0) * ratio)
    return amount * spec["head"] if head else amount


def shots_to_kill(spec, distance, head=False):
    return math.ceil(HEALTH / damage_at(spec, distance, head) - 1e-9)


def one_shot_head_range(spec):
    """Largest distance at which one headshot still kills, or None."""
    if damage_at(spec, 0.0, True) < HEALTH:
        return None
    if damage_at(spec, spec["range"], True) >= HEALTH:
        return spec["range"]
    low, high = 0.0, spec["range"]
    for _ in range(60):
        mid = (low + high) / 2.0
        if damage_at(spec, mid, True) >= HEALTH:
            low = mid
        else:
            high = mid
    return low


def load(path):
    rows = defaultdict(list)
    with open(path, errors="replace") as handle:
        for line in handle:
            if line.startswith("GUNPLAY_"):
                kind, _, payload = line.partition(" ")
                rows[kind[len("GUNPLAY_"):]].append(json.loads(payload))
    return rows


def pct(value):
    return "%.0f%%" % (100.0 * value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("--weapons", default="game/scripts/gameplay/weapons.gd")
    arguments = parser.parse_args()
    spec = read_weapons(arguments.weapons)
    rows = load(arguments.log)
    names = [w for w in ORDER if w in spec]

    print("### Data and what it implies (analytic, from weapons.gd; 100 health, no armour)\n")
    print("| Weapon | Cost | Damage | Head x | Interval | Rounds/min | Damage/s | Body shots to kill at 0 / 20 / 40 m | Time to kill, body, 0 m | One-shot headshot up to | Magazine | Reload |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | ---: |")
    for name in names:
        w = spec[name]
        near = shots_to_kill(w, 0.0)
        reach = one_shot_head_range(w)
        print("| %s | %d | %g | %g | %.3f s | %.0f | %.0f | %d / %d / %d | %.2f s | %s | %d | %.2f s |" % (
            name, w["cost"], w["damage"], w["head"], w["interval"], 60.0 / w["interval"], w["damage"] / w["interval"],
            near, shots_to_kill(w, min(20.0, w["range"])), shots_to_kill(w, min(40.0, w["range"])), (near - 1) * w["interval"],
            "%.0f m" % reach if reach else "never", w["magazine"], w["reload"]))

    if rows.get("PROFILE"):
        print("\n### Cadence and recoil, one magazine held down from rest (measured)\n")
        print("| Weapon | Interval data | Interval measured | Seconds to empty | Peak climb | Shots to the 0.16 rad cap | Recoil after shots 1-6 (rad) | Time to clear |")
        print("| --- | ---: | ---: | ---: | ---: | ---: | --- | ---: |")
        for row in sorted(rows["PROFILE"], key=lambda r: names.index(r["weapon"])):
            cap = row["shots_to_cap"]
            print("| %s | %.3f s | %.4f s | %.2f s | %.3f rad (%.1f deg) | %s | %s | %.2f s |" % (
                row["weapon"], row["interval_data"], row["interval_measured"], row["seconds_to_empty"], row["recoil_peak_y_rad"],
                math.degrees(row["recoil_peak_y_rad"]), cap if cap > 0 else "never", ", ".join("%.3f" % v for v in row["recoil_after_shot_y"][:6]), row["recovery_seconds"]))

    if rows.get("SPREAD"):
        print("\n### Spread, radians and centimetres of scatter at 20 m (each axis, uniform +-)\n")
        print("| Weapon | Standing | Crouched | Walking | Airborne |")
        print("| --- | ---: | ---: | ---: | ---: |")
        for row in sorted(rows["SPREAD"], key=lambda r: names.index(r["weapon"])):
            cells = ["%.4f (%.0f cm)" % (row[k], row[k] * 20.0 * 100.0) for k in ("standing_rad", "crouched_rad", "walking_rad", "airborne_rad")]
            print("| %s | %s |" % (row["weapon"], " | ".join(cells)))

    if rows.get("TIMING"):
        print("\n### Reload and draw (measured)\n")
        print("| Weapon | Reload data | Reload measured | Draw delay |")
        print("| --- | ---: | ---: | ---: |")
        for row in sorted(rows["TIMING"], key=lambda r: names.index(r["weapon"])):
            print("| %s | %.2f s | %.3f s | %.2f s |" % (row["weapon"], row["reload_data"], row["reload_measured"], row["deploy_seconds"]))

    if rows.get("ACCURACY"):
        trials = rows["ACCURACY"][0]["trials"]
        modes = ["hold", "burst3", "advance"]
        labels = {"hold": "trigger held (semi-auto: clicked at its own rate)", "burst3": "three-round bursts, 0.3 s apart", "advance": "trigger held while walking at the target"}
        for mode in modes:
            subset = [r for r in rows["ACCURACY"] if r["mode"] == mode]
            if not subset:
                continue
            distances = sorted({r["distance"] for r in subset})
            print("\n### Standing target, perfect chest aim, %s (%d trials per cell)\n" % (labels[mode], trials))
            print("Each cell: hit rate of fired shots / share of trials that killed / median seconds from first shot to kill.\n")
            print("| Weapon | %s |" % " | ".join("%g m" % d for d in distances))
            print("| --- | %s |" % " | ".join("---" for _ in distances))
            for name in names:
                cells = []
                for d in distances:
                    match = [r for r in subset if r["weapon"] == name and r["distance"] == d]
                    if not match:
                        cells.append("beyond range")
                        continue
                    r = match[0]
                    kill_time = "%.2f s" % r["kill_time_median_s"] if r["kill_time_median_s"] >= 0 else "no kill"
                    cells.append("%s / %s / %s" % (pct(r["hit_rate"]), pct(r["kill_rate"]), kill_time))
                print("| %s | %s |" % (name, " | ".join(cells)))

    if rows.get("DUEL"):
        distances = sorted({r["distance"] for r in rows["DUEL"]})
        duel_count = rows["DUEL"][0]["duels"]
        for d in distances:
            print("\n### Duels at %g m: both fire on the same tick at the other's chest (%d duels per pair)\n" % (d, duel_count))
            print("Each cell: row weapon wins / column weapon wins / both dead / neither dead. The same-weapon cells should be near even; they are the harness's own fairness check.\n")
            print("| Row vs column | %s |" % " | ".join(names))
            print("| --- | %s |" % " | ".join("---" for _ in names))
            lookup = {}
            for r in rows["DUEL"]:
                if r["distance"] == d:
                    lookup[(r["a"], r["b"])] = (r["a_wins"], r["b_wins"], r["trades"], r["unresolved"], r["duels"])
                    lookup[(r["b"], r["a"])] = (r["b_wins"], r["a_wins"], r["trades"], r["unresolved"], r["duels"])
            for a in names:
                cells = []
                for b in names:
                    value = lookup.get((a, b))
                    if value is None:
                        cells.append("")
                    else:
                        cells.append("%s / %s / %s / %s" % tuple(pct(v / value[4]) for v in value[:4]))
                print("| %s | %s |" % (a, " | ".join(cells)))


if __name__ == "__main__":
    main()
