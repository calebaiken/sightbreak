#!/usr/bin/env python3
"""Does one squad win more rounds than the other, whichever side it plays?

    scripts/squad_balance.py DIR [--resamples 4000]

DIR holds logs written by game/tests/bot_objective_metrics.gd (<difficulty>-<seed>[s].log). Actors 1-5 attack in
rounds 1-6 and defend in rounds 7-12 unless the match was started with --swap-start (then the reverse); round
order inside a log is the round number. Prints, per difficulty, how many rounds actors 1-5 won, their share, and a
95% interval from a bootstrap that resamples whole matches (rounds inside a match are not independent). A fair
engine gives about 50%; an interval that excludes 50% is a squad effect, not a role effect.
Observation only: it reads logs and changes nothing.
"""
import argparse
import collections
import glob
import json
import os
import random

HALFTIME_ROUNDS = 6


def load(directory):
    matches = collections.defaultdict(list)
    for path in sorted(glob.glob(os.path.join(directory, "*.log"))):
        difficulty = os.path.basename(path).split("-")[0]
        rounds = []
        meta = {}
        with open(path, errors="replace") as handle:
            for line in handle:
                if line.startswith("BOT_METRIC_ROUND "):
                    rounds.append(json.loads(line[len("BOT_METRIC_ROUND "):]))
                elif line.startswith("BOT_METRIC_MATCH "):
                    meta = json.loads(line[len("BOT_METRIC_MATCH "):])
        if not rounds:
            continue
        swap = bool(meta.get("swap_start", False))
        # Per round: 1 if actors 1-5 won it, else 0.
        low_ids_won = []
        for index, row in enumerate(rounds):
            low_ids_attack = (index < HALFTIME_ROUNDS) != swap
            attackers_won = row["winner"] == 0
            low_ids_won.append(1 if attackers_won == low_ids_attack else 0)
        matches[difficulty].append({"name": os.path.basename(path), "won": low_ids_won, "reverse": bool(meta.get("reverse_order", False))})
    return matches


def share(rows):
    total = sum(len(m["won"]) for m in rows)
    return sum(sum(m["won"]) for m in rows) / total if total else float("nan")


def bootstrap(rows, resamples, rng):
    values = []
    for _ in range(resamples):
        sample = [rows[rng.randrange(len(rows))] for _ in rows]
        values.append(share(sample))
    values.sort()
    return values[int(0.025 * resamples)], values[int(0.975 * resamples) - 1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory")
    parser.add_argument("--resamples", type=int, default=4000)
    arguments = parser.parse_args()
    rng = random.Random(20261022)
    matches = load(arguments.directory)
    print("%-7s %7s %7s %12s %8s   %s" % ("diff", "matches", "rounds", "ids1-5 won", "share", "95% interval (matches resampled)"))
    for difficulty in ("easy", "normal", "hard"):
        rows = matches.get(difficulty, [])
        if not rows:
            continue
        total = sum(len(m["won"]) for m in rows)
        won = sum(sum(m["won"]) for m in rows)
        low, high = bootstrap(rows, arguments.resamples, rng)
        flags = " (processing order reversed)" if any(m["reverse"] for m in rows) else ""
        print("%-7s %7d %7d %12d %7.0f%%   %.0f%% to %.0f%%%s" % (difficulty, len(rows), total, won, 100 * share(rows), 100 * low, 100 * high, flags))
        # Per start order, so a squad effect is not hidden by the mix.
        for label, subset in (("ids 1-5 attack first", [m for m in rows if not m["name"].split("-")[1].endswith("s.log")]), ("ids 6-10 attack first", [m for m in rows if m["name"].split("-")[1].endswith("s.log")])):
            if subset:
                print("        %-22s matches=%d rounds=%d ids1-5 share=%.0f%%" % (label, len(subset), sum(len(m["won"]) for m in subset), 100 * share(subset)))


if __name__ == "__main__":
    main()
