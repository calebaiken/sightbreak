#!/usr/bin/env python3
"""Aggregates audit.sh logs (a directory of DIFFICULTY-SEED.log files, or a .jsonl of FUZZ_RESULT objects) by difficulty.

usage: compare.py DIR_OR_JSONL [DIR_OR_JSONL]
Rates are over rounds, with Wilson 95% intervals; rounds within a match are not independent, so the intervals are indicative.
"""
import json, sys, glob, math, collections, statistics
def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z*z/n
    c = (p + z*z/(2*n)) / d; h = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / d
    return (max(0, c-h), min(1, c+h))
def load(path):
    out = collections.defaultdict(list)
    if path.endswith(".jsonl"):
        for line in open(path):
            r = json.loads(line); out[r["difficulty"]].append(r)
        return out
    for f in sorted(glob.glob(path + "/*.log")):
        for l in open(f, errors="replace"):
            if l.startswith("FUZZ_RESULT "):
                r = json.loads(l[12:]); out[r["difficulty"]].append(r)
    return out
def pct(k, n): lo, hi = wilson(k, n); return "%3d%% (%d-%d%%)" % (round(100*k/n) if n else 0, round(100*lo), round(100*hi))
def summarize(label, d):
    data = load(d)
    print("=== %s ===" % label)
    print("diff   matches rounds  median live round s (p10-p90)  plant rate        attacker round wins  detonations  time-expired  median closest approach  stuck/match  violations")
    for diff in ("easy", "normal", "hard"):
        rs = data.get(diff, [])
        if not rs: continue
        rounds = [x for r in rs for x in r["per_round"]]
        n = len(rounds)
        ends = sorted(x["end_t"] for x in rounds)
        q = lambda p: ends[min(len(ends)-1, int(p*len(ends)))]
        planted = sum(1 for x in rounds if x["plant_t"] >= 0)
        reasons = [s for r in rs for s in r["reasons"]]
        att = sum(1 for s in reasons if s.startswith("Attackers win"))
        det = sum(1 for s in reasons if "detonated" in s)
        exp = sum(1 for s in reasons if "Time expired" in s)
        mins = sorted(x["min_site_dist"] for x in rounds)
        stuck = statistics.mean(r["stuck_unique"] for r in rs)
        viol = sum(len(r["violations"]) for r in rs)
        incomplete = sum(1 for r in rs if r["end"] != "match_over")
        print("%-6s %-7d %-7d %5.1f (%4.1f-%5.1f)             %-17s %-20s %-12d %-13d %-24.1f %-12.1f %d%s" % (diff, len(rs), n, statistics.median(ends), q(0.1), q(0.9), pct(planted, n), pct(att, len(reasons)), det, exp, statistics.median(mins), stuck, viol, "  INCOMPLETE=%d" % incomplete if incomplete else ""))
    return data
if __name__ == "__main__":
    summarize("A: " + sys.argv[1], sys.argv[1])
    if len(sys.argv) > 2: summarize("B: " + sys.argv[2], sys.argv[2])
