# Independent recomputation of the bot metrics

Reviewer: a separate general-purpose Claude subagent, fresh context, read-only analysis in its own work directory. It received only the raw logs (seeds 31-36, 24 matches, 224 rounds), the harness source and the author's claim, and recomputed every number with its own code. Same model family as the author.

Subject: the 24 logs measured on the "before" build (`db3981e`) and on layout v3 before the last changes (mid exit widened, exit assignment). The table in `docs/design/RELAY_YARD_LAYOUT.md` for those seeds is this data. The final build was re-measured on new seeds; see the design document.

## What it confirmed

All claimed values reproduce (median round time, first kill, plant, carrier at site, attacker wins, clock, kill distance, first kill in a spawn zone, round and match counts). Integrity checks are clean: round lines equal the match `rounds` field in all 24 logs, no duplicated or missing rounds, kills and planted rounds match the match summaries, no byte-identical logs, `seed` and `difficulty` fields match file names. The one rounding nit: 62 of 67 is 92.5%, written as 92% in the first draft.

Supported strongly: later first kills (1.6 s to 5.6 s normal, 0.4 s to 5.3 s hard), shorter kill distances (29.6 m to 13.7 m normal, 41.4 m to 14.9 m hard), first kills out of spawn zones (92.5% to 0% normal, 100% to 0% hard), the normal-difficulty plant and carrier-at-site rates (6% to 66% and 6% to 70%), normal median round time (13.3 s to 23.4 s), and hard clock-outs (25% to 2%). The effect holds in every seed and in rounds 1 to 6 alone (like-for-like round mix).

## What it did not support

1. **Attacker win rate is not a balance measure here.** The squad that attacks in rounds 1 to 6 (actors 1-5) won all 12 "after" matches. It won round 1 in 12 of 12 and round 7, when it defends, in 11 of 12. That is a squad effect, not a role effect. Sign-test p about 0.0005 for 12 of 12. The pooled attacker win rate then depends on how many second-half rounds get played, and matches end early. Weighting the two halves equally gives about 43% (normal after) and 47% (hard after), against 19% and 28% before. Hypothesis, untested at the time: actors are processed in id order each tick, so the lower ids shoot first in a same-tick trade. Logged as finding F2 and tested in the next measurement by running every seed with both squads attacking first.
2. **Hard difficulty plant 0% to 2%** is one round (seed 36). The supported statement is that hard bots still essentially never plant. The hard median round time (15.1 s to 16.3 s, difference +1.2 s, 95% interval -2.1 to +5.7) is unchanged, although the distribution changed: mean 36.6 s to 19.6 s and 25% of rounds hitting the 100 s cap down to 2%.
3. **Normal clock-out 1% to 2%** is one round against one round.
4. **Every attacker win in "after" is by eliminating the defenders** (31 of 31 normal, 31 of 31 hard). "Relay device detonated" occurs in none of the 224 rounds. Ten of the 31 normal-after plants were defused.

## Intervals (95%, resampling matches, 6 per cell)

| Cell | Plant | Attacker win |
| --- | --- | --- |
| normal before | 4/67 = 6.0% (match bootstrap 2.9 to 9.1; t on match rates 1.1 to 10.8) | 19.4% (11.8 to 29.4) |
| normal after | 31/47 = 66.0% (57.8 to 72.9; 55.1 to 76.6) | 66.0% (56.0 to 77.3) |
| hard before | 0/59 (exact upper bound 6.1% by round) | 32.2% (18.0 to 52.9) |
| hard after | 1/51 = 2.0% (0 to 6.5) | 60.8% (49.1 to 74.5) |

With 6 matches per cell the percentile bootstrap is too narrow; read the t intervals as the conservative bound. Plant-rate difference on normal: +60 points (51 to 68). On hard: +2 points (0 to 6.5).

## Other observations kept

- Fewer rounds per match after the change (11.2 to 7.8 normal), because one squad reaches 7 wins sooner. Rounds 8 to 12 (the long-sightline rifle rounds) were 37% of before-normal and 11% of after-normal; the like-for-like rounds 1-6 check removes that confound.
- Hard before had two kinds of clock-out: 11 spawn-snipe standoffs (first kill within 1.1 s, survivors idle for about 100 s) and 4 round-7 stalls with no engagement after the first kills.
- `carrier_died_at` is almost never recorded (11 of 224 rounds). Unused in any claim.
- Nothing in the logs records the map version; before and after rest on the archive names.
- Recommended: at least 20 to 30 matches per cell, both squads starting as attackers, fixed match length or rounds 1 to 6 only, role win rates per half.
