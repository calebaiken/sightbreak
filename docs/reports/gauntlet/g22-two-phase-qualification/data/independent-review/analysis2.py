import sys, json, random, math, collections
sys.path.insert(0, "/tmp/claude-0/-home-user-sightbreak/dfa39eb1-8f79-5aa4-a243-6ac88bc445cd/scratchpad/review-g22")
import parse as P

A, _ = P.load(P.DIRS["after"]); B, _ = P.load(P.DIRS["before"]); R, _ = P.load(P.DIRS["reverse"])

def rounds_of(rec):
    out = []
    first_att_A = not rec["swap"]
    for r in rec["rounds"]:
        att_is_A = first_att_A if r["round"] <= 6 else (not first_att_A)
        a_win = (att_is_A and r["winner"] == 0) or ((not att_is_A) and r["winner"] == 1)
        out.append(dict(round=r["round"], att_is_A=att_is_A, att_won=(r["winner"] == 0), A_won=a_win,
                        reason=r["reason"], planted=r["planted_at"] >= 0))
    return out

def boot_stat(clusters, stat, B=10000, seed=7):
    rng = random.Random(seed); m = len(clusters); vals = []
    for _ in range(B):
        s = [clusters[rng.randrange(m)] for _ in range(m)]
        v = stat(s)
        if v is not None: vals.append(v)
    vals.sort(); n = len(vals)
    return vals[int(.025 * n)], vals[int(.975 * n) - 1]

def describe(name, recs):
    rr = [rounds_of(r) for r in recs]
    flat = [x for m in rr for x in m]
    n = len(flat)
    att = sum(x["att_won"] for x in flat)
    print("%s: attacker win rate %d/%d = %.1f%%" % (name, att, n, 100 * att / n))
    for lo, hi, lab in [(1, 6, "rounds1-6"), (7, 12, "rounds7-12")]:
        f = [x for x in flat if lo <= x["round"] <= hi]
        print("   %s attacker wins %d/%d = %.1f%%" % (lab, sum(x["att_won"] for x in f), len(f), 100 * sum(x["att_won"] for x in f) / len(f)))
    # round-by-round attacker win rate
    by = collections.defaultdict(lambda: [0, 0])
    for x in flat:
        by[x["round"]][0] += x["att_won"]; by[x["round"]][1] += 1
    print("   attacker win by round:", " ".join("%d:%d/%d" % (k, by[k][0], by[k][1]) for k in sorted(by)))
    # reasons
    c = collections.Counter(x["reason"] for x in flat)
    print("   reasons:", dict(c))
    # role x squad
    for sq, lab in [(True, "ids1-5 attacking"), (False, "ids6-10 attacking")]:
        f = [x for x in flat if x["att_is_A"] == sq]
        w = sum(x["att_won"] for x in f)
        print("   %s: attackers won %d/%d = %.1f%%" % (lab, w, len(f), 100 * w / len(f)))
    # role-adjusted squad contrast: P(att wins | ids1-5 attack) - P(att wins | ids6-10 attack)
    def contrast(cl):
        f = [x for m in cl for x in m]
        a = [x for x in f if x["att_is_A"]]; b = [x for x in f if not x["att_is_A"]]
        return sum(x["att_won"] for x in a) / len(a) - sum(x["att_won"] for x in b) / len(b)
    est = contrast(rr)
    lo, hi = boot_stat(rr, contrast)
    print("   role-adjusted contrast (att win | ids1-5 att) - (att win | ids6-10 att) = %+.1f pp  boot95=[%+.1f, %+.1f]  (>0 => ids1-5 stronger)" % (100 * est, 100 * lo, 100 * hi))
    # first-attacker squad share (swap-invariant)
    def first_att(cl):
        # cl is list of per-match round lists; need swap flag: encode via att_is_A at round1
        w = n_ = 0
        for m in cl:
            for x in m:
                fa_is_A = m[0]["att_is_A"]
                a_won = x["A_won"]
                w += (a_won if fa_is_A else (not a_won)); n_ += 1
        return w / n_
    est = first_att(rr); lo, hi = boot_stat(rr, first_att)
    print("   share of rounds won by the squad that attacked first = %.1f%%  boot95=[%.1f, %.1f]" % (100 * est, 100 * lo, 100 * hi))
    # ids1-5 share, cluster by seed (sensitivity): clusters = all matches sharing a seed
    byseed = collections.defaultdict(list)
    for r in recs: byseed[r["seed"]].append(r)
    cl = list(byseed.values())
    def share(c):
        w = sum(r["w"] for g in c for r in g); n_ = sum(r["n"] for g in c for r in g); return w / n_
    lo, hi = boot_stat(cl, share)
    print("   ids1-5 share, clustered by SEED (%d clusters): %.1f%% boot95=[%.1f, %.1f]" % (len(cl), 100 * share(cl), 100 * lo, 100 * hi))
    # noswap vs swap difference
    ns = [r for r in recs if not r["swap"]]; sw = [r for r in recs if r["swap"]]
    if ns and sw:
        d_est = share([ns]) - share([sw])
        rng = random.Random(11); vals = []
        for _ in range(10000):
            a = [ns[rng.randrange(len(ns))] for _ in ns]; b = [sw[rng.randrange(len(sw))] for _ in sw]
            vals.append(share([a]) - share([b]))
        vals.sort()
        print("   ids1-5 share noswap - swap = %+.1f pp boot95=[%+.1f, %+.1f]" % (100 * d_est, 100 * vals[250], 100 * vals[9749]))
    # round-count / draws summary
    cnt = collections.Counter(r["n"] for r in recs)
    print("   rounds/match distribution:", dict(sorted(cnt.items())), " max sim_seconds=%.0f" % max(r["sim"] for r in recs))
    print("   match scores for ids1-5 (w:l) distribution of margin:", dict(sorted(collections.Counter(2 * r["w"] - r["n"] for r in recs).items())))

describe("AFTER all", A)
describe("AFTER normal", [r for r in A if r["difficulty"] == "normal"])
describe("AFTER hard", [r for r in A if r["difficulty"] == "hard"])
describe("BEFORE all", B)
describe("REVERSE", R)

# matched seeds 41-46 after vs before
print()
A46 = [r for r in A if r["seed"] <= 46]
print("AFTER restricted to seeds 41-46 (same seeds as BEFORE):")
print(P.fmt(A46, "after seeds41-46 all"))
print(P.fmt([r for r in A if r["seed"] > 46], "after seeds61-84 all"))
print(P.fmt(B, "before seeds41-46 all"))
# paired by (diff,seed,swap)
bkey = {(r["difficulty"], r["seed"], r["swap"]): r for r in B}
d = []
for r in A46:
    b = bkey[(r["difficulty"], r["seed"], r["swap"])]
    d.append((r["w"] / r["n"]) - (b["w"] / b["n"]))
print("paired per-match share difference after-before: mean %+.1f pp, sd %.1f, n=%d, se %.1f" % (100 * sum(d) / len(d), 100 * (sum((x - sum(d) / len(d)) ** 2 for x in d) / (len(d) - 1)) ** .5, len(d), 100 * (sum((x - sum(d) / len(d)) ** 2 for x in d) / (len(d) - 1)) ** .5 / math.sqrt(len(d))))
# duplicates check
sig = collections.Counter()
for r in A + B + R:
    sig[tuple((x["winner"], round(x["live_time"], 2)) for x in r["rounds"])] += 1
print("duplicate round-sequences across all logs:", [k for k, v in sig.items() if v > 1][:3], sum(1 for v in sig.values() if v > 1))
# difference before vs after, bootstrapped (independent samples; shares)
rng = random.Random(5); vals = []
for _ in range(10000):
    a = [A[rng.randrange(len(A))] for _ in A]; b = [B[rng.randrange(len(B))] for _ in B]
    wa = sum(x["w"] for x in a) / sum(x["n"] for x in a); wb = sum(x["w"] for x in b) / sum(x["n"] for x in b)
    vals.append(wb - wa)
vals.sort()
print("before - after share difference: boot95 = [%+.1f, %+.1f] pp" % (100 * vals[250], 100 * vals[9749]))
