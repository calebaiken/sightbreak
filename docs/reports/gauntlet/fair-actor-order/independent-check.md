# Independent check: recomputing the squad shares from the raw logs

Reviewer: a general-purpose Claude subagent, fresh context, read-only, with no access to `scripts/squad_balance.py` or to the author's results. Same model family as the builder, so this is a check of the arithmetic and of the claims, **not** independent human acceptance. The reviewer wrote its own code and was given only the raw per-match logs and the rules of the harness (halftime after round 6, `winner` 0 = attackers, `swap_start`).

Round 1 covered sets A, B and C (seeds 41-46). Round 2 covered the later sets D and E and the pooled result (see the end of this file). The report below is the reviewer's, copied as received and lightly reformatted; the numbers and judgments are its own.

## Round 1: sets A, B, C

**Method.** Parsed the raw lines. Share = rounds won by ids 1-5 (attackers if (round <= 6) != swap_start, otherwise defenders) divided by rounds played. Interval: percentile bootstrap resampling whole matches within each cell, 10,000 resamples, seed 20240607.

| Set | Diff | Matches | Rounds | 1-5 wins | Share | 95% CI |
|---|---|---|---|---|---|---|
| A | normal | 12 | 114 | 81 | .711 | .621-.806 |
| A | hard | 12 | 123 | 76 | .618 | .528-.716 |
| A | all | 24 | 237 | 157 | .662 | .594-.735 |
| B | normal | 12 | 130 | 79 | .608 | .546-.689 |
| B | hard | 12 | 122 | 74 | .607 | .508-.707 |
| B | all | 24 | 252 | 153 | .607 | .548-.671 |
| C | normal | 12 | 140 | 67 | .479 | .429-.532 |
| C | hard | 12 | 121 | 57 | .471 | .357-.596 |
| C | all | 24 | 261 | 124 | .475 | .414-.537 |

By start order (both difficulties, 12 matches each):

| Set | swap_start false | swap_start true |
|---|---|---|
| A | .645 (.554-.741) | .681 (.584-.790) |
| B | .541 (.469-.602) | .684 (.597-.785) |
| C | .455 (.385-.539) | .496 (.403-.589) |

**Checks.** All 72 files pass.

- Each has exactly one MATCH line, and `rounds` equals the ROUND line count (750 total).
- Round counts run 7-12, numbered 1..n in order.
- Filename difficulty, seed and swap match the JSON.
- Every `phase` is `match_over`.
- There are no error or warning lines; the only other content is the Godot banner.
- No two files are byte-identical, and nothing looks truncated.

Odd things:

- `attack_score` and `defend_score` are not attacker and defender round counts. They are squad totals that swap sides at halftime. This reading matches the reviewer's round-derived totals in 72 of 72 matches, which independently validates its side mapping. Reading them as first-half sides matches only 20 of 72.
- Matches are first-to-7. 41 ended before round 12, 11 ended at 12 with a 7+ score, and 20 ended 6-6 at 12 rounds.
- Attackers win only 24%, 18% and 26% of rounds (A, B, C), and the bomb was planted in only 43 of 750 rounds.
- Ids 1-5 win 92%, 90% and 71% of rounds as defenders (A, B, C). They win 40%, 27% and 23% as attackers.
- About 80% of rounds have a first kill under 2 s, including kills at 42 m at t=0.3 s. Rounds are largely decided by spawn-fight order.
- A hard-44s R8 and A hard-45s R8 are identical round records (a 1.8 s spawn-kill). Probably a coincidence of a deterministic opening.
- Matches are lopsided (for example C hard-42s is 7-0, B hard-43 is 7-1). Per-match share spread is about 1.3x binomial, so the match-level bootstrap is warranted.

**Critique.**

- **A has a clear squad effect: supported.** The share is 66.2% and the interval excludes 50, as do both orders. Ids 1-5 won 17 matches, drew 5 and lost 2.
- **B "reduces but does not remove": half supported.**
  - "Does not remove" holds. B is 60.7% (54.8-67.1) and 1-5 won 14 matches, drew 9 and lost 1.
  - "Reduces" is not supported. A minus B is +5.6 points, with a CI of -3.5 to +14.6.
  - B's effect also depends on start order. The swap=false interval (.469-.602) includes 50, while swap=true is .684.
  - Even with equal squads, first-to-7 plus the defender edge shifts the order split by about +-3 points (the reviewer's simulation: .47 and .53). The B gap of 14 points is bigger than that, but the intervals overlap.
- **C "no detectable squad effect": too weak to claim as stated.**
  - C is 47.5% (41.4-53.7). Not rejecting 50 here is absence of evidence, not evidence of absence.
  - The interval allows a 6-10 advantage of up to 8.6 points, so a 5-point residual cannot be excluded in that direction. The upper end (+3.7) only just excludes a +5 residual for ids 1-5.
  - Ids 1-5 lost 12 matches and won 6 in C, so the point estimate leans against them.
  - The hard cell (35.7-59.6, 24 points wide) says nothing. The normal cell alone is tighter (42.9-53.2).
  - What is supported: C is lower than B by 13.3 points (CI 4.7 to 22.0), and A is above C.
- **The share confounds squad with side exposure.** With defenders winning about 80% of rounds, any build that changes side balance moves the share. C also shifts the attacker win rate. A "habits symmetric" change could therefore move this metric without touching any squad effect.
- **Sample size.** The bootstrap SE is about 0.031 per 24 matches, so a 5-point residual needs SE of about 0.018 for 80% power. That is about 72-94 matches per build (roughly 800-1000 rounds), 3-4x the current sample. Showing the CI half-width is at most 5 points needs about 36-46 matches. Per-difficulty claims need those numbers within each difficulty. Pair up swapped and unswapped matches, and report match results alongside round share.

**What the author changed because of this review.** The README no longer says the shuffle "reduces" the effect, no longer says C shows "no detectable squad effect" from 24 matches, and the commit message of the shuffle commit was reworded. The sample-size estimate set the size of the confirmation run (72 normal matches of the final code, sets C, D and E).

## Round 2: sets D and E, and the pooled result

Asked to recompute the two later sets and the pooled figure with its own code. Same method: whole-match bootstrap within each cell, 10,000 resamples, seed 20240607, percentile interval.

| Cell | Matches | Rounds | Share | 95% CI |
|---|---|---|---|---|
| D normal | 12 | 138 | .493 | .438-.543 |
| D hard | 12 | 115 | .565 | .426-.699 |
| D all | 24 | 253 | .526 | .456-.594 |
| E normal | 48 | 517 | .507 | .462-.553 |
| C+D+E normal | 72 | 795 | .499 | .468-.531 |
| C+D+E hard | 24 | 236 | .517 | .426-.610 |

Stratifying the C+D+E normal resampling by start order gives .469-.530.

**Checks on the 72 new files: all pass.** One MATCH line each, `rounds` equal to the ROUND line count, round counts 1-12 numbered in order, filename difficulty, seed and swap match the JSON, every phase `match_over`, score lines agree with the round totals under the halftime-swap reading, no error lines, no identical files, no repeated round records, seeds disjoint from C and from each other. Attackers win 26-29% of rounds in C, D and E. Plants: 14, 17 and 52 per set (E is about 10% of rounds).

**Order split, C+D+E normal.** swap_start false: .465 (.424-.504). swap_start true: .535 (.488-.584). The reviewer reads the 7-point gap as the first-to-7 plus defender-edge artifact it simulated earlier (about +-3 points per order with equal squads), not as a squad effect.

**Match results for ids 1-5, C+D+E normal:** 23 won, 23 drawn (6-6), 26 lost.

**Does 72 normal matches support "the pooled interval excludes a squad residual of 5 points in either direction"?** Yes for normal, as a statement about the pooled average: the interval .468-.531 sits inside .45-.55 and the standard error is 0.016. Caveats, in the reviewer's words:

- The sentence does not hold for hard. Pooled hard is .426-.610, which is useless at 24 matches. The D hard point estimate was +6.5 points.
- It says nothing about residuals that depend on start order or on side.
- It depends on C, D and E being the same code, which the logs cannot confirm. The extra sets were added after C's interval looked inconclusive.

**How the author answers the last two caveats.** Same code: the working tree under test for C, D and E has the same `game/` content as the final commit (`git diff` between the tree and the commit is empty for `game/` and `scripts/validate.sh`); the start state of each run is in `data/source-states.txt`, where the diff hashes recorded when runs B and C started are reproduced exactly from the final commits. The logs themselves carry no commit stamp. Added sets: yes, D and E were added because this reviewer called C too weak, and their size (72 normal matches in total) came from the reviewer's power estimate before the new data existed. All sets are reported, none dropped. A reader who discounts C for being fitted on the seeds that exposed the cause can use D+E alone: normal 330 of 655 rounds, 50.4%.
