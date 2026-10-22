#!/usr/bin/env python3
"""Summarize logs written by game/tests/bot_objective_metrics.gd.

    scripts/summarize_bot_metrics.py DIR [--kills]

DIR holds one log per match named <difficulty>-<seed>.log. Prints, per difficulty: matches and rounds,
median/p10/p90 live round time, plant rate, attacker win share, how often the device carrier reached a site,
the share of rounds that ran out the clock, the median time of the first kill, and the round-end reasons.
--kills adds where and how far apart kills happen (positions are 8 m bins; z0 is the attacker end).
Observation only. Rates are over rounds and say nothing about human play.
"""
import argparse
import collections
import glob
import json
import os
import statistics


def load(directory):
    rounds = collections.defaultdict(list)
    matches = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(directory, "*.log"))):
        difficulty = os.path.basename(path).split("-")[0]
        with open(path, errors="replace") as handle:
            for line in handle:
                if line.startswith("BOT_METRIC_ROUND "):
                    rounds[difficulty].append(json.loads(line[len("BOT_METRIC_ROUND "):]))
                elif line.startswith("BOT_METRIC_MATCH "):
                    matches[difficulty].append(json.loads(line[len("BOT_METRIC_MATCH "):]))
    return rounds, matches


def percent(part, whole):
    return "%.0f%%" % (100.0 * part / whole) if whole else "n/a"


def quantile(values, fraction):
    return values[min(len(values) - 1, int(fraction * len(values)))]


def summary(rounds, matches):
    print("%-7s %7s %7s %9s %9s %9s %7s %8s %12s %9s %12s" % ("diff", "matches", "rounds", "med_live", "p10_live", "p90_live", "plant", "atk_win", "carrier@site", "time_out", "first_kill"))
    for difficulty in ("easy", "normal", "hard"):
        data = rounds.get(difficulty, [])
        if not data:
            continue
        live = sorted(r["live_time"] for r in data)
        kills = sorted(r["first_kill_at"] for r in data if r["first_kill_at"] >= 0)
        count = len(data)
        print("%-7s %7d %7d %8.1fs %8.1fs %8.1fs %7s %8s %12s %9s %11.1fs" % (
            difficulty, len(matches[difficulty]), count, statistics.median(live), quantile(live, 0.1), quantile(live, 0.9),
            percent(sum(1 for r in data if r["planted_at"] >= 0), count),
            percent(sum(1 for r in data if r["winner"] == 0), count),
            percent(sum(1 for r in data if r["carrier_at_site_at"] >= 0), count),
            percent(sum(1 for r in data if r["reason"] == "Time expired"), count),
            statistics.median(kills) if kills else -1.0))
        print("        reasons:", dict(collections.Counter(r["reason"] for r in data)))


def kill_report(rounds):
    for difficulty in ("easy", "normal", "hard"):
        data = rounds.get(difficulty, [])
        kills = [dict(k, first=(i == 0)) for r in data for i, k in enumerate(r.get("kills", []))]
        if not kills:
            continue
        print("\n== %s: %d kills in %d rounds" % (difficulty, len(kills), len(data)))
        for team, name in ((0, "attacker victims"), (1, "defender victims")):
            group = [k for k in kills if k["victim_team"] == team]
            if group:
                distance = sorted(k["distance"] for k in group)
                print("%-17s n=%3d  distance med %.1f m  p10 %.1f  p90 %.1f   victim z med %.1f   time med %.1fs" % (
                    name, len(group), statistics.median(distance), quantile(distance, 0.1), quantile(distance, 0.9),
                    statistics.median(k["victim"][1] for k in group), statistics.median(k["t"] for k in group)))
        cells = collections.Counter((int((k["victim"][0] + 24) // 8), int((k["victim"][1] + 24) // 8)) for k in kills if k["first"])
        print("first-kill victim cells (columns x west to east, rows z attacker end to defender end):")
        for row in range(6):
            print("  z%d: " % row + " ".join("%2d" % cells.get((column, row), 0) for column in range(6)))
        stuck = [r.get("stuck_bots_max", 0) for r in data]
        print("most bots stuck >1 s at once in a round: mean %.2f, max %d" % (statistics.mean(stuck), max(stuck)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("directory")
    parser.add_argument("--kills", action="store_true")
    args = parser.parse_args()
    rounds, matches = load(args.directory)
    summary(rounds, matches)
    if args.kills:
        kill_report(rounds)


if __name__ == "__main__":
    main()
