#!/usr/bin/env python3
"""Does one squad win more rounds than the other, whichever side it plays?

    scripts/squad_balance.py DIR [DIR ...] [--against OTHER_DIR [OTHER_DIR ...]] [--resamples 4000]

DIR holds logs written by game/tests/bot_objective_metrics.gd (<difficulty>-<seed>[s].log). Actors 1-5 attack in
rounds 1-6 and defend in rounds 7-12 unless the match was started with --swap-start (then the reverse); round
order inside a log is the round number. Prints, per difficulty and pooled, how many rounds actors 1-5 won, their
share, a 95% interval from a bootstrap that resamples whole matches (rounds inside a match are not independent),
and how many matches they won, drew and lost (the match line's scores follow the squads through halftime).
A fair engine gives about 50%; an interval that excludes 50% is a squad effect, not a role effect.
An interval that includes 50% is not proof of fairness: read its width.

Several DIRs are pooled. --against OTHER_DIR also prints share(DIR) minus share(OTHER_DIR) with an interval from
resampling the matches of both sets independently.

Observation only: it reads logs and changes nothing.
"""
import argparse
import collections
import glob
import json
import os
import random

HALFTIME_ROUNDS = 6


def load(directories):
    matches = collections.defaultdict(list)
    for path in sorted(p for directory in directories for p in glob.glob(os.path.join(directory, "*.log"))):
        name = os.path.basename(path)
        difficulty = name.split("-")[0]
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
        # Match result for actors 1-5 from the rounds themselves. The match line's attack_score and defend_score
        # swap values at halftime so they follow the sides, not the squads: the squad that attacked first ends with
        # defend_score. That reading is only a cross-check (it must agree for every match that reached halftime).
        mine = sum(low_ids_won)
        theirs = len(low_ids_won) - mine
        first = int(meta.get("attack_score", 0))
        second = int(meta.get("defend_score", 0))
        low, high = (first, second) if swap else (second, first)
        matches[difficulty].append({"name": name, "swap": swap, "won": low_ids_won, "reverse": bool(meta.get("reverse_order", False)), "match": (mine > theirs) - (mine < theirs), "score_mismatch": (low, high) != (mine, theirs)})
    return matches


def share(rows):
    total = sum(len(m["won"]) for m in rows)
    return sum(sum(m["won"]) for m in rows) / total if total else float("nan")


def resample(rows, rng):
    return [rows[rng.randrange(len(rows))] for _ in rows]


def interval(values):
    values = sorted(values)
    count = len(values)
    return values[int(0.025 * count)], values[int(0.975 * count) - 1]


def cells(matches):
    out = [(difficulty, matches[difficulty]) for difficulty in ("easy", "normal", "hard") if matches.get(difficulty)]
    if len(out) > 1:
        out.append(("all", [m for _, rows in out for m in rows]))
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", nargs="+")
    parser.add_argument("--against", nargs="+")
    parser.add_argument("--resamples", type=int, default=4000)
    arguments = parser.parse_args()
    rng = random.Random(20261022)
    matches = load(arguments.directory)
    print("%-7s %7s %7s %12s %8s   %-24s %s" % ("diff", "matches", "rounds", "ids1-5 won", "share", "95% interval", "ids 1-5 matches W-D-L"))
    for difficulty, rows in cells(matches):
        total = sum(len(m["won"]) for m in rows)
        won = sum(sum(m["won"]) for m in rows)
        low, high = interval([share(resample(rows, rng)) for _ in range(arguments.resamples)])
        results = collections.Counter(m["match"] for m in rows)
        flags = " (processing order reversed)" if any(m["reverse"] for m in rows) else ""
        mismatched = sum(1 for m in rows if m["score_mismatch"])
        flags += "  [%d match(es) where the logged score disagrees with the round count]" % mismatched if mismatched else ""
        print("%-7s %7d %7d %12d %7.1f%%   %5.1f%% to %5.1f%%         %d-%d-%d%s" % (difficulty, len(rows), total, won, 100 * share(rows), 100 * low, 100 * high, results[1], results[0], results[-1], flags))
        if difficulty != "all":
            # Per start order, so a squad effect is not hidden by the mix. Matches end at 7 wins, so the two
            # start orders are not exact mirrors; read the pooled row first.
            for label, subset in (("ids 1-5 attack first", [m for m in rows if not m["swap"]]), ("ids 6-10 attack first", [m for m in rows if m["swap"]])):
                if subset:
                    print("        %-22s matches=%d rounds=%d ids1-5 share=%.0f%%" % (label, len(subset), sum(len(m["won"]) for m in subset), 100 * share(subset)))
    if arguments.against:
        other = dict(cells(load(arguments.against)))
        print()
        print("share minus share of the --against set, matches of each set resampled independently")
        for difficulty, rows in cells(matches):
            if difficulty not in other:
                continue
            differences = [share(resample(rows, rng)) - share(resample(other[difficulty], rng)) for _ in range(arguments.resamples)]
            low, high = interval(differences)
            print("%-7s %+6.1f points   95%% interval %+6.1f to %+6.1f" % (difficulty, 100 * (share(rows) - share(other[difficulty])), 100 * low, 100 * high))


if __name__ == "__main__":
    main()
