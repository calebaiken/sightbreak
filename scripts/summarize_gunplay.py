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
    if distance > spec["range"] + 1e-9:
        return None
    return math.ceil(HEALTH / damage_at(spec, distance, head) - 1e-9)


def shots_text(spec, distance):
    count = shots_to_kill(spec, distance)
    return "-" if count is None else str(count)


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


def wilson(successes, total, z=1.96):
    """95% Wilson score interval for a proportion of independent trials."""
    if total == 0:
        return 0.0, 1.0
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def interval_text(successes, total):
    low, high = wilson(successes, total)
    return "%s-%s" % (pct(low), pct(high))


def floor_tenth(value):
    return math.floor(value * 10.0 + 1e-9) / 10.0


def stability(paths):
    """How much the same measurement cell moves between runs with different seeds."""
    runs = [load(path) for path in paths]
    print("Cells compared across %d runs (%s). Spread = largest minus smallest value of the cell." % (len(runs), ", ".join(paths)))
    worst = {}
    for kind, key_fields, value_fields in (
        ("ACCURACY", ("weapon", "distance", "mode"), ("hit_rate", "kill_rate", "kill_time_median_s", "head_share_of_hits")),
        ("DUEL", ("a", "b", "distance"), ("a_wins", "b_wins")),
    ):
        cells = defaultdict(list)
        for rows in runs:
            for row in rows.get(kind, []):
                cells[tuple(row[f] for f in key_fields)].append(row)
        for field in value_fields:
            spreads = []
            for key, rows in cells.items():
                if len(rows) < 2:
                    continue
                values = [r[field] for r in rows]
                if field in ("a_wins", "b_wins"):
                    values = [v / r["duels"] for v, r in zip(values, rows)]
                if field == "kill_time_median_s" and any(v < 0 for v in values):
                    continue
                spreads.append((max(values) - min(values), key, values))
            spreads.sort(reverse=True)
            if spreads:
                top = spreads[0]
                print("%-9s %-20s cells=%3d  largest spread %.3f at %s  values %s" % (kind, field, len(spreads), top[0], "/".join(str(k) for k in top[1]), ", ".join("%.3f" % v for v in top[2])))
                worst[(kind, field)] = top[0]
    return worst


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("log")
    parser.add_argument("--weapons", default="game/scripts/gameplay/weapons.gd")
    parser.add_argument("--stability", nargs="+", metavar="LOG", help="print how far the same cells differ between these logs (different seeds) instead of the tables")
    arguments = parser.parse_args()
    if arguments.stability:
        stability([arguments.log] + arguments.stability)
        return
    spec = read_weapons(arguments.weapons)
    rows = load(arguments.log)
    names = [w for w in ORDER if w in spec]

    print("### Data and what it implies (analytic, from weapons.gd; 100 health, no armour)\n")
    print("A dash means the shot does not reach that far. Shots to kill use the damage after falloff at that distance.\n")
    print("| Weapon | Cost | Damage | Head x | Interval | Rounds/min | Damage/s | Body shots to kill at 0 / 20 / 40 m | Time to kill, body, 0 m | One-shot headshot up to | Magazine | Reload |")
    print("| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | ---: |")
    for name in names:
        w = spec[name]
        near = shots_to_kill(w, 0.0)
        reach = one_shot_head_range(w)
        print("| %s | %d | %g | %g | %.3f s | %.0f | %.0f | %s / %s / %s | %.2f s | %s | %d | %.2f s |" % (
            name, w["cost"], w["damage"], w["head"], w["interval"], 60.0 / w["interval"], w["damage"] / w["interval"],
            shots_text(w, 0.0), shots_text(w, 20.0), shots_text(w, 40.0), (near - 1) * w["interval"],
            "%.1f m" % floor_tenth(reach) if reach else "never", w["magazine"], w["reload"]))

    if rows.get("PROFILE"):
        print("\n### Cadence and recoil, one magazine held down from rest (measured)\n")
        print("Recoil at fire is what the shot itself carries (the climb from earlier shots, before this shot's own kick). Recoil after the shot is the view kick the player sees.\n")
        print("| Weapon | Interval data | Interval measured | Seconds to empty | Peak view climb | Recoil carried by shots 1-6 (rad) | Carried by the last shot | Time to clear after release |")
        print("| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |")
        for row in sorted(rows["PROFILE"], key=lambda r: names.index(r["weapon"])):
            print("| %s | %.3f s | %.4f s | %.2f s | %.3f rad (%.1f deg) | %s | %.3f rad | %.2f s |" % (
                row["weapon"], row["interval_data"], row["interval_measured"], row["seconds_to_empty"], row["recoil_peak_y_rad"],
                math.degrees(row["recoil_peak_y_rad"]), ", ".join("%.3f" % v for v in row["recoil_at_fire_y"][:6]), row["recoil_at_fire_y_last"], row["recovery_seconds"]))

    if rows.get("SPREAD"):
        print("\n### Spread, radians and centimetres of scatter at 20 m (each axis, uniform +-)\n")
        print("| Weapon | Standing | Crouched | Walking | Airborne |")
        print("| --- | ---: | ---: | ---: | ---: |")
        for row in sorted(rows["SPREAD"], key=lambda r: names.index(r["weapon"])):
            cells = ["%.4f (%.0f cm)" % (row[k], row[k] * 20.0 * 100.0) for k in ("standing_rad", "crouched_rad", "walking_rad", "airborne_rad")]
            print("| %s | %s |" % (row["weapon"], " | ".join(cells)))

    if rows.get("TIMING"):
        print("\n### Reload and draw (measured in 60 Hz ticks)\n")
        print("Measured values include the tick that requests the action and the tick that completes it, so they read up to two ticks (0.033 s) above the data.\n")
        print("| Weapon | Reload data | Reload measured | Draw data | Draw measured |")
        print("| --- | ---: | ---: | ---: | ---: |")
        for row in sorted(rows["TIMING"], key=lambda r: names.index(r["weapon"])):
            print("| %s | %.2f s | %.3f s (%d ticks) | %.2f s | %.3f s (%d ticks) |" % (row["weapon"], row["reload_data"], row["reload_measured"], row["reload_ticks"], row["deploy_data"], row["draw_measured"], row["draw_ticks"]))

    if rows.get("ACCURACY"):
        trials = rows["ACCURACY"][0]["trials"]
        modes = ["hold", "comp", "head", "burst3", "advance"]
        labels = {
            "hold": "aimed at the chest, trigger held, recoil not countered (semi-auto: clicked at its own rate)",
            "comp": "aimed at the chest, trigger held, the shooter pulls down by exactly the recoil carried (the weapon's ceiling under perfect spray control)",
            "head": "aimed at the centre of the head, recoil countered (every kill here is a headshot kill)",
            "burst3": "aimed at the chest, three-round bursts, 0.3 s apart",
            "advance": "aimed at the chest, trigger held while walking at the target, re-aimed every tick",
        }
        for mode in modes:
            subset = [r for r in rows["ACCURACY"] if r["mode"] == mode]
            if not subset:
                continue
            distances = sorted({r["distance"] for r in rows["ACCURACY"]})
            print("\n### Standing target, %s (%d trials per cell)\n" % (labels[mode], trials))
            print("Each cell: hit rate of fired shots / share of trials that killed within one magazine (95% Wilson interval) / median seconds from first shot to kill, over the trials that killed. Cells where fewer than 30 trials killed show the count, because the median then describes only the lucky trials.\n")
            print("| Weapon | %s |" % " | ".join("%g m" % d for d in distances))
            print("| --- | %s |" % " | ".join("---" for _ in distances))
            for name in names:
                cells = []
                ran = any(r["weapon"] == name for r in subset)
                for d in distances:
                    match = [r for r in subset if r["weapon"] == name and r["distance"] == d]
                    if not match:
                        cells.append("beyond range" if d > spec[name]["range"] + 1e-9 else "not run")
                        continue
                    r = match[0]
                    kill_time = "%.2f s" % r["kill_time_median_s"] if r["kill_time_median_s"] >= 0 else "no kill"
                    if 0 < r["kills"] < 30:
                        kill_time += " (n=%d)" % r["kills"]
                    cells.append("%s / %s (%s) / %s" % (pct(r["hit_rate"]), pct(r["kill_rate"]), interval_text(r["kills"], r["trials"]), kill_time))
                if not ran:
                    cells = ["not run (semi-automatic)" if mode == "burst3" else "not run"] * len(distances)
                print("| %s | %s |" % (name, " | ".join(cells)))

    if rows.get("DUEL"):
        distances = sorted({r["distance"] for r in rows["DUEL"]})
        duel_count = rows["DUEL"][0]["duels"]
        for d in distances:
            print("\n### Duels at %g m: both fire on the same tick at the other's chest (%d duels per pair)\n" % (d, duel_count))
            print("Each cell: row weapon wins / column weapon wins / neither dead after the magazines (a same-tick double kill cannot occur: the first actor processed in a tick fires and the dead cannot answer). The same-weapon cells are the harness's own fairness check; the 95% Wilson interval of the row weapon's wins is in brackets.\n")
            print("| Row vs column | %s |" % " | ".join(names))
            print("| --- | %s |" % " | ".join("---" for _ in names))
            lookup = {}
            for r in rows["DUEL"]:
                if r["distance"] == d:
                    lookup[(r["a"], r["b"])] = (r["a_wins"], r["b_wins"], r["unresolved"], r["duels"])
                    if r["a"] != r["b"]:
                        lookup[(r["b"], r["a"])] = (r["b_wins"], r["a_wins"], r["unresolved"], r["duels"])
            for a_name in names:
                cells = []
                for b_name in names:
                    value = lookup.get((a_name, b_name))
                    if value is None:
                        cells.append("")
                    else:
                        wins, losses, none, total = value
                        cells.append("%s / %s / %s [%s]" % (pct(wins / total), pct(losses / total), pct(none / total), interval_text(wins, total)))
                print("| %s | %s |" % (a_name, " | ".join(cells)))


if __name__ == "__main__":
    main()
