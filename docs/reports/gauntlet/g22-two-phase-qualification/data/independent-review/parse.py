import json, os, re, sys, glob, random, math

S = "/tmp/claude-0/-home-user-sightbreak/dfa39eb1-8f79-5aa4-a243-6ac88bc445cd/scratchpad"
DIRS = {"after": S + "/qualify-run/bots", "before": S + "/stock-before", "reverse": S + "/stock-reverse"}
FN = re.compile(r"^(easy|normal|hard)-(\d+)(s?)\.log$")

def load(dirpath):
    out = []
    issues = []
    for p in sorted(glob.glob(dirpath + "/*.log")):
        name = os.path.basename(p)
        m = FN.match(name)
        if not m:
            issues.append((name, "unexpected filename"))
            continue
        diff, seed, s = m.group(1), int(m.group(2)), m.group(3) == "s"
        rounds, match = [], []
        with open(p, encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.startswith("BOT_METRIC_ROUND "):
                    rounds.append(json.loads(line[len("BOT_METRIC_ROUND "):]))
                elif line.startswith("BOT_METRIC_MATCH "):
                    match.append(json.loads(line[len("BOT_METRIC_MATCH "):]))
        rec = {"file": name, "difficulty": diff, "seed": seed, "swap": s, "rounds": rounds, "match": match}
        # --- integrity checks
        if len(match) != 1:
            issues.append((name, "MATCH lines = %d" % len(match)))
            rec["ok"] = False
            out.append(rec)
            continue
        M = match[0]
        if M["difficulty"] != diff: issues.append((name, "difficulty mismatch %s" % M["difficulty"]))
        if M["seed"] != seed: issues.append((name, "seed mismatch %s" % M["seed"]))
        if bool(M["swap_start"]) != s: issues.append((name, "swap flag mismatch"))
        rev_expected = (dirpath.endswith("stock-reverse"))
        if bool(M.get("reverse_order", False)) != rev_expected: issues.append((name, "reverse flag %s" % M.get("reverse_order")))
        if M["phase"] != "match_over": issues.append((name, "phase %s (incomplete)" % M["phase"]))
        n = len(rounds)
        if M["rounds"] != n: issues.append((name, "MATCH rounds %d != ROUND lines %d" % (M["rounds"], n)))
        nums = [r["round"] for r in rounds]
        if nums != list(range(1, n + 1)): issues.append((name, "round numbers not 1..n: %s" % nums))
        if any(r["winner"] not in (0, 1) for r in rounds): issues.append((name, "bad winner value"))
        # end condition
        a, d = M["attack_score"], M["defend_score"]
        if a + d != n: issues.append((name, "scores %d+%d != rounds %d" % (a, d, n)))
        if not (max(a, d) >= 7 or n == 12): issues.append((name, "ended early: %d:%d after %d rounds" % (a, d, n)))
        if n < 7: issues.append((name, "fewer than 7 rounds (halftime swap not reached)"))
        # --- derivation 1: from round numbers + harness halftime logic
        first_att_is_A = not s   # True: ids 1-5 attack in rounds 1-6
        w1 = 0
        for r in rounds:
            att_is_A = first_att_is_A if r["round"] <= 6 else (not first_att_is_A)
            if (att_is_A and r["winner"] == 0) or ((not att_is_A) and r["winner"] == 1):
                w1 += 1
        # --- derivation 2: from the carrier id printed per round (carrier is a team-0 = attacker)
        w2 = 0
        carrier_bad = 0
        for r in rounds:
            c = r["carrier"]
            if c < 1 or c > 10:
                carrier_bad += 1
                continue
            att_is_A = c <= 5
            if (att_is_A and r["winner"] == 0) or ((not att_is_A) and r["winner"] == 1):
                w2 += 1
        # --- derivation 3: from final score line (scores follow squads across halftime)
        # after halftime attack_score belongs to the second-half attackers.
        if n >= 7:
            # non-swap: second-half attackers = ids 6-10 -> ids1-5 = defend_score ; swap: second half attackers = ids 1-5 -> attack_score
            w3 = d if not s else a
        else:
            w3 = None
        # consistency of carrier vs. harness-logic side
        side_mismatch = 0
        for r in rounds:
            att_is_A = first_att_is_A if r["round"] <= 6 else (not first_att_is_A)
            c = r["carrier"]
            if 1 <= c <= 10 and ((c <= 5) != att_is_A):
                side_mismatch += 1
        rec.update(ok=True, n=n, w=w1, w_carrier=w2, w_final=w3, carrier_bad=carrier_bad,
                   side_mismatch=side_mismatch, a=a, d=d,
                   att_wins=sum(1 for r in rounds if r["winner"] == 0),
                   kills=M["kills"], sim=M["sim_seconds"], planted=M["planted_rounds"],
                   wh1=sum(1 for r in rounds if r["round"] <= 6 and ((first_att_is_A and r["winner"] == 0) or ((not first_att_is_A) and r["winner"] == 1))),
                   n1=sum(1 for r in rounds if r["round"] <= 6))
        if w1 != w2: issues.append((name, "round-derived %d != carrier-derived %d" % (w1, w2)))
        if w3 is not None and w1 != w3: issues.append((name, "round-derived %d != final-score-derived %d (score %d:%d)" % (w1, w3, a, d)))
        if side_mismatch: issues.append((name, "carrier side disagrees with harness side in %d rounds" % side_mismatch))
        if carrier_bad: issues.append((name, "carrier invalid in %d rounds" % carrier_bad))
        out.append(rec)
    return out, issues

def wdl(recs):
    W = D = L = 0
    for r in recs:
        if 2 * r["w"] > r["n"]: W += 1
        elif 2 * r["w"] == r["n"]: D += 1
        else: L += 1
    return W, D, L

def wdl_final(recs):
    # match result by final score line for squad ids 1-5
    W = D = L = 0
    for r in recs:
        x, y = (r["d"], r["a"]) if not r["swap"] else (r["a"], r["d"])
        if x > y: W += 1
        elif x == y: D += 1
        else: L += 1
    return W, D, L

def boot(recs, B=10000, seed=20261024):
    rng = random.Random(seed)
    ws = [r["w"] for r in recs]; ns = [r["n"] for r in recs]
    m = len(recs)
    vals = []
    for _ in range(B):
        sw = sn = 0
        for _ in range(m):
            i = rng.randrange(m)
            sw += ws[i]; sn += ns[i]
        vals.append(sw / sn)
    vals.sort()
    return vals[int(0.025 * B)], vals[int(0.975 * B) - 1]

def cluster_ci(recs):
    # ratio estimator, delta-method cluster-robust SE
    m = len(recs); W = sum(r["w"] for r in recs); N = sum(r["n"] for r in recs)
    p = W / N
    nbar = N / m
    s2 = sum((r["w"] - p * r["n"]) ** 2 for r in recs) / (m - 1)
    se = math.sqrt(m * s2) / N * math.sqrt(1)  # sqrt(m/(m-1)) folded into s2
    se = math.sqrt(s2 / m) / nbar
    # naive binomial SE
    se0 = math.sqrt(p * (1 - p) / N)
    return p, se, se0, (p - 0.5) / se

def fmt(recs, label):
    if not recs: return "%-28s (none)" % label
    W = sum(r["w"] for r in recs); N = sum(r["n"] for r in recs)
    lo, hi = boot(recs)
    p, se, se0, z = cluster_ci(recs)
    w, d, l = wdl(recs)
    return "%-28s m=%3d rounds=%4d wins=%4d share=%5.1f%%  boot95=[%5.1f,%5.1f]  clusterSE=%.1fpp (binom %.1fpp, deff=%.2f) z=%.2f  W-D-L=%d-%d-%d" % (
        label, len(recs), N, W, 100 * W / N, 100 * lo, 100 * hi, 100 * se, 100 * se0, (se / se0) ** 2, z, w, d, l)

if __name__ == "__main__":
    allrecs = {}
    for k, p in DIRS.items():
        recs, issues = load(p)
        allrecs[k] = recs
        print("=====", k, len(recs), "files; issues:", len(issues))
        for i in issues: print("   ISSUE", i)
        good = [r for r in recs if r.get("ok")]
        for lab, f in [("normal", lambda r: r["difficulty"] == "normal"), ("hard", lambda r: r["difficulty"] == "hard"), ("combined", lambda r: True)]:
            print(fmt([r for r in good if f(r)], k + " " + lab))
        for lab, f in [("normal-diff,ids1-5 att first", lambda r: not r["swap"]), ("s-files, ids6-10 att first", lambda r: r["swap"])]:
            for dn in ("normal", "hard", None):
                sub = [r for r in good if f(r) and (dn is None or r["difficulty"] == dn)]
                print(fmt(sub, "%s %s/%s" % (k, dn or "both", "noswap" if not sub or not sub[0]["swap"] else "swap")))
        print("W-D-L by final score lines (all):", wdl_final(good), " by round-derived:", wdl(good))
